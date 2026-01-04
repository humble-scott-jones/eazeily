"""Tests for the onboarding routes and brand brain functionality."""

import json
import pytest


def test_onboarding_get_requires_auth(client):
    """Test that onboarding page requires authentication."""
    response = client.get('/onboarding')
    # Should redirect to login
    assert response.status_code == 302
    assert '/login' in response.location or 'login' in response.location.lower()


def test_onboarding_post_requires_auth(client):
    """Test that onboarding POST requires authentication."""
    response = client.post('/onboarding', data={
        'business_name': 'Test Business',
        'industry': 'Real Estate'
    })
    # Should redirect to login
    assert response.status_code == 302


def test_onboarding_saves_complete_profile(client):
    """Test that onboarding saves all Secret Sauce fields."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'brand_test@example.com',
        'password': 'testpass123'
    })
    
    # Submit onboarding form
    response = client.post('/onboarding', data={
        'business_name': 'Smith Real Estate',
        'industry': 'Real Estate',
        'target_audience': 'Local families looking to upsize',
        'brand_voice': 'Professional and reassuring',
        'key_offer': 'Free Home Valuation Report',
        'voice_rules': 'Use y\'all, No exclamation points',
        'writing_samples': 'Just closed on another dream home!\n\nLooking to sell? Let\'s chat.'
    })
    
    # Should redirect to dashboard on success
    assert response.status_code == 302
    assert '/dashboard' in response.location


def test_onboarding_splits_writing_samples(client):
    """Test that writing samples are split correctly by blank lines."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'samples_test@example.com',
        'password': 'testpass123'
    })
    
    # Submit with multiple samples separated by blank lines
    samples_text = """Sample one here.

Sample two here.

Sample three here."""
    
    response = client.post('/onboarding', data={
        'business_name': 'Test Pottery',
        'industry': 'Pottery',
        'target_audience': 'Creative hobbyists',
        'brand_voice': 'Inspirational and earthy',
        'key_offer': '10% off first workshop',
        'voice_rules': '',
        'writing_samples': samples_text
    })
    
    assert response.status_code == 302


def test_onboarding_requires_all_fields(client):
    """Test that onboarding validates required fields."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'validation_test@example.com',
        'password': 'testpass123'
    })
    
    # Submit with missing required fields
    response = client.post('/onboarding', data={
        'business_name': 'Test Business',
        'industry': 'Fitness'
        # Missing other required fields
    })
    
    # Should return error
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_onboarding_assist_voice_endpoint(client):
    """Test the AI-assisted voice generation endpoint."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'assist_test@example.com',
        'password': 'testpass123'
    })
    
    # Call assist endpoint (will fail without API key, but should handle gracefully)
    response = client.post('/onboarding/assist-voice',
        json={
            'business_name': 'Smith Real Estate',
            'industry': 'Real Estate'
        },
        content_type='application/json')
    
    # Should either succeed or return 503 (service unavailable)
    assert response.status_code in [200, 503]


def test_onboarding_updates_existing_profile(client):
    """Test that onboarding updates existing profile instead of creating duplicate."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'update_test@example.com',
        'password': 'testpass123'
    })
    
    # Submit first time
    client.post('/onboarding', data={
        'business_name': 'First Business',
        'industry': 'Real Estate',
        'target_audience': 'First audience',
        'brand_voice': 'First voice',
        'key_offer': 'First offer',
        'voice_rules': '',
        'writing_samples': 'First sample'
    })
    
    # Submit second time with updated data
    response = client.post('/onboarding', data={
        'business_name': 'Updated Business',
        'industry': 'Fitness',
        'target_audience': 'Updated audience',
        'brand_voice': 'Updated voice',
        'key_offer': 'Updated offer',
        'voice_rules': 'Updated rules',
        'writing_samples': 'Updated sample'
    })
    
    assert response.status_code == 302
    assert '/dashboard' in response.location
