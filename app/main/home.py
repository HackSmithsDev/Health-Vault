from flask import current_app, render_template, request, jsonify, url_for, redirect, session
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename

from . import main_bp

from app.extensions import db
from app.models import ClinicalSession
import os

@main_bp.route('/')
def show_login_dialog():
    return render_template('login_dialog.html')

@main_bp.route('/index')
@login_required
def index():
    # Logic can branch here based on session['user_role'] if the UI differs
    # In your main.py route:
    if session.get('user_role') == 'patient':
        # Fetch sessions for the specific patient
        # We rename the variable to 'health_records' to match your template
        health_records = ClinicalSession.query.options(
            db.joinedload(ClinicalSession.images),
            db.joinedload(ClinicalSession.reports)
        ).filter_by(patient_id=current_user.id).order_by(ClinicalSession.created_at.desc()).limit(10).all()

        return render_template('patient_index.html', health_records=health_records)
    else:
        # For clinicians, show all recent sessions
        recent_sessions = ClinicalSession.query.options(
            db.joinedload(ClinicalSession.images),
            db.joinedload(ClinicalSession.reports)
        ).order_by(ClinicalSession.created_at.desc()).limit(10).all()
        pending_count = ClinicalSession.query.filter_by(status='pending').count()
        flagged_count = ClinicalSession.query.filter_by(status='flagged').count()
        return render_template('index.html', recent_sessions=recent_sessions, 
                               pending_count=pending_count, flagged_count=flagged_count)

# --- 1. DUAL AVATAR LOGIC ---
@main_bp.route('/update-user-avatar', methods=['POST'])
@login_required
def update_user_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['avatar']
    ext = os.path.splitext(file.filename)[1]
    
    # Determine role for naming
    role = session.get('user_role', 'user')
    filename = secure_filename(f"{role}_{current_user.id}{ext}")

    if current_user.avatar_path and 'default' not in current_user.avatar_path:
        # Note: Added a check to ensure we don't crash if file is already missing
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.avatar_path.replace('uploads/', ''))
        if os.path.exists(old_path): os.remove(old_path)
    
    rel_path = f"uploads/user_avatars/{filename}"
    abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'user_avatars', filename)
    file.save(abs_path)

    current_user.avatar_path = rel_path
    db.session.commit()
    return jsonify({'message': 'Success', 'path': rel_path})


# --- 2. PROFILE & SECURITY LOGIC ---
@main_bp.route('/update-details', methods=['POST'])
@login_required
def update_details():
    """Branching logic to update either Provider or Patient details."""
    try:
        current_user.full_name = request.form.get('full_name')
        
        # Provider-Specific Fields
        if session.get('user_role') == 'provider':
            current_user.institution_name = request.form.get('institution_name')
            current_user.profession = request.form.get('profession')
            current_user.hospital_license = request.form.get('hospital_license')
            exp = request.form.get('experience')
            current_user.experience = int(exp) if exp else 0
            
        # Patient-Specific Fields
        elif session.get('user_role') == 'patient':
            current_user.blood_group = request.form.get('blood_group')
            # Add other patient fields as needed

        db.session.commit()
        return jsonify({"status": "success", "message": "Clinical Profile synced!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@main_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.pop('user_role', None)
    logout_user() # Safe to call even if already logged out
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "redirect": url_for('auth.login')})
    
    return redirect(url_for('auth.login'))