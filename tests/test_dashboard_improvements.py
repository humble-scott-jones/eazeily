"""Test the dashboard navigation and generation improvements."""
import pytest
from app import create_app
from models import db, User, VoiceProfile
import os


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    with app.app_context():
        # Create a test user for each test
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            user = User(email='test@example.com', password_hash='')
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
    
    return app.test_client()


@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client."""
    # Login
    response = client.post('/auth/login', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    return client


def test_dashboard_requires_authentication(client):
    """Test that dashboard requires login."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_dashboard_accessible_when_authenticated(authenticated_client):
    """Test that authenticated users can access dashboard."""
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    assert b'Co-Pilot Content Generator' in response.data


def test_navigation_menu_has_logout_link(authenticated_client):
    """Test that navigation menu includes logout link."""
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Check for logout link
    assert 'logout' in html.lower() or 'log out' in html.lower()
    assert '/auth/logout' in html


def test_navigation_menu_has_mobile_menu_button(authenticated_client):
    """Test that navigation includes mobile menu button."""
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Check for mobile menu button
    assert 'mobile-menu-button' in html


def test_settings_route_redirects_to_onboarding(authenticated_client):
    """Test that settings route redirects to onboarding."""
    response = authenticated_client.get('/settings', follow_redirects=False)
    assert response.status_code == 302
    assert '/onboarding' in response.location


def test_generate_api_without_api_key_returns_503(authenticated_client, monkeypatch):
    """Test that generate API returns 503 when API key is missing."""
    # Remove API keys from environment
    monkeypatch.delenv('GENAI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    
    response = authenticated_client.post('/api/generate', json={
        'topic': 'Test post',
        'platform': 'LinkedIn',
        'task_type': 'post'
    })
    
    assert response.status_code == 503
    data = response.get_json()
    assert 'error' in data
    assert 'not configured' in data['error'] or 'API key' in data['error']


def test_generate_api_validates_topic_required(authenticated_client):
    """Test that generate API validates required topic field."""
    response = authenticated_client.post('/api/generate', json={
        'platform': 'LinkedIn',
        'task_type': 'post'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Topic is required' in data['error']


def test_logout_endpoint_works(authenticated_client):
    """Test that logout endpoint works."""
    response = authenticated_client.get('/auth/logout')
    assert response.status_code == 200
    
    # Try to access dashboard after logout
    response = authenticated_client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.location


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
