"""Test profile API contract for BUG-001: stable profile endpoint contract."""
import pytest
from app import app


def test_profile_missing_returns_stable_contract(client):
    """GET /api/profile with no profile should return profile_status='missing'."""
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    
    # Verify stable contract fields
    assert body.get('ok') is True
    assert 'request_id' in body
    assert 'profile_status' in body
    assert 'profile' in body
    assert 'warnings' in body
    
    # Verify profile_status is "missing"
    assert body['profile_status'] == 'missing'
    assert isinstance(body['warnings'], list)
    assert len(body['warnings']) > 0
    
    # Profile should still be a valid dict with defaults
    profile = body['profile']
    assert isinstance(profile, dict)
    assert profile.get('company') == ''
    assert profile.get('industry') == ''
    assert profile.get('tone') == ''


def test_profile_partial_returns_stable_contract(client):
    """Profile with some fields should return profile_status='partial'."""
    # Create a profile with only company set
    payload = {'company': 'Test Co'}
    create_resp = client.post('/api/profile', json=payload)
    assert create_resp.status_code == 200
    
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    
    # Verify stable contract
    assert body.get('ok') is True
    assert 'request_id' in body
    assert 'profile_status' in body
    assert 'profile' in body
    assert 'warnings' in body
    
    # Should be partial (has company but missing other fields)
    assert body['profile_status'] == 'partial'
    assert isinstance(body['warnings'], list)
    assert len(body['warnings']) > 0
    
    profile = body['profile']
    assert profile.get('company') == 'Test Co'


def test_profile_ready_returns_stable_contract(client):
    """Profile with all key fields should return profile_status='ready'."""
    payload = {
        'company': 'Complete Co',
        'industry': 'Technology',
        'tone': 'professional',
        'platforms': ['instagram', 'linkedin']
    }
    create_resp = client.post('/api/profile', json=payload)
    assert create_resp.status_code == 200
    
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    
    # Verify stable contract
    assert body.get('ok') is True
    assert 'request_id' in body
    assert 'profile_status' in body
    assert 'profile' in body
    assert 'warnings' in body
    
    # Should be ready (all key fields present)
    assert body['profile_status'] == 'ready'
    assert isinstance(body['warnings'], list)
    
    profile = body['profile']
    assert profile.get('company') == 'Complete Co'
    assert profile.get('industry') == 'Technology'
    assert profile.get('tone') == 'professional'
    assert profile.get('platforms') == ['instagram', 'linkedin']


def test_profile_request_id_always_present(client):
    """request_id should always be present in response."""
    # Test missing profile
    resp1 = client.get('/api/profile')
    assert resp1.status_code == 200
    body1 = resp1.get_json()
    assert 'request_id' in body1
    assert body1['request_id']
    
    # Test with profile
    client.post('/api/profile', json={'company': 'Test'})
    resp2 = client.get('/api/profile')
    assert resp2.status_code == 200
    body2 = resp2.get_json()
    assert 'request_id' in body2
    assert body2['request_id']


def test_profile_error_returns_stable_contract(client, monkeypatch):
    """Database errors should return stable error contract."""
    # Simulate database error
    def mock_get_db():
        raise Exception("Simulated DB failure")
    
    import app as app_module
    monkeypatch.setattr(app_module, 'get_db', mock_get_db)
    
    resp = client.get('/api/profile')
    assert resp.status_code == 500
    body = resp.get_json()
    
    # Verify error contract
    assert body.get('ok') is False
    assert 'request_id' in body
    assert 'error' in body
    
    error = body['error']
    assert isinstance(error, dict)
    assert 'code' in error
    assert 'message' in error
    assert error['code'] == 'profile_load_error'
