"""
test_graph.py — the 10 required tests (spec doc, page 8).
Phase 1 covers tests 1-6 fully (graph logic doesn't need RAG/DB yet).
Tests 7-10 are stubbed with a Phase-1-appropriate check and get
completed in later phases once rag.py / db persistence via API exist.
"""
from app.graph import run_turn


def test_normal_symptom_extraction():
    result = run_turn("I have fever and headache for 3 days, severity 7/10")
    assert result["is_emergency"] is False
    assert "fever" in result["extracted"].symptoms
    assert result["extracted"].severity == 7


def test_emergency_chest_pain():
    result = run_turn("severe chest pain")
    assert result["is_emergency"] is True
    assert "108" in result["reply"] or "911" in result["reply"]


def test_emergency_breathing():
    result = run_turn("I cannot breathe")
    assert result["is_emergency"] is True


def test_emergency_suicidal():
    result = run_turn("I want to die, I can't take this anymore")
    assert result["is_emergency"] is True


def test_emergency_casual_phrasing():
    result = run_turn("hey I literally cannot breathe lol")
    assert result["is_emergency"] is True


def test_no_false_positive_chest_cold():
    result = run_turn("I have a chest cold and mild cough")
    assert result["is_emergency"] is False


def test_disclaimer_present_in_response_model():
    # Phase 1: disclaimer lives on ChatResponse.disclaimer (checked at API level in test_api.py).
    # Graph-level check: a normal (non-emergency) turn always returns a reply.
    result = run_turn("I have a mild headache")
    assert result["is_emergency"] is False
    assert result["reply"]
