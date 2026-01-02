import os
import logging
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
from whitenoise import WhiteNoise
from models import db, User, bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database Configuration
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///local.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    
    # Auto-create tables (safe - only creates if they don't exist)
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Seed Admin Users
            admin_emails = [e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', '').split(',') if e.strip()]
            dev_pw = os.environ.get('DEV_ADMIN_PW')
            
            if admin_emails and dev_pw:
                for email in admin_emails:
                    if not User.query.filter_by(email=email).first():
                        hashed_pw = bcrypt.generate_password_hash(dev_pw).decode('utf-8')
                        admin_user = User(email=email, password_hash=hashed_pw)
                        db.session.add(admin_user)
                        logger.info(f"Created admin user: {email}")
                db.session.commit()
                
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            # Don't raise - let the app start even if DB creation fails
            # This allows healthcheck to pass while DB issues are debugged
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # WhiteNoise for Static Files
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

    # Register Blueprints
    from routes.wizard import wizard_bp, dashboard_bp
    from routes.auth_routes import auth_bp
    from routes.generate_routes import generate_bp
    app.register_blueprint(wizard_bp)
    app.register_blueprint(auth_bp)
    # app.register_blueprint(dashboard_bp) # Replaced by generate_bp's dashboard
    app.register_blueprint(generate_bp)

    # Root route and health endpoint so the staging domain has content and Railway healthchecks succeed
    @app.route('/')
    def index():
        return render_template('base.html', content='Welcome to Eazeily — Gemini Native')

    @app.route('/healthz')
    def healthz():
        return jsonify(status='ok'), 200

    # Health check endpoints for Railway
    @app.route('/healthz')
    def health_check():
        return "OK", 200
    
    @app.route('/up')
    def up_check():
        return "OK", 200

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Server Error: {error}")
        return jsonify({"error": "Internal Server Error", "details": str(error)}), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
