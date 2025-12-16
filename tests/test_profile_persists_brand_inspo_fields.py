"""
Test that brand inspiration fields persist correctly in profile API.

This test verifies that:
1. Brand inspirations can be saved with profile
2. Brand anti-inspirations can be saved
3. Vibe preset can be saved
4. Data is retrieved correctly
5. Updates work properly
"""

import pytest
import json


def test_profile_persists_brand_inspo_fields(client):
    """Test that POST /api/profile persists brand inspiration fields."""
    
    # Create user
    signup_response = client.post('/api/signup', json={
        'email': 'persist_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code == 200
    
    # Save profile with all brand inspiration fields
    profile_data = {
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['instagram', 'facebook'],
        'brand_keywords': ['sustainable', 'eco'],
        'company': 'Test Store',
        'include_images': True,
        'brand_inspirations': [
            {'name': 'Apple', 'why': 'Clean design'},
            {'name': 'Nike', 'why': 'Bold and inspiring'},
            {'name': 'Patagonia', 'why': 'Mission-driven'}
        ],
        'brand_anti_inspirations': [
            {'name': 'Fast Fashion', 'why': 'Too trendy'},
            {'name': 'Generic Corp', 'why': 'No personality'}
        ],
        'vibe_preset': 'premium_minimal'
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] is True
    profile_id = data['id']
    
    # Get profile and verify
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    
    profile = data['profile']
    assert profile['id'] == profile_id
    
    # Verify brand inspirations
    assert 'brand_inspirations' in profile
    assert len(profile['brand_inspirations']) == 3
    assert profile['brand_inspirations'][0]['name'] == 'Apple'
    assert profile['brand_inspirations'][0]['why'] == 'Clean design'
    assert profile['brand_inspirations'][1]['name'] == 'Nike'
    assert profile['brand_inspirations'][2]['name'] == 'Patagonia'
    
    # Verify anti-inspirations
    assert 'brand_anti_inspirations' in profile
    assert len(profile['brand_anti_inspirations']) == 2
    assert profile['brand_anti_inspirations'][0]['name'] == 'Fast Fashion'
    assert profile['brand_anti_inspirations'][1]['name'] == 'Generic Corp'
    
    # Verify vibe preset
    assert profile['vibe_preset'] == 'premium_minimal'


def test_profile_persists_brand_inspo_empty_arrays(client):
    """Test that empty arrays are handled correctly."""
    
    client.post('/api/signup', json={
        'email': 'empty_test@example.com',
        'password': 'testpass123'
    })
    
    # Save with empty arrays
    profile_data = {
        'industry': 'healthcare',
        'tone': 'professional',
        'platforms': ['linkedin'],
        'company': 'Clinic',
        'brand_inspirations': [],
        'brand_anti_inspirations': [],
        'vibe_preset': None
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Get and verify
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    
    profile = data['profile']
    assert profile['brand_inspirations'] == []
    assert profile['brand_anti_inspirations'] == []
    assert profile['vibe_preset'] is None


def test_profile_persists_brand_inspo_update(client):
    """Test that brand inspiration can be updated."""
    
    client.post('/api/signup', json={
        'email': 'update_test@example.com',
        'password': 'testpass123'
    })
    
    # Initial save without inspirations
    client.post('/api/profile', json={
        'industry': 'fitness',
        'tone': 'warm',
        'platforms': ['instagram'],
        'company': 'Gym'
    })
    
    # Update with brand inspirations
    update_data = {
        'industry': 'fitness',
        'tone': 'warm',
        'platforms': ['instagram'],
        'company': 'Gym',
        'brand_inspirations': [
            {'name': 'Lululemon', 'why': 'Wellness focus'}
        ],
        'vibe_preset': 'playful_bold'
    }
    
    response = client.post('/api/profile', json=update_data)
    assert response.status_code == 200
    
    # Verify update
    response = client.get('/api/profile')
    profile = response.get_json()['profile']
    
    assert len(profile['brand_inspirations']) == 1
    assert profile['brand_inspirations'][0]['name'] == 'Lululemon'
    assert profile['vibe_preset'] == 'playful_bold'
    
    # Update again - change vibe preset
    update_data['vibe_preset'] = 'friendly_modern'
    update_data['brand_inspirations'].append({'name': 'Nike', 'why': 'Motivational'})
    
    client.post('/api/profile', json=update_data)
    
    # Verify second update
    response = client.get('/api/profile')
    profile = response.get_json()['profile']
    
    assert len(profile['brand_inspirations']) == 2
    assert profile['vibe_preset'] == 'friendly_modern'


def test_profile_persists_brand_inspo_max_brands(client):
    """Test saving with max number of brands (4) and anti-brands (3)."""
    
    client.post('/api/signup', json={
        'email': 'max_test@example.com',
        'password': 'testpass123'
    })
    
    # Save with max brands
    profile_data = {
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['instagram'],
        'company': 'Store',
        'brand_inspirations': [
            {'name': 'Brand1', 'why': 'Reason1'},
            {'name': 'Brand2', 'why': 'Reason2'},
            {'name': 'Brand3', 'why': 'Reason3'},
            {'name': 'Brand4', 'why': 'Reason4'}
        ],
        'brand_anti_inspirations': [
            {'name': 'AntiBrand1', 'why': 'Why1'},
            {'name': 'AntiBrand2', 'why': 'Why2'},
            {'name': 'AntiBrand3', 'why': 'Why3'}
        ]
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Verify all saved
    response = client.get('/api/profile')
    profile = response.get_json()['profile']
    
    assert len(profile['brand_inspirations']) == 4
    assert len(profile['brand_anti_inspirations']) == 3
    
    # Verify specific values
    assert profile['brand_inspirations'][0]['name'] == 'Brand1'
    assert profile['brand_inspirations'][3]['name'] == 'Brand4'
    assert profile['brand_anti_inspirations'][2]['name'] == 'AntiBrand3'
