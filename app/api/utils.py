from flask import current_app
from app.extensions import db
from app.models import ClinicalSession, DiagnosticReport, DiagnosticUnit, Subject, Chapter, MedicalImage, Message
from datetime import datetime

from app.services.ai import get_specialist_ai, get_image_router


def run_async_intake(session_id, upload_path, filename):
    with current_app.app_context():
        try:
            session = ClinicalSession.query.get(session_id)
            
            # 1. AI PREDICTION (Returns raw indices)
            # Returns: {'unit_id': 'pulmonology', 'subject_id': 'copd_screening', 'chapter_id': 'pathophysiology', 'confidence': 88.5}
            vision_result = get_image_router().route_and_diagnose(upload_path)
            
            # 2. TIER 1: UNIT ID
            # The router already returns the string ID for the Unit (e.g., 'pulmonology')
            unit = DiagnosticUnit.query.get(vision_result['unit_id'])

            # 3. TIER 2: SUBJECT ID (Positional Lookup)
            target_subject = Subject.query.get(vision_result['subject_id']) 
            
            # 4. TIER 3: CHAPTER ID (Positional Lookup)
            target_chapter = Chapter.query.get(vision_result['chapter_id'])

            # 5. SYNC TO SESSION (Saving the actual IDs)
            session.unit_id = unit.id                # e.g., 'pulmonology'
            session.subject_id = target_subject.id    # e.g., 'copd_screening'
            session.current_chapter_id = target_chapter.id # e.g., 'pathophysiology'
            
            session.session_name = f"{target_subject.name}: {target_chapter.name}"

            # GENERATE INITIAL INSIGHT (Context-Locked to the Chapter)
            # Inside run_async_intake
            confidence = vision_result.get('confidence', 0)
            if confidence < 40:
                session.status = 'Flagged: Low Confidence'
                ai_response = "The system detected the scan with low confidence. Manual clinical review is required before proceeding."
            else:
                ai_response = get_specialist_ai().generate_clinical_insight(
                    unit_id=unit.id,
                    subject_name=target_subject.name,
                    chapter_name=target_chapter.name,
                    vision_data=vision_result
                )

            # SAVE RECORDS (Using your existing helpers)
            img = save_image_record(session_id, f"uploads/clinical_images/{filename}", unit.id)
            
            # We pass the Subject and Chapter names to the report helper
            vision_result['subject_name'] = target_subject.name
            vision_result['chapter_name'] = target_chapter.name
            
            report = create_diagnostic_report(session_id, vision_result, ai_response, "Stitch-HNN-v1")
            
            save_message(session_id, 'user', "Initial scan submitted for autonomous intake.", image_id=img.id)
            save_message(session_id, 'ai', ai_response, report_id=report.id)

            session.status = 'Completed'
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Intake Critical Failure: {str(e)}")


def background_storage_worker(session_id, u_text, a_text, action, vision_result, image_path, unit_id):
    
    with current_app.app_context():
        try:
            img_id = None
            rep_id = None

            # A. Save Image via Helper
            if image_path:
                img_record = save_image_record(session_id, image_path, unit_id)
                img_id = img_record.id

            # B. Save Report via Helper if chip was 'generate_report'
            if action == "generate_report":
                new_rep = create_diagnostic_report(session_id, vision_result, a_text, "M2-Command")
                rep_id = new_rep.id

            # C. Save Interaction via Helper
            save_message(session_id, 'user', u_text, image_id=img_id)
            save_message(session_id, 'ai', a_text, report_id=rep_id)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Async DB Error: {str(e)}")


def save_message(session_id, sender, content, image_id=None, report_id=None):
    """Helper to save a Message record."""
    try:
        msg = Message(
            session_id=session_id,
            sender=sender,
            content=content,
            image_id=image_id,
            report_id=report_id
        )
        db.session.add(msg)
        db.session.flush()  # Get ID before commit
        return msg
    except Exception as e:
        current_app.logger.error(f"Error saving message: {str(e)}")
        raise

def save_image_record(session_id, file_path, unit_id):
    """Helper to save a MedicalImage record."""
    try:
        modality = file_path.split('.')[-1].upper()  # Simple modality inference
        new_image = MedicalImage(session_id=session_id, modality=modality, file_path=file_path)
        db.session.add(new_image)
        db.session.flush()  # Get ID before commit
        return new_image
    except Exception as e:
        current_app.logger.error(f"Error saving image record: {str(e)}")
        raise

def create_diagnostic_report(session_id, vision_data, ai_insight, model_name="M2-Hybrid"):
    """
    Ensures a single source of truth. 
    If a report exists, it enhances the existing record instead of creating a duplicate.
    """
    try:
        report = DiagnosticReport.query.filter_by(session_id=session_id).first()

        if report:
            # CLINICAL ENHANCEMENT: Don't change the Subject/Confidence
            # Just append the new analysis to the JSON and return the existing ID
            updated_json = report.report_json or {}
            
            # Store the evolution in a 'history' key inside the JSON
            if 'evolution' not in updated_json:
                updated_json['evolution'] = []
            
            updated_json['evolution'].append({
                "timestamp": datetime.now().isoformat(),
                "insight": ai_insight,
                "model": model_name
            })
            
            report.report_json = updated_json
            # We don't change report.prediction_label or confidence_score
            # because those are based on the raw M2 vision data.
            return report
        else:
            # INITIAL REGISTRATION REPORT
            report = DiagnosticReport(
                session_id=session_id,
                model_name=model_name,
                prediction_label=vision_data.get('subject_name', 'Unknown'),
                chapter_label=vision_data.get('chapter_name', 'Unknown'),
                confidence_score=vision_data.get('confidence', 0),
                report_json={"initial_analysis": ai_insight},
                clinical_notes="Baseline analysis generated."
            )
            db.session.add(report)
            db.session.flush()
            return report
            
    except Exception as e:
        current_app.logger.error(f"Error in diagnostic logic: {str(e)}")
        raise
