"""Tests for smart merge import functionality."""
import json
from unittest.mock import patch, MagicMock


def test_text_similarity():
    """Test the _text_similarity function."""
    from routes.chat_routes import _text_similarity
    
    # Test identical text
    assert _text_similarity("hello world", "hello world") == 1.0
    
    # Test completely different text
    assert _text_similarity("hello world", "foo bar") == 0.0
    
    # Test partial overlap
    similarity = _text_similarity("warm and friendly", "warm and professional")
    assert 0.4 < similarity < 0.8  # Should have some overlap
    
    # Test case insensitivity
    assert _text_similarity("HELLO WORLD", "hello world") == 1.0
    
    # Test empty strings
    assert _text_similarity("", "hello") == 0.0
    assert _text_similarity("hello", "") == 0.0


def test_fallback_text_merge_brand_voice():
    """Test _fallback_text_merge for brand_voice field."""
    from routes.chat_routes import _fallback_text_merge
    
    # Test combining descriptors
    current = "warm and friendly"
    new = "professional and innovative"
    result = _fallback_text_merge('brand_voice', current, new)
    
    # MUST use AND logic - both values should be preserved
    assert 'warm' in result.lower()
    assert 'friendly' in result.lower()
    assert 'professional' in result.lower()
    assert 'innovative' in result.lower()


def test_fallback_text_merge_target_audience():
    """Test _fallback_text_merge for target_audience field."""
    from routes.chat_routes import _fallback_text_merge
    
    # Test combining sentences
    current = "Busy working parents"
    new = "Tech-savvy millennials"
    result = _fallback_text_merge('target_audience', current, new)
    
    # Should contain both (either combined or prefer longer)
    # At minimum, should preserve information from both
    assert len(result) >= max(len(current), len(new))


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
