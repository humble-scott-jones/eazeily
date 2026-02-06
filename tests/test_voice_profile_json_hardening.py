"""
Tests for VoiceProfile JSON getter hardening.

This test suite ensures that VoiceProfile JSON getters handle malformed JSON gracefully
and return safe default values instead of raising exceptions.
"""
import json
import pytest
from models import (VoiceProfile, User, db, 
                    safe_json_loads_list, safe_json_loads_dict,
                    safe_json_dumps_list, safe_json_dumps_dict)


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


class TestSafeJsonDumpsHelpers:
    """Test the safe JSON serialization helper functions."""
    
    def test_safe_json_dumps_list_valid(self):
        """Test that valid list is serialized correctly."""
        result = safe_json_dumps_list(['item1', 'item2'])
        assert result == '["item1", "item2"]'
    
    def test_safe_json_dumps_list_empty(self):
        """Test that empty list is serialized correctly."""
        result = safe_json_dumps_list([])
        assert result == '[]'
    
    def test_safe_json_dumps_list_none(self):
        """Test that None returns empty list JSON."""
        result = safe_json_dumps_list(None)
        assert result == '[]'
    
    def test_safe_json_dumps_list_non_list(self):
        """Test that non-list input returns empty list JSON."""
        result = safe_json_dumps_list({'not': 'a list'})
        assert result == '[]'
    
    def test_safe_json_dumps_list_string(self):
        """Test that string input returns empty list JSON."""
        result = safe_json_dumps_list("not a list")
        assert result == '[]'
    
    def test_safe_json_dumps_dict_valid(self):
        """Test that valid dict is serialized correctly."""
        result = safe_json_dumps_dict({'key': 'value'})
        assert result == '{"key": "value"}'
    
    def test_safe_json_dumps_dict_empty(self):
        """Test that empty dict is serialized correctly."""
        result = safe_json_dumps_dict({})
        assert result == '{}'
    
    def test_safe_json_dumps_dict_none(self):
        """Test that None returns empty dict JSON."""
        result = safe_json_dumps_dict(None)
        assert result == '{}'
    
    def test_safe_json_dumps_dict_non_dict(self):
        """Test that non-dict input returns empty dict JSON."""
        result = safe_json_dumps_dict(['not', 'a', 'dict'])
        assert result == '{}'
    
    def test_safe_json_dumps_dict_string(self):
        """Test that string input returns empty dict JSON."""
        result = safe_json_dumps_dict("not a dict")
        assert result == '{}'


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
    
    def test_style_guide_property_with_malformed_defaults(self, app_context):
        """Test style_guide property returns None when defaults is malformed."""
        profile = VoiceProfile()
        profile.defaults = '{"style_guide": "test"'  # Malformed JSON
        result = profile.style_guide
        # Should return None since get_defaults() returns {} for malformed JSON
        assert result is None
    
    def test_style_guide_property_with_valid_defaults(self, app_context):
        """Test style_guide property works with valid defaults."""
        profile = VoiceProfile()
        profile.defaults = '{"style_guide": "Be concise and clear"}'
        result = profile.style_guide
        assert result == "Be concise and clear"


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
        # Note: defaults and examples are not directly exposed in /api/profile response,
        # but they are tested through unit tests in TestVoiceProfileJsonGetters
    
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


class TestSafeJsonSetters:
    """Test that setters validate and produce safe JSON output."""
    
    @pytest.fixture
    def app_context(self, client):
        """Provide Flask app context for database operations."""
        from app import create_app
        test_app = create_app()
        with test_app.app_context():
            yield test_app
    
    def test_set_platforms_with_valid_list(self, app_context):
        """Test set_platforms with valid list produces valid JSON."""
        profile = VoiceProfile()
        profile.set_platforms(['twitter', 'linkedin'])
        
        # Should be valid JSON
        parsed = json.loads(profile.platforms)
        assert parsed == ['twitter', 'linkedin']
    
    def test_set_platforms_with_none(self, app_context):
        """Test set_platforms with None produces empty list JSON."""
        profile = VoiceProfile()
        profile.set_platforms(None)
        
        parsed = json.loads(profile.platforms)
        assert parsed == []
    
    def test_set_platforms_with_non_list(self, app_context):
        """Test set_platforms with non-list produces empty list JSON."""
        profile = VoiceProfile()
        profile.set_platforms("not a list")
        
        parsed = json.loads(profile.platforms)
        assert parsed == []
    
    def test_set_brand_keywords_with_valid_list(self, app_context):
        """Test set_brand_keywords stores valid list data correctly."""
        profile = VoiceProfile()
        profile.set_brand_keywords(['keyword1', 'keyword2'])
        
        parsed = json.loads(profile.brand_keywords)
        assert parsed == ['keyword1', 'keyword2']
    
    def test_set_scraped_meta_with_valid_dict(self, app_context):
        """Test set_scraped_meta with valid dict produces valid JSON."""
        profile = VoiceProfile()
        profile.set_scraped_meta({'key': 'value', 'count': 42})
        
        parsed = json.loads(profile.scraped_meta)
        assert parsed == {'key': 'value', 'count': 42}
    
    def test_set_scraped_meta_with_none(self, app_context):
        """Test set_scraped_meta with None produces empty dict JSON."""
        profile = VoiceProfile()
        profile.set_scraped_meta(None)
        
        parsed = json.loads(profile.scraped_meta)
        assert parsed == {}
    
    def test_set_scraped_meta_with_non_dict(self, app_context):
        """Test set_scraped_meta with non-dict produces empty dict JSON."""
        profile = VoiceProfile()
        profile.set_scraped_meta(['not', 'a', 'dict'])
        
        parsed = json.loads(profile.scraped_meta)
        assert parsed == {}
    
    def test_setter_roundtrip_preserves_data(self, app_context):
        """Test that setting and getting data preserves the values."""
        profile = VoiceProfile()
        
        test_data = ['item1', 'item2', 'item3']
        profile.set_goals(test_data)
        result = profile.get_goals()
        
        assert result == test_data
    
    def test_all_setters_produce_valid_json(self, app_context):
        """Test that all setters produce valid, parseable JSON."""
        profile = VoiceProfile()
        
        # Test all list setters
        profile.set_platforms(['twitter'])
        profile.set_brand_keywords(['keyword'])
        profile.set_niche_keywords(['niche'])
        profile.set_goals(['goal'])
        profile.set_writing_samples(['sample'])
        profile.set_brand_inspirations(['brand'])
        profile.set_brand_anti_inspirations(['anti'])
        profile.set_customers(['customer'])
        profile.set_examples(['example'])
        
        # All should be valid JSON
        assert json.loads(profile.platforms) == ['twitter']
        assert json.loads(profile.brand_keywords) == ['keyword']
        assert json.loads(profile.niche_keywords) == ['niche']
        assert json.loads(profile.goals) == ['goal']
        assert json.loads(profile.writing_samples) == ['sample']
        assert json.loads(profile.brand_inspirations) == ['brand']
        assert json.loads(profile.brand_anti_inspirations) == ['anti']
        assert json.loads(profile.customers) == ['customer']
        assert json.loads(profile.examples) == ['example']
        
        # Test dict setters
        profile.set_defaults({'key': 'value'})
        profile.set_scraped_meta({'meta': 'data'})
        
        assert json.loads(profile.defaults) == {'key': 'value'}
        assert json.loads(profile.scraped_meta) == {'meta': 'data'}


