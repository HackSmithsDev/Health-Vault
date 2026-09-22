from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from .utils import generate_unique_id

# --- SHARED SETTINGS MODEL ---

class SettingsData(db.Model):
    """
    Unified preferences for both Providers and Patients.
    Handles UI customization and AI behavior.
    """
    __tablename__ = 'settings_data'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys for dual-user architecture
    provider_id = db.Column(db.String(50), db.ForeignKey('providers.id'), nullable=True)
    patient_id = db.Column(db.String(50), db.ForeignKey('patients.id'), nullable=True)
    
    # UI Customization
    language = db.Column(db.String(50), default='English')
    font_style = db.Column(db.String(50), default='system')
    font_size = db.Column(db.Integer, default=14)
    
    # AI Engine Configuration
    intelligence_mode = db.Column(db.String(50), default='Instant')
    agent_avatar_path = db.Column(db.String(255), default='assets/avatars/default_agent.png')
    
    # Compliance & Reporting
    show_digital_stamp = db.Column(db.Boolean, default=True)
    header_style = db.Column(db.String(50), default='Standard')

    def __repr__(self):
        owner = f"Provider:{self.provider_id}" if self.provider_id else f"Patient:{self.patient_id}"
        return f'<SettingsData for {owner}>'
    
    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        self.language = 'English'
        self.font_style = 'system'
        self.font_size = 14
        self.intelligence_mode = 'Instant'
        self.agent_avatar_path = 'assets/avatars/default_agent.png'
        self.show_digital_stamp = True
        self.header_style = 'Standard'


# --- PROVIDER MODEL (Hospitals, Clinics, Practitioners) ---

class Provider(db.Model, UserMixin):
    """Professional medical user with institutional authority."""
    __tablename__ = 'providers'
    
    id = db.Column(db.String(50), primary_key=True, default=generate_unique_id)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Institutional Identity
    full_name = db.Column(db.String(150), nullable=False)
    institution_name = db.Column(db.String(200))
    hospital_license = db.Column(db.String(50))
    personal_license = db.Column(db.String(50))
    date_of_registration = db.Column(db.Date)
    profession = db.Column(db.String(100)) # e.g., Oncology, Radiology
    experience = db.Column(db.Integer, default=0)
    
    # Clinical Assets
    avatar_path = db.Column(db.String(255), default='assets/avatars/default_doctor.png')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship: 1-to-1 with Settings
    settings_data = db.relationship('SettingsData', backref='provider', uselist=False, cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


# --- PATIENT MODEL (Health Consumers) ---

class Patient(db.Model, UserMixin):
    """End-user receiving clinical insights or educational courses."""
    __tablename__ = 'patients'
    
    id = db.Column(db.String(50), primary_key=True, default=generate_unique_id)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Patient Identity
    full_name = db.Column(db.String(150), nullable=False)
    medical_record_number = db.Column(db.String(50), unique=True) # MRN
    date_of_birth = db.Column(db.Date)
    blood_group = db.Column(db.String(5))
    
    # Assets & Metadata
    avatar_path = db.Column(db.String(255), default='assets/avatars/default_patient.png')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship: 1-to-1 with Settings
    settings_data = db.relationship('SettingsData', backref='patient', uselist=False, cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    issue_type = db.Column(db.String(50), nullable=False)
    issue_details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    provider_id = db.Column(db.String(50), db.ForeignKey('providers.id'), nullable=True)
    patient_id = db.Column(db.String(50), db.ForeignKey('patients.id'), nullable=True)