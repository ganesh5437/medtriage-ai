"""
schemas.py — Pydantic request/response models.
symptom_extraction_node output is validated against SymptomExtraction (gap-fix:
structured LLM output validation).
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = None  # None -> server creates a new session
    message: str = Field(min_length=1, max_length=4000)


class SymptomExtraction(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    duration: str | None = None
    severity: int | None = Field(default=None, ge=0, le=10)
    location: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    is_emergency: bool
    extracted: SymptomExtraction
    disclaimer: str = "⚠ AI-generated. Not reviewed by a licensed clinician. Not a diagnosis."


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=6)
    role: str  # "patient" | "clinician"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
