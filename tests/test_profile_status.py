"""Tests for profile status determination and endpoint response."""
import pytest
from app import app


def test_profile_status_missing_when_no_profile(client):
    """When no profile exists, profile_status should be 'missing'."""
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('ok') is True
    assert body.get('profile_status') == 'missing'
    assert body.get('reason')
    assert 'No profile settings' in body.get('reason')
    assert body.get('recommended_action')
    assert 'Setup Wizard' in body.get('recommended_action')


def test_profile_status_partial_when_incomplete(client):
    """When profile has some but not all fields, status should be 'partial'."""
    # Save partial profile with just company
    payload = {'company': 'Test Co'}
    client.post('/api/profile', json=payload)
    
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('ok') is True
    assert body.get('profile_status') == 'partial'
    assert body.get('reason')
    assert 'incomplete' in body.get('reason').lower()


def test_profile_status_partial_when_missing_tone(client):
    """When profile has company/industry but no tone, status should be 'partial'."""
    payload = {
        'company': 'Test Co',
        'industry': 'Technology',
        'platforms': ['instagram']
    }
    client.post('/api/profile', json=payload)
    
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('ok') is True
    assert body.get('profile_status') == 'partial'
    assert 'tone' in body.get('reason').lower()


def test_profile_status_ready_when_complete(client):
    """When profile has all key fields, status should be 'ready'."""
    payload = {
        'company': 'Complete Co',
        'industry': 'Technology',
        'tone': 'professional',
        'platforms': ['instagram', 'linkedin'],
        'brand_keywords': ['innovation', 'tech']
    }
    client.post('/api/profile', json=payload)
    
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('ok') is True
    assert body.get('profile_status') == 'ready'
    assert body.get('reason') is None
    assert body.get('recommended_action') is None


def test_profile_status_ready_with_minimal_fields(client):
    """Profile with just industry, tone, and platforms should be 'ready'."""
    payload = {
        'industry': 'Retail',
        'tone': 'friendly',
        'platforms': ['instagram']
    }
    client.post('/api/profile', json=payload)
    
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('ok') is True
    assert body.get('profile_status') == 'ready'


def test_profile_includes_request_id(client):
    """Profile endpoint should always include request_id."""
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('request_id')
    assert isinstance(body.get('request_id'), str)


def test_profile_stable_schema_on_error(client, monkeypatch):
    """When DB errors occur, response should still have stable schema."""
    def boom():
        raise RuntimeError('db unavailable')
    
    # Import app module to patch get_db
    import app as app_module
    monkeypatch.setattr(app_module, 'get_db', boom)
    
    resp = client.get('/api/profile')
    assert resp.status_code == 500
    body = resp.get_json()
    assert body.get('ok') is False
    assert body.get('error')
    assert body.get('request_id')
