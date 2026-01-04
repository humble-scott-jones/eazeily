"""Test the /emergency-hatch database reset route."""
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


def test_emergency_hatch_without_key_returns_403(client):
    """Test that /emergency-hatch without key returns 403."""
    response = client.get('/emergency-hatch')
    assert response.status_code == 403
    assert b'Unauthorized' in response.data


def test_emergency_hatch_with_wrong_key_returns_403(client):
    """Test that /emergency-hatch with wrong key returns 403."""
    response = client.get('/emergency-hatch?key=wrong-key')
    assert response.status_code == 403
    assert b'Unauthorized' in response.data


def test_emergency_hatch_with_correct_key_resets_database(client, app):
    """Test that /emergency-hatch with correct key resets the database."""
    # First, create a different user
    with app.app_context():
        hashed_pw = bcrypt.generate_password_hash('testpass').decode('utf-8')
        user = User(email='test@example.com', password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        
        # Verify user exists
        assert User.query.filter_by(email='test@example.com').first() is not None
    
    # Now trigger the emergency hatch
    response = client.get('/emergency-hatch?key=let-me-in')
    assert response.status_code == 200
    assert b'System Reset Successful' in response.data
    assert b'/auth/login' in response.data
    
    # Verify old user is gone and new user exists
    with app.app_context():
        assert User.query.filter_by(email='test@example.com').first() is None
        admin_user = User.query.filter_by(email='hi.scott.jones@gmail.com').first()
        assert admin_user is not None


def test_emergency_hatch_creates_specific_admin_user(client, app):
    """Test that /emergency-hatch creates the specific admin user with correct credentials."""
    response = client.get('/emergency-hatch?key=let-me-in')
    assert response.status_code == 200
    
    # Verify the specific user was created
    with app.app_context():
        admin_user = User.query.filter_by(email='hi.scott.jones@gmail.com').first()
        assert admin_user is not None
        assert admin_user.email == 'hi.scott.jones@gmail.com'
        
        # Verify the password is correct
        assert bcrypt.check_password_hash(admin_user.password_hash, 'password123')


def test_emergency_hatch_success_message_includes_credentials(client):
    """Test that successful emergency hatch returns credentials in response."""
    response = client.get('/emergency-hatch?key=let-me-in')
    assert response.status_code == 200
    assert b'hi.scott.jones@gmail.com' in response.data
    assert b'password123' in response.data
    assert b'Go to Login' in response.data
    assert b'href' in response.data
    assert b'/auth/login' in response.data


def test_emergency_hatch_response_has_success_indicator(client):
    """Test that the response has a visual success indicator."""
    response = client.get('/emergency-hatch?key=let-me-in')
    assert response.status_code == 200
    assert b'System Reset Successful' in response.data
    # Check for the green color indicator
    assert b"color: green" in response.data
