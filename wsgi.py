import os
from app import create_app
from config import DevelopmentConfig, ProductionConfig

# Determine which configuration to use based on an environment variable
# Default to Development if not specified
env = os.getenv('FLASK_ENV', 'development')

if env == 'production':
    app = create_app(ProductionConfig)
else:
    app = create_app(DevelopmentConfig)

if __name__ == "__main__":
    # In a clinical/production environment, we use 0.0.0.0 to 
    # allow access within a hospital local network if needed.
    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('FLASK_RUN_PORT'))