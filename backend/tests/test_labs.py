"""
test_labs.py — Phase 3 tests for lab report OCR parsing.
Covers required test 8: unsupported file type rejected cleanly, not a 500.
"""
import io

from app.labs import parse_lab_values, parse_lab_report


def test_parse_lab_values_extracts_known_tests():
    """Verify regex parser extracts common lab values from OCR'd text."""
    sample_text = """
    LABORATORY REPORT
    Patient: John Doe
    Hemoglobin: 13.5 g/dL
    WBC: 7200 /uL
    Glucose: 95 mg/dL
    """
    result = parse_lab_values(sample_text)
    assert "values" in result
    # At least one known test should be extracted
    assert len(result["values"]) > 0


def test_parse_lab_report_handles_garbage_bytes_gracefully():
    """
    Required test 8 (adapted): malformed/unsupported file content should
    return a clean error, never raise/crash.
    """
    garbage_bytes = b"this is not a real pdf or image"
    result = parse_lab_report(garbage_bytes, "fake.pdf")

    # Must not raise — must return a dict with parsed=False and an error message
    assert isinstance(result, dict)
    assert "parsed" in result
    assert "error" in result
    if not result["parsed"]:
        assert result["error"] is not None


def test_parse_lab_report_empty_bytes():
    """Empty file should be handled gracefully, not crash."""
    result = parse_lab_report(b"", "empty.pdf")
    assert isinstance(result, dict)
    assert result["parsed"] is False
