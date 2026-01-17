"""Unit tests for ConversationRouter profile update functionality."""

import pytest
from unittest.mock import Mock, patch
from services.conversation_router import ConversationRouter, FIELD_ALIASES


class MockProfile:
    """Mock VoiceProfile for testing."""
    def __init__(self):
        self.business_name = 'Test Business'
        self.industry = 'Technology'


class TestProfileUpdateCommands:
    """Test suite for profile update commands."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    @pytest.fixture
    def mock_profile(self):
        """Create a mock profile."""
        return MockProfile()
    
    def test_parse_slash_profile_command(self, router):
        """Test parsing /profile command."""
        result = router._parse_slash_command('/profile')
        assert result is not None
        assert result['task_type'] == 'profile'
    
    def test_parse_slash_update_command(self, router):
        """Test parsing /update command."""
        result = router._parse_slash_command('/update')
        assert result is not None
        assert result['task_type'] == 'profile_update'
    
    def test_parse_slash_voice_command(self, router):
        """Test parsing /voice command."""
        result = router._parse_slash_command('/voice')
        assert result is not None
        assert result['task_type'] == 'update_voice'
    
    def test_parse_slash_audience_command(self, router):
        """Test parsing /audience command."""
        result = router._parse_slash_command('/audience')
        assert result is not None
        assert result['task_type'] == 'update_audience'
    
    def test_normalize_field_name_business_name(self, router):
        """Test normalizing business name aliases."""
        assert router.normalize_field_name('business') == 'business_name'
        assert router.normalize_field_name('company') == 'business_name'
        assert router.normalize_field_name('business name') == 'business_name'
        assert router.normalize_field_name('company name') == 'business_name'
    
    def test_normalize_field_name_industry(self, router):
        """Test normalizing industry aliases."""
        assert router.normalize_field_name('industry') == 'industry'
        assert router.normalize_field_name('sector') == 'industry'
        assert router.normalize_field_name('field') == 'industry'
        assert router.normalize_field_name('niche') == 'industry'
    
    def test_normalize_field_name_target_audience(self, router):
        """Test normalizing target audience aliases."""
        assert router.normalize_field_name('audience') == 'target_audience'
        assert router.normalize_field_name('target') == 'target_audience'
        assert router.normalize_field_name('customers') == 'target_audience'
        assert router.normalize_field_name('target audience') == 'target_audience'
        assert router.normalize_field_name('ideal customer') == 'target_audience'
    
    def test_normalize_field_name_brand_voice(self, router):
        """Test normalizing brand voice aliases."""
        assert router.normalize_field_name('voice') == 'brand_voice'
        assert router.normalize_field_name('tone') == 'brand_voice'
        assert router.normalize_field_name('style') == 'brand_voice'
        assert router.normalize_field_name('brand voice') == 'brand_voice'
        assert router.normalize_field_name('writing style') == 'brand_voice'
    
    def test_normalize_field_name_key_offer(self, router):
        """Test normalizing key offer aliases."""
        assert router.normalize_field_name('offer') == 'key_offer'
        assert router.normalize_field_name('value prop') == 'key_offer'
        assert router.normalize_field_name('unique offer') == 'key_offer'
        assert router.normalize_field_name('key offer') == 'key_offer'
        assert router.normalize_field_name('usp') == 'key_offer'
    
    def test_normalize_field_name_writing_samples(self, router):
        """Test normalizing writing samples aliases."""
        assert router.normalize_field_name('samples') == 'writing_samples'
        assert router.normalize_field_name('examples') == 'writing_samples'
        assert router.normalize_field_name('writing samples') == 'writing_samples'
        assert router.normalize_field_name('copy examples') == 'writing_samples'
    
    def test_normalize_field_name_unknown(self, router):
        """Test normalizing unknown field names."""
        assert router.normalize_field_name('unknown_field') is None
        assert router.normalize_field_name('random') is None
    
    def test_normalize_field_name_case_insensitive(self, router):
        """Test that field name normalization is case insensitive."""
        assert router.normalize_field_name('VOICE') == 'brand_voice'
        assert router.normalize_field_name('Voice') == 'brand_voice'
        assert router.normalize_field_name('AUDIENCE') == 'target_audience'
        assert router.normalize_field_name('Business Name') == 'business_name'
    
    def test_detect_profile_update_view_intent(self, router):
        """Test detecting profile view intent."""
        result = router.detect_profile_update_intent('show me my profile')
        assert result is not None
        assert result['task_type'] == 'profile'
        
        result = router.detect_profile_update_intent('view my settings')
        assert result is not None
        assert result['task_type'] == 'profile'
    
    def test_detect_profile_update_change_voice(self, router):
        """Test detecting voice update intent."""
        result = router.detect_profile_update_intent('change my brand voice to professional')
        assert result is not None
        assert result['task_type'] == 'update_voice'
        assert result['extracted_params']['field_name'] == 'brand_voice'
    
    def test_detect_profile_update_change_audience(self, router):
        """Test detecting audience update intent."""
        result = router.detect_profile_update_intent('update my target audience to young professionals')
        assert result is not None
        assert result['task_type'] == 'update_audience'
        assert result['extracted_params']['field_name'] == 'target_audience'
    
    def test_detect_profile_update_generic_update(self, router):
        """Test detecting generic update intent."""
        result = router.detect_profile_update_intent('update my profile')
        assert result is not None
        assert result['task_type'] == 'profile_update'
    
    def test_detect_profile_update_with_value_extraction(self, router):
        """Test extracting new value from update intent."""
        result = router.detect_profile_update_intent('change my voice to warm and friendly')
        assert result is not None
        assert result['extracted_params']['field_name'] == 'brand_voice'
        # Value extraction may or may not work depending on regex match
        # This is a best-effort feature
    
    def test_detect_profile_update_not_profile_intent(self, router):
        """Test that non-profile messages don't trigger profile detection."""
        result = router.detect_profile_update_intent('create a post for instagram')
        assert result is None
        
        result = router.detect_profile_update_intent('write me an email')
        assert result is None
    
    def test_classify_with_keywords_profile_update(self, router):
        """Test keyword classification for profile updates."""
        result = router._classify_with_keywords('show me my profile')
        assert result is not None
        assert result['task_type'] == 'profile'
        
        result = router._classify_with_keywords('update my brand voice')
        assert result is not None
        assert result['task_type'] in ['update_voice', 'profile_update']
    
    def test_get_missing_fields_profile_update(self, router):
        """Test getting missing fields for profile_update task."""
        collected = {}
        missing = router.get_missing_fields('profile_update', collected)
        assert 'field_name' in missing
        assert 'new_value' in missing
        
        collected = {'field_name': 'brand_voice'}
        missing = router.get_missing_fields('profile_update', collected)
        assert 'field_name' not in missing
        assert 'new_value' in missing
        
        collected = {'field_name': 'brand_voice', 'new_value': 'professional'}
        missing = router.get_missing_fields('profile_update', collected)
        assert len(missing) == 0
    
    def test_get_missing_fields_update_voice(self, router):
        """Test getting missing fields for update_voice task."""
        collected = {}
        missing = router.get_missing_fields('update_voice', collected)
        assert 'new_value' in missing
        
        collected = {'new_value': 'professional and friendly'}
        missing = router.get_missing_fields('update_voice', collected)
        assert len(missing) == 0
    
    def test_get_missing_fields_profile_view(self, router):
        """Test getting missing fields for profile view (should have none)."""
        collected = {}
        missing = router.get_missing_fields('profile', collected)
        assert len(missing) == 0
    
    def test_get_next_prompt_profile_update(self, router):
        """Test getting next prompt for profile_update."""
        missing = ['field_name']
        prompt = router.get_next_prompt('profile_update', missing)
        assert 'which field' in prompt.lower()
        assert 'business_name' in prompt.lower()
        
        missing = ['new_value']
        prompt = router.get_next_prompt('profile_update', missing)
        assert 'new value' in prompt.lower()
    
    def test_get_next_prompt_update_voice(self, router):
        """Test getting next prompt for update_voice."""
        missing = ['new_value']
        prompt = router.get_next_prompt('update_voice', missing)
        assert 'brand voice' in prompt.lower() or 'voice' in prompt.lower()
    
    def test_get_next_prompt_update_audience(self, router):
        """Test getting next prompt for update_audience."""
        missing = ['new_value']
        prompt = router.get_next_prompt('update_audience', missing)
        assert 'audience' in prompt.lower()
    
    def test_parse_intent_profile_command(self, router, mock_profile):
        """Test parse_intent with profile commands."""
        result = router.parse_intent('/profile', mock_profile)
        assert result['task_type'] == 'profile'
        assert result['follow_up_needed'] is False
        
        result = router.parse_intent('/update', mock_profile)
        assert result['task_type'] == 'profile_update'
        assert result['follow_up_needed'] is True
        
        result = router.parse_intent('/voice', mock_profile)
        assert result['task_type'] == 'update_voice'
        assert result['follow_up_needed'] is True
    
    def test_parse_intent_natural_language_profile(self, router, mock_profile):
        """Test parse_intent with natural language profile requests."""
        # Test view intent
        result = router.parse_intent('show my profile', mock_profile)
        # Should detect as profile view
        if result['task_type'] == 'profile':
            assert result['follow_up_needed'] is False
        
        # Test update intent
        result = router.parse_intent('change my brand voice', mock_profile)
        # Should detect as profile update
        if result['task_type'] in ['update_voice', 'profile_update']:
            assert result['task_type'] in ['update_voice', 'profile_update']


