"""Test Brand Kit API contract for stable keys and request_id."""

import pytest
import json


def test_brand_kit_get_contract_has_stable_keys(client):
    """Test GET /api/brand_kit returns stable contract keys."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    data = response.get_json()
    
    # Must have stable keys
    assert 'ok' in data
    assert 'request_id' in data
    assert 'brand_kit' in data
    
    # ok should be boolean
    assert isinstance(data['ok'], bool)
    assert data['ok'] is True
    
    # request_id should be a string
    assert isinstance(data['request_id'], str)
    assert len(data['request_id']) > 0
    
    # brand_kit should be a dict
    assert isinstance(data['brand_kit'], dict)


def test_brand_kit_post_contract_has_stable_keys(client):
    """Test POST /api/brand_kit returns stable contract keys."""
    # First, sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Post a brand kit
    brand_kit = {
        'business': {
            'company_name': 'Test Co',
            'industry_id': 'retail'
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    
    # Must have stable keys
    assert 'ok' in data
    assert 'request_id' in data
    assert 'brand_kit' in data
    
    # ok should be boolean
    assert isinstance(data['ok'], bool)
    assert data['ok'] is True
    
    # request_id should be a string
    assert isinstance(data['request_id'], str)
    assert len(data['request_id']) > 0
    
    # brand_kit should be a dict with version
    assert isinstance(data['brand_kit'], dict)
    assert data['brand_kit']['version'] == 1


def test_brand_kit_post_requires_authentication(client):
    """Test POST /api/brand_kit requires authentication."""
    brand_kit = {
        'business': {
            'company_name': 'Test Co'
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert response.status_code == 401
    
    data = response.get_json()
    assert data['ok'] is False
    assert 'request_id' in data
    assert 'error' in data


def test_brand_kit_get_works_without_authentication(client):
    """Test GET /api/brand_kit works for anonymous users with defaults."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert 'brand_kit' in data
    
    # Should return default structure
    brand_kit = data['brand_kit']
    assert brand_kit['version'] == 1
    assert brand_kit['meta']['tier'] == 'minimum'
    assert brand_kit['meta']['completeness_score'] == 0


def test_brand_kit_post_and_get_roundtrip(client):
    """Test that posted brand kit can be retrieved with same data."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Post brand kit
    original_kit = {
        'business': {
            'company_name': 'Roundtrip Co',
            'industry_id': 'healthcare',
            'contact_email': 'contact@example.com'
        },
        'services': {
            'primary_services': ['Primary 1', 'Primary 2'],
            'pricing_style': 'fixed'
        },
        'audience': {
            'target_roles': ['Doctors'],
            'top_pains': ['Time management'],
            'desired_outcomes': ['Better efficiency']
        },
        'positioning': {
            'differentiators': ['Fast', 'Reliable']
        }
    }
    
    post_response = client.post('/api/brand_kit', json={'brand_kit': original_kit})
    assert post_response.status_code == 200
    post_data = post_response.get_json()
    assert post_data['ok'] is True
    
    # Get brand kit
    get_response = client.get('/api/brand_kit')
    assert get_response.status_code == 200
    get_data = get_response.get_json()
    assert get_data['ok'] is True
    
    retrieved_kit = get_data['brand_kit']
    
    # Verify key data was preserved
    assert retrieved_kit['business']['company_name'] == 'Roundtrip Co'
    assert retrieved_kit['business']['industry_id'] == 'healthcare'
    assert retrieved_kit['business']['contact_email'] == 'contact@example.com'
    assert retrieved_kit['services']['primary_services'] == ['Primary 1', 'Primary 2']
    assert retrieved_kit['services']['pricing_style'] == 'fixed'
    assert retrieved_kit['audience']['target_roles'] == ['Doctors']
    assert retrieved_kit['positioning']['differentiators'] == ['Fast', 'Reliable']


def test_brand_kit_request_id_is_unique(client):
    """Test that each request gets a unique request_id."""
    response1 = client.get('/api/brand_kit')
    response2 = client.get('/api/brand_kit')
    
    data1 = response1.get_json()
    data2 = response2.get_json()
    
    # Both should have request_ids
    assert 'request_id' in data1
    assert 'request_id' in data2
    
    # Request IDs should be different (very high probability)
    # Note: theoretically they could be the same, but with 8-char hex it's extremely unlikely
    assert data1['request_id'] != data2['request_id']


def test_brand_kit_version_is_always_1(client):
    """Test that brand kit version is always 1."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Post without version
    brand_kit = {
        'business': {
            'company_name': 'No Version Co'
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['brand_kit']['version'] == 1


def test_brand_kit_error_response_contract(client):
    """Test that error responses have consistent contract."""
    # Try to POST without authentication
    response = client.post('/api/brand_kit', json={'brand_kit': {}})
    assert response.status_code == 401
    
    data = response.get_json()
    
    # Error response should have these keys
    assert 'ok' in data
    assert data['ok'] is False
    assert 'request_id' in data
    assert isinstance(data['request_id'], str)
    assert 'error' in data
    assert isinstance(data['error'], str)


def test_brand_kit_meta_updated_at_is_iso_timestamp(client):
    """Test that meta.updated_at is a valid ISO timestamp."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Post brand kit
    brand_kit = {
        'business': {
            'company_name': 'Timestamp Co'
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    updated_at = data['brand_kit']['meta']['updated_at']
    
    # Should be a string in ISO format
    assert isinstance(updated_at, str)
    # Should contain 'T' (ISO format separator)
    assert 'T' in updated_at
    # Should be parseable as datetime
    from datetime import datetime
    parsed = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
    assert parsed is not None
