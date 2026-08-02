"""
reports.py — compiles a session's chat history, symptoms, differential,
and lab findings into a structured pre-consultation report, and renders
it as a downloadable PDF (reportlab).
"""
import io
import logging

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from sqlalchemy.orm import Session as DBSession

from app.db import ChatSession, Message, Symptom, LabReport, Report

logger = logging.getLogger("medtriage.reports")

DISCLAIMER = "⚠ AI-generated. Not reviewed by a licensed clinician. Not a diagnosis."


def compile_report(db: DBSession, session_id: str) -> dict:
    try:
        session = db.get(ChatSession, session_id)
        if not session:
            return {"error": "Session not found"}

        messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at)
            .all()
        )
        symptoms = db.query(Symptom).filter(Symptom.session_id == session_id).all()
        lab_reports = db.query(LabReport).filter(LabReport.session_id == session_id).all()

        chief_complaint = next((m.content for m in messages if m.role == "patient"), "Not specified")
        symptom_list = [s.name for s in symptoms] if symptoms else []

        lab_findings = {}
        for lr in lab_reports:
            if lr.parsed_json and lr.parsed_json.get("values"):
                lab_findings.update(lr.parsed_json["values"])

        return {
            "session_id": session_id,
            "status": session.status,
            "chief_complaint": chief_complaint,
            "symptoms": symptom_list,
            "message_count": len(messages),
            "lab_findings": lab_findings,
            "recommended_tests": [],
            "referral_suggestion": "Clinician evaluation recommended based on reported symptoms.",
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        logger.error("Report compilation failed for session %s: %s", session_id, exc)
        return {"error": f"Could not compile report: {str(exc)[:200]}"}


def generate_pdf(report: dict) -> bytes:
    try:
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=16)
        h_style = ParagraphStyle('h', parent=styles['Heading2'], fontSize=12, spaceBefore=10)
        body_style = ParagraphStyle('body', parent=styles['Normal'], fontSize=10, leading=14)
        disclaimer_style = ParagraphStyle('disc', parent=body_style, textColor=colors.HexColor("#b45309"))

        story = [
            Paragraph("MedTriage AI — Pre-Consultation Report", title_style),
            Spacer(1, 6),
            HRFlowable(width="100%", color=colors.grey),
            Spacer(1, 10),
        ]

        if "error" in report:
            story.append(Paragraph(f"Error: {report['error']}", body_style))
        else:
            story.append(Paragraph("Chief Complaint", h_style))
            story.append(Paragraph(report.get("chief_complaint", "Not specified"), body_style))

            story.append(Paragraph("Reported Symptoms", h_style))
            symptoms = report.get("symptoms", [])
            story.append(Paragraph(", ".join(symptoms) if symptoms else "None recorded", body_style))

            story.append(Paragraph("Lab Findings", h_style))
            lab_findings = report.get("lab_findings", {})
            if lab_findings:
                for test, data in lab_findings.items():
                    story.append(Paragraph(f"{test}: {data.get('value')} {data.get('unit', '')}", body_style))
            else:
                story.append(Paragraph("No lab data uploaded", body_style))

            story.append(Paragraph("Referral Suggestion", h_style))
            story.append(Paragraph(report.get("referral_suggestion", ""), body_style))

        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", color=colors.grey))
        story.append(Spacer(1, 6))
        story.append(Paragraph(report.get("disclaimer", DISCLAIMER), disclaimer_style))

        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.7 * inch, bottomMargin=0.7 * inch)
        doc.build(story)
        return buffer.getvalue()

    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        doc.build([Paragraph("Report could not be generated. Please contact support.", styles['Normal'])])
        return buffer.getvalue()