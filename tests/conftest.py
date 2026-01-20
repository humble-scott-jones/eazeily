import os
import sys
import tempfile
import json
import sqlite3
import pytest
from pathlib import Path

# ensure repo root is on sys.path so `import app` works when pytest runs
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Use reduced PBKDF2 iterations during tests unless the caller explicitly
# overrides the setting. This keeps the suite from spending most of its time
# hashing passwords created by signup/login flows.
os.environ.setdefault('FAST_PASSWORD_HASH', '12000')
os.environ.setdefault('FLASK_ENV', 'test')
os.environ.setdefault('DISABLE_RATE_LIMITS', '1')

# Skip e2e tests requiring playwright unless explicitly enabled
collect_ignore_glob = []
if os.getenv('RUN_UI_SMOKE') != '1':
    collect_ignore_glob.append('e2e/*.py')

import app as togetherly_app
from tests.e2e.conftest import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('ALLOW_DEV_DEBUG', '1')
    monkeypatch.delenv('ADMIN_EMAILS', raising=False)
    monkeypatch.delenv('DATABASE_URL', raising=False)
    # Use a temporary database file for isolation
    db_file = tmp_path / "test_togetherly.db"
    # Set TEST_DB_PATH env var BEFORE importing/creating the app
    monkeypatch.setenv('TEST_DB_PATH', str(db_file))
    
    # Now set the module-level DB_PATH for compatibility
    togetherly_app.DB_PATH = str(db_file)
    
    # Create a fresh app instance with the test database
    from app import create_app
    test_app = create_app()
    test_app.DB_PATH = str(db_file)  # type: ignore[attr-defined]
    test_app.config['TESTING'] = True
    
    # Initialize the database with SQLAlchemy
    with test_app.app_context():
        from models import db
        db.create_all()
    
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_client(client, tmp_path, monkeypatch):
    """Fixture that provides a client with an authenticated user session."""
    # Set fake API key for tests
    monkeypatch.setenv('GENAI_API_KEY', 'test-fake-api-key-for-testing')
    
    from models import User, VoiceProfile, db
    from app import create_app
    
    # Create test app context
    test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    
    with test_app.app_context():
        # Create a test user
        user = User(email='test@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # Create a test profile for the user
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business',
            industry='Technology',
            target_audience='Small businesses',
            brand_voice='Professional and friendly',
            key_offer='Quality software solutions'
        )
        profile.set_writing_samples(['Sample post about technology.', 'Another example post.'])
        db.session.add(profile)
        db.session.commit()
        
        # Store user ID for session setup
        user_id = user.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    return client


def get_user_row(db_path, email):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()
    con.close()
    return r
