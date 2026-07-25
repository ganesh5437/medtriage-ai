"""
main.py — FastAPI app entrypoint. Phase 1 routes: /health, /chat,
/auth/register, /auth/login. Rest of the endpoints (upload-lab, voice,
report, sessions) land in later phases.
"""
import logging

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.db import init_db, get_db, ChatSession, Message, User, LabReport
from app.schemas import (
    ChatRequest, ChatResponse, HealthResponse, SymptomExtraction,
    RegisterRequest, LoginRequest, TokenResponse, LabUploadResponse,
)
from app.graph import run_turn
from app.security import hash_password, verify_password, create_access_token, sanitize_text
from app.rag import load_knowledge_base
from app.labs import parse_lab_report

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("medtriage.main")

app = FastAPI(title="MedTriage AI", version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    load_knowledge_base()
    logger.info("MedTriage AI started. LLM_PROVIDER=%s", settings.LLM_PROVIDER)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version=settings.APP_VERSION, llm_provider=settings.LLM_PROVIDER)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        clean_message = sanitize_text(payload.message)

        session_id = payload.session_id
        if not session_id:
            session = ChatSession(status="active")
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id

        result = run_turn(clean_message)
        is_emergency = bool(result.get("is_emergency"))
        extracted: SymptomExtraction = result.get("extracted") or SymptomExtraction()
        reply = result.get("reply", "")

        # persist — never let a DB failure surface to the patient
        try:
            db.add(Message(session_id=session_id, role="patient", content=clean_message))
            db.add(Message(session_id=session_id, role="ai", content=reply))
            if is_emergency:
                from app.db import EmergencyEvent
                db.add(EmergencyEvent(session_id=session_id, trigger_reason=result.get("emergency_reason") or "unknown"))
                session = db.get(ChatSession, session_id)
                if session:
                    session.status = "emergency"
            db.commit()
        except Exception as db_exc:
            logger.error("DB write failed on /chat: %s", db_exc)
            db.rollback()

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            is_emergency=is_emergency,
            extracted=extracted,
            differential=result.get("differential", []),
        )
    except Exception as exc:
        logger.error("Unhandled error in /chat: %s", exc)
        raise HTTPException(status_code=500, detail="Something went wrong processing your message.")


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.role not in ("patient", "clinician"):
        raise HTTPException(status_code=400, detail="role must be 'patient' or 'clinician'")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, role=user.role)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, role=user.role)


# Allowed lab file types (gap-fix: file upload validation — MIME by content, not just extension)
_ALLOWED_LAB_MIME_PREFIXES = ("application/pdf", "image/jpeg", "image/png")


@app.post("/upload-lab", response_model=LabUploadResponse)
async def upload_lab(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # Validate session exists
        session = db.get(ChatSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Read file bytes
        file_bytes = await file.read()

        # gap-fix: max file size 5MB
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size is {settings.MAX_UPLOAD_MB}MB.",
            )

        # gap-fix: whitelist actual MIME type by inspecting file bytes, not just extension
        detected_mime = file.content_type or ""
        is_pdf_magic = file_bytes[:4] == b"%PDF"
        is_jpeg_magic = file_bytes[:3] == b"\xff\xd8\xff"
        is_png_magic = file_bytes[:8] == b"\x89PNG\r\n\x1a\n"

        if not (is_pdf_magic or is_jpeg_magic or is_png_magic):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only PDF, JPG, and PNG lab reports are accepted.",
            )

        # Parse the lab report — never raises (error handling spec)
        result = parse_lab_report(file_bytes, file.filename or "upload")

        # Persist — never let a DB failure block the response
        try:
            db.add(LabReport(
                session_id=session_id,
                file_url=file.filename,
                parsed_json=result,
            ))
            db.commit()
        except Exception as db_exc:
            logger.error("DB write failed on /upload-lab: %s", db_exc)
            db.rollback()

        return LabUploadResponse(
            session_id=session_id,
            parsed=result["parsed"],
            values=result["values"],
            error=result["error"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unhandled error in /upload-lab: %s", exc)
        # gap-fix: lab parse failure never blocks the rest of the session
        return LabUploadResponse(
            session_id=session_id,
            parsed=False,
            values={},
            error="Lab report could not be processed. You can continue the session without it.",
        )
