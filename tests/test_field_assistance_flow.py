"""Unit tests for field assistance flow with NEW field commands.

Tests the AI-assisted field completion flow introduced in PR #275.
These tests verify that:
1. NEW field commands (/name, /industry, /keywords, /goals, /offer) use field_assistance
2. EXISTING commands (/voice, /audience, /samples) maintain their original task types
   BUT now also use the field_assistance flow in the chat handler when no value is provided
3. Field commands with values trigger direct updates
4. Field commands without values trigger AI assistance flow
"""

import pytest
from unittest.mock import Mock
from services.conversation_router import ConversationRouter, FIELD_COMMANDS


class MockProfile:
    """Mock VoiceProfile for testing."""
    def __init__(self):
        self.business_name = 'Test Business'
        self.industry = 'Technology'
        self.brand_voice = 'Professional and friendly'
        self.target_audience = 'Tech startups'


class TestNewFieldCommands:
    """Test suite for NEW field commands that use field_assistance flow."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    @pytest.fixture
    def mock_profile(self):
        """Create a mock profile."""
        return MockProfile()
    
    # NEW field commands only - not including existing /voice, /audience, /samples
    NEW_FIELD_COMMANDS = {
        '/name': 'business_name',
        '/industry': 'industry',
        '/keywords': 'brand_keywords',
        '/goals': 'goals',
        '/offer': 'key_offer',
    }
    
    def test_bare_field_command_triggers_assistance(self, router):
        """Test that bare NEW field commands trigger field assistance."""
        for command, field_name in self.NEW_FIELD_COMMANDS.items():
            result = router._parse_slash_command(command)
            assert result is not None, f"Command {command} should be recognized"
            assert result['task_type'] == 'field_assistance', \
                f"Bare {command} should trigger field_assistance, got {result['task_type']}"
            assert result['field'] == field_name, \
                f"Field should be {field_name}, got {result.get('field')}"
    
    def test_field_command_with_value_triggers_update(self, router):
        """Test that field commands with values trigger direct update."""
        test_cases = [
            ('/name Acme Corp', 'business_name', 'Acme Corp'),
            ('/industry Restaurant', 'industry', 'Restaurant'),
            ('/keywords Fresh, Local, Organic', 'brand_keywords', 'Fresh, Local, Organic'),
            ('/goals Increase awareness', 'goals', 'Increase awareness'),
            ('/offer Free delivery on orders over $50', 'key_offer', 'Free delivery on orders over $50'),
        ]
        
        for command, expected_field, expected_value in test_cases:
            result = router._parse_slash_command(command)
            assert result is not None, f"Command {command} should be recognized"
            assert result['task_type'] == 'update_field', \
                f"{command} with value should trigger update_field, got {result['task_type']}"
            assert result['field'] == expected_field, \
                f"Field should be {expected_field}, got {result.get('field')}"
            assert result['value'] == expected_value, \
                f"Value should be '{expected_value}', got '{result.get('value')}'"
    
    def test_existing_commands_now_use_field_assistance(self, router):
        """Test that existing commands now use field_assistance flow when sent bare."""
        # /voice should now return field_assistance when sent bare
        result = router._parse_slash_command('/voice')
        assert result is not None
        assert result['task_type'] == 'field_assistance', \
            f"/voice should return field_assistance, got {result['task_type']}"
        assert result['field'] == 'brand_voice'
        
        # /audience should now return field_assistance when sent bare
        result = router._parse_slash_command('/audience')
        assert result is not None
        assert result['task_type'] == 'field_assistance', \
            f"/audience should return field_assistance, got {result['task_type']}"
        assert result['field'] == 'target_audience'
        
        # /samples should now return field_assistance when sent bare
        result = router._parse_slash_command('/samples')
        assert result is not None
        assert result['task_type'] == 'field_assistance', \
            f"/samples should return field_assistance, got {result['task_type']}"
        assert result['field'] == 'writing_samples'
        
        # /offer should now return field_assistance when sent bare
        result = router._parse_slash_command('/offer')
        assert result is not None
        assert result['task_type'] == 'field_assistance', \
            f"/offer should return field_assistance, got {result['task_type']}"
        assert result['field'] == 'key_offer'
    
    def test_existing_commands_with_values(self, router):
        """Test that existing commands with values use update_field."""
        # /voice with value should use update_field
        result = router._parse_slash_command('/voice warm and friendly')
        assert result is not None
        assert result['task_type'] == 'update_field'
        assert result['field'] == 'brand_voice'
        assert result['value'] == 'warm and friendly'
        
        # /audience with value should use update_field
        result = router._parse_slash_command('/audience tech startups')
        assert result is not None
        assert result['task_type'] == 'update_field'
        assert result['field'] == 'target_audience'
        assert result['value'] == 'tech startups'
        
        # /samples with value should use update_field
        result = router._parse_slash_command('/samples Check out our new collection!')
        assert result is not None
        assert result['task_type'] == 'update_field'
        assert result['field'] == 'writing_samples'
        assert result['value'] == 'Check out our new collection!'
        
        # /offer with value should use update_field
        result = router._parse_slash_command('/offer Free 30-day trial')
        assert result is not None
        assert result['task_type'] == 'update_field'
        assert result['field'] == 'key_offer'
        assert result['value'] == 'Free 30-day trial'
    
    def test_field_commands_constant_defined(self):
        """Test that FIELD_COMMANDS constant is properly defined."""
        assert FIELD_COMMANDS is not None
        assert isinstance(FIELD_COMMANDS, dict)
        
        # Verify ALL 8 field commands are present
        assert '/name' in FIELD_COMMANDS
        assert '/industry' in FIELD_COMMANDS
        assert '/voice' in FIELD_COMMANDS
        assert '/audience' in FIELD_COMMANDS
        assert '/offer' in FIELD_COMMANDS
        assert '/samples' in FIELD_COMMANDS
        assert '/keywords' in FIELD_COMMANDS
        assert '/goals' in FIELD_COMMANDS
        
        # Verify field mappings
        assert FIELD_COMMANDS['/name'] == 'business_name'
        assert FIELD_COMMANDS['/industry'] == 'industry'
        assert FIELD_COMMANDS['/voice'] == 'brand_voice'
        assert FIELD_COMMANDS['/audience'] == 'target_audience'
        assert FIELD_COMMANDS['/offer'] == 'key_offer'
        assert FIELD_COMMANDS['/samples'] == 'writing_samples'
        assert FIELD_COMMANDS['/keywords'] == 'brand_keywords'
        assert FIELD_COMMANDS['/goals'] == 'goals'
    
    def test_parse_intent_with_new_field_commands(self, router, mock_profile):
        """Test parse_intent with NEW field commands."""
        # Bare command
        result = router.parse_intent('/keywords', mock_profile)
        assert result['task_type'] == 'field_assistance'
        assert result['field'] == 'brand_keywords'
        
        # Command with value
        result = router.parse_intent('/keywords Fresh, Local', mock_profile)
        assert result['task_type'] == 'update_field'
        assert result['field'] == 'brand_keywords'
        assert result['value'] == 'Fresh, Local'
    
    def test_parse_intent_with_existing_commands(self, router, mock_profile):
        """Test parse_intent with EXISTING commands - verify new behavior."""
        # /voice should now use field_assistance when bare
        result = router.parse_intent('/voice', mock_profile)
        assert result['task_type'] == 'field_assistance'
        assert result['field'] == 'brand_voice'
        
        # /audience should now use field_assistance when bare
        result = router.parse_intent('/audience', mock_profile)
        assert result['task_type'] == 'field_assistance'
        assert result['field'] == 'target_audience'
        
        # /voice with value should use update_field
        result = router.parse_intent('/voice warm and friendly', mock_profile)
        assert result['task_type'] == 'update_field'
        assert result['field'] == 'brand_voice'
        assert result['value'] == 'warm and friendly'
        assert result['follow_up_needed'] is True


class TestFieldCommandEdgeCases:
    """Test edge cases for field command handling."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    def test_field_command_with_whitespace_value(self, router):
        """Test handling of field commands with whitespace in values."""
        result = router._parse_slash_command('/keywords  Fresh, Local  ')
        assert result is not None
        assert result['task_type'] == 'update_field'
        assert result['value'] == 'Fresh, Local'  # Should be trimmed
    
    def test_field_command_case_insensitive(self, router):
        """Test that field commands are case insensitive."""
        result = router._parse_slash_command('/KEYWORDS')
        assert result is not None
        assert result['task_type'] == 'field_assistance'
        
        result = router._parse_slash_command('/Keywords Fresh')
        assert result is not None
        assert result['task_type'] == 'update_field'
    
    def test_invalid_command_returns_none(self, router):
        """Test that invalid commands return None."""
        result = router._parse_slash_command('/notacommand')
        assert result is None
        
        result = router._parse_slash_command('/xyz')
        assert result is None


