"""
llm.py — single interface to the LLM. Rest of the app NEVER imports
anthropic/openai directly, only this module.

Phase 1: mock mode only (rule-based, zero API key needed).
Phase 2+ will add real anthropic/openai calls behind the same functions,
with automatic fallback to mock on any API failure (error-handling spec).
"""
import re
import logging

from app.config import settings
from app.schemas import SymptomExtraction

logger = logging.getLogger("medtriage.llm")

# --- Emergency keyword patterns (fast path, runs before any LLM call) ---
EMERGENCY_PATTERNS = [
    r"\bchest pain\b",
    r"\bcan'?t breathe\b",
    r"\bcannot breathe\b",
    r"\bcan'?t catch (my )?breath\b",
    r"\bsevere bleeding\b",
    r"\bwant to die\b",
    r"\bkill myself\b",
    r"\bsuicid\w*\b",
    r"\bcan'?t take this anymore\b",
    r"\bstroke\b",
    r"\bface (is )?drooping\b",
    r"\bslurred speech\b",
]

# things that LOOK like emergencies but aren't (avoid false positives)
SAFE_OVERRIDE_PATTERNS = [
    r"\bchest cold\b",
    r"\bchest of drawers\b",
]

EMERGENCY_NUMBERS = {"india": "108", "us": "911", "eu": "112"}


def check_emergency(text: str) -> tuple[bool, str | None]:
    """Fast keyword-pattern emergency gate. Returns (is_emergency, reason)."""
    lowered = text.lower()

    for safe in SAFE_OVERRIDE_PATTERNS:
        if re.search(safe, lowered):
            # a safe phrase matched — still check other real patterns aren't ALSO present
            remaining = re.sub(safe, "", lowered)
            for pat in EMERGENCY_PATTERNS:
                if re.search(pat, remaining):
                    return True, pat
            return False, None

    for pat in EMERGENCY_PATTERNS:
        if re.search(pat, lowered):
            return True, pat

    return False, None


def emergency_reply() -> str:
    return (
        "🚨 EMERGENCY DETECTED. Please contact emergency services immediately:\n"
        f"India: {EMERGENCY_NUMBERS['india']} | US: {EMERGENCY_NUMBERS['us']} | EU: {EMERGENCY_NUMBERS['eu']}\n"
        "This is not a diagnosis. Please seek immediate in-person medical help."
    )


# --- Mock symptom extraction (rule-based, zero API key) ---
_KNOWN_SYMPTOMS = [
    "fever", "cough", "headache", "nausea", "chest tightness", "abdominal pain",
    "rash", "joint pain", "fatigue", "weakness", "dizziness",
    "shortness of breath", "sore throat", "back pain", "chills",
    "vomiting", "diarrhea", "blurred vision",
]


def _mock_extract(text: str) -> SymptomExtraction:
    lowered = text.lower()
    found = [s for s in _KNOWN_SYMPTOMS if s in lowered]

    duration = None
    dur_match = re.search(r"(\d+)\s*(day|days|week|weeks|hour|hours)", lowered)
    if dur_match:
        duration = dur_match.group(0)

    severity = None
    sev_match = re.search(r"(\d{1,2})\s*/\s*10", lowered)
    if sev_match:
        severity = min(int(sev_match.group(1)), 10)

    return SymptomExtraction(symptoms=found, duration=duration, severity=severity, location=None)


def extract_symptoms(text: str) -> SymptomExtraction:
    """
    Structured symptom extraction. Phase 1 always uses mock rules;
    Phase 2+ routes through real LLM when LLM_PROVIDER != mock, with
    automatic fallback to this mock function on any API failure.
    """
    try:
        if settings.LLM_PROVIDER == "mock":
            return _mock_extract(text)
        # Phase 2+ real LLM call goes here. Falls back to mock on failure.
        return _mock_extract(text)
    except Exception as exc:  # never let extraction crash the turn
        logger.error("LLM extraction failed, falling back to mock: %s", exc)
        return _mock_extract(text)


def generate_reply(text: str, extracted: SymptomExtraction) -> str:
    """Simple mock conversational reply based on extraction."""
    if extracted.symptoms:
        symptom_list = ", ".join(extracted.symptoms)
        parts = [f"I've noted the following symptoms: {symptom_list}."]
        if extracted.duration:
            parts.append(f"Duration noted as {extracted.duration}.")
        if extracted.severity is not None:
            parts.append(f"Severity noted as {extracted.severity}/10.")
        parts.append("Could you tell me more — any other symptoms, or anything that makes it better or worse?")
        return " ".join(parts)
    return "Thanks for sharing that. Could you describe your main symptom, how long it's lasted, and how severe it feels (1-10)?"
