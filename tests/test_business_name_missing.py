"""Test that when business name is not found in scraper, user is asked in chat."""
import json
import pytest
from unittest.mock import patch


def test_missing_business_name_asks_user(authenticated_client, monkeypatch):
    """Test that when business name is not found, user is asked to provide it."""
    
    # Mock scraper to return data without business name
    def mock_scrape_url(url, max_length=6000):
        return "=== KEY PAGE INFO ===\nPage Title: Some Content\n\n=== PAGE CONTENT ===\nGeneric content"
    
    def mock_extract_business_info(text, url=""):
        return {
            'business_name': None,  # Not found!
            'industry': 'Software / Tech / Startup',
            'key_customers': 'Tech professionals',
            'voice_tone_and_style': 'professional and friendly',
            'key_offer': 'Great service',
            'brand_keywords': ['innovative'],
            'content_goals_ai': ['Drive growth']
        }
    
    monkeypatch.setattr('services.scraper_service.scrape_url', mock_scrape_url)
    monkeypatch.setattr('services.scraper_service.extract_business_info', mock_extract_business_info)
    
    # Request import with URL
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should ask for business name instead of showing merge
    assert data['action'] == 'continue'
    assert 'business name' in data['response'].lower()
    assert 'what' in data['response'].lower() or 'name of your business' in data['response'].lower()
    
    # Should have pending task for business_name field
    assert data['pending_task'] is not None
    assert data['pending_task']['field_name'] == 'business_name'
    assert data['pending_task']['imported_url'] == 'https://example.com'
    assert 'extracted_data' in data['pending_task']


def test_business_name_provided_continues_merge(authenticated_client, monkeypatch):
    """Test that after providing business name, merge continues with other fields."""
    
    # Mock scraper to return data without business name
    def mock_scrape_url(url, max_length=6000):
        return "=== KEY PAGE INFO ===\nPage Title: Some Content\n\n=== PAGE CONTENT ===\nGeneric content"
    
    def mock_extract_business_info(text, url=""):
        return {
            'business_name': None,  # Not found!
            'industry': 'Software / Tech / Startup',
            'key_customers': 'Tech professionals',
            'voice_tone_and_style': 'professional and friendly',
            'key_offer': 'Great service',
            'brand_keywords': ['innovative'],
            'content_goals_ai': ['Drive growth']
        }
    
    monkeypatch.setattr('services.scraper_service.scrape_url', mock_scrape_url)
    monkeypatch.setattr('services.scraper_service.extract_business_info', mock_extract_business_info)
    
    # Step 1: Request import
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    pending_task = data['pending_task']
    
    # Step 2: Provide business name
    response = authenticated_client.post('/api/chat', json={
        'message': 'My Awesome Company',
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should now show merge comparison with other fields
    assert data['action'] == 'continue'
    assert 'My Awesome Company' in data['response']
    assert 'what else I found' in data['response'].lower() or 'here' in data['response'].lower()
    
    # Should have import_merge pending task now
    assert data['pending_task'] is not None
    assert data['pending_task']['flow'] == 'import_merge'
    assert 'comparisons' in data['pending_task']


def test_business_name_found_shows_normal_merge(authenticated_client, monkeypatch):
    """Test that when business name is found, normal merge flow works."""
    
    # Mock scraper to return data WITH business name
    def mock_scrape_url(url, max_length=6000):
        return "=== KEY PAGE INFO ===\nPage Title: Example Business\n\n=== PAGE CONTENT ===\nContent"
    
    def mock_extract_business_info(text, url=""):
        return {
            'business_name': 'Example Business',  # Found!
            'industry': 'Software / Tech / Startup',
            'key_customers': 'Tech professionals',
            'voice_tone_and_style': 'professional',
            'key_offer': 'Great service',
            'brand_keywords': ['innovative'],
            'content_goals_ai': ['Drive growth']
        }
    
    monkeypatch.setattr('services.scraper_service.scrape_url', mock_scrape_url)
    monkeypatch.setattr('services.scraper_service.extract_business_info', mock_extract_business_info)
    
    # Request import
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should show normal merge (not ask for business name)
    assert data['action'] == 'continue'
    assert 'comparing your profile' in data['response'].lower()
    assert data['pending_task']['flow'] == 'import_merge'
