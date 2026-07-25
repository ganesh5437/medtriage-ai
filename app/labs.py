"""
labs.py — Lab report parsing via OCR.
Uses pytesseract + pdf2image (gap-fix: named OCR libraries).
Extracts raw text from uploaded lab PDF/image, then pulls out common
lab value patterns (e.g. "Hemoglobin: 13.5 g/dL").

Error handling (spec): if parse fails, return partial success with raw
text and don't block the rest of the session (gap-fix: file upload validation).
"""
import io
import logging
import re

logger = logging.getLogger("medtriage.labs")

# Common lab test patterns: "Test Name: value unit" or "Test Name value unit"
LAB_VALUE_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z\s\(\)]{2,40}?)[\s:]+(\d+\.?\d*)\s*(g/dL|mg/dL|mmol/L|IU/L|U/L|%|/µL|/uL|cells/mcL|mEq/L|ng/mL|pg/mL|mIU/L)",
    re.IGNORECASE,
)

# Known lab test names to help filter noise
KNOWN_LAB_TESTS = [
    "hemoglobin", "hematocrit", "wbc", "white blood cell", "rbc", "red blood cell",
    "platelet", "glucose", "creatinine", "bun", "sodium", "potassium", "chloride",
    "co2", "calcium", "total protein", "albumin", "bilirubin", "alt", "ast",
    "alkaline phosphatase", "cholesterol", "triglycerides", "hdl", "ldl",
    "hba1c", "tsh", "t3", "t4", "crp", "esr", "troponin", "d-dimer",
    "ferritin", "vitamin b12", "vitamin d", "iron", "urea",
]


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract raw text from an uploaded lab report using OCR.
    Supports PDF (via pdf2image + pytesseract) and images (JPG/PNG direct OCR).
    """
    try:
        import pytesseract
        from PIL import Image

        lower_name = filename.lower()

        if lower_name.endswith(".pdf"):
            from pdf2image import convert_from_bytes
            pages = convert_from_bytes(file_bytes, dpi=200)
            text_parts = []
            for page_img in pages:
                text_parts.append(pytesseract.image_to_string(page_img))
            return "\n".join(text_parts)
        else:
            # JPG/PNG — direct OCR
            image = Image.open(io.BytesIO(file_bytes))
            return pytesseract.image_to_string(image)

    except Exception as exc:
        logger.error("OCR extraction failed for %s: %s", filename, exc)
        raise


def parse_lab_values(raw_text: str) -> dict:
    """
    Parse structured lab values from OCR'd raw text.
    Returns {"values": {test_name: {"value": x, "unit": y}}, "raw_text": text}
    """
    values = {}

    for match in LAB_VALUE_PATTERN.finditer(raw_text):
        test_name_raw = match.group(1).strip()
        value = match.group(2)
        unit = match.group(3)

        # Filter: only keep if it roughly matches a known lab test
        test_name_lower = test_name_raw.lower()
        is_known = any(known in test_name_lower for known in KNOWN_LAB_TESTS)

        if is_known:
            # Normalize test name (title case, trim)
            clean_name = test_name_raw.strip().title()
            values[clean_name] = {"value": float(value), "unit": unit}

    return {
        "values": values,
        "raw_text": raw_text[:2000],  # cap stored raw text
    }


def parse_lab_report(file_bytes: bytes, filename: str) -> dict:
    """
    Main entrypoint: extract + parse a lab report.
    Never raises — returns {"parsed": bool, "values": {...}, "raw_text": str, "error": str|None}
    (gap-fix: error handling — never blocks report generation)
    """
    try:
        raw_text = extract_text_from_file(file_bytes, filename)
        if not raw_text or not raw_text.strip():
            return {
                "parsed": False,
                "values": {},
                "raw_text": "",
                "error": "No text could be extracted from the file. It may be a scanned image with poor quality, or an unsupported format.",
            }

        parsed = parse_lab_values(raw_text)
        return {
            "parsed": True,
            "values": parsed["values"],
            "raw_text": parsed["raw_text"],
            "error": None,
        }

    except Exception as exc:
        logger.error("Lab report parsing failed for %s: %s", filename, exc)
        return {
            "parsed": False,
            "values": {},
            "raw_text": "",
            "error": f"Could not parse this lab report: {str(exc)[:200]}",
        }
