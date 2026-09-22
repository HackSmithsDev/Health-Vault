def get_signup_template(full_name):
    """Professional onboarding email for the clinical registry."""
    return f"""
    <div style="font-family: 'Inter', Helvetica, Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #d1d9e6; border-radius: 8px; padding: 40px; color: #1e293b; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #0a58ca; margin: 0; font-size: 24px;">STITCH AI</h1>
            <p style="color: #64748b; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Clinical Diagnostic Portal</p>
        </div>
        <h2 style="color: #0f172a; margin-top: 0;">Access Granted: {full_name}</h2>
        <p>Your practitioner account has been successfully verified and registered in the Stitch AI ecosystem.</p>
        
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin: 25px 0;">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #334155;">Institutional Access Initialized:</p>
            <ul style="margin: 0; padding-left: 20px; color: #475569;">
                <li>Access to 5 Core Clinical Units (Pulmonology, Radiology, etc.)</li>
                <li>Secure Triage Session Workspace</li>
                <li>AI-Assisted Diagnostic Literacy Modules</li>
            </ul>
        </div>
        
        <p style="font-size: 14px; color: #64748b;">This account is tied to your professional medical license. Ensure all diagnostic sessions follow your institution's compliance protocols.</p>
        <p style="margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
            Regards,<br><strong>Stitch Clinical Systems</strong>
        </p>
    </div>
    """

def get_signup_template_for_patient(full_name, temp_password, link):
    """
    Returns a professional HTML email template for new clinical patients.
    Includes temporary access credentials and security instructions.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .email-container {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #e1e8ed; border-radius: 8px; overflow: hidden; }}
            .header {{ background-color: #0d6efd; color: white; padding: 30px; text-align: center; }}
            .content {{ padding: 30px; background-color: #ffffff; }}
            .credentials-box {{ background-color: #f8f9fa; border: 1px dashed #0d6efd; padding: 20px; border-radius: 6px; margin: 20px 0; text-align: center; }}
            .footer {{ background-color: #f4f7f9; padding: 20px; text-align: center; font-size: 12px; color: #777; }}
            .btn {{ background-color: #0d6efd; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 10px; }}
            .warning {{ color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 4px; font-size: 13px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Stitch AI</h1>
                <p>Advanced Clinical Diagnostics</p>
            </div>
            <div class="content">
                <h2>Welcome, {full_name}</h2>
                <p>A clinical practitioner has registered your profile on the <strong>Stitch AI Secure Network</strong>. You can now access your diagnostic reports, scan history, and AI-assisted clinical insights.</p>
                
                <div class="credentials-box">
                    <p style="margin: 0; font-weight: bold; color: #0d6efd;">Your Temporary Password:</p>
                    <h3 style="letter-spacing: 2px; font-size: 24px; margin: 10px 0;">{temp_password}</h3>
                    <a href="{link}" class="btn">Access Patient Portal</a>
                </div>

                <div class="warning">
                    <strong>Security Notice:</strong> For your protection, please update this password immediately upon your first login under <em>Settings > Security</em>.
                </div>
            </div>
            <div class="footer">
                <p>&copy; 2026 Stitch AI Clinical Network. All rights reserved.<br>
                This is an automated clinical notification. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_login_alert_template(email, time_str, ip_address="Unknown"):
    """Security alert for clinical compliance (HIPAA/GDPR style)."""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; border-top: 4px solid #0a58ca; padding: 30px; border-left: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;">
        <h3 style="color: #b91c1c; margin-top: 0;">Security Alert: New Clinical Login</h3>
        <p>A new login was recorded for practitioner: <strong>{email}</strong></p>
        <div style="background: #f1f5f9; padding: 15px; border-radius: 4px; font-family: monospace;">
            <strong>Timestamp:</strong> {time_str}<br>
            <strong>IP Address:</strong> {ip_address}
        </div>
        <p style="margin-top: 20px; font-size: 13px; color: #666;">If this was not an authorized access by you, please contact your Hospital IT Administrator or reset your credentials immediately to prevent unauthorized data access.</p>
    </div>
    """

def get_forgot_password_template(otp):
    """MFA / Recovery token template."""
    return f"""
    <div style="font-family: sans-serif; text-align: center; max-width: 450px; margin: auto; padding: 40px; border: 1px solid #e2e8f0; border-radius: 12px;">
        <div style="color: #0a58ca; font-weight: bold; font-size: 20px; margin-bottom: 10px;">Security Verification</div>
        <p style="color: #475569;">Use the following clinical authorization code to reset your access. Valid for 15 minutes.</p>
        <div style="font-size: 36px; font-family: 'Courier New', monospace; font-weight: bold; letter-spacing: 10px; padding: 25px; background: #eff6ff; color: #1e40af; border: 1px dashed #bfdbfe; display: inline-block; border-radius: 8px; margin: 20px 0;">
            {otp}
        </div>
        <p style="color: #94a3b8; font-size: 12px;">Strictly Confidential: Do not share this code with hospital staff or third parties.</p>
    </div>
    """

