from app import db
from .user_models import Provider, Patient, SettingsData, Reviews
from .clinicals_models import DiagnosticUnit, Subject, Chapter, ClinicalSession, MedicalImage, DiagnosticReport, Message, SupportMessage

# Export for easy importing elsewhere
__all__ = ["Provider", "Patient", "SettingsData", "Reviews", "DiagnosticUnit", "Subject", "Chapter", "ClinicalSession", "MedicalImage", "DiagnosticReport", "Message", "SupportMessage"]