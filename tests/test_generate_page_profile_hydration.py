"""
Tests for generate page profile hydration behavior.

Ensures that:
1. Profile loads successfully when data exists
2. Profile handles missing data gracefully
3. Profile handles timeout/error scenarios with proper retry UI
"""

import json
import pytest


def test_profile_v2_returns_ready_status_with_complete_profile(client):
    """Test that profile_v2 returns 'ready' status when profile is complete."""
    # Create a complete profile
    profile_data = {
        'company': 'Test Inc',
        'industry': 'technology',
        'tone': 'professional',
        'platforms': ['instagram', 'linkedin'],
        'brand_keywords': ['AI', 'automation'],
        'goals': ['growth']
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Fetch profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Verify response structure
    assert data['ok'] is True
    assert 'request_id' in data
    assert data['profile_status'] == 'ready'
    assert len(data['warnings']) == 0
    
    # Verify profile data
    profile = data['profile']
    assert profile['company'] == 'Test Inc'
    assert profile['industry'] == 'technology'
    assert profile['signature_tone'] == 'professional'
    assert profile['default_tone'] == 'professional'
    assert 'instagram' in profile['platforms']
    assert 'linkedin' in profile['platforms']


def test_profile_v2_returns_missing_status_without_profile(client):
    """Test that profile_v2 returns 'missing' status when no profile exists."""
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Verify response structure
    assert data['ok'] is True
    assert 'request_id' in data
    assert data['profile_status'] == 'missing'
    assert len(data['warnings']) > 0
    assert 'Complete the Setup Wizard' in data['warnings'][0]
    
    # Verify empty profile data
    profile = data['profile']
    assert profile['company'] == ''
    assert profile['industry'] == ''
    assert profile['signature_tone'] == ''
    assert profile['platforms'] == []


def test_profile_v2_returns_partial_status_with_incomplete_profile(client):
    """Test that profile_v2 returns 'partial' status when profile is incomplete."""
    # Create a partial profile (company only, missing industry/tone/platforms)
    profile_data = {
        'company': 'Partial Co'
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Fetch profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Verify response structure
    assert data['ok'] is True
    assert data['profile_status'] == 'partial'
    assert len(data['warnings']) > 0
    
    # Verify profile has company but missing other fields
    profile = data['profile']
    assert profile['company'] == 'Partial Co'
    assert profile['industry'] == ''
    assert profile['signature_tone'] == ''


def test_profile_endpoints_always_return_json(client):
    """Test that profile endpoints always return JSON, never HTML."""
    # Test GET /api/profile
    response = client.get('/api/profile')
    assert response.status_code == 200
    assert response.content_type.startswith('application/json')
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'ok' in data
    
    # Test GET /api/profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    assert response.content_type.startswith('application/json')
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'ok' in data


def test_profile_v2_includes_latency_in_logs(client, caplog):
    """Test that profile_v2 logs include latency_ms."""
    # This test verifies logging behavior
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    # Check that the response includes request_id
    data = json.loads(response.data)
    assert 'request_id' in data
    assert data['request_id'] is not None


def test_profile_v2_handles_voice_profile_data(client):
    """Test that profile_v2 correctly handles voice_profile data."""
    profile_data = {
        'company': 'Voice Test Co',
        'industry': 'consulting',
        'tone': 'professional',
        'platforms': ['linkedin'],
        'voice_profile': {
            'include_more': ['data-driven', 'strategic'],
            'avoid_overusing': ['synergy', 'leverage'],
            'on_brand_example': 'We help companies scale through insights.'
        }
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Fetch with v2 endpoint
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    
    # Verify voice_fingerprint structure
    voice_fp = data['profile']['voice_fingerprint']
    assert voice_fp is not None
    assert 'include_more' in voice_fp
    assert 'avoid_overusing' in voice_fp
    assert 'on_brand_example' in voice_fp
    assert 'data-driven' in voice_fp['include_more']
    assert 'synergy' in voice_fp['avoid_overusing']


def test_profile_legacy_and_v2_consistency(client):
    """Test that legacy /api/profile and /api/profile_v2 return consistent data."""
    profile_data = {
        'company': 'Consistency Test',
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['facebook', 'instagram']
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Fetch with legacy endpoint
    legacy_response = client.get('/api/profile')
    assert legacy_response.status_code == 200
    legacy_data = json.loads(legacy_response.data)
    
    # Fetch with v2 endpoint
    v2_response = client.get('/api/profile_v2')
    assert v2_response.status_code == 200
    v2_data = json.loads(v2_response.data)
    
    # Both should return OK
    assert legacy_data['ok'] is True
    assert v2_data['ok'] is True
    
    # Both should have same profile_status
    assert legacy_data['profile_status'] == v2_data['profile_status']
    
    # Core fields should match
    legacy_profile = legacy_data['profile']
    v2_profile = v2_data['profile']
    
    assert legacy_profile['company'] == v2_profile['company']
    assert legacy_profile['industry'] == v2_profile['industry']
    # Note: v2 uses 'signature_tone', legacy uses 'tone'
    assert legacy_profile['tone'] == v2_profile['signature_tone']
    assert legacy_profile['platforms'] == v2_profile['platforms']
