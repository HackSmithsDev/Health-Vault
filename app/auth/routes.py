import secrets
import logging
from flask import request, redirect, render_template, jsonify, current_app, session, url_for
from app.extensions import db, executor 
from app.models import Provider, Patient, SettingsData
from app.models.clinicals_models import DiagnosticUnit
from flask_login import login_user, logout_user
from . import auth_bp

# Utility to access Redis
def get_redis():
    return current_app.redis

from app.services.email import (
    send_signup_email, 
    send_login_notification, 
    send_otp_email, 
    send_password_reset_success_email
)

@auth_bp.route('/check-email', methods=['GET'])
def check_email():
    """AJAX endpoint to check if email exists in the Clinical Vault."""
    email = request.args.get('email')
    if not email:
        return jsonify({"exists": False})
    
    exists = Provider.query.filter_by(email=email).first() or \
             Patient.query.filter_by(email=email).first()
    return jsonify({"exists": bool(exists)})

# --- 1. DUAL-TABLE LOGIN ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Try Provider first, then Patient
        user = Provider.query.filter_by(email=email).first()
        role = 'provider'

        if not user:
            user = Patient.query.filter_by(email=email).first()
            role = 'patient'
        
        if user and user.verify_password(password):
            session['user_role'] = role
            login_user(user)
            
            # Async login notification
            executor.submit(send_login_notification, user, request.remote_addr)
            
            return jsonify({"status": "success", "redirect": url_for('main.index')})
        
        return jsonify({"status": "error", "message": "Invalid clinical credentials"}), 401
        
    return render_template('auth.html')

# --- 2. PRACTITIONER SIGNUP ---
@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Practitioner Registration: Maps profession to Diagnostic Units."""
    data = request.get_json()
    email = data.get('email')

    # Ensure email is unique across the whole system
    if Provider.query.filter_by(email=email).first() or Patient.query.filter_by(email=email).first():
        return jsonify({"status": "error", "message": "Institutional email already in use"}), 400

    try:
        # Create Provider Object
        new_provider = Provider(
            email=email,
            full_name=data.get('full_name'),
            institution_name=data.get('institution_name'),
            hospital_license=data.get('hospital_license', secrets.token_hex(4).upper()),
            personal_license=data.get('personal_license', secrets.token_hex(4).upper()),
            date_of_registration=data.get('registration_date'),
            profession=data.get('profession'), # Mapped from your dynamic Unit list
            experience=int(data.get('experience', 0))
        )
        new_provider.password = data.get('password')

        # Initialize shared clinical settings
        new_settings = SettingsData(provider=new_provider)
        
        db.session.add(new_provider)
        db.session.add(new_settings)
        db.session.commit()
        
        # Async welcome email
        executor.submit(send_signup_email, new_provider)
        
        session['user_role'] = 'provider'
        login_user(new_provider)
        return jsonify({"status": "success", "redirect": url_for('main.index')})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registry Failure: {str(e)}")
        return jsonify({"status": "error", "message": "Clinical database sync error"}), 500

# --- 3. PASSWORD RECOVERY (MFA) ---



@auth_bp.route("/forget_password", methods=['POST'])
def forgot_password():
    email = request.get_json().get('email')
    user = Provider.query.filter_by(email=email).first() or Patient.query.filter_by(email=email).first()
    
    if not user:
        # Security best practice: don't reveal if user exists
        return jsonify({"status": "success", "message": "Verification token sent."})

    otp = f"{secrets.randbelow(1000000):06d}"
    get_redis().set(f"reset_otp:{email}", otp, ex=900) # 15 min expiry
    
    # Offload email to executor to prevent timeout
    executor.submit(send_otp_email, email, otp)
    return jsonify({"status": "success"})

@auth_bp.route("/verify_otp", methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    stored_otp = get_redis().get(f"reset_otp:{email}")
    
    if stored_otp and stored_otp == data.get('otp'):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid or expired token"}), 400

@auth_bp.route("/reset_password", methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    
    # Double check OTP again for final update
    stored_otp = get_redis().get(f"reset_otp:{email}")
    if not stored_otp or stored_otp != data.get('otp'):
        return jsonify({"status": "error", "message": "Session expired"}), 400
        
    user = Provider.query.filter_by(email=email).first() or Patient.query.filter_by(email=email).first()
    
    if user:
        user.password = data.get('password') 
        db.session.commit()
        get_redis().delete(f"reset_otp:{email}")
        executor.submit(send_password_reset_success_email, user)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Identity not found"}), 404

@auth_bp.route('/logout')
def logout():
    session.pop('user_role', None)
    logout_user()
    return redirect(url_for('auth.login'))