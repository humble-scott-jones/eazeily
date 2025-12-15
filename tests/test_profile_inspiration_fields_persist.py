"""Test that brand inspiration fields persist correctly in the database."""

import pytest
import json


def test_save_brand_inspirations_via_profile_endpoint(client):
    """Test that brand inspirations can be saved and retrieved via /api/profile."""
    
    # Prepare test data
    brand_inspirations = [
        {"name": "Apple", "why": "Clean and minimal"},
        {"name": "Nike", "why": "Bold and inspiring"},
        {"name": "Patagonia", "why": "Authentic and mission-driven"}
    ]
    
    brand_anti_inspirations = [
        {"name": "Generic Corp", "why": "Too salesy"}
    ]
    
    vibe_preset = "premium_minimal"
    
    # POST to save profile with inspirations
    response = client.post('/api/profile', json={
        'company': 'Test Company',
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['instagram', 'facebook'],
        'brand_inspirations': brand_inspirations,
        'brand_anti_inspirations': brand_anti_inspirations,
        'vibe_preset': vibe_preset
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] is True
    profile_id = data['id']
    
    # GET to retrieve profile
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] is True
    
    profile = data['profile']
    assert profile['id'] == profile_id
    assert profile['company'] == 'Test Company'
    
    # Verify brand inspirations were saved and retrieved
    assert 'brand_inspirations' in profile
    assert len(profile['brand_inspirations']) == 3
    assert profile['brand_inspirations'][0]['name'] == 'Apple'
    assert profile['brand_inspirations'][0]['why'] == 'Clean and minimal'
    
    # Verify anti-inspirations
    assert 'brand_anti_inspirations' in profile
    assert len(profile['brand_anti_inspirations']) == 1
    assert profile['brand_anti_inspirations'][0]['name'] == 'Generic Corp'
    
    # Verify vibe preset
    assert profile['vibe_preset'] == vibe_preset


def test_update_existing_profile_with_inspirations(client):
    """Test updating an existing profile with brand inspirations."""
    
    # Create initial profile without inspirations
    response = client.post('/api/profile', json={
        'company': 'Test Company',
        'industry': 'retail',
        'tone': 'friendly'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    profile_id = data['id']
    
    # Update profile with inspirations
    brand_inspirations = [
        {"name": "Tesla", "why": "Innovative and forward-thinking"}
    ]
    
    response = client.post('/api/profile', json={
        'company': 'Test Company',
        'industry': 'retail',
        'tone': 'friendly',
        'brand_inspirations': brand_inspirations
    })
    
    assert response.status_code == 200
    
    # Verify inspirations were added
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    
    profile = data['profile']
    assert profile['id'] == profile_id
    assert len(profile['brand_inspirations']) == 1
    assert profile['brand_inspirations'][0]['name'] == 'Tesla'


def test_empty_inspirations_defaults(client):
    """Test that missing inspiration fields default to empty arrays."""
    
    # Create profile without any inspiration fields
    response = client.post('/api/profile', json={
        'company': 'Test Company',
        'industry': 'retail',
        'tone': 'friendly'
    })
    
    assert response.status_code == 200
    
    # Get profile and check defaults
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    
    profile = data['profile']
    assert 'brand_inspirations' in profile
    assert profile['brand_inspirations'] == []
    assert 'brand_anti_inspirations' in profile
    assert profile['brand_anti_inspirations'] == []
    assert profile['vibe_preset'] is None


def test_vibe_preset_only_without_brands(client):
    """Test that vibe preset can be set without brand inspirations."""
    
    response = client.post('/api/profile', json={
        'company': 'Test Company',
        'industry': 'healthcare',
        'tone': 'professional',
        'vibe_preset': 'clinical_trustworthy'
    })
    
    assert response.status_code == 200
    
    # Verify vibe preset was saved
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    
    profile = data['profile']
    assert profile['vibe_preset'] == 'clinical_trustworthy'
    assert profile['brand_inspirations'] == []
