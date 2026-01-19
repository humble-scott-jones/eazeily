"""Tests for the field assistance flow (AI-assisted profile field completion)."""

import pytest
from services.conversation_router import ConversationRouter, FIELD_COMMANDS


class TestFieldAssistanceFlow:
    """Tests for the new field assistance flow."""
    
    @pytest.fixture
    def router(self):
        """Create a conversation router instance."""
        return ConversationRouter()
    
    def test_bare_field_command_triggers_assistance(self, router):
        """Test that bare field commands like /keywords trigger field assistance."""
        # Test all field commands
        for command, field_name in FIELD_COMMANDS.items():
            result = router._parse_slash_command(command)
            
            assert result is not None, f"Command {command} should be recognized"
            assert result['task_type'] == 'field_assistance', f"Command {command} should trigger field_assistance"
            assert result['field'] == field_name, f"Command {command} should map to field {field_name}"
    
    def test_field_command_with_value_triggers_direct_update(self, router):
        """Test that field commands with values trigger direct update."""
        test_cases = [
            ('/keywords Fresh, Local, Handmade', 'brand_keywords', 'Fresh, Local, Handmade'),
            ('/voice warm and friendly', 'brand_voice', 'warm and friendly'),
            ('/audience busy professionals', 'target_audience', 'busy professionals'),
            ('/goals Brand awareness', 'goals', 'Brand awareness'),
            ('/offer Free trial', 'key_offer', 'Free trial'),
            ('/name My Business', 'business_name', 'My Business'),
        ]
        
        for command_input, expected_field, expected_value in test_cases:
            result = router._parse_slash_command(command_input)
            
            assert result is not None, f"Command {command_input} should be recognized"
            assert result['task_type'] == 'update_field', f"Command {command_input} should trigger update_field"
            assert result['field'] == expected_field, f"Expected field {expected_field}, got {result.get('field')}"
            assert result['value'] == expected_value, f"Expected value '{expected_value}', got '{result.get('value')}'"
    
    def test_field_commands_mapping_completeness(self):
        """Test that FIELD_COMMANDS covers all 8 profile fields."""
        expected_fields = {
            'business_name',
            'industry',
            'brand_voice',
            'target_audience',
            'key_offer',
            'writing_samples',
            'brand_keywords',
            'goals',
        }
        
        actual_fields = set(FIELD_COMMANDS.values())
        
        assert actual_fields == expected_fields, (
            f"FIELD_COMMANDS should cover all 8 profile fields. "
            f"Missing: {expected_fields - actual_fields}, "
            f"Extra: {actual_fields - expected_fields}"
        )
    
    def test_all_field_commands_in_command_map(self, router):
        """Test that all field commands are registered in COMMAND_MAP."""
        for command in FIELD_COMMANDS.keys():
            assert command in router.COMMAND_MAP, f"Command {command} should be in COMMAND_MAP"
