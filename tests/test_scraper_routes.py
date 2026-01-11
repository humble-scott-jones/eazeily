"""Tests for scraper API endpoints."""

import pytest
import json
import time
from unittest.mock import patch, MagicMock


def test_scrape_endpoint_requires_auth(client):
    """Test that /api/scrape requires authentication."""
    response = client.post('/api/scrape', 
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    # Flask-Login redirects to login page (302) when not authenticated
    assert response.status_code in [302, 401]


def test_scrape_endpoint_validates_url(client):
    """Test that /api/scrape validates URL format."""
    # Sign up and login
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Test missing URL
    response = client.post('/api/scrape', 
                          json={},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['ok'] is False
    assert 'invalid_url' in data['error']['code']
    
    # Test invalid URL format
    response = client.post('/api/scrape', 
                          json={'url': 'not-a-url'},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['ok'] is False


def test_scrape_endpoint_respects_kill_switch(client, monkeypatch):
    """Test that scraping respects OUTBOUND_KILL_SWITCH."""
    monkeypatch.setenv('OUTBOUND_KILL_SWITCH', 'true')
    
    # Sign up and login
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    response = client.post('/api/scrape', 
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    assert response.status_code == 503
    data = json.loads(response.data)
    assert data['ok'] is False
    assert 'service_disabled' in data['error']['code']


@patch('routes.scraper_routes.scrape_url')
@patch('routes.scraper_routes.extract_business_info')
def test_scrape_endpoint_starts_job(mock_extract, mock_scrape, client):
    """Test that /api/scrape starts a background job."""
    # Mock scraping functions
    mock_scrape.return_value = "Sample scraped text about a business"
    mock_extract.return_value = {
        'business_name': 'Acme Corp',
        'industry': 'Software / Tech / Startup',
        'key_customers': 'Small businesses looking for productivity tools',
        'brand_keywords': ['innovative', 'reliable', 'simple'],
        'niche_keywords': ['SaaS', 'productivity', 'workflow']
    }
    
    # Sign up and login
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Start scrape
    response = client.post('/api/scrape', 
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['ok'] is True
    assert 'job_id' in data
    job_id = data['job_id']
    
    # Give the background thread a moment to complete
    time.sleep(0.5)
    
    # Check job status
    response = client.get(f'/api/scrape-job/{job_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['ok'] is True
    assert data['job']['status'] in ['running', 'finished']


def test_scrape_job_endpoint_not_found(client):
    """Test that /api/scrape-job returns 404 for unknown job."""
    # Sign up and login
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    response = client.get('/api/scrape-job/nonexistent-job-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['ok'] is False
    assert 'job_not_found' in data['error']['code']


@patch('routes.scraper_routes.scrape_url')
@patch('routes.scraper_routes.extract_business_info')
def test_scrape_updates_profile(mock_extract, mock_scrape, client):
    """Test that successful scraping updates the user's profile."""
    # Mock scraping functions
    mock_scrape.return_value = "Sample business text"
    mock_extract.return_value = {
        'business_name': 'Test Business',
        'industry': 'Retail / Boutique',
        'key_customers': 'Fashion-conscious shoppers',
        'brand_keywords': ['stylish', 'affordable'],
        'niche_keywords': ['vintage', 'sustainable']
    }
    
    # Sign up and login
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Start scrape
    response = client.post('/api/scrape', 
                          json={'url': 'https://testbusiness.com'},
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    job_id = data['job_id']
    
    # Wait for job to complete
    for _ in range(10):  # Wait up to 5 seconds
        time.sleep(0.5)
        response = client.get(f'/api/scrape-job/{job_id}')
        data = json.loads(response.data)
        if data['job']['status'] == 'finished':
            break
    
    # Check that profile was updated
    response = client.get('/api/profile')
    assert response.status_code == 200
    profile_data = json.loads(response.data)
    profile = profile_data['profile']
    
    assert profile['scraped_url'] == 'https://testbusiness.com'
    assert profile['scrape_status'] == 'finished'
    assert profile['company'] == 'Test Business'
    assert profile['industry'] == 'Retail / Boutique'
    assert 'stylish' in profile['brand_keywords']


@patch('routes.scraper_routes.scrape_url')
def test_scrape_handles_failure(mock_scrape, client):
    """Test that scraping handles failures gracefully."""
    # Mock scraping failure
    mock_scrape.return_value = None
    
    # Sign up and login
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Start scrape
    response = client.post('/api/scrape', 
                          json={'url': 'https://example.com'},
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    job_id = data['job_id']
    
    # Wait for job to complete
    for _ in range(10):
        time.sleep(0.5)
        response = client.get(f'/api/scrape-job/{job_id}')
        data = json.loads(response.data)
        if data['job']['status'] in ['finished', 'failed']:
            break
    
    # Job should have failed
    assert data['job']['status'] == 'failed'
    assert data['job']['result']['ok'] is False
    
    # Profile should show failed status
    response = client.get('/api/profile')
    profile_data = json.loads(response.data)
    assert profile_data['profile']['scrape_status'] == 'failed'
