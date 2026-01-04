import os
import logging
from flask import Flask, render_template, jsonify, request
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
                        admin_user = User(email=email, password_hash='')  # Temporary value
                        admin_user.set_password(dev_pw)
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

    # Database reset route (for development/staging use only)
    @app.route('/nuke-db')
    def nuke_db():
        # Simple safety lock
        if request.args.get('key') != 'reset-me-now':
            return "Unauthorized", 403

        # The Nuclear Option
        db.drop_all()
        db.create_all()
        return "💥 Database wiped and recreated. <a href='/auth/signup'>Go Sign Up</a>"

    # Emergency Hatch Route - for staging recovery
    @app.route('/emergency-hatch')
    def emergency_hatch():
        # 1. Simple Security Lock
        if request.args.get('key') != 'let-me-in':
            return "Unauthorized", 403

        # 2. The Wipe
        try:
            db.drop_all()
            db.create_all()

            # 3. The Admin Creation
            admin = User(email="hi.scott.jones@gmail.com", password_hash='')  # Temporary value
            admin.set_password("password123")

            db.session.add(admin)
            db.session.commit()

            return """
            <div style='font-family: sans-serif; padding: 20px;'>
                <h1 style='color: green;'>✅ System Reset Successful</h1>
                <p>The database has been wiped and restored.</p>
                <p><strong>Your Login Credentials:</strong></p>
                <ul>
                    <li>Email: <b>hi.scott.jones@gmail.com</b></li>
                    <li>Password: <b>password123</b></li>
                </ul>
                <br>
                <a href='/auth/login' style='background: #000; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>Go to Login</a>
            </div>
            """
        except Exception as e:
            return f"<h1 style='color: red;'>Error: {str(e)}</h1>"

    @app.route('/reset-password-tool', methods=['GET', 'POST'])
    def reset_password_tool():
        """Admin password reset tool - allows resetting any user's password."""
        # Simple security key to prevent public abuse
        if request.args.get('key') != 'fix-my-auth':
            return "Unauthorized", 403

        if request.method == 'POST':
            email = request.form.get('email')
            new_pass = request.form.get('password')

            if not email or not new_pass:
                return "Email and password required", 400

            user = User.query.filter_by(email=email).first()

            if not user:
                return "User not found", 404

            # Uses the FIXED logic from User model
            user.set_password(new_pass)
            db.session.commit()

            return f"Password for {email} has been reset. <a href='/auth/login'>Login Now</a>"

        return """
        <form method="POST">
            <h3>Admin Password Reset</h3>
            <input type="email" name="email" placeholder="User Email" required style="display:block; margin: 10px 0;">
            <input type="text" name="password" placeholder="New Password" required style="display:block; margin: 10px 0;">
            <button type="submit">Reset Password</button>
        </form>
        """

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
    user = User(email=email, password_hash='')  # Temporary value
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    print(f"Successfully created admin: {email}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
