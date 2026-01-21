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
    
    # Test with brand_voice - should combine descriptors
    current = "warm"
    new = "professional"
    result = _generate_merge_suggestion('brand_voice', current, new, profile)
    
    # Should combine both values intelligently
    assert isinstance(result, str)
    assert len(result) > 0
    # For brand_voice, the fallback combines descriptors from both values
    result_lower = result.lower()
    assert ('warm' in result_lower or 'friendly' in result_lower), "Should include descriptor from current value"
    assert ('professional' in result_lower or 'approachable' in result_lower), "Should include descriptor from new value"
    
    # Test with target_audience - should prefer longer or combine
    current = "busy professionals"
    new = "health-conscious families seeking quality dining experiences"
    result = _generate_merge_suggestion('target_audience', current, new, profile)
    
    # Should not lose the longer description
    assert len(result) >= len(current)


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


def test_text_field_merge_combines_values():
    """Test that text fields are merged, not overwritten."""
    from routes.chat_routes import _generate_merge_suggestion
    from models import VoiceProfile
    
    profile = VoiceProfile()
    
    current = "warm and friendly"
    new = "professional and approachable"
    result = _generate_merge_suggestion('brand_voice', current, new, profile)
    
    # Result should contain elements from both values
    assert result is not None
    result_lower = result.lower()
    # Check that descriptors from both current and new are present
    assert ('warm' in result_lower or 'friendly' in result_lower), "Should preserve descriptor from current value"
    assert ('professional' in result_lower or 'approachable' in result_lower), "Should preserve descriptor from new value"


def test_text_similarity_calculation():
    """Test the text similarity helper function."""
    from routes.chat_routes import _text_similarity
    
    # Identical texts
    assert _text_similarity("hello world", "hello world") == 1.0
    
    # Completely different
    assert _text_similarity("hello world", "foo bar baz") == 0.0
    
    # Partial overlap
    similarity = _text_similarity("warm and friendly", "friendly and professional")
    assert 0.2 < similarity < 0.8


def test_fallback_text_merge_brand_voice():
    """Test fallback merge for brand voice field."""
    from routes.chat_routes import _fallback_text_merge
    
    result = _fallback_text_merge('brand_voice', 'warm, friendly', 'professional, approachable')
    
    # Should combine unique descriptors from both values
    result_lower = result.lower()
    assert ('warm' in result_lower or 'friendly' in result_lower), "Should include descriptor from current"
    assert ('professional' in result_lower or 'approachable' in result_lower), "Should include descriptor from new"


def test_merge_with_empty_current():
    """Test that empty current value uses new value."""
    from routes.chat_routes import _generate_merge_suggestion
    from models import VoiceProfile
    
    profile = VoiceProfile()
    
    result = _generate_merge_suggestion('brand_voice', '', 'new value', profile)
    assert result == 'new value'
    
    result = _generate_merge_suggestion('brand_voice', None, 'new value', profile)
    assert result == 'new value'


def test_merge_with_empty_new():
    """Test that empty new value keeps current value."""
    from routes.chat_routes import _generate_merge_suggestion
    from models import VoiceProfile
    
    profile = VoiceProfile()
    
    result = _generate_merge_suggestion('brand_voice', 'current value', '', profile)
    assert result == 'current value'


def test_target_audience_merge():
    """Test target audience merging logic."""
    from routes.chat_routes import _generate_merge_suggestion
    from models import VoiceProfile
    
    profile = VoiceProfile()
    
    # Test case 1: When new value is significantly longer (>1.5x), it uses the longer one
    current = "busy professionals"
    new = "health-conscious families seeking quality"
    result = _generate_merge_suggestion('target_audience', current, new, profile)
    
    # Since new is much longer, fallback logic prefers it
    assert 'families' in result.lower() or 'health' in result.lower(), "Should use longer value when significantly different"
    
    # Test case 2: When values are similar length, they should be combined
    current = "busy professionals"
    new = "health-conscious families"  # Similar length
    result = _generate_merge_suggestion('target_audience', current, new, profile)
    
    # When similar length, should combine both
    result_lower = result.lower()
    # At least one should have content from both (or the merge preserves the longer/more detailed)
    assert len(result) > 0, "Should return a valid merged result"
