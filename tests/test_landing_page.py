"""Tests for landing page and waitlist functionality."""
import json


def test_landing_page_renders(client):
    """Test that landing page route exists and renders."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Togetherly' in response.data
    assert b'Simple, smart social media' in response.data
    assert b'that sounds like you' in response.data


def test_landing_page_has_pricing(client):
    """Test that landing page includes pricing information."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'pricing' in response.data.lower()
    assert b'$14' in response.data or b'Pro' in response.data


def test_landing_page_has_features(client):
    """Test that landing page includes features section."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'features' in response.data.lower()
    assert b'Industry-Specific' in response.data or b'industry' in response.data.lower()


def test_landing_page_has_waitlist_form(client):
    """Test that landing page includes waitlist signup form."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'waitlist' in response.data.lower() or b'Get Started' in response.data


def test_app_route_exists(client):
    """Test that /app route exists for main application."""
    response = client.get('/app')
    assert response.status_code == 200
    assert b'Togetherly' in response.data


def test_waitlist_api_valid_email(client):
    """Test waitlist API with valid email."""
    response = client.post('/api/waitlist', 
                          json={'email': 'test@example.com'},
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['ok'] is True


def test_waitlist_api_invalid_email(client):
    """Test waitlist API with invalid email."""
    response = client.post('/api/waitlist',
                          json={'email': 'invalid-email'},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['ok'] is False
    assert 'email' in data['error'].lower()


def test_waitlist_api_duplicate_email(client):
    """Test waitlist API prevents duplicate emails."""
    email = 'duplicate@example.com'
    
    # First submission should succeed
    response1 = client.post('/api/waitlist',
                           json={'email': email},
                           content_type='application/json')
    assert response1.status_code == 200
    
    # Second submission should fail
    response2 = client.post('/api/waitlist',
                           json={'email': email},
                           content_type='application/json')
    assert response2.status_code == 400
    data = json.loads(response2.data)
    assert data['ok'] is False
    assert 'already' in data['error'].lower()


def test_waitlist_api_missing_email(client):
    """Test waitlist API with missing email."""
    response = client.post('/api/waitlist',
                          json={},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['ok'] is False
