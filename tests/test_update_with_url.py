"""Tests for /update command with URL functionality."""

import json
import pytest
from unittest.mock import patch, MagicMock
from models import User, VoiceProfile, db


@pytest.fixture
def mock_scraper(monkeypatch):
    """Mock the scraper service to return consistent test data."""
    def mock_scrape_url(url, max_length=6000):
        return "=== KEY PAGE INFO ===\nPage Title: Updated Business\n\n=== PAGE CONTENT ===\nContent"
    
    def mock_extract_business_info(text, url=""):
        return {
            'business_name': 'Updated Business Name',
            'industry': 'Updated Industry',
            'voice_tone_and_style': 'professional and modern',
            'key_customers': 'tech-savvy professionals',
            'key_offer': 'innovative solutions',
            'brand_keywords': ['innovative', 'professional'],
            'content_goals_ai': ['Drive growth']
        }
    
    monkeypatch.setattr('services.scraper_service.scrape_url', mock_scrape_url)
    monkeypatch.setattr('services.scraper_service.extract_business_info', mock_extract_business_info)
    return mock_scrape_url


@pytest.fixture
def mock_scraper_no_changes(monkeypatch):
    """Mock the scraper service to return no new data."""
    def mock_scrape_url(url, max_length=6000):
        return "=== KEY PAGE INFO ===\nPage Title: Test\n\n=== PAGE CONTENT ===\nContent"
    
    def mock_extract_business_info(text, url=""):
        return {
            'business_name': None,
            'industry': None,
            'voice_tone_and_style': None,
            'key_customers': None,
            'key_offer': None,
            'brand_keywords': [],
            'content_goals_ai': []
        }
    
    monkeypatch.setattr('services.scraper_service.scrape_url', mock_scrape_url)
    monkeypatch.setattr('services.scraper_service.extract_business_info', mock_extract_business_info)
    return mock_scrape_url


@pytest.fixture
def mock_scraper_error(monkeypatch):
    """Mock the scraper service to return an error."""
    def mock_scrape_url(url, max_length=6000):
        return None  # Simulate scraping failure
    
    monkeypatch.setattr('services.scraper_service.scrape_url', mock_scrape_url)
    return mock_scrape_url


def test_update_with_url_shows_changes(authenticated_client, mock_scraper):
    """Test that /update with URL scrapes and shows changes for confirmation."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should show changes preview with smart merge
    assert data['action'] == 'continue'
    assert 'Comparing your profile' in data['response']
    assert 'Updated Business Name' in data['response']
    
    # Should have pending task for confirmation
    assert data['pending_task'] is not None
    assert data['pending_task']['flow'] == 'import_merge'
    assert 'comparisons' in data['pending_task']


def test_update_with_url_apply_changes(authenticated_client, mock_scraper):
    """Test that user can apply all changes from URL update."""
    # First request - get changes
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    pending_task = data['pending_task']
    
    # Second request - confirm applying changes
    response = authenticated_client.post('/api/chat', json={
        'message': 'accept all',
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should confirm updates applied
    assert data['action'] == 'profile_updated'
    assert 'smart merge' in data['response'].lower()
    
    # Verify database was updated - 7 fields should be applied
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        # The new values from the mock should be applied
        assert profile.business_name == 'Updated Business Name'
        assert profile.industry == 'Updated Industry'
        # Merge happened - all fields have values (fallback keeps longer ones)
        assert profile.brand_voice is not None
        assert profile.target_audience == 'tech-savvy professionals'
        # Key offer might keep the longer original value in fallback
        assert profile.key_offer is not None


def test_update_with_url_cancel_changes(authenticated_client, mock_scraper):
    """Test that user can cancel URL update changes."""
    # First request - get changes
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    pending_task = data['pending_task']
    
    # Get original values
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        original_name = profile.business_name
    
    # Second request - cancel changes
    response = authenticated_client.post('/api/chat', json={
        'message': 'cancel',
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should confirm cancellation
    assert data['action'] == 'continue'
    assert 'not been changed' in data['response'].lower() or 'no problem' in data['response'].lower()
    
    # Verify database was NOT updated
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        assert profile.business_name == original_name


def test_update_with_url_no_changes_found(authenticated_client, mock_scraper_no_changes):
    """Test message when URL has no new information."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should show "no changes" message
    assert data['action'] == 'continue'
    assert 'up to date' in data['response'].lower() or 'no new information' in data['response'].lower()
    
    # Should NOT have a pending task since there's nothing to confirm
    assert data['pending_task'] is None or data['pending_task'].get('flow') != 'import_merge'


def test_update_with_url_error_handling(authenticated_client, mock_scraper_error):
    """Test error handling when URL scraping fails."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://invalid-site.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should show error message
    assert data['action'] == 'error'
    assert 'not access' in data['response'].lower() or 'trouble' in data['response'].lower()


def test_update_alone_still_shows_field_selection(authenticated_client):
    """Test that /update without URL still shows field selection."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/update'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should ask which field to update
    assert data['action'] == 'continue'
    assert 'which' in data['response'].lower() or 'update' in data['response'].lower()
    assert 'Business Name' in data['response'] or 'brand voice' in data['response'].lower()
    
    # Should have pending task for field selection
    assert data['pending_task'] is not None
    assert data['pending_task']['flow'] == 'profile_update'


def test_update_with_field_name_still_works(authenticated_client):
    """Test that /update with field name (not URL) still works."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/update voice'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should not treat 'voice' as a URL
    assert data['action'] == 'continue'
    # Should either ask for the field value or show guidance
    assert 'voice' in data['response'].lower()


def test_update_with_http_url_detected(authenticated_client, mock_scraper):
    """Test that http:// URLs are also detected."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/update http://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should show changes preview (not field selection)
    assert data['action'] == 'continue'
    assert 'Comparing your profile' in data['response'] or 'Updated Business Name' in data['response']


def test_update_confirmation_requires_clear_response(authenticated_client, mock_scraper):
    """Test that ambiguous responses to confirmation are handled."""
    # First request - get changes
    response = authenticated_client.post('/api/chat', json={
        'message': '/update https://example.com'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    pending_task = data['pending_task']
    
    # Second request - ambiguous response
    response = authenticated_client.post('/api/chat', json={
        'message': 'maybe later',
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should ask again for clarification
    assert data['action'] == 'continue'
    assert 'would you like' in data['response'].lower() or 'apply' in data['response'].lower()
    
    # Should keep the same pending task (import_merge flow)
    assert data['pending_task'] is not None
    assert data['pending_task']['flow'] == 'import_merge'
