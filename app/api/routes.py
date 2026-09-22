import os
import secrets
from flask import render_template, request, jsonify, current_app, send_file, session, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy.orm import joinedload

from app.extensions import db, executor
from app.models import Provider, Patient, SettingsData, ClinicalSession, DiagnosticReport, Message, Subject, SupportMessage
from app.services.ai import get_specialist_ai, get_image_router
from app.services.email import send_signup_email_for_patient, send_account_verification_email_for_patient
from app.services.report import generate_clinical_pdf
from . import api_bp


@api_bp.route('/units/<string:unit_id>/subjects', methods=['GET'])
@login_required
def get_subjects_by_unit(unit_id):
    """Returns a list of subjects associated with a specific diagnostic unit."""
    
    subjects = Subject.query.filter_by(unit_id=unit_id).all()
    return jsonify([
        {"id": sub.id, "name": sub.name} for sub in subjects
    ])

@api_bp.route('/session/<string:id>/status', methods=['GET'])
@login_required
def get_session_status(id):
    session = ClinicalSession.query.get_or_404(id)
    return jsonify({
        "status": session.status,
        "unit": session.unit_id,
        "subject": session.subject_id
    })


@api_bp.route('/session/<string:id>', methods=['GET'])
@login_required
def session_detail(id):
    # 1. Fetch the session with its related unit/subject data
    clinical_session = ClinicalSession.query.get_or_404(id)
    
    # Security Check
    if not isinstance(current_user, Provider) or clinical_session.provider_id != current_user.id:
        return "Unauthorized", 403

    # 2. Fetch messages using joinedload for both image and report
    # This prevents the N+1 problem by doing a single SQL JOIN
    messages = Message.query.filter_by(session_id=id)\
                            .options(joinedload(Message.image), joinedload(Message.report))\
                            .order_by(Message.timestamp.asc()).all()

    # Track if we've already displayed the "Master Report"
    master_report_displayed = False

    for msg in messages:
        # Only show the diagnostic card for the FIRST AI report (The Registration)
        if msg.sender == 'ai' and msg.report and not master_report_displayed:
            msg.report_data = {
                "report_id": msg.report.id,
                "prediction_label": msg.report.prediction_label,
                "confidence_score": msg.report.confidence_score,
                "is_master": True
            }
            master_report_displayed = True 
        else:
            # All other AI messages, even if linked to an updated report, 
            # appear as standard clinical text to avoid redundant confidence bars.
            msg.report_data = None

    return render_template('session.html', 
                           clinical_session=clinical_session, 
                           messages=messages)


@api_bp.route('/my-health/chat/<string:session_id>', methods=['GET'])
@login_required
def patient_ai_chat(session_id):
    # 1. Ownership check
    clinical_session = ClinicalSession.query.filter_by(
        id=session_id, patient_id=current_user.id
    ).first_or_404()

    report = DiagnosticReport.query.filter_by(session_id=session_id).first()

    # 2. Fetch history
    chat_history = SupportMessage.query.filter_by(session_id=session_id)\
                                     .order_by(SupportMessage.timestamp.asc()).all()

    # 3. If NO history exists, generate an initial "Welcome" message
    if not chat_history and report:
        welcome_text = f"Hello. I've reviewed your results regarding **{clinical_session.unit_id}**. " \
                       f"The clinical finding is **{report.prediction_label}**. " \
                       "I'm here to help you understand what this means and what steps you might take next. " \
                       "What would you like to know first?"
        
        initial_msg = SupportMessage(
            session_id=session_id,
            patient_id=current_user.id,
            sender='ai',
            content=welcome_text
        )
        db.session.add(initial_msg)
        db.session.commit()
        
        # Refresh chat_history to include the new welcome message
        chat_history = [initial_msg]

    return render_template('patient_chat.html', 
                           session=clinical_session, 
                           report=report, 
                           chat_history=chat_history)


# --- 1. PATIENT & ADMISSION MANAGEMENT ---

@api_bp.route('/check-patient', methods=['GET'])
@login_required
def check_patient():
    email = request.args.get('email')
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400
        
    # Generate a secure code
    code = secrets.randbelow(899999) + 100000  # 6-digit code
    redis_key = f"patient_verification:{email}"
    
    # Check if patient exists for the email greeting
    patient = Patient.query.filter_by(email=email).first()
    full_name = patient.full_name if patient else "New Patient"
    
    # Store in Redis (300s = 5 mins)
    current_app.redis.setex(redis_key, 300, code)
    
    # Dispatch Email
    send_account_verification_email_for_patient(email, full_name, code)

    # SUCCESS: Return status so JS can reveal the codeSection
    return jsonify({
        "status": "success", 
        "message": "Verification code dispatched"
    })


