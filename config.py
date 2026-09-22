import os
from dotenv import load_dotenv

# Load the .env file from the root directory
load_dotenv()

class Config:
    """Base configuration."""
    # Application Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    
    # PostgreSQL Connection
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Mail Credentials
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # Flask-Executor Configuration
    EXECUTOR_TYPE = 'thread'
    EXECUTOR_MAX_WORKERS = 4 # Adjust based on your CPU for AI tasks [cite: 78]

    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')

    # AI Model Paths
    AI_WEIGHTS_DIR = os.path.join(os.getcwd(), 'ai', 'weights')

class DevelopmentConfig(Config):
    """Development-specific config."""
    DEBUG = True

class ProductionConfig(Config):
    """Production-specific config."""
    DEBUG = False
    # In production, we'd ensure TLS is strictly enforced