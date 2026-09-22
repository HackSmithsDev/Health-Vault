from flask import current_app, render_template, request, jsonify, url_for, redirect, session
from flask_login import login_required, current_user, logout_user

from app.services.email import send_review_received_email, send_account_deletion_email

from . import main_bp

from app.extensions import db
from app.models import SettingsData, Reviews
from app.services.email import send_account_deletion_email


@main_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_p = request.form.get('old_password')
    new_p = request.form.get('new_password')

    if not current_user.verify_password(old_p):
        return jsonify({"status": "error", "message": "Current password is wrong"}), 400

    try:
        current_user.password = new_p 
        db.session.commit()
        return jsonify({"status": "success", "message": "Security updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Update failed"}), 500

# --- 3. SETTINGS & SUPPORT ---

@main_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    settings_data = current_user.settings_data
    
    # Fallback to create settings if they don't exist
    if not settings_data:
        if session.get('user_role') == 'provider':
            settings_data = SettingsData(provider_id=current_user.id)
        else:
            settings_data = SettingsData(patient_id=current_user.id)
        db.session.add(settings_data)
        db.session.commit()

    return render_template('settings.html', settings=settings_data)


@main_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    # Fetch the settings linked to the current user
    settings_data = current_user.settings_data
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # --- ACTION 1: Update SettingsData Model ---
    settings_data.language = data.get('language', settings_data.language)
    settings_data.intelligence_mode = data.get('intelligence_mode', settings_data.intelligence_mode)
    settings_data.font_style = data.get('font_style', settings_data.font_style)
    settings_data.font_size = data.get('font_size', settings_data.font_size)
    settings_data.header_style = data.get('header_style', settings_data.header_style)
    
    # Handle the checkbox boolean
    settings_data.show_digital_stamp = bool(data.get('show_digital_stamp', settings_data.show_digital_stamp))

    # --- ACTION 2: Update Identity (Provider or Patient Model) ---
    # We only update if the keys exist to prevent overwriting with None
    if data.get('full_name'):
        current_user.full_name = data.get('full_name')
    
    # Ensuring the 2026 requirement: Profession must be one of the 5 Units
    if data.get('profession'):
        current_user.profession = data.get('profession')
        
    if data.get('institution_name'):
        current_user.institution_name = data.get('institution_name')

    try:
        db.session.commit()
        return jsonify({"status": "success", "message": "Clinical Registry Synchronized"})
    except Exception as e:
        db.session.rollback()
        # Log the error for your M2 Mac console
        print(f"Database Error: {str(e)}")
        return jsonify({"status": "error", "message": "Integrity Error: Check required identity fields."}), 500

    
@main_bp.route('/settings/reset', methods=['POST'])
@login_required
def reset_settings():
    settings_data = current_user.settings_data
    settings_data.reset_to_defaults()
    try:
        db.session.commit()
        return jsonify({"status": "success", "message": "Settings reset to defaults"})
    except Exception as e:
        db.session.rollback()
        print(f"Database Error: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to reset settings."}), 500
    

@main_bp.route('/review-support', methods=['POST'])
@login_required
def review_support():
    issue_type = request.form.get('issue')
    issue_details = request.form.get('details')
    
    if not issue_details:
        return jsonify({"status": "error", "message": "Clinical details are required"}), 400

    try:
        # 1. Log the Incident in the Clinical Registry
        review = Reviews(
            issue_type=issue_type, 
            issue_details=issue_details, 
            provider_id=current_user.id if session.get('user_role') == 'provider' else None, 
            patient_id=current_user.id if session.get('user_role') == 'patient' else None
        )
        db.session.add(review)
        db.session.commit()
        
        # Replace with your actual mail sending utility (e.g., Flask-Mail or SendGrid)
        send_review_received_email(current_user.email, current_user.full_name, issue_type, issue_details)

        return jsonify({
            "status": "success", 
            "message": "Incident logged and confirmation email dispatched."
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Support Route Error: {str(e)}")
        return jsonify({"status": "error", "message": "System failed to log incident"}), 500
    

@main_bp.route('/delete_account', methods=['DELETE'])
@login_required
def delete_account():
    user_email = current_user.email
    user_name = current_user.full_name
    user_obj = current_user 

    try:
        # Extract role before logging out
        role = session.get('user_role')
        logout_user()

        if role == 'provider':
            db.session.delete(user_obj)
            db.session.commit()

        session.pop('user_role', None)
        
        try:
            send_account_deletion_email(user_email, user_name)
        except Exception as mail_err:
            current_app.logger.error(f"Post-deletion email failed: {mail_err}")

        return jsonify({"status": "success", "redirect": url_for('auth.login')})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to delete account."}), 500