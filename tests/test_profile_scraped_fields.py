"""Test that scraped profile fields are available to generator."""

import pytest
import json


def test_profile_fields_available_to_api(client):
    """Test that profile with scraped fields can be retrieved via API."""
    # Sign up
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create profile with scraped fields
    profile_data = {
        'company': 'Test Business',
        'industry': 'Software / Tech / Startup',
        'tone': 'Professional and friendly',
        'customers': ['small businesses', 'startups', 'freelancers'],
        'scraped_url': 'https://example.com',
        'scraped_meta': {
            'extracted_at': '2026-01-11T00:00:00',
            'business_name': 'Test Business',
            'keywords': ['innovative', 'reliable']
        },
        'scrape_status': 'finished'
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Retrieve profile
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    profile = data['profile']
    assert profile['company'] == 'Test Business'
    assert profile['customers'] == ['small businesses', 'startups', 'freelancers']
    assert profile['scraped_url'] == 'https://example.com'
    assert profile['scraped_meta']['business_name'] == 'Test Business'
    assert profile['scrape_status'] == 'finished'


def test_profile_v2_includes_scraped_fields(client):
    """Test that profile_v2 endpoint includes scraped fields."""
    # Sign up
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create profile with scraped fields
    profile_data = {
        'company': 'Acme Corp',
        'customers': ['enterprise clients'],
        'scraped_url': 'https://acme.example.com'
    }
    
    client.post('/api/profile', json=profile_data)
    
    # Retrieve via profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    profile = data['profile']
    assert profile['company'] == 'Acme Corp'
    assert profile['customers'] == ['enterprise clients']
    assert profile['scraped_url'] == 'https://acme.example.com'


def test_empty_profile_has_default_scraped_fields(client):
    """Test that empty profile returns default values for scraped fields."""
    # Sign up (creates user but no profile yet)
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Get profile before any data is saved
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    profile = data['profile']
    assert profile['customers'] == []
    assert profile['scraped_url'] == ''
    assert profile['scraped_meta'] == {}
    assert profile['scrape_status'] == 'none'