@api_bp.route('/clinical/patient/verify', methods=['POST'])
@login_required
def verify_patient():
    code = request.form.get('code')
    email = request.form.get('email')

    if not code or not email:
        return jsonify({"status": "error", "message": "Code and email required"}), 400

    redis_key = f"patient_verification:{email}"
    stored_code = current_app.redis.get(redis_key)

    if not stored_code or stored_code != code:
        return jsonify({"status": "error", "message": "Invalid verification code"}), 400

    patient = Patient.query.filter_by(email=email).first()
    if patient:
        return jsonify({
            "exists": True,
            "full_name": patient.full_name,
            "mrn": patient.medical_record_number
        })
    return jsonify({"exists": False})


@api_bp.route('/clinical/admission', methods=['POST'])
@login_required
def clinical_admission():
    """
    Unified Admission: Registers new patient (if needed) and starts a session.
    """
    if session.get('user_role') != 'provider':
        return jsonify({"status": "error", "message": "Only providers can admit patients"}), 403

    data = request.form if request.form else request.get_json()
    # Look for 'scans' (the name attribute in your HTML)
    uploaded_files = request.files.getlist('scans') 

    # Take the first file for the initial processing
    file = uploaded_files[0]
        
    email = data.get('email')

    if not email:
        return jsonify({"status": "error", "message": "Email not provided."}), 400
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"status": "error", "message": "Diagnostic scan required."}), 400

    try:
        # Step 1: Handle Patient Record
        patient = Patient.query.filter_by(email=email).first()
        
        if not patient:
            # Handle Date of Birth from the new modal field
            dob_str = data.get('dob')
            dob_dt = datetime.strptime(dob_str, '%Y-%m-%d') if dob_str else None

            temp_password = secrets.token_urlsafe(8)
            patient = Patient(
                email=email,
                full_name=data.get('full_name'),
                medical_record_number=data.get('mrn'),
                blood_group=data.get('blood_group'),
                date_of_birth=dob_dt 
            )
            # Use your model's password hashing method if applicable
            patient.password = temp_password 
            db.session.add(patient)
            db.session.flush() 
            
            # Initialize settings for the new patient
            new_settings = SettingsData(patient_id=patient.id)
            db.session.add(new_settings)
            
            # Send credentials via the email service
            send_signup_email_for_patient(patient, temp_password)


        # Step 2: Create the Clinical Session with valid FKs
        new_session = ClinicalSession(
            patient_id=patient.id,
            provider_id=current_user.id,
            session_name=data.get('session_name') or "Automated Intake",
            unit_id=None,    # Set to None so AI can fill it later
            subject_id=None, # Set to None so AI can fill it later
            current_chapter_id=None, # Match the name in models.py
            status='Processing'
        )

        db.session.add(new_session)
        db.session.flush() 

        # 3. SAVE FILE LOCALLY (Immediate)
        filename = secure_filename(f"INTAKE_{new_session.id}_{file.filename}")
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'clinical_images', filename)
        file.save(upload_path)

        # 4. TRIGGER BACKGROUND INTAKE (Asynchronous)
        # Offload the heavy Vision + AI + DB logic to the executor
        from .utils import run_async_intake
        executor.submit(run_async_intake, new_session.id, upload_path, filename)

        db.session.commit()

        # 5. INSTANT REDIRECT
        return jsonify({
            "status": "success",
            "redirect_url": url_for('api.session_detail', id=new_session.id)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/session/<string:session_id>/ai/command', methods=['POST'])
@login_required
def ai_command_gateway(session_id):
    clinical_session = ClinicalSession.query.get_or_404(session_id)
    # Using the fix we discussed for Provider identity
    if not isinstance(current_user, Provider) or clinical_session.provider_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    file = request.files.get('file')
    if file:
        query = request.form.get('query', '').strip()
        action = request.form.get('action', 'chat')
    else:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        action = data.get('action', 'chat')

    specialist = get_specialist_ai()
    
    # 1. Fetch Context
    report = DiagnosticReport.query.filter_by(session_id=session_id)\
                                   .order_by(DiagnosticReport.created_at.desc()).first()
    
    history = Message.query.filter_by(session_id=session_id)\
                           .order_by(Message.timestamp.desc()).limit(6).all()
    history.reverse()

    # Initial context from last report
    vision_context = {
        "subject_id": report.prediction_label,
        "chapter_id": report.chapter_label,
        "confidence": report.confidence_score * 100
    } if report else None

    new_image_path = None
    if file:
        filename = secure_filename(f"SUPP_{session_id}_{file.filename}")
        new_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'clinical_images', filename)
        file.save(new_image_path)
        # Update context from new scan
        vision_context = get_image_router().route_and_diagnose(new_image_path)

    try:
        # Determine specific Subject/Chapter strings for the Specialist
        # Prioritizes the most recent vision_context (new scan) over old report
        sub_name = vision_context.get('subject_id', "Unknown Subject") if vision_context else "General"
        chap_name = vision_context.get('chapter_id', "General Analysis") if vision_context else "Intake"

        prompt_prefix = ""
        if action == "generate_report":
            prompt_prefix = "STRUCTURED MEDICAL REPORT REQUEST: "
        elif action == "differential":
            prompt_prefix = "DIFFERENTIAL DIAGNOSIS REQUEST: "

        # UPDATED CALL: Matches the 6-parameter signature (including query)
        ai_response_text = specialist.generate_clinical_insight(
            unit_id=clinical_session.unit_id,
            subject_name=sub_name,
            chapter_name=chap_name,
            vision_data=vision_context,
            query=f"{prompt_prefix}{query}" if query else None,
            history=history
        )

        # 3. Asynchronous Storage
        from .utils import background_storage_worker
        executor.submit(
            background_storage_worker,
            session_id=session_id,
            u_text=query or (f"Scan submitted" if file else f"Action: {action}"),
            a_text=ai_response_text,
            action=action,
            vision_result=vision_context,
            image_path=f"uploads/clinical_images/{os.path.basename(new_image_path)}" if file else None,
            unit_id=clinical_session.unit_id
        )

        return jsonify({
            "status": "success",
            "ai_message": ai_response_text,
            "action_performed": action,
            "timestamp": datetime.now().strftime('%I:%M %p')
        })

    except Exception as e:
        current_app.logger.error(f"Gateway Error: {str(e)}")
        return jsonify({"status": "error", "message": "Specialist failed."}), 500
    

@api_bp.route('/report/<int:report_id>/export', methods=['GET'])
@login_required
def export_report_pdf(report_id):
    # 1. Fetch the report object
    report = DiagnosticReport.query.get_or_404(report_id)
    
    # 2. Generate the PDF buffer using the report ID
    # Note: Ensure generate_clinical_pdf is expecting an ID or the object
    pdf_buffer = generate_clinical_pdf(report.id)
    
    # 3. Send the buffer as a downloadable file
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Stitch_Report_{report.id}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )


