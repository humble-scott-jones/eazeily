"""Test that dashboard and generate routes require authentication."""
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


def test_dashboard_requires_authentication(client):
    """Test that /dashboard redirects to login when not authenticated."""
    response = client.get('/dashboard')
    # Flask-Login redirects to login page when @login_required fails
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_generate_api_requires_authentication(client):
    """Test that /api/generate redirects to login when not authenticated."""
    response = client.post(
        '/api/generate',
        json={
            'topic': 'Test topic',
            'platform': 'LinkedIn'
        }
    )
    # Flask-Login redirects to login page for unauthenticated requests
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_dashboard_accessible_when_authenticated(client, app):
    """Test that /dashboard is accessible when authenticated."""
    # Create and login a user
    with app.app_context():
        hashed_pw = bcrypt.generate_password_hash('testpass').decode('utf-8')
        user = User(email='test@example.com', password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
    
    # Login
    login_response = client.post(
        '/auth/login',
        json={'email': 'test@example.com', 'password': 'testpass'}
    )
    assert login_response.status_code == 200
    
    # Now access dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200


def test_generate_api_accessible_when_authenticated(client, app):
    """Test that /api/generate works when authenticated."""
    # Create and login a user
    with app.app_context():
        hashed_pw = bcrypt.generate_password_hash('testpass').decode('utf-8')
        user = User(email='test@example.com', password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
    
    # Login
    login_response = client.post(
        '/auth/login',
        json={'email': 'test@example.com', 'password': 'testpass'}
    )
    assert login_response.status_code == 200
    
    # Now access generate API
    response = client.post(
        '/api/generate',
        json={
            'topic': 'Innovation in business',
            'platform': 'LinkedIn'
        }
    )
    # Should return 200 or 500 (if API key missing), but not 401
    assert response.status_code in [200, 500]
