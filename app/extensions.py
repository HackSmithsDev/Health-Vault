from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_executor import Executor
from flask_migrate import Migrate

# Initialize the extensions without an app object
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
executor = Executor()
migrate = Migrate()