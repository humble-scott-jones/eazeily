"""Test the /nuke-db database reset route."""
import pytest
from app import create_app
from models import db, User, bcrypt


@pytest.fixture
def app():
    """Create a test Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


def test_nuke_db_without_key_returns_403(client):
    """Test that /nuke-db without key returns 403."""
    response = client.get('/nuke-db')
    assert response.status_code == 403
    assert b'Unauthorized' in response.data


def test_nuke_db_with_wrong_key_returns_403(client):
    """Test that /nuke-db with wrong key returns 403."""
    response = client.get('/nuke-db?key=wrong-key')
    assert response.status_code == 403
    assert b'Unauthorized' in response.data


def test_nuke_db_with_correct_key_resets_database(client, app):
    """Test that /nuke-db with correct key resets the database."""
    # First, create a user
    with app.app_context():
        hashed_pw = bcrypt.generate_password_hash('testpass').decode('utf-8')
        user = User(email='test@example.com', password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        
        # Verify user exists
        assert User.query.filter_by(email='test@example.com').first() is not None
    
    # Now nuke the database
    response = client.get('/nuke-db?key=reset-me-now')
    assert response.status_code == 200
    assert b'Database wiped and recreated' in response.data
    assert b'/auth/signup' in response.data
    
    # Verify user is gone
    with app.app_context():
        assert User.query.filter_by(email='test@example.com').first() is None


def test_nuke_db_success_message_includes_signup_link(client):
    """Test that successful nuke returns a link to signup."""
    response = client.get('/nuke-db?key=reset-me-now')
    assert response.status_code == 200
    assert b'Go Sign Up' in response.data
    assert b'href' in response.data
    assert b'/auth/signup' in response.data