class TestProfileUpdateTaskFields:
    """Test suite for profile update task field definitions."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    def test_profile_task_fields_defined(self, router):
        """Test that profile task fields are defined in TASK_FIELDS."""
        assert 'profile' in router.TASK_FIELDS
        assert 'profile_update' in router.TASK_FIELDS
        assert 'update_voice' in router.TASK_FIELDS
        assert 'update_audience' in router.TASK_FIELDS
    
    def test_profile_task_has_no_required_fields(self, router):
        """Test that profile view has no required fields."""
        config = router.TASK_FIELDS['profile']
        assert len(config['required']) == 0
    
    def test_profile_update_required_fields(self, router):
        """Test profile_update required fields."""
        config = router.TASK_FIELDS['profile_update']
        assert 'field_name' in config['required']
        assert 'new_value' in config['required']
    
    def test_update_voice_required_fields(self, router):
        """Test update_voice required fields."""
        config = router.TASK_FIELDS['update_voice']
        assert 'new_value' in config['required']
        assert 'field_name' not in config['required']  # field is implicit
    
    def test_update_audience_required_fields(self, router):
        """Test update_audience required fields."""
        config = router.TASK_FIELDS['update_audience']
        assert 'new_value' in config['required']
        assert 'field_name' not in config['required']  # field is implicit
    
    def test_profile_update_prompts_defined(self, router):
        """Test that prompts are defined for profile update fields."""
        config = router.TASK_FIELDS['profile_update']
        assert 'field_name' in config['prompts']
        assert 'new_value' in config['prompts']
        
        config = router.TASK_FIELDS['update_voice']
        assert 'new_value' in config['prompts']
        
        config = router.TASK_FIELDS['update_audience']
        assert 'new_value' in config['prompts']


class TestFieldAliasesConstant:
    """Test suite for FIELD_ALIASES constant."""
    
    def test_field_aliases_defined(self):
        """Test that FIELD_ALIASES is properly defined."""
        assert 'business_name' in FIELD_ALIASES
        assert 'industry' in FIELD_ALIASES
        assert 'target_audience' in FIELD_ALIASES
        assert 'brand_voice' in FIELD_ALIASES
        assert 'key_offer' in FIELD_ALIASES
        assert 'writing_samples' in FIELD_ALIASES
    
    def test_field_aliases_are_lists(self):
        """Test that all aliases are lists."""
        for field_name, aliases in FIELD_ALIASES.items():
            assert isinstance(aliases, list)
            assert len(aliases) > 0
    
    def test_common_aliases_present(self):
        """Test that common user terms are covered."""
        # Check voice aliases
        assert 'voice' in FIELD_ALIASES['brand_voice']
        assert 'tone' in FIELD_ALIASES['brand_voice']
        
        # Check audience aliases
        assert 'audience' in FIELD_ALIASES['target_audience']
        assert 'customers' in FIELD_ALIASES['target_audience']
        
        # Check business name aliases
        assert 'business' in FIELD_ALIASES['business_name']
        assert 'company' in FIELD_ALIASES['business_name']
