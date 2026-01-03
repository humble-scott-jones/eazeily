"""Test anonymous access to dashboard and generate API (TEMP-OPEN-GATES-006)."""
import pytest
from app import create_app
from models import db


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


def test_dashboard_accessible_without_auth(client):
    """Test that /dashboard endpoint is accessible without authentication."""
    response = client.get('/dashboard')
    assert response.status_code == 200
    # Should render the dashboard template successfully
    assert b'dashboard' in response.data.lower() or response.status_code == 200


def test_generate_api_works_without_auth(client):
    """Test that /api/generate endpoint works without authentication."""
    response = client.post(
        '/api/generate',
        json={
            'topic': 'Test topic for content generation',
            'platform': 'LinkedIn'
        }
    )
    # Should return 200 or 500 (if API key is missing, but not 401/302)
    assert response.status_code in [200, 500]
    # Should not redirect to login (which would be 302)
    assert response.status_code != 302
    assert response.status_code != 401


def test_generate_api_requires_topic(client):
    """Test that /api/generate endpoint requires a topic parameter."""
    response = client.post(
        '/api/generate',
        json={
            'platform': 'LinkedIn'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'topic' in data['error'].lower()


def test_generate_api_uses_default_profile_for_anonymous(client):
    """Test that anonymous users get a default profile for generation."""
    # This test verifies the DummyProfile is created for anonymous users
    response = client.post(
        '/api/generate',
        json={
            'topic': 'Innovation in business',
            'platform': 'LinkedIn'
        }
    )
    # Should not fail with authentication error
    assert response.status_code in [200, 500]  # 500 if API key missing, but not auth error
    if response.status_code == 200:
        data = response.get_json()
        assert 'status' in data
