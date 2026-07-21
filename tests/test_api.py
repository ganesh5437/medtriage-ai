"""
test_api.py — API integration tests via httpx TestClient.
Covers required tests 9 and 10 (session persisted to DB, health endpoint),
plus test 8 (disclaimer always present) at the API layer.
"""
import os
import sys

# Use a throwaway SQLite DB for tests so we never touch dev data
os.environ["DATABASE_URL"] = "sqlite:///./test_medtriage.db"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal, Message, ChatSession, init_db

# TestClient() without a `with` block does not fire FastAPI startup events,
# so we create tables explicitly here (init_db is idempotent).
init_db()

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_disclaimer_always_present():
    resp = client.post("/chat", json={"message": "I have a fever and cough"})
    assert resp.status_code == 200
    body = resp.json()
    assert "AI-generated" in body["disclaimer"]


def test_session_persisted_to_db():
    resp = client.post("/chat", json={"message": "I have joint pain for 2 days"})
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    db = SessionLocal()
    try:
        session = db.get(ChatSession, session_id)
        assert session is not None
        messages = db.query(Message).filter(Message.session_id == session_id).all()
        assert len(messages) >= 2  # patient turn + ai turn
    finally:
        db.close()


def test_register_and_login():
    resp = client.post("/auth/register", json={
        "name": "Test Patient", "email": "test_patient@example.com",
        "password": "secret123", "role": "patient",
    })
    assert resp.status_code == 200
    assert resp.json()["role"] == "patient"

    resp = client.post("/auth/login", json={"email": "test_patient@example.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
