import os
import sqlite3
import uuid
from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
CORS(app)

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "swelly.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            confirmed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()

@app.before_request
def ensure_db():
    init_db()

@app.get("/")
def landing():
    """Landing page with email collection."""
    return render_template("landing.html")

@app.post("/api/waitlist")
def api_waitlist():
    """Add email to waitlist."""
    try:
        data = request.get_json(force=True)
        email = (data.get('email') or '').strip().lower()

        if not email or '@' not in email:
            return jsonify({'ok': False, 'error': 'Invalid email address'}), 400

        db = get_db()
        db.execute("INSERT INTO waitlist (email) VALUES (?)", (email,))
        db.commit()

        return jsonify({'ok': True, 'message': 'Successfully added to waitlist'})

    except sqlite3.IntegrityError:
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
