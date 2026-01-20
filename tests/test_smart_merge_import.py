"""Tests for smart merge import functionality."""
import json
from unittest.mock import patch, MagicMock


def test_format_field_value():
    """Test the _format_field_value helper function."""
    from routes.chat_routes import _format_field_value
    
    # Test None
    assert _format_field_value(None) == "(empty)"
    
    # Test empty string
    assert _format_field_value("") == "(empty)"
    assert _format_field_value("   ") == "(empty)"
    
    # Test short string
    assert _format_field_value("Test value") == "Test value"
    
    # Test long string (truncated)
    long_string = "a" * 200
    result = _format_field_value(long_string)
    assert len(result) == 153  # 150 chars + "..."
    assert result.endswith("...")
    
    # Test list
    assert _format_field_value([]) == "(empty)"
    assert _format_field_value(["a", "b", "c"]) == "a, b, c"
    assert _format_field_value(["a", "b", "c", "d", "e"]) == "a, b, c (+2 more)"


def test_generate_merge_suggestion_lists():
    """Test merge suggestion for list fields."""
    from routes.chat_routes import _generate_merge_suggestion
    from models import VoiceProfile
    
    profile = VoiceProfile()
    
    # Test brand_keywords merge (deduplication)
    current = ["fresh", "local", "organic"]
    new = ["local", "sustainable", "farm-to-table"]
    result = _generate_merge_suggestion('brand_keywords', current, new, profile)
    
    assert isinstance(result, list)
    assert "fresh" in result
    assert "local" in result
    assert "organic" in result
    assert "sustainable" in result
    assert "farm-to-table" in result
    # Should not have duplicates
    assert result.count("local") == 1


def test_generate_merge_suggestion_text_fallback():
    """Test merge suggestion fallback for text fields when AI unavailable."""
    from routes.chat_routes import _generate_merge_suggestion
    from models import VoiceProfile
    
    profile = VoiceProfile()
    
    # Test with longer new value
    current = "Short"
    new = "A much longer and more detailed description"
    result = _generate_merge_suggestion('brand_voice', current, new, profile)
    
    # Should prefer the longer value
    assert result == new
    
    # Test with longer current value
    current = "A much longer and more detailed description"
    new = "Short"
    result = _generate_merge_suggestion('brand_voice', current, new, profile)
    
    # Should prefer the longer value
    assert result == current


def test_import_merge_flow_accept(app, authenticated_client):
    """Test the full import merge flow with acceptance."""
    # Step 1: Initiate import
    with patch('services.scraper_service.scrape_url') as mock_scrape, \
         patch('services.scraper_service.extract_business_info') as mock_extract:
        
        mock_scrape.return_value = "=== KEY PAGE INFO ===\nPage Title: Test Business\n\n=== PAGE CONTENT ===\nContent"
        mock_extract.return_value = {
            'business_name': 'Test Business',
            'industry': 'Software / Tech / Startup',
            'key_customers': 'Tech startups',
            'voice_tone_and_style': 'professional and innovative',
            'key_offer': 'Free trial',
            'brand_keywords': ['innovative', 'reliable'],
            'content_goals_ai': ['Drive growth'],
        }
        
        response = authenticated_client.post('/api/chat', json={
            'message': '/update https://example.com'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'continue'
        assert 'Comparing your profile' in data['response']
        pending_task = data['pending_task']
        assert pending_task['flow'] == 'import_merge'
    
    # Step 2: Accept the suggestions
    response = authenticated_client.post('/api/chat', json={
        'message': 'accept all',
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'profile_updated'
    assert 'smart merge' in data['response']


def test_import_merge_flow_cancel(app, authenticated_client):
    """Test the import merge flow with cancellation."""
    # Step 1: Initiate import
    with patch('services.scraper_service.scrape_url') as mock_scrape, \
         patch('services.scraper_service.extract_business_info') as mock_extract:
        
        mock_scrape.return_value = "=== KEY PAGE INFO ===\nPage Title: Test Business\n\n=== PAGE CONTENT ===\nContent"
        mock_extract.return_value = {
            'business_name': 'Test Business',
            'industry': 'Software / Tech / Startup',
            'key_customers': None,
            'voice_tone_and_style': None,
            'key_offer': None,
            'brand_keywords': [],
            'content_goals_ai': [],
        }
        
        response = authenticated_client.post('/api/chat', json={
            'message': '/update https://example.com'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        pending_task = data['pending_task']
    
    # Step 2: Cancel
    response = authenticated_client.post('/api/chat', json={
        'message': 'cancel',
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    assert "hasn't been changed" in data['response']
