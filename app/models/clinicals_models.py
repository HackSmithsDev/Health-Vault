import secrets
from app.extensions import db
from datetime import datetime, timezone

# --- TIER 1-3: THE KNOWLEDGE REGISTRY ---

class DiagnosticUnit(db.Model):
    """The 5 Units: PULMONOLOGY, RADIOLOGY, CARDIOLOGY, HEMATOLOGY, NEUROLOGY."""
    __tablename__ = 'diagnostic_units'
    id = db.Column(db.String(50), primary_key=True) # e.g., 'pulmonology'
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), index=True)
    
    subjects = db.relationship('Subject', backref='unit', lazy='selectin', cascade="all, delete-orphan")
    sessions = db.relationship('ClinicalSession', backref='unit_ref', lazy='dynamic')

class Subject(db.Model):
    """The 2-5 Subjects per Unit: e.g., Pneumonia Triage, Glioma Analysis."""
    __tablename__ = 'subjects'
    id = db.Column(db.String(50), primary_key=True) # e.g., 'pneumonia_triage'
    name = db.Column(db.String(100), nullable=False, index=True)
    unit_id = db.Column(db.String(50), db.ForeignKey('diagnostic_units.id'), nullable=False)
    
    chapters = db.relationship('Chapter', backref='subject', lazy='selectin', cascade="all, delete-orphan")

class Chapter(db.Model):
    """The 3-5 Chapters per Subject: e.g., Pathophysiology, Radiographic Signs."""
    __tablename__ = 'chapters'
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.String(50), db.ForeignKey('subjects.id'), nullable=False)

# --- THE CLINICAL WORKFLOW ---

class ClinicalSession(db.Model):
    """The central container for a diagnostic event (A Patient Case)."""
    __tablename__ = 'clinical_sessions'
    
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(secrets.token_hex(3)).upper())
    session_name = db.Column(db.String(255), nullable=False, index=True) 
    status = db.Column(db.String(20), default='Pending', index=True) # Pending, Analyzed, Flagged, Resolved
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Hierarchy Tracking
    unit_id = db.Column(db.String(50), db.ForeignKey('diagnostic_units.id'), nullable=True)
    subject_id = db.Column(db.String(50), db.ForeignKey('subjects.id'), nullable=True)
    current_chapter_id = db.Column(db.String(50), db.ForeignKey('chapters.id'), nullable=True)

    # Actor Relationships
    provider_id = db.Column(db.String(50), db.ForeignKey('providers.id'), nullable=False)
    patient_id = db.Column(db.String(50), db.ForeignKey('patients.id'), nullable=False)

    provider = db.relationship('Provider', backref='sessions', lazy='joined')
    patient = db.relationship('Patient', backref='sessions', lazy='joined')
    current_chapter = db.relationship('Chapter', foreign_keys=[current_chapter_id])

    # Data Cascades
    images = db.relationship('MedicalImage', backref='session', lazy='selectin', cascade="all, delete-orphan")
    reports = db.relationship('DiagnosticReport', backref='session', cascade="all, delete-orphan")
    messages = db.relationship('Message', backref='session', cascade="all, delete-orphan")

# --- DATA & OUTPUTS ---

class MedicalImage(db.Model):
    """Metadata for uploaded scans (XRAY, MRI, ECG, etc)."""
    __tablename__ = 'medical_images'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), db.ForeignKey('clinical_sessions.id'), nullable=False)
    modality = db.Column(db.String(20), nullable=False) # 'XRAY', 'MRI'
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class DiagnosticReport(db.Model):
    """The structured AI output for a specific case."""
    __tablename__ = 'diagnostic_reports'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), db.ForeignKey('clinical_sessions.id'), nullable=False)
    
    model_name = db.Column(db.String(100))
    prediction_label = db.Column(db.String(100), index=True) # e.g. "Pneumonia"
    chapter_label = db.Column(db.String(100))              # e.g. "Radiographic Signs"
    confidence_score = db.Column(db.Float)
    report_json = db.Column(db.JSON) 
    clinical_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Message(db.Model):
    """Audit trail of the Physician-AI interaction."""
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), db.ForeignKey('clinical_sessions.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('diagnostic_reports.id'), nullable=True)
    sender = db.Column(db.String(20)) # 'user' or 'ai'
    content = db.Column(db.Text, nullable=False)
    
    image_id = db.Column(db.Integer, db.ForeignKey('medical_images.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    image = db.relationship('MedicalImage', backref='message', lazy='joined')
    report = db.relationship('DiagnosticReport', foreign_keys=[report_id], backref='message')

class SupportMessage(db.Model):
    """Private patient-facing AI chat. Clinicians cannot see this."""
    __tablename__ = 'support_messages'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), db.ForeignKey('clinical_sessions.id'))
    patient_id = db.Column(db.String(50), db.ForeignKey('patients.id'))
    sender = db.Column(db.String(20)) # 'patient' or 'ai'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))