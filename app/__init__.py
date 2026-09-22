import os
import redis
import fakeredis
from flask import Flask, session
from config import DevelopmentConfig
from .extensions import db, login_manager, mail, executor, migrate
from .models.clinicals_models import DiagnosticUnit

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Directory Logic ---
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    # 32MB limit for high-res medical scans (X-rays/MRIs)
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 
    
    # --- Initialize Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.show_login_dialog'  # Redirect to login dialog for unauthorized access
    mail.init_app(app)
    executor.init_app(app)
    migrate.init_app(app, db) # Links Migration to App + DB

    # --- Optimized Redis Setup ---
    # Using a try/except block to fallback to fakeredis if the server is down
    try:
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379')
        app.redis = redis.from_url(redis_url, decode_responses=True)
        app.redis.ping()
    except (redis.ConnectionError, Exception):
        app.logger.warning("⚠️ Redis server not found. Falling back to FakeRedis.")
        app.redis = fakeredis.FakeRedis(decode_responses=True)

    # --- Blueprint Registration ---
    from .main import main_bp
    from .auth import auth_bp
    from .api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')

    # --- Dual-User Table Loader ---
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user_models import Provider, Patient
        # Retrieve role from session to know which table to query
        role = session.get('user_role') 
        if role == 'patient':
            return Patient.query.get(user_id)
        return Provider.query.get(user_id)

    # --- Startup Tasks ---
    with app.app_context():
        # Create necessary folders for clinical assets
        folders = ['user_avatars', 'clinical_images', 'pdfs']
        for folder in folders:
            path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
            os.makedirs(path, exist_ok=True)
            
        # Ensure weights folder exists for your ResNet-18 pth files
        os.makedirs(app.config.get('AI_WEIGHTS_DIR', 'ai/weights'), exist_ok=True)

    # Global context processor for the sidebar/navigation
    @app.context_processor
    def inject_diagnostic_units():
        # Returns the 4 Units (Pulm, Rad, Hem, Neuro) to every template
        return dict(diagnostic_units=DiagnosticUnit.query.all())

    return app