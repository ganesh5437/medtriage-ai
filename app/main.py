"""
main.py — FastAPI app entrypoint. Phase 1 routes: /health, /chat,
/auth/register, /auth/login. Rest of the endpoints (upload-lab, voice,
report, sessions) land in later phases.
"""
import logging
import io

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import init_db, get_db, ChatSession, Message, User, LabReport, Report, Symptom
from app.schemas import (
    ChatRequest, ChatResponse, HealthResponse, SymptomExtraction,
    RegisterRequest, LoginRequest, TokenResponse, LabUploadResponse, VoiceResponse,
)
from app.graph import run_turn
from app.security import hash_password, verify_password, create_access_token, sanitize_text
from app.rag import load_knowledge_base
from app.labs import parse_lab_report
from app.voice import transcribe_audio
from app.reports import compile_report, generate_pdf

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
            for symptom_name in extracted.symptoms:
                db.add(Symptom(
                    session_id=session_id,
                    name=symptom_name,
                    duration=extracted.duration,
                    severity=extracted.severity,
                ))
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


# Max audio file size — reuse same limit as lab uploads (gap-fix: file validation)
_MAX_AUDIO_MB = settings.MAX_UPLOAD_MB * 4  # audio files run bigger than lab docs


@app.post("/voice", response_model=VoiceResponse)
async def voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()

        max_bytes = _MAX_AUDIO_MB * 1024 * 1024
        if len(audio_bytes) > max_bytes:
            return VoiceResponse(
                success=False,
                text="",
                error=f"Audio file too large. Max size is {_MAX_AUDIO_MB}MB.",
            )

        if not audio_bytes:
            return VoiceResponse(success=False, text="", error="Empty audio file received.")

        result = transcribe_audio(audio_bytes, file.filename or "audio.webm")

        return VoiceResponse(
            success=result["success"],
            text=result["text"],
            error=result["error"],
        )

    except Exception as exc:
        logger.error("Unhandled error in /voice: %s", exc)
        # gap-fix: voice failure falls back to text input, never crashes
        return VoiceResponse(
            success=False,
            text="",
            error="Voice unavailable. Please type your message.",
        )


@app.get("/report/{session_id}")
def get_report(session_id: str, db: Session = Depends(get_db)):
    report = compile_report(db, session_id)
    if "error" in report and report["error"] == "Session not found":
        raise HTTPException(status_code=404, detail="Session not found")
    return report


@app.get("/report/{session_id}/pdf")
def get_report_pdf(session_id: str, db: Session = Depends(get_db)):
    report = compile_report(db, session_id)
    if "error" in report and report["error"] == "Session not found":
        raise HTTPException(status_code=404, detail="Session not found")

    pdf_bytes = generate_pdf(report)

    # Persist the generated report (best-effort, never blocks download)
    try:
        existing = db.query(Report).filter(Report.session_id == session_id).first()
        if not existing:
            db.add(Report(
                session_id=session_id,
                differential_json=report.get("differential", {}),
                recommendations_json={"lab_findings": report.get("lab_findings", {})},
                status="pending",
            ))
            db.commit()
    except Exception as db_exc:
        logger.error("DB write failed on /report/pdf: %s", db_exc)
        db.rollback()

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{session_id}.pdf"},
    )


@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.started_at.desc()).all()
    result = []
    for s in sessions:
        symptom_names = [sym.name for sym in db.query(Symptom).filter(Symptom.session_id == s.id).all()]
        result.append({
            "session_id": s.id,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "symptoms_summary": symptom_names,
        })
    return {"sessions": result}


@app.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at)
        .all()
    )
    return {
        "session_id": session_id,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in messages
        ],
    }