@api_bp.route('/support/<string:session_id>/chat', methods=['POST'])
@login_required
def support_chat(session_id):
    # 1. Ownership Check (Ensures patients can't query other people's data)
    clinical_session = ClinicalSession.query.filter_by(
        id=session_id, patient_id=current_user.id
    ).first_or_404()

    data = request.get_json()
    patient_message = data.get('message')

    if not patient_message:
        return jsonify({"error": "Empty message"}), 400

    # 2. Save Patient Message to History
    new_msg = SupportMessage(
        session_id=session_id,
        patient_id=current_user.id,
        sender='patient',
        content=patient_message
    )
    db.session.add(new_msg)

    # 3. Get the "Source of Truth" for the AI
    # We pull the official report so the AI knows the diagnosis it is explaining
    report = DiagnosticReport.query.filter_by(session_id=session_id).first()
    
    # 4. Generate AI Response (Liaison Mode)
    # Note: In a real app, you'd call your Groq/LLM service here with a specific System Prompt
    specialist = get_specialist_ai()
    ai_reply_text = specialist.generate_patient_friendly_explanation(
        query=patient_message,
        report=report,
        unit=clinical_session.unit_id
    )

    # 5. Save AI Message to History
    ai_msg = SupportMessage(
        session_id=session_id,
        patient_id=current_user.id,
        sender='ai',
        content=ai_reply_text
    )
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({
        "reply": ai_reply_text,
        "status": "success"
    })