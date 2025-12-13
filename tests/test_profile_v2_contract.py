"""
Tests for /api/profile_v2 endpoint contract and behavior.

Ensures the new v2 endpoint returns stable keys for all cases:
- ready: profile has all required fields
- partial: profile exists but missing some fields
- missing: no profile saved yet
"""

import json
import pytest


def test_profile_v2_returns_stable_contract_when_missing(client):
    """Test that profile_v2 returns expected keys when no profile exists."""
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Check stable top-level keys
    assert 'ok' in data
    assert data['ok'] is True
    assert 'request_id' in data
    assert 'profile_status' in data
    assert 'profile' in data
    assert 'warnings' in data
    
    # Check profile status
    assert data['profile_status'] in ['missing', 'partial', 'ready']
    
    # Check profile has required keys
    profile = data['profile']
    assert 'company' in profile
    assert 'industry' in profile
    assert 'signature_tone' in profile
    assert 'default_tone' in profile
    assert 'platforms' in profile
    assert 'timezone' in profile
    assert 'voice_fingerprint' in profile or profile['voice_fingerprint'] is None
    assert 'updated_at' in profile or profile['updated_at'] is None
    
    # For missing profile, expect warnings
    if data['profile_status'] == 'missing':
        assert len(data['warnings']) > 0


def test_profile_v2_returns_stable_contract_when_partial(client):
    """Test that profile_v2 returns expected keys when profile is partial."""
    # Create a partial profile (only company, no industry/tone/platforms)
    response = client.post('/api/profile', 
        json={'company': 'Test Company'},
        content_type='application/json')
    assert response.status_code == 200
    
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Check stable contract
    assert data['ok'] is True
    assert 'request_id' in data
    assert data['profile_status'] == 'partial'
    assert 'profile' in data
    assert 'warnings' in data
    
    # Profile should have the company we saved
    assert data['profile']['company'] == 'Test Company'
    
    # Should have warnings about missing fields
    assert len(data['warnings']) > 0


def test_profile_v2_returns_stable_contract_when_ready(client):
    """Test that profile_v2 returns expected keys when profile is complete."""
    # Create a complete profile
    profile_data = {
        'company': 'Complete Co',
        'industry': 'technology',
        'tone': 'professional',
        'platforms': ['instagram', 'linkedin'],
        'brand_keywords': ['saas', 'automation'],
        'goals': ['growth']
    }
    
    response = client.post('/api/profile', 
        json=profile_data,
        content_type='application/json')
    assert response.status_code == 200
    
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Check stable contract
    assert data['ok'] is True
    assert 'request_id' in data
    assert data['profile_status'] == 'ready'
    assert 'profile' in data
    assert 'warnings' in data
    
    # Profile should have all fields
    profile = data['profile']
    assert profile['company'] == 'Complete Co'
    assert profile['industry'] == 'technology'
    assert profile['signature_tone'] == 'professional'
    assert profile['default_tone'] == 'professional'
    assert 'instagram' in profile['platforms']
    assert 'linkedin' in profile['platforms']
    
    # Ready profile should have minimal warnings
    assert len(data['warnings']) == 0


def test_profile_v2_request_id_always_present(client):
    """Test that request_id is always returned, even on errors."""
    # Make multiple requests and verify each has a request_id
    for _ in range(3):
        response = client.get('/api/profile_v2')
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] is not None
        assert len(str(data['request_id'])) > 0


def test_profile_v2_backward_compatibility_fields(client):
    """Test that v2 endpoint includes backward compatibility fields."""
    profile_data = {
        'company': 'Test Inc',
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['facebook'],
        'brand_keywords': ['fashion', 'style'],
        'niche_keywords': ['sustainable'],
        'goals': ['awareness', 'sales']
    }
    
    client.post('/api/profile', json=profile_data, content_type='application/json')
    
    response = client.get('/api/profile_v2')
    data = json.loads(response.data)
    
    profile = data['profile']
    
    # Check backward compatibility fields
    assert 'brand_keywords' in profile
    assert 'niche_keywords' in profile
    assert 'goals' in profile
    assert 'id' in profile
    assert 'industry_key' in profile
    
    assert profile['brand_keywords'] == ['fashion', 'style']
    assert profile['niche_keywords'] == ['sustainable']
    assert profile['goals'] == ['awareness', 'sales']


def test_profile_v2_voice_fingerprint_structure(client):
    """Test that voice_fingerprint has expected structure when present."""
    # Create profile with voice_profile data
    profile_data = {
        'company': 'Voice Co',
        'industry': 'consulting',
        'tone': 'professional',
        'platforms': ['linkedin'],
        'voice_profile': {
            'include_more': ['expertise', 'data-driven'],
            'avoid_overusing': ['synergy', 'leverage'],
            'on_brand_example': 'We help companies scale through strategic insights.'
        }
    }
    
    client.post('/api/profile', json=profile_data, content_type='application/json')
    
    response = client.get('/api/profile_v2')
    data = json.loads(response.data)
    
    voice_fp = data['profile']['voice_fingerprint']
    
    # Should have the expected structure
    assert voice_fp is not None
    assert 'include_more' in voice_fp
    assert 'avoid_overusing' in voice_fp
    assert 'on_brand_example' in voice_fp
    
    assert voice_fp['include_more'] == ['expertise', 'data-driven']
    assert voice_fp['avoid_overusing'] == ['synergy', 'leverage']
    assert 'strategic insights' in voice_fp['on_brand_example']
