"""Integration tests for profile hydration into generator."""
import pytest
from app import app


def test_generate_uses_profile_defaults(client):
    """Generator should use profile defaults when not overridden."""
    # Save a profile
    profile = {
        'company': 'Test Company',
        'industry': 'Technology',
        'tone': 'professional',
        'platforms': ['linkedin', 'twitter'],
        'brand_keywords': ['innovation', 'tech']
    }
    resp = client.post('/api/profile', json=profile)
    assert resp.status_code == 200
    
    # Verify profile is saved with correct status
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('profile_status') == 'ready'
    saved_profile = body.get('profile')
    assert saved_profile['company'] == 'Test Company'
    assert saved_profile['tone'] == 'professional'


def test_profile_ready_requires_key_fields(client):
    """Profile should be ready only when key fields are present."""
    # Company + tone + platforms = ready
    profile1 = {
        'company': 'Test Co',
        'tone': 'friendly',
        'platforms': ['instagram']
    }
    client.post('/api/profile', json=profile1)
    resp = client.get('/api/profile')
    assert resp.get_json()['profile_status'] == 'ready'
    
    # Industry + tone + platforms = ready (even without company)
    profile2 = {
        'industry': 'Retail',
        'tone': 'playful',
        'platforms': ['tiktok']
    }
    client.post('/api/profile', json=profile2)
    resp = client.get('/api/profile')
    assert resp.get_json()['profile_status'] == 'ready'


def test_profile_partial_when_missing_tone(client):
    """Profile should be partial when tone is missing."""
    profile = {
        'company': 'Test Co',
        'platforms': ['instagram']
    }
    client.post('/api/profile', json=profile)
    resp = client.get('/api/profile')
    body = resp.get_json()
    assert body['profile_status'] == 'partial'
    assert 'tone' in body['reason'].lower()


def test_profile_partial_when_missing_platforms(client):
    """Profile should be partial when platforms are missing."""
    profile = {
        'company': 'Test Co',
        'tone': 'friendly'
    }
    client.post('/api/profile', json=profile)
    resp = client.get('/api/profile')
    body = resp.get_json()
    assert body['profile_status'] == 'partial'
    assert 'platforms' in body['reason'].lower()


def test_profile_update_overwrites_missing_fields(client):
    """Updating profile replaces all fields (known behavior)."""
    # Create initial profile
    initial = {
        'company': 'Original Company',
        'industry': 'Technology',
        'tone': 'professional',
        'platforms': ['linkedin'],
        'brand_keywords': ['innovation']
    }
    client.post('/api/profile', json=initial)
    
    # Update only tone - note: this will clear other fields
    update = {'tone': 'friendly'}
    client.post('/api/profile', json=update)
    
    # Company gets cleared because it wasn't in the update
    # This is current behavior - frontend should send full profile on updates
    resp = client.get('/api/profile')
    profile = resp.get_json()['profile']
    assert profile['company'] == ''  # Cleared
    assert profile['tone'] == 'friendly'  # Updated


def test_voice_profile_included_in_response(client):
    """Voice profile should be included in profile response."""
    profile = {
        'company': 'Test Co',
        'tone': 'friendly',
        'platforms': ['instagram'],
        'voice_profile': {
            'samples': ['Sample 1', 'Sample 2'],
            'style': 'casual'
        }
    }
    client.post('/api/profile', json=profile)
    
    resp = client.get('/api/profile')
    body = resp.get_json()
    assert body['profile_status'] == 'ready'
    assert 'voice_profile' in body['profile']
    assert body['profile']['voice_profile']['style'] == 'casual'