class TestNormalizeJsonFields:
    """Test the normalize_json_fields method for repairing malformed data."""
    
    @pytest.fixture
    def app_context(self, client):
        """Provide Flask app context for database operations."""
        from app import create_app
        test_app = create_app()
        with test_app.app_context():
            yield test_app
    
    def test_normalize_repairs_malformed_json(self, app_context):
        """Test that normalize_json_fields repairs malformed JSON."""
        profile = VoiceProfile()
        
        # Set malformed JSON directly
        profile.platforms = '[invalid json'
        profile.brand_keywords = '{"not": "a list"}'
        profile.goals = '["goal1"'
        
        # Normalize
        repaired = profile.normalize_json_fields()
        
        # Should have repaired these fields
        assert 'platforms' in repaired
        assert 'brand_keywords' in repaired
        assert 'goals' in repaired
        
        # Fields should now contain valid JSON
        assert json.loads(profile.platforms) == []
        assert json.loads(profile.brand_keywords) == []
        assert json.loads(profile.goals) == []
    
    def test_normalize_preserves_valid_json(self, app_context):
        """Test that normalize_json_fields doesn't change valid JSON."""
        profile = VoiceProfile()
        
        # Set valid data using setters
        profile.set_platforms(['twitter', 'linkedin'])
        profile.set_goals(['growth'])
        
        # Store original values
        original_platforms = profile.platforms
        original_goals = profile.goals
        
        # Normalize
        repaired = profile.normalize_json_fields()
        
        # Should not have repaired anything
        assert len(repaired) == 0
        
        # Values should be unchanged
        assert profile.platforms == original_platforms
        assert profile.goals == original_goals
    
    def test_normalize_handles_empty_fields(self, app_context):
        """Test that normalize_json_fields handles empty/None fields."""
        profile = VoiceProfile()
        
        # All fields are None/empty by default
        repaired = profile.normalize_json_fields()
        
        # Should not report any repairs for empty fields
        assert len(repaired) == 0
    
    def test_normalize_returns_repair_details(self, app_context):
        """Test that normalize_json_fields returns details about repairs."""
        profile = VoiceProfile()
        
        # Set malformed JSON
        profile.platforms = '[invalid json'
        
        # Normalize
        repaired = profile.normalize_json_fields()
        
        # Should include details
        assert 'platforms' in repaired
        assert 'original' in repaired['platforms']
        assert 'repaired' in repaired['platforms']
        assert repaired['platforms']['original'] == '[invalid json'
        assert repaired['platforms']['repaired'] == '[]'
    
    def test_normalize_all_fields(self, app_context):
        """Test normalizing all fields at once."""
        profile = VoiceProfile()
        
        # Corrupt all JSON fields
        profile.platforms = '[bad'
        profile.brand_keywords = '{bad}'
        profile.niche_keywords = 'bad'
        profile.goals = '["bad"'
        profile.writing_samples = '{"bad"}'
        profile.brand_inspirations = '[bad]'
        profile.brand_anti_inspirations = 'bad'
        profile.customers = '["bad"'
        profile.examples = '{bad}'
        profile.defaults = '{"bad"'
        profile.scraped_meta = '[bad]'
        
        # Normalize
        repaired = profile.normalize_json_fields()
        
        # All should be repaired
        assert len(repaired) == 11  # All 11 JSON fields
        
        # All should now be valid JSON
        assert json.loads(profile.platforms) == []
        assert json.loads(profile.brand_keywords) == []
        assert json.loads(profile.niche_keywords) == []
        assert json.loads(profile.goals) == []
        assert json.loads(profile.writing_samples) == []
        assert json.loads(profile.brand_inspirations) == []
        assert json.loads(profile.brand_anti_inspirations) == []
        assert json.loads(profile.customers) == []
        assert json.loads(profile.examples) == []
        assert json.loads(profile.defaults) == {}
        assert json.loads(profile.scraped_meta) == {}