class TestBackwardCompatibility:
    """Test backward compatibility with existing command behavior."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    @pytest.fixture
    def mock_profile(self):
        """Create a mock profile."""
        return MockProfile()
    
    def test_profile_update_commands_unchanged(self, router, mock_profile):
        """Test that profile update commands work as before."""
        # /profile should still work
        result = router.parse_intent('/profile', mock_profile)
        assert result['task_type'] == 'profile'
        
        # /update should still work
        result = router.parse_intent('/update', mock_profile)
        assert result['task_type'] == 'profile_update'
    
    def test_content_generation_commands_unchanged(self, router, mock_profile):
        """Test that content generation commands are unaffected."""
        # /post should still work
        result = router.parse_intent('/post', mock_profile)
        assert result['task_type'] == 'post'
        
        # /email should still work
        result = router.parse_intent('/email', mock_profile)
        assert result['task_type'] == 'email'
        
        # /caption should still work
        result = router.parse_intent('/caption', mock_profile)
        assert result['task_type'] == 'caption'
    
    def test_task_fields_defined_for_new_types(self, router):
        """Test that TASK_FIELDS includes new task types."""
        assert 'field_assistance' in router.TASK_FIELDS
        assert 'update_field' in router.TASK_FIELDS
        
        # Verify required fields
        assert 'field' in router.TASK_FIELDS['field_assistance']['required']
        assert 'field' in router.TASK_FIELDS['update_field']['required']
        assert 'value' in router.TASK_FIELDS['update_field']['required']
