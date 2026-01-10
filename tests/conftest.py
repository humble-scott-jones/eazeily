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


def get_user_row(db_path, email):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()
    con.close()
    return r
