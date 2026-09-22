from flask_mail import Message
from flask import current_app, url_for
from datetime import datetime
# Import from extensions to avoid circular dependency
from app.extensions import executor, mail 
from .templates import (
    get_account_verificaton_template,
    get_signup_template, 
    get_signup_template_for_patient,
    get_login_alert_template,
    get_forgot_password_template, 
    get_reset_success_template,
    get_account_deleted_template,
    get_report_notification_template,
    get_review_received_template
)

@executor.job
def send_email(subject, recipient, html_body):
    """
    Core asynchronous sending logic. 
    Using @executor.job ensures clinical UI doesn't lag during SMTP handshakes.
    """
    try:
        # Get the actual app instance for the context
        app = current_app._get_current_object()
        with app.app_context():
            msg = Message(subject=subject, recipients=[recipient])
            msg.html = html_body
            mail.send(msg)
        return True
    except Exception as e:
        # Logged for HIPAA/Audit compliance
        print(f"SMTP Error: {str(e)}") 
        return False

def send_signup_email(user):
    """Registry confirmation for Providers or Patients."""
    html = get_signup_template(user.full_name)
    subject = f"Stitch AI: Registration Confirmed for {user.full_name}"
    return send_email.submit(subject, user.email, html)

def send_signup_email_for_patient(patient, temp_password):
    """Specialized signup email for Patients with temporary credentials."""
    link = url_for('auth.login', _external=True)
    html = get_signup_template_for_patient(patient.full_name, temp_password, link)
    subject = f"Stitch AI: Welcome {patient.full_name} - Your Account Details"
    return send_email.submit(subject, patient.email, html)

def send_login_notification(user, ip_address):
    """Security alert for clinical access monitoring."""
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    html = get_login_alert_template(user.email, now, ip_address)
    subject = "STITCH SECURITY: New Access Detected"
    return send_email.submit(subject, user.email, html)

def send_otp_email(email, otp):
    """Secure Authorization Token for MFA."""
    html = get_forgot_password_template(otp)
    subject = "Stitch AI: Secure Authorization Token"
    return send_email.submit(subject, email, html)

def send_password_reset_success_email(email):
    """Notification of successful password change."""
    html = get_reset_success_template()
    subject = "Stitch AI: Password Reset Successful"
    return send_email.submit(subject, email, html)

def send_account_deletion_email(email, full_name):
    """Final audit notification for decommissioned accounts."""
    html = get_account_deleted_template(full_name)
    subject = "Stitch AI: Clinical Account Decommissioned"
    return send_email.submit(subject, email, html)

def send_account_verification_email_for_patient(email, full_name, code):
    """Email with verification code for patient registration."""
    html = get_account_verificaton_template(full_name, code)  # Using the correct template
    subject = "Stitch AI: Patient Verification Code"
    return send_email.submit(subject, email, html)

def send_report_notification_email(patient_email,  patient_name, provider_name, provider_email, report_summary):
    """Notify patients of new clinical reports."""
    link = url_for('main.index', _external=True)  # Link to patient portal
    html = get_report_notification_template(patient_name, provider_name, provider_email, report_summary, link)
    subject = "Stitch AI: New Clinical Report Available"
    return send_email.submit(subject, patient_email, html)

def send_review_received_email(email, full_name, issue_type, issue_details):
    """Acknowledgment email for received support reviews."""
    html = get_review_received_template(full_name, issue_type, issue_details)
    subject = "Stitch AI: Support Request Received"
    return send_email.submit(subject, email, html)