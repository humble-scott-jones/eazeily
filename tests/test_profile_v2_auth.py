"""
Tests for /api/profile_v2 authentication handling.

Ensures the endpoint returns proper JSON responses for auth cases:
- Returns profile data when session exists
- Does NOT return 401 for anonymous users (profile is session-based, not auth-required)
- Returns valid JSON (never HTML) for all error cases
"""

import json
import pytest


def test_profile_v2_works_without_authentication(client):
    """
    Test that profile_v2 works for anonymous users (session-based profiles).
    
    The app uses session-based profiles (not user accounts), so anonymous
    users should be able to save and retrieve profiles without authentication.
    """
    # Anonymous user creates a profile
    response = client.post('/api/profile', 
        json={'company': 'Anonymous Co', 'tone': 'friendly'},
        content_type='application/json')
    assert response.status_code == 200
    
    # Anonymous user can retrieve profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    assert data['profile']['company'] == 'Anonymous Co'


def test_profile_v2_returns_json_not_html(client):
    """Test that profile_v2 always returns JSON, never HTML."""
    response = client.get('/api/profile_v2')
    
    # Check Content-Type header
    assert response.content_type.startswith('application/json')
    
    # Verify it's valid JSON
    data = json.loads(response.data)
    assert isinstance(data, dict)
    
    # Should not contain HTML
    response_text = response.data.decode('utf-8')
    assert '<!doctype' not in response_text.lower()
    assert '<html' not in response_text.lower()


def test_profile_v2_with_authenticated_user(client):
    """Test profile_v2 works for authenticated users."""
    # Create and login a user
    client.post('/signup', data={
        'email': 'test@example.com',
        'password': 'password123',
        'name': 'Test User'
    }, follow_redirects=True)
    
    # Create profile as authenticated user
    profile_data = {
        'company': 'Auth Test Inc',
        'industry': 'technology',
        'tone': 'professional',
        'platforms': ['linkedin']
    }
    
    response = client.post('/api/profile', 
        json=profile_data,
        content_type='application/json')
    assert response.status_code == 200
    
    # Fetch profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    assert data['profile']['company'] == 'Auth Test Inc'
    assert data['profile_status'] == 'ready'


def test_profile_v2_error_response_format(client, monkeypatch):
    """Test that error responses follow the expected format."""
    # Simulate a database error by breaking the get_db function
    def broken_get_db():
        raise Exception("Simulated DB error")
    
    import app as app_module
    monkeypatch.setattr(app_module, 'get_db', broken_get_db)
    
    response = client.get('/api/profile_v2')
    
    # Should return 500 but with valid JSON
    assert response.status_code == 500
    assert response.content_type.startswith('application/json')
    
    data = json.loads(response.data)
    
    # Check error response structure
    assert data['ok'] is False
    assert 'request_id' in data
    assert 'error' in data
    assert isinstance(data['error'], dict)
    assert 'code' in data['error']
    assert 'message' in data['error']
    assert data['error']['code'] == 'internal_error'


def test_profile_v2_preserves_session_profile(client):
    """Test that profile_v2 correctly retrieves session-based profiles."""
    # Create a profile in session
    response = client.post('/api/profile', 
        json={
            'company': 'Session Co',
            'industry': 'healthcare',
            'tone': 'professional',
            'platforms': ['facebook', 'instagram']
        },
        content_type='application/json')
    
    assert response.status_code == 200
    profile_response = json.loads(response.data)
    profile_id = profile_response['id']
    
    # Fetch with profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Should match the profile we created
    assert data['profile']['id'] == profile_id
    assert data['profile']['company'] == 'Session Co'
    assert data['profile']['industry'] == 'healthcare'
    assert data['profile']['signature_tone'] == 'professional'
    assert 'facebook' in data['profile']['platforms']
    assert 'instagram' in data['profile']['platforms']
