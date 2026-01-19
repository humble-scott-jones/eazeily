"""Tests for the /import command flow and profile import functionality."""

import json
import pytest
from unittest.mock import patch, MagicMock


def test_social_style_endpoint_requires_auth(client):
    """Test that /onboarding/social-style requires authentication."""
    response = client.post('/onboarding/social-style', json={
        'url': 'https://example.com',
        'consent': True
    })
    # Should redirect to login or return 401
    assert response.status_code in [302, 401]


def test_social_style_requires_url(authenticated_client):
    """Test that social-style endpoint requires a URL."""
    response = authenticated_client.post('/onboarding/social-style', json={
        'consent': True
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'URL' in data['error']


def test_social_style_requires_consent(authenticated_client):
    """Test that social-style endpoint requires consent."""
    response = authenticated_client.post('/onboarding/social-style', json={
        'url': 'https://example.com'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'consent' in data['error'].lower()


@patch('services.scraper_service.extract_business_info')
@patch('services.scraper_service.scrape_url')
def test_social_style_extracts_complete_profile(mock_scrape, mock_extract, authenticated_client):
    """Test that social-style extracts all profile fields from a website."""
    # Mock scraper response
    mock_scrape.return_value = "Sample text from website about our bakery"
    
    # Mock AI extraction with complete data
    mock_extract.return_value = {
        'business_name': 'Sunny Side Bakery',
        'industry': 'Food & Beverage',
        'voice_tone_and_style': 'Warm, community-focused, quality-driven',
        'key_customers': 'Local families and food enthusiasts',
        'key_offer': 'Traditional European recipes using organic local ingredients',
        'brand_keywords': ['artisan', 'fresh', 'local', 'organic'],
        'niche_keywords': ['community', 'traditional'],
        'sample_posts': [
            'Every morning, we bake with the same love and care...',
            'Our small batches mean exceptional quality...'
        ]
    }
    
    response = authenticated_client.post('/onboarding/social-style', json={
        'url': 'https://sunnysidebakery.com',
        'consent': True
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Verify suggestions are returned
    assert 'suggestions' in data
    suggestions = data['suggestions']
    
    # Check all fields are present
    assert suggestions['business_name'] == 'Sunny Side Bakery'
    assert suggestions['industry'] == 'Food & Beverage'
    assert suggestions['key_customers'] == 'Local families and food enthusiasts'
    assert suggestions['key_offer'] == 'Traditional European recipes using organic local ingredients'
    assert 'brand_keywords' in suggestions
    assert len(suggestions['brand_keywords']) > 0
    assert 'niche_keywords' in suggestions
    assert 'sample_posts' in suggestions or 'sample_copy' in suggestions


@patch('services.scraper_service.extract_business_info')
@patch('services.scraper_service.scrape_url')
def test_social_style_handles_partial_extraction(mock_scrape, mock_extract, authenticated_client):
    """Test that social-style handles partial data extraction gracefully."""
    # Mock scraper response
    mock_scrape.return_value = "Sample text from website"
    
    # Mock AI extraction with only partial data
    mock_extract.return_value = {
        'business_name': 'Test Business',
        'industry': 'Technology',
        'voice_tone_and_style': None,
        'key_customers': None,
        'key_offer': None,
        'brand_keywords': [],
        'niche_keywords': []
    }
    
    response = authenticated_client.post('/onboarding/social-style', json={
        'url': 'https://testbusiness.com',
        'consent': True
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Verify suggestions are returned even with partial data
    assert 'suggestions' in data
    suggestions = data['suggestions']
    
    # Check that present fields are there
    assert suggestions['business_name'] == 'Test Business'
    assert suggestions['industry'] == 'Technology'


def test_profile_api_accepts_import_data(authenticated_client):
    """Test that /api/profile accepts and saves imported data."""
    import_data = {
        'company': 'Sunny Side Bakery',
        'industry': 'Food & Beverage',
        'brand_voice': 'Warm, community-focused',
        'target_audience': 'Local families',
        'key_offer': 'Traditional European recipes',
        'brand_keywords': ['artisan', 'fresh', 'local'],
        'niche_keywords': ['organic', 'community'],
        'writing_samples': [
            'Every morning, we bake with love...',
            'Our small batches mean quality...'
        ],
        'scraped_url': 'https://sunnysidebakery.com'
    }
    
    response = authenticated_client.post('/api/profile', 
        json=import_data,
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] is True
    
    # Verify data was saved by fetching profile
    get_response = authenticated_client.get('/api/profile')
    assert get_response.status_code == 200
    get_data = get_response.get_json()
    
    profile = get_data['profile']
    assert profile['company'] == 'Sunny Side Bakery'
    assert profile['industry'] == 'Food & Beverage'
    assert profile['brand_voice'] == 'Warm, community-focused'
    assert profile['target_audience'] == 'Local families'
    assert profile['key_offer'] == 'Traditional European recipes'
    assert len(profile['brand_keywords']) == 3
    assert len(profile['niche_keywords']) == 2
    assert len(profile['writing_samples']) == 2
    assert profile['scraped_url'] == 'https://sunnysidebakery.com'


def test_profile_api_maps_key_customers_to_target_audience(authenticated_client):
    """Test that key_customers field is mapped to target_audience."""
    import_data = {
        'company': 'Test Business',
        'industry': 'Technology',
        'key_customers': 'Small business owners and entrepreneurs'
    }
    
    response = authenticated_client.post('/api/profile', 
        json=import_data,
        content_type='application/json'
    )
    
    assert response.status_code == 200
    
    # Verify mapping by fetching profile
    get_response = authenticated_client.get('/api/profile')
    profile = get_response.get_json()['profile']
    
    # key_customers should be mapped to target_audience
    assert profile['target_audience'] == 'Small business owners and entrepreneurs'


def test_profile_api_handles_sample_posts_as_writing_samples(authenticated_client):
    """Test that sample_posts from scraper are saved as writing_samples."""
    import_data = {
        'company': 'Test Business',
        'industry': 'Technology',
        'writing_samples': [
            'Sample post 1 from scraper',
            'Sample post 2 from scraper',
            'Sample post 3 from scraper'
        ]
    }
    
    response = authenticated_client.post('/api/profile', 
        json=import_data,
        content_type='application/json'
    )
    
    assert response.status_code == 200
    
    # Verify samples are saved
    get_response = authenticated_client.get('/api/profile')
    profile = get_response.get_json()['profile']
    
    assert len(profile['writing_samples']) == 3
    assert 'Sample post 1 from scraper' in profile['writing_samples']


@patch('services.scraper_service.scrape_url')
def test_social_style_handles_scraping_errors(mock_scrape, authenticated_client):
    """Test that social-style handles scraping errors gracefully."""
    # Mock scraper to return None (failed scrape)
    mock_scrape.return_value = None
    
    response = authenticated_client.post('/onboarding/social-style', json={
        'url': 'https://invalid-url.com',
        'consent': True
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_profile_completeness_increases_after_import(authenticated_client):
    """Test that profile completeness increases after importing data."""
    # Get initial profile (should be empty)
    before_response = authenticated_client.get('/api/profile')
    before_data = before_response.get_json()
    before_profile = before_data['profile']
    
    # Save imported data
    import_data = {
        'company': 'Complete Bakery',
        'industry': 'Food & Beverage',
        'brand_voice': 'Warm and welcoming',
        'target_audience': 'Local families',
        'key_offer': 'Fresh baked goods daily',
        'writing_samples': ['Sample 1', 'Sample 2']
    }
    
    save_response = authenticated_client.post('/api/profile', 
        json=import_data,
        content_type='application/json'
    )
    assert save_response.status_code == 200
    
    # Get updated profile
    after_response = authenticated_client.get('/api/profile')
    after_data = after_response.get_json()
    after_profile = after_data['profile']
    
    # Verify that more fields are now filled
    assert after_profile['company'] != ''
    assert after_profile['industry'] != ''
    assert after_profile['brand_voice'] != ''
    assert after_profile['target_audience'] != ''
    assert after_profile['key_offer'] != ''
    assert len(after_profile['writing_samples']) > 0
