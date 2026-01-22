import os
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from flask import Flask, request, jsonify, render_template, g, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
CORS(app)

# Database setup
# Default to local postgres if not set
DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/togetherly_v2")

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        g.db.autocommit = True
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS waitlist (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE,
                confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

@app.before_request
def ensure_db():
    # In production, migrate properly. For now, init if needed.
    pass # Disabling auto-init on every request for Postgres performance

@app.context_processor
def utility_processor():
    """Provide URL helpers for template."""
    def auth_signup():
        return url_for('auth_signup')
    def auth_login():
        return url_for('auth_login')
    def generate_dashboard():
        return url_for('generate_dashboard')
    
    # Mock url_for for auth and generate namespaces
    class URLFor:
        def __call__(self, endpoint):
            if endpoint == 'auth.signup':
                return url_for('auth_signup')
            elif endpoint == 'auth.login':
                return url_for('auth_login')
            elif endpoint == 'generate.dashboard':
                return url_for('generate_dashboard')
            return '#'
    
    return dict(url_for=URLFor())

# Dummy routes for URL generation
@app.route("/signup")
def auth_signup():
    """Placeholder signup route."""
    return "Signup page - this is a demo landing page"

@app.route("/login")
def auth_login():
    """Placeholder login route."""
    return "Login page - this is a demo landing page"

@app.route("/dashboard")
def generate_dashboard():
    """Placeholder dashboard route."""
    return "Dashboard - this is a demo landing page"

@app.get("/")
def landing():
    """Landing page with email collection."""
    # For standalone landing page, we don't have user auth
    # So provide a simple object that always returns False
    class AnonymousUser:
        @property
        def is_authenticated(self):
            return False
    
    return render_template("landing.html", current_user=AnonymousUser())

@app.post("/api/waitlist")
def api_waitlist():
    """Add email to waitlist."""
    try:
        data = request.get_json(force=True)
        email = (data.get('email') or '').strip().lower()

        if not email or '@' not in email:
            return jsonify({'ok': False, 'error': 'Invalid email address'}), 400

        db = get_db()
        with db.cursor() as cur:
             cur.execute("INSERT INTO waitlist (email) VALUES (%s)", (email,))
        # autocommit is on

        return jsonify({'ok': True, 'message': 'Successfully added to waitlist'})

    except psycopg2.IntegrityError:
        return jsonify({'ok': False, 'error': 'Email already registered'}), 400
    except Exception as e:
        return jsonify({'ok': False, 'error': 'Server error'}), 500

@app.get("/health")
def health_check():
    """Health check endpoint for Railway."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
