"""Tests for new profile management slash commands."""

import pytest
from unittest.mock import Mock, patch
from services.conversation_router import ConversationRouter


class MockProfile:
    """Mock VoiceProfile for testing."""
    def __init__(self):
        self.business_name = 'Test Business'
        self.industry = 'Technology'
        self.brand_voice = 'Professional and friendly'
        self.target_audience = 'Small business owners'
        self.key_offer = 'Best in class service'
        
    def get_writing_samples(self):
        return ['Sample 1', 'Sample 2']
    
    def set_writing_samples(self, samples):
        self._samples = samples


class TestProfileSlashCommands:
    """Test suite for profile slash commands."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    @pytest.fixture
    def mock_profile(self):
        """Create a mock profile."""
        return MockProfile()
    
    def test_samples_command_in_map(self, router):
        """Test /samples command is in COMMAND_MAP."""
        assert '/samples' in router.COMMAND_MAP
        assert router.COMMAND_MAP['/samples'] == 'update_samples'
    
    def test_import_command_in_map(self, router):
        """Test /import command is in COMMAND_MAP."""
        assert '/import' in router.COMMAND_MAP
        assert router.COMMAND_MAP['/import'] == 'import_profile'
    
    def test_parse_samples_command(self, router):
        """Test parsing /samples command."""
        result = router._parse_slash_command('/samples')
        assert result is not None
        assert result['task_type'] == 'update_samples'
        assert 'extracted_params' in result
    
    def test_parse_import_command_with_url(self, router):
        """Test parsing /import command with URL."""
        result = router._parse_slash_command('/import https://example.com')
        assert result is not None
        assert result['task_type'] == 'import_profile'
        # URL should be in extracted params (if extraction logic exists)
    
    def test_parse_import_command_without_url(self, router):
        """Test parsing /import command without URL."""
        result = router._parse_slash_command('/import')
        assert result is not None
        assert result['task_type'] == 'import_profile'
    
    def test_samples_task_fields_config(self, router):
        """Test update_samples has proper TASK_FIELDS config."""
        assert 'update_samples' in router.TASK_FIELDS
        config = router.TASK_FIELDS['update_samples']
        assert 'required' in config
        assert 'sample_text' in config['required']
        assert 'prompts' in config
    
    def test_import_task_fields_config(self, router):
        """Test import_profile has proper TASK_FIELDS config."""
        assert 'import_profile' in router.TASK_FIELDS
        config = router.TASK_FIELDS['import_profile']
        assert 'required' in config
        assert 'url' in config['required']
        assert 'prompts' in config
    
    def test_parse_intent_samples(self, router, mock_profile):
        """Test parsing intent for /samples command."""
        result = router.parse_intent('/samples', mock_profile)
        assert result['task_type'] == 'update_samples'
        assert result['intent'] == 'generate'
    
    def test_parse_intent_import(self, router, mock_profile):
        """Test parsing intent for /import command."""
        result = router.parse_intent('/import https://example.com', mock_profile)
        assert result['task_type'] == 'import_profile'
        assert result['intent'] == 'generate'
    
    def test_get_missing_fields_samples(self, router):
        """Test getting missing fields for update_samples."""
        collected = {}
        missing = router.get_missing_fields('update_samples', collected)
        assert 'sample_text' in missing
        
        collected = {'sample_text': 'My sample'}
        missing = router.get_missing_fields('update_samples', collected)
        assert len(missing) == 0
    
    def test_get_missing_fields_import(self, router):
        """Test getting missing fields for import_profile."""
        collected = {}
        missing = router.get_missing_fields('import_profile', collected)
        assert 'url' in missing
        
        collected = {'url': 'https://example.com'}
        missing = router.get_missing_fields('import_profile', collected)
        assert len(missing) == 0
    
    def test_get_next_prompt_samples(self, router):
        """Test getting next prompt for samples collection."""
        missing = ['sample_text']
        prompt = router.get_next_prompt('update_samples', missing)
        assert 'sample' in prompt.lower()
        assert 'paste' in prompt.lower() or 'writing' in prompt.lower()
    
    def test_get_next_prompt_import(self, router):
        """Test getting next prompt for import."""
        missing = ['url']
        prompt = router.get_next_prompt('import_profile', missing)
        assert 'url' in prompt.lower()
    
    def test_is_ready_to_generate_samples(self, router):
        """Test checking if ready to generate for samples."""
        collected = {}
        assert not router.is_ready_to_generate('update_samples', collected)
        
        collected = {'sample_text': 'My writing sample'}
        assert router.is_ready_to_generate('update_samples', collected)
    
    def test_is_ready_to_generate_import(self, router):
        """Test checking if ready to generate for import."""
        collected = {}
        assert not router.is_ready_to_generate('import_profile', collected)
        
        collected = {'url': 'https://example.com'}
        assert router.is_ready_to_generate('import_profile', collected)
