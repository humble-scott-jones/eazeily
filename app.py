import os
import logging
import sqlite3
from flask import Flask, render_template, jsonify, request
from flask_login import LoginManager
from sqlalchemy import inspect, text
from whitenoise import WhiteNoise
from models import db, User, bcrypt

# Optional sqlite path used by tests
DB_PATH = os.getenv("DB_PATH")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db():
    """Return a sqlite3 connection when DB_PATH is set (used in tests)."""
    if DB_PATH:
        conn = sqlite3.connect(DB_PATH)
        return conn
    raise RuntimeError("DB_PATH not configured for sqlite test database")

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database Configuration
    # Check if we're in test mode (DB_PATH env var or module variable is set by tests)
    test_db_path = os.getenv('TEST_DB_PATH') or DB_PATH
    if test_db_path:
        # Use SQLite for tests
        db_url = f'sqlite:///{test_db_path}'
        logger.info(f"Using SQLite test database: {db_url}")
    else:
        # Use PostgreSQL for production/development
        db_url = os.environ.get("DATABASE_URL")
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        # Enforce Postgres - fail if not configured, or default to local postgres
        if not db_url:
             # Default to local postgres for development if not specified
             db_url = 'postgresql://localhost/togetherly_v2'
             logger.warning(f"DATABASE_URL not set, defaulting to {db_url}")
          
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
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
                        # Postgres specific DDL as default
                        try:
                            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();'))
                            db.session.commit()
                        except Exception as e:
                            logger.error(f"Failed to add column: {e}")
                            db.session.rollback()
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
    from routes.onboarding_routes import onboarding_bp
    from routes.profile_routes import profile_bp
    from routes.scraper_routes import scraper_bp
    from routes.chat_routes import chat_bp
    from routes.history_routes import history_bp
    app.register_blueprint(wizard_bp)
    app.register_blueprint(auth_bp)
    # Register chat_bp before generate_bp so /api/chat routes to the real implementation
    app.register_blueprint(chat_bp)
    # app.register_blueprint(dashboard_bp) # Replaced by generate_bp's dashboard
    app.register_blueprint(generate_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(scraper_bp)
    app.register_blueprint(history_bp)

    # Root route and health endpoint so the staging domain has content and Railway healthchecks succeed
    @app.route('/')
    def index():
        return render_template('landing.html')

    # Health check endpoints for Railway and CI
    @app.route('/healthz')
    def healthz():
        return jsonify(status='ok'), 200
    
    @app.route('/up')
    def up_check():
        return "OK", 200
    
    @app.route('/__dev__/ping')
    def dev_ping():
        """Development/CI health check endpoint."""
        return "pong", 200
    
    # Demo API endpoint for landing page
    @app.route('/api/demo/generate', methods=['POST'])
    def demo_generate():
        """Generate sample content for landing page demo."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid request'}), 400
            
            prompt = data.get('prompt', '').strip()
            
            # Validate input
            if not prompt or len(prompt) > 500:
                return jsonify({'error': 'Prompt must be between 1 and 500 characters'}), 400
            
            # Simple rate limiting: max 10 requests per session
            from flask import session
            if 'demo_count' not in session:
                session['demo_count'] = 0
            
            session['demo_count'] += 1
            if session['demo_count'] > 10:
                return jsonify({'error': 'Demo limit reached. Sign up for unlimited content!'}), 429
            
            prompt_lower = prompt.lower()
            
            # Simple demo responses based on keywords
            responses = {
                'instagram': """🎉 Weekend Sale Alert!

This Saturday & Sunday only: Take 20% off everything in-store and online! Time to treat yourself. 🛍️✨

Tag a friend who needs this! 👇

#WeekendSale #ShopLocal #SmallBusiness #SaleAlert #ShopSmall #SupportLocal""",
                
                'email': """Subject: Exciting News: We're Launching Something New! 🎉

Hey there!

We've been working on something special, and we can't wait to share it with you.

Starting next week, we're introducing [Your New Service]—designed to make your life easier and more enjoyable.

Here's what makes it great:
• Benefit 1: Saves you time
• Benefit 2: Better results
• Benefit 3: Easy to use

Want early access? Reply to this email and you'll be first in line!

Thanks for being part of our community.

[Your Name]
[Your Business]""",
                
                'facebook': """🎯 Special Offer Inside!

Tired of [common problem]? We've got you covered.

For a limited time, get 25% off our most popular product. It's perfect for [target audience] who want [desired outcome].

👉 Click the link in our bio to claim your discount before it's gone!

Limited spots available. Don't miss out! 💪

#Ad #LimitedOffer #SmallBusiness""",
                
                'sale': """🔥 FLASH SALE ALERT 🔥

48 Hours Only! Get 30% off everything in our store.

Whether you've been eyeing [Product A] or [Product B], now's your chance to save big.

Sale ends Sunday at midnight. Shop now! 🛒

#FlashSale #LimitedTime #SaveBig #ShopNow""",
                
                'new': """✨ Something New Has Arrived!

We're thrilled to announce our latest addition: [Product/Service Name]

Perfect for anyone who wants [benefit]. This has been months in the making, and we're so excited to finally share it with you.

Available now—limited quantities! Get yours before they're gone.

#NewArrival #Exciting #SmallBusiness #ShopLocal""",
                
                'product': """Introducing: The Game-Changer You've Been Waiting For

Meet [Product Name]—the solution to [problem].

✨ Feature 1: [Benefit]
✨ Feature 2: [Benefit]  
✨ Feature 3: [Benefit]

Made with love for people who care about quality. Only $[Price] for a limited time.

Ready to upgrade? Link in bio! 🔗

#ProductLaunch #Quality #SmallBusiness"""
            }
            
            # Find matching response
            content = None
            for keyword, response in responses.items():
                if keyword in prompt_lower:
                    content = response
                    break
            
            # Default response if no match
            if not content:
                content = """✨ Here's Your Content!

Based on your request, here's a custom piece of content crafted just for your business.

This would include:
• Your unique brand voice
• Platform-specific formatting
• Relevant hashtags
• Call-to-action

Sign up to create real content with your actual brand voice! 🚀

#ContentCreation #SmallBusiness #Marketing"""
            
            return jsonify({'content': content, 'success': True})
            
        except Exception as e:
            logger.error(f"Demo generation error: {e}")
            return jsonify({'error': 'Something went wrong. Please try again.'}), 500

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
    
    # Brand Engine Reset Route
    @app.route('/reset-brand-engine')
    def reset_brand_engine():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return "Unauthorized", 403
        db.drop_all()
        db.create_all()
        return "✅ Engine Reset. <a href='/onboarding'>Start Onboarding</a>"

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
        """Admin password reset tool - allows resetting any user's password.
        
        Note: Uses simple security key as specified in requirements.
        For production, consider environment variable or OAuth.
        """
        # Simple security key to prevent public abuse (as specified in requirements)
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
            <input type="password" name="password" placeholder="New Password" required style="display:block; margin: 10px 0;">
            <button type="submit">Reset Password</button>
        </form>
        """

    @app.route('/fix-my-account')
    def fix_my_account():
        """Emergency account fix route - rebuilds database with proper schema.
        
        WARNING: This deletes all data. Only use in staging/development.
        """
        # Only for authorized users
        if request.args.get('key') != 'fix-it-now':
            return "403 Forbidden", 403

        # 1. Reset DB Schema (Safe-ish way to ensure column types are right)
        # WARNING: This deletes data. If you have production data, do not run drop_all.
        # For Staging: It is the only way to fix the column type 'String' vs 'Text' issue.
        db.drop_all()
        db.create_all()

        # 2. Create Fresh Admin
        user = User(email="hi.scott.jones@gmail.com")
        user.set_password("password123")  # Uses the NEW robust logic
        db.session.add(user)
        db.session.commit()

        return "✅ Database rebuilt. User 'hi.scott.jones@gmail.com' password set to 'password123'. <a href='/auth/login'>Login</a>"

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Server Error: {error}")
        return jsonify({"error": "Internal Server Error", "details": str(error)}), 500

    return app

app = create_app()


def init_db():
    """Compatibility helper for tests to initialize the configured database."""
    if DB_PATH:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, is_paid INTEGER DEFAULT 0)')
        cur.execute('CREATE TABLE IF NOT EXISTS generation_usage (id TEXT PRIMARY KEY, user_id TEXT, period TEXT, reels_generated INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)')
        conn.commit()
        conn.close()
        return

    with app.app_context():
        db.create_all()

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

# Demo route for typewriter effect (development only)
@app.route('/demo/typewriter')
def typewriter_demo():
    """Demo page for typewriter effect"""
    return render_template('typewriter_demo.html')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
