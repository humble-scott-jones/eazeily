"""Test that wizard saves brand inspiration data correctly."""

import pytest
import json


def test_wizard_saves_brand_inspiration_with_profile(client):
    """Test that submitting wizard with brand inspiration data saves correctly."""
    
    # Create a user first
    signup_response = client.post('/api/signup', json={
        'email': 'wizard_brand_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code == 200
    
    # Simulate wizard submission with brand inspiration
    profile_data = {
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['instagram', 'facebook'],
        'brand_keywords': ['sustainable', 'eco-friendly'],
        'niche_keywords': ['sustainable', 'eco-friendly'],
        'company': 'Green Store',
        'include_images': True,
        'brand_inspirations': [
            {'name': 'Patagonia', 'why': 'authentic and mission-driven'},
            {'name': 'Allbirds', 'why': 'simple and sustainable'}
        ],
        'brand_anti_inspirations': [
            {'name': 'Fast Fashion Co', 'why': 'too salesy'}
        ],
        'vibe_preset': 'friendly_modern'
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] is True
    
    # Retrieve and verify
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    
    profile = data['profile']
    assert profile['industry'] == 'retail'
    assert profile['tone'] == 'friendly'
    
    # Verify brand inspirations were saved
    assert len(profile['brand_inspirations']) == 2
    assert profile['brand_inspirations'][0]['name'] == 'Patagonia'
    assert profile['brand_inspirations'][0]['why'] == 'authentic and mission-driven'
    
    # Verify anti-inspirations
    assert len(profile['brand_anti_inspirations']) == 1
    assert profile['brand_anti_inspirations'][0]['name'] == 'Fast Fashion Co'
    
    # Verify vibe preset
    assert profile['vibe_preset'] == 'friendly_modern'


def test_wizard_saves_empty_brand_inspiration(client):
    """Test that wizard works when brand inspiration is skipped (empty)."""
    
    # Create a user
    signup_response = client.post('/api/signup', json={
        'email': 'wizard_skip_brand@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code == 200
    
    # Submit without brand inspiration (user skipped step)
    profile_data = {
        'industry': 'healthcare',
        'tone': 'professional',
        'platforms': ['linkedin'],
        'brand_keywords': ['wellness'],
        'niche_keywords': ['wellness'],
        'company': 'Health Clinic',
        'include_images': True,
        'brand_inspirations': [],
        'brand_anti_inspirations': [],
        'vibe_preset': None
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Verify it saved correctly
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    
    profile = data['profile']
    assert profile['brand_inspirations'] == []
    assert profile['brand_anti_inspirations'] == []
    assert profile['vibe_preset'] is None


def test_wizard_can_update_brand_inspiration_later(client):
    """Test that user can save without brand inspiration, then add it later."""
    
    # Create user and initial profile
    client.post('/api/signup', json={
        'email': 'wizard_update@example.com',
        'password': 'testpass123'
    })
    
    # Initial save without brand inspiration
    client.post('/api/profile', json={
        'industry': 'fitness',
        'tone': 'warm',
        'platforms': ['instagram'],
        'brand_keywords': ['yoga'],
        'company': 'Yoga Studio'
    })
    
    # Update with brand inspiration
    update_data = {
        'industry': 'fitness',
        'tone': 'warm',
        'platforms': ['instagram'],
        'brand_keywords': ['yoga'],
        'company': 'Yoga Studio',
        'brand_inspirations': [
            {'name': 'Lululemon', 'why': 'inspiring and wellness-focused'}
        ]
    }
    
    response = client.post('/api/profile', json=update_data)
    assert response.status_code == 200
    
    # Verify update worked
    response = client.get('/api/profile')
    profile = response.get_json()['profile']
    
    assert len(profile['brand_inspirations']) == 1
    assert profile['brand_inspirations'][0]['name'] == 'Lululemon'


def test_wizard_vibe_preset_only(client):
    """Test saving with only vibe preset, no specific brands."""
    
    client.post('/api/signup', json={
        'email': 'wizard_vibe_only@example.com',
        'password': 'testpass123'
    })
    
    profile_data = {
        'industry': 'healthcare',
        'tone': 'professional',
        'platforms': ['linkedin'],
        'brand_keywords': ['care'],
        'company': 'Medical Practice',
        'brand_inspirations': [],
        'vibe_preset': 'clinical_trustworthy'
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Verify
    response = client.get('/api/profile')
    profile = response.get_json()['profile']
    
    assert profile['vibe_preset'] == 'clinical_trustworthy'
    assert profile['brand_inspirations'] == []
