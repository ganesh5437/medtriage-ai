"""
db.py — SQLAlchemy 2.0 models + session dependency.
SQLite by default (zero setup). Set DATABASE_URL to switch to Postgres.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, String, Text, Integer, DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, sessionmaker, Session,
)

from app.config import settings


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- users (gap-fix: auth register) ---
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # patient | clinician
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String)
    dob: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Clinician(Base):
    __tablename__ = "clinicians"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String)
    license_no: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ChatSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str | None] = mapped_column(String, ForeignKey("patients.id"), nullable=True)
    clinician_id: Mapped[str | None] = mapped_column(String, ForeignKey("clinicians.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")  # active|pending|reviewed|emergency
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    role: Mapped[str] = mapped_column(String)  # patient|ai
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Symptom(Base):
    __tablename__ = "symptoms"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    name: Mapped[str] = mapped_column(String)
    onset: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class LabReport(Base):
    __tablename__ = "lab_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    differential_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendations_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    disclaimer_text: Mapped[str] = mapped_column(
        Text, default="⚠ AI-generated. Not reviewed by a licensed clinician. Not a diagnosis."
    )
    status: Mapped[str] = mapped_column(String, default="pending")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    reviewed_by: Mapped[str | None] = mapped_column(String, ForeignKey("clinicians.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    trigger_reason: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# --- engine / session setup ---
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
