"""
Tests for VoiceProfile JSON getter hardening.

This test suite ensures that VoiceProfile JSON getters handle malformed JSON gracefully
and return safe default values instead of raising exceptions.
"""
import pytest
from models import VoiceProfile, User, db, safe_json_loads_list, safe_json_loads_dict


class TestSafeJsonHelpers:
    """Test the safe JSON parsing helper functions."""
    
    def test_safe_json_loads_list_valid(self):
        """Test that valid JSON list is parsed correctly."""
        result = safe_json_loads_list('["item1", "item2"]')
        assert result == ["item1", "item2"]
    
    def test_safe_json_loads_list_empty_string(self):
        """Test that empty string returns default empty list."""
        result = safe_json_loads_list('')
        assert result == []
    
    def test_safe_json_loads_list_none(self):
        """Test that None returns default empty list."""
        result = safe_json_loads_list(None)
        assert result == []
    
    def test_safe_json_loads_list_invalid_json(self):
        """Test that invalid JSON returns default empty list."""
        result = safe_json_loads_list('{"not": "a list"}')
        assert result == []
    
    def test_safe_json_loads_list_malformed_json(self):
        """Test that malformed JSON returns default empty list."""
        result = safe_json_loads_list('[invalid json')
        assert result == []
    
    def test_safe_json_loads_list_custom_default(self):
        """Test that custom default is returned on error."""
        result = safe_json_loads_list('invalid', default=['custom'])
        assert result == ['custom']
    
    def test_safe_json_loads_dict_valid(self):
        """Test that valid JSON dict is parsed correctly."""
        result = safe_json_loads_dict('{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_safe_json_loads_dict_empty_string(self):
        """Test that empty string returns default empty dict."""
        result = safe_json_loads_dict('')
        assert result == {}
    
    def test_safe_json_loads_dict_none(self):
        """Test that None returns default empty dict."""
        result = safe_json_loads_dict(None)
        assert result == {}
    
    def test_safe_json_loads_dict_invalid_json(self):
        """Test that invalid JSON returns default empty dict."""
        result = safe_json_loads_dict('["not", "a", "dict"]')
        assert result == {}
    
    def test_safe_json_loads_dict_malformed_json(self):
        """Test that malformed JSON returns default empty dict."""
        result = safe_json_loads_dict('{"invalid": json}')
        assert result == {}
    
    def test_safe_json_loads_dict_custom_default(self):
        """Test that custom default is returned on error."""
        result = safe_json_loads_dict('invalid', default={'custom': 'default'})
        assert result == {'custom': 'default'}


class TestVoiceProfileJsonGetters:
    """Test VoiceProfile JSON getters with various edge cases."""
    
    @pytest.fixture
    def app_context(self, client):
        """Provide Flask app context for database operations."""
        from app import create_app
        test_app = create_app()
        with test_app.app_context():
            yield test_app
    
    def test_get_platforms_valid_json(self, app_context):
        """Test get_platforms with valid JSON."""
        profile = VoiceProfile()
        profile.platforms = '["twitter", "linkedin"]'
        result = profile.get_platforms()
        assert result == ["twitter", "linkedin"]
    
    def test_get_platforms_malformed_json(self, app_context):
        """Test get_platforms with malformed JSON returns empty list."""
        profile = VoiceProfile()
        profile.platforms = '[invalid json'
        result = profile.get_platforms()
        assert result == []
    
    def test_get_platforms_wrong_type(self, app_context):
        """Test get_platforms with wrong JSON type returns empty list."""
        profile = VoiceProfile()
        profile.platforms = '{"not": "a list"}'
        result = profile.get_platforms()
        assert result == []
    
    def test_get_platforms_none(self, app_context):
        """Test get_platforms with None returns empty list."""
        profile = VoiceProfile()
        profile.platforms = None
        result = profile.get_platforms()
        assert result == []
    
    def test_get_brand_keywords_malformed_json(self, app_context):
        """Test get_brand_keywords with malformed JSON."""
        profile = VoiceProfile()
        profile.brand_keywords = '["keyword1", invalid]'
        result = profile.get_brand_keywords()
        assert result == []
    
    def test_get_niche_keywords_malformed_json(self, app_context):
        """Test get_niche_keywords with malformed JSON."""
        profile = VoiceProfile()
        profile.niche_keywords = 'not json at all'
        result = profile.get_niche_keywords()
        assert result == []
    
    def test_get_goals_malformed_json(self, app_context):
        """Test get_goals with malformed JSON."""
        profile = VoiceProfile()
        profile.goals = '["goal1"'
        result = profile.get_goals()
        assert result == []
    
    def test_get_writing_samples_malformed_json(self, app_context):
        """Test get_writing_samples with malformed JSON."""
        profile = VoiceProfile()
        profile.writing_samples = '{malformed}'
        result = profile.get_writing_samples()
        assert result == []
    
    def test_get_brand_inspirations_malformed_json(self, app_context):
        """Test get_brand_inspirations with malformed JSON."""
        profile = VoiceProfile()
        profile.brand_inspirations = '["brand1",'
        result = profile.get_brand_inspirations()
        assert result == []
    
    def test_get_brand_anti_inspirations_malformed_json(self, app_context):
        """Test get_brand_anti_inspirations with malformed JSON."""
        profile = VoiceProfile()
        profile.brand_anti_inspirations = '["anti1"]}'
        result = profile.get_brand_anti_inspirations()
        assert result == []
    
    def test_get_customers_malformed_json(self, app_context):
        """Test get_customers with malformed JSON."""
        profile = VoiceProfile()
        profile.customers = 'not a json array'
        result = profile.get_customers()
        assert result == []
    
    def test_get_scraped_meta_malformed_json(self, app_context):
        """Test get_scraped_meta with malformed JSON."""
        profile = VoiceProfile()
        profile.scraped_meta = '{"key": "value"'
        result = profile.get_scraped_meta()
        assert result == {}
    
    def test_get_scraped_meta_wrong_type(self, app_context):
        """Test get_scraped_meta with wrong JSON type returns empty dict."""
        profile = VoiceProfile()
        profile.scraped_meta = '["not", "a", "dict"]'
        result = profile.get_scraped_meta()
        assert result == {}
    
    def test_get_defaults_malformed_json(self, app_context):
        """Test get_defaults with malformed JSON."""
        profile = VoiceProfile()
        profile.defaults = '{"style_guide": "test"'
        result = profile.get_defaults()
        assert result == {}
    
    def test_get_examples_malformed_json(self, app_context):
        """Test get_examples with malformed JSON."""
        profile = VoiceProfile()
        profile.examples = '["example1", "example2"'
        result = profile.get_examples()
        assert result == []


class TestApiProfileWithMalformedJson:
    """Test /api/profile endpoint with malformed JSON in database."""
    
    def test_api_profile_get_with_malformed_json_succeeds(self, authenticated_client):
        """Test that /api/profile GET succeeds even with malformed JSON in database."""
        from models import VoiceProfile, db
        from flask import current_app
        
        # Get the authenticated user's profile and corrupt its JSON fields
        with authenticated_client.application.app_context():
            profile = VoiceProfile.query.first()
            assert profile is not None
            
            # Intentionally corrupt various JSON fields
            profile.platforms = '[invalid json'
            profile.brand_keywords = '{"not": "a list"}'
            profile.niche_keywords = 'not json at all'
            profile.goals = '["goal1"'
            profile.writing_samples = '{malformed}'
            profile.brand_inspirations = '["brand1",'
            profile.brand_anti_inspirations = '["anti1"]}'
            profile.customers = 'not a json array'
            profile.scraped_meta = '{"key": "value"'
            profile.defaults = '{"style": "test"'
            profile.examples = '["ex1"'
            db.session.commit()
        
        # Make request to /api/profile
        response = authenticated_client.get('/api/profile')
        
        # Verify the request succeeds (doesn't crash with 500)
        assert response.status_code == 200
        
        # Verify response structure
        data = response.get_json()
        assert data['ok'] is True
        assert 'profile' in data
        
        # Verify all malformed JSON fields return safe defaults
        profile_data = data['profile']
        assert profile_data['platforms'] == []
        assert profile_data['brand_keywords'] == []
        assert profile_data['niche_keywords'] == []
        assert profile_data['goals'] == []
        assert profile_data['writing_samples'] == []
        assert profile_data['brand_inspirations'] == []
        assert profile_data['brand_anti_inspirations'] == []
        assert profile_data['customers'] == []
        assert profile_data['scraped_meta'] == {}
    
    def test_api_profile_get_with_partial_malformed_json(self, authenticated_client):
        """Test that /api/profile GET handles mix of valid and malformed JSON."""
        from models import VoiceProfile, db
        
        with authenticated_client.application.app_context():
            profile = VoiceProfile.query.first()
            assert profile is not None
            
            # Mix of valid and malformed JSON
            profile.platforms = '["twitter", "linkedin"]'  # Valid
            profile.brand_keywords = '[invalid json'  # Invalid
            profile.goals = '["goal1", "goal2"]'  # Valid
            profile.scraped_meta = '{"key": "value"'  # Invalid
            db.session.commit()
        
        response = authenticated_client.get('/api/profile')
        assert response.status_code == 200
        
        data = response.get_json()
        profile_data = data['profile']
        
        # Valid JSON should be parsed correctly
        assert profile_data['platforms'] == ["twitter", "linkedin"]
        assert profile_data['goals'] == ["goal1", "goal2"]
        
        # Invalid JSON should return safe defaults
        assert profile_data['brand_keywords'] == []
        assert profile_data['scraped_meta'] == {}
