import os
import logging
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
from sqlalchemy import inspect
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

            # Runtime schema fix: ensure common columns exist (helps recover older DBs)
            try:
                inspector = inspect(db.engine)
                if 'user' in inspector.get_table_names():
                    user_columns = [c['name'] for c in inspector.get_columns('user')]
                    if 'created_at' not in user_columns:
                        dialect = db.engine.dialect.name
                        logger.info(f"Adding missing column created_at to 'user' table for dialect {dialect}")
                        if dialect == 'postgresql':
                            db.session.execute('ALTER TABLE "user" ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();')
                        elif dialect == 'sqlite':
                            # SQLite supports adding a column but without NOT NULL constraints if table already exists
                            db.session.execute('ALTER TABLE user ADD COLUMN created_at DATETIME;')
                        else:
                            # Fallback: try a generic TIMESTAMP column
                            db.session.execute('ALTER TABLE "user" ADD COLUMN created_at TIMESTAMP;')
                        db.session.commit()
            except Exception as se:
                # Log and continue; schema fixes are best-effort in staging/dev only
                logger.warning(f"Runtime schema check failed: {se}")

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
        return render_template('index.html')

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

# CLI Commands
import click
from flask.cli import with_appcontext

@app.cli.command("create-admin")
@click.argument("email")
@click.argument("password")
@with_appcontext
def create_admin(email, password):
    """Creates a new admin user."""
    # Check if user exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        print(f"User {email} already exists.")
        return

    # Create new user
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(email=email, password_hash=hashed_pw)

    db.session.add(user)
    db.session.commit()
    print(f"Successfully created admin: {email}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