def get_reset_success_template(full_name):
    """Credential update confirmation."""
    return f"""
    <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 30px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f0fdf4;">
        <h3 style="color: #166534; margin-top: 0;">Credential Update Verified</h3>
        <p>Dear {full_name},</p>
        <p>The password for your clinical portal has been successfully updated. No further action is required at this time.</p>
    </div>
    """

def get_account_deleted_template(full_name):
    """Institutional confirmation of data decommissioning."""
    return f"""
    <div style="font-family: sans-serif; max-width: 550px; margin: auto; border: 1px solid #fecaca; padding: 40px; border-radius: 8px;">
        <h2 style="color: #991b1b; margin-top: 0;">Registry Decommissioned</h2>
        <p>Practitioner: {full_name},</p>
        <p>We confirm that your access to the Stitch AI Clinical Portal has been revoked and all associated session logs and metadata have been purged from the active registry.</p>
        <p style="font-size: 12px; color: #666; font-style: italic;">Reference ID: DEL-{full_name[:3].upper()}-2026</p>
    </div>
    """

def get_account_verificaton_template(full_name, verification_code):
    """Email template for patient account verification."""
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #e1e8ed; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #0d6efd; color: white; padding: 30px; text-align: center;">
            <h1>Stitch AI</h1>
            <p>Advanced Clinical Diagnostics</p>
        </div>
        <div style="padding: 30px; background-color: #ffffff;">
            <h2>Account Verification Required</h2>
            <p>Dear {full_name},</p>
            <p>A practitioner has registered your email on the Stitch AI Clinical Portal. To access your diagnostic reports and clinical insights, please verify your account using the code below:</p>
            <div style="font-size: 36px; font-family: 'Courier New', monospace; font-weight: bold; letter-spacing: 10px; padding: 25px; background: #eff6ff; color: #1e40af; border: 1px dashed #bfdbfe; display: inline-block; border-radius: 8px; margin: 20px 0;">
                {verification_code}
            </div>
            <p style="color: #94a3b8; font-size: 12px;">This code is valid for 5 minutes. Do not share this code with anyone.</p>
        </div>
        <div style="background-color: #f4f7f9; padding: 20px; text-align: center; font-size: 12px; color: #777;">
            &copy; 2026 Stitch AI Clinical Network. All rights reserved.<br>
            This is an automated clinical notification. Please do not reply.
        </div>
    </div>
    """

def get_report_notification_template(patient_name, provider_name, provider_email, report_summary, link):
    """Email template to notify patients of new clinical reports."""
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #e1e8ed; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #0d6efd; color: white; padding: 30px; text-align: center;">
            <h1>Stitch AI</h1>
            <p>Advanced Clinical Diagnostics</p>
        </div>
        <div style="padding: 30px; background-color: #ffffff;">
            <h2>New Clinical Report Available</h2>
            <p>Dear {patient_name},</p>
            <p>Your healthcare provider, {provider_name} ({provider_email}), has uploaded a new diagnostic report to your Stitch AI Patient Portal.</p>
            <div style="background-color: #f8f9fa; border: 1px dashed #0d6efd; padding: 20px; border-radius: 6px; margin: 20px 0;">
                <p style="margin: 0; font-weight: bold; color: #0d6efd;">Report Summary:</p>
                <p style="margin-top: 10px;">{report_summary}</p>
            </div>
            <a href="{link}" class="btn" style="background-color: #0d6efd; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Your Report</a>
        </div>
        <div style="background-color: #f4f7f9; padding: 20px; text-align: center; font-size: 12px; color: #777;">
            &copy; 2026 Stitch AI Clinical Network. All rights reserved.<br>
            This is an automated clinical notification. Please do not reply.
        </div>
    </div>
    """


def get_review_received_template(full_name, issue_type, issue_details):
    """Acknowledgment email for received support reviews."""
    return f"""
    <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 30px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f0fdf4;">
        <h3 style="color: #166534; margin-top: 0;">Support Request Received</h3>
        <p>Dear {full_name},</p>
        <p>Thank you for reaching out to Stitch AI Support. We have received your request regarding the following issue:</p>
        <div style="background-color: #f8f9fa; border: 1px dashed #0d6efd; padding: 20px; border-radius: 6px; margin: 20px 0;">
            <p style="margin: 0; font-weight: bold; color: #0d6efd;">Issue Type:</p>
            <p style="margin-top: 10px;">{issue_type}</p>
            <p style="margin-top: 10px;"><strong>Details:</strong> {issue_details}</p>
        </div>
        <p style="font-size: 14px; color: #475569;">Our support team will review your request and get back to you within 24-48 hours. If your issue is urgent, please contact our support hotline.</p>
    </div>
    """