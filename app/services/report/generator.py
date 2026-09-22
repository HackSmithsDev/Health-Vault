from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io

from app.models.clinicals_models import DiagnosticReport

def generate_clinical_pdf(report_id):
    report = DiagnosticReport.query.get(report_id)
    session = report.session
    provider = session.provider
    patient = session.patient

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    
    # --- Header: Institutional Info ---
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"STITCH AI - CLINICAL REPORT")
    p.setFont("Helvetica", 10)
    p.drawString(100, 735, f"Institution: {provider.institution_name}")
    p.drawString(100, 720, f"Practitioner: {provider.full_name} ({provider.profession})")
    
    # --- Patient Metadata ---
    p.line(100, 710, 500, 710)
    p.drawString(100, 695, f"Patient Name: {patient.full_name if patient else 'N/A'}")
    p.drawString(100, 680, f"MRN: {patient.medical_record_number if patient else 'N/A'}")
    
    # --- AI Findings ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 650, "AI DIAGNOSTIC SUMMARY")
    p.setFont("Helvetica", 11)
    p.drawString(100, 635, f"Modality: {session.images[0].modality if session.images else 'Unknown'}")
    p.drawString(100, 620, f"Primary Prediction: {report.prediction_label}")
    p.drawString(100, 605, f"AI Confidence: {round(report.confidence_score * 100, 2)}%")
    p.drawString(100, 590, f"Engine Version: {report.model_name}")
    
    # --- Clinical Notes ---
    p.drawString(100, 560, "CLINICAL OBSERVATIONS:")
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 545, report.clinical_notes or "No manual notes provided.")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer