import os
import logging
from flask import Flask
from flask_login import LoginManager
from whitenoise import WhiteNoise
from models import db, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database Configuration
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///local.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    try:
        db.init_app(app)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # WhiteNoise for Static Files
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

    # Register Blueprints
    from routes.wizard import wizard_bp
    app.register_blueprint(wizard_bp)

    # Auto-create tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully.")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            # We might want to continue even if this fails, or fail hard.
            # For now, log it.

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
