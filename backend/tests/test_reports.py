"""
test_reports.py — Phase 5 tests for report synthesis + PDF generation.
"""
from app.reports import generate_pdf, DISCLAIMER


def test_generate_pdf_produces_valid_pdf_bytes():
    report = {
        "chief_complaint": "fever and cough",
        "symptoms": ["fever", "cough"],
        "lab_findings": {"Hemoglobin": {"value": 13.5, "unit": "g/dL"}},
        "referral_suggestion": "See a clinician.",
        "disclaimer": DISCLAIMER,
    }
    pdf_bytes = generate_pdf(report)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_handles_error_report_gracefully():
    report = {"error": "Session not found"}
    pdf_bytes = generate_pdf(report)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_handles_empty_report():
    pdf_bytes = generate_pdf({})
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"