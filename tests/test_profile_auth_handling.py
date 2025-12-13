"""Test profile API authentication handling for BUG-001."""
import pytest
from app import app


def test_profile_unauth_returns_json_not_html(client):
    """
    Test that unauthenticated requests return JSON response, not HTML.
    
    Note: Currently /api/profile doesn't require authentication, so it
    returns profile_status='missing' for users without profiles. This test
    verifies the response is always JSON, never HTML.
    """
    resp = client.get('/api/profile')
    
    # Should return JSON, not HTML
    assert resp.content_type.startswith('application/json')
    
    # Should return valid JSON response
    body = resp.get_json()
    assert body is not None
    assert isinstance(body, dict)
    
    # Should have standard contract fields
    assert 'ok' in body
    assert 'request_id' in body


def test_profile_no_session_returns_json(client):
    """Profile endpoint without session should return JSON with missing status."""
    # Make request without setting up any session
    resp = client.get('/api/profile')
    
    assert resp.status_code == 200
    assert resp.content_type.startswith('application/json')
    
    body = resp.get_json()
    assert body.get('ok') is True
    assert body.get('profile_status') == 'missing'
    assert 'request_id' in body
