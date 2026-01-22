"""Test fix for profile update commands creating duplicate question loop.

This test verifies the fix for the bug where /audience [value] and /voice [value]
commands were asking the question again instead of updating immediately.
"""

import pytest
import json
from unittest.mock import patch, MagicMock


def test_audience_command_with_value_updates_immediately(authenticated_client):
    """Test that /audience [value] updates profile immediately without asking again."""
    
    # Mock the generation service to avoid actual API calls
    with patch('routes.chat_routes._handle_update_field') as mock_update:
        mock_update.return_value = {
            'response': '✅ **Target Audience updated!**\n\nI\'ve saved: busy entrepreneurs\n\nThis will help me create better content for you. Ready to create something?',
            'action': 'profile_updated',
            'suggestions': ['Create content', 'Update another field', 'View my profile']
        }
        
        response = authenticated_client.post(
            '/api/chat',
            data=json.dumps({
                'message': '/audience busy entrepreneurs or solopreneurs who are looking to generate content that sounds like them faster',
                'history': [],
                'pending_task': None
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should NOT ask the question again
        assert 'Who is your ideal customer?' not in data['response']
        
        # Should confirm the update
        assert 'updated' in data['response'].lower() or 'saved' in data['response'].lower()
        
        # Verify _handle_update_field was called with correct parameters
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == 'target_audience'  # field
        assert 'busy entrepreneurs' in call_args[0][1]  # value


def test_voice_command_with_value_updates_immediately(authenticated_client):
    """Test that /voice [value] updates profile immediately without asking again."""
    
    with patch('routes.chat_routes._handle_update_field') as mock_update:
        mock_update.return_value = {
            'response': '✅ **Brand Voice updated!**\n\nI\'ve saved: warm and friendly\n\nThis will help me create better content for you. Ready to create something?',
            'action': 'profile_updated',
            'suggestions': ['Create content', 'Update another field', 'View my profile']
        }
        
        response = authenticated_client.post(
            '/api/chat',
            data=json.dumps({
                'message': '/voice warm and friendly',
                'history': [],
                'pending_task': None
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should NOT ask the question again
        assert 'How would you describe your brand voice?' not in data['response']
        
        # Should confirm the update
        assert 'updated' in data['response'].lower() or 'saved' in data['response'].lower()
        
        # Verify _handle_update_field was called with correct parameters
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == 'brand_voice'  # field
        assert call_args[0][1] == 'warm and friendly'  # value


def test_bare_audience_command_prompts_for_value(authenticated_client):
    """Test that /audience (no value) prompts for value once."""
    
    with patch('routes.chat_routes._handle_field_assistance') as mock_assist:
        mock_assist.return_value = {
            'response': 'Define Target Audience 🎯 - Who is your ideal customer? Be specific!',
            'action': 'continue',
            'pending_task': {
                'flow': 'field_update',
                'task_type': 'field_assistance',
                'field': 'target_audience'
            }
        }
        
        response = authenticated_client.post(
            '/api/chat',
            data=json.dumps({
                'message': '/audience',
                'history': [],
                'pending_task': None
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should ask for the value
        assert data['action'] == 'continue'
        assert 'pending_task' in data
        
        # Verify _handle_field_assistance was called
        mock_assist.assert_called_once()


def test_bare_voice_command_prompts_for_value(authenticated_client):
    """Test that /voice (no value) prompts for value once."""
    
    with patch('routes.chat_routes._handle_field_assistance') as mock_assist:
        mock_assist.return_value = {
            'response': 'Brand Voice 🎤 - How would you describe your brand voice?',
            'action': 'continue',
            'pending_task': {
                'flow': 'field_update',
                'task_type': 'field_assistance',
                'field': 'brand_voice'
            }
        }
        
        response = authenticated_client.post(
            '/api/chat',
            data=json.dumps({
                'message': '/voice',
                'history': [],
                'pending_task': None
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should ask for the value
        assert data['action'] == 'continue'
        assert 'pending_task' in data
        
        # Verify _handle_field_assistance was called
        mock_assist.assert_called_once()


def test_follow_up_after_prompt_updates_profile(authenticated_client):
    """Test that follow-up answer after prompt updates profile correctly."""
    
    with patch('routes.chat_routes._handle_update_field') as mock_update:
        mock_update.return_value = {
            'response': '✅ **Target Audience updated!**\n\nI\'ve saved: tech startups\n\nThis will help me create better content for you.',
            'action': 'profile_updated',
            'suggestions': ['Create content', 'Update another field', 'View my profile']
        }
        
        # Simulate being in a pending field_update task
        response = authenticated_client.post(
            '/api/chat',
            data=json.dumps({
                'message': 'tech startups looking for scalable solutions',
                'history': [],
                'pending_task': {
                    'flow': 'field_update',
                    'task_type': 'field_assistance',
                    'field': 'target_audience'
                }
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should update the profile
        assert data['action'] == 'profile_updated'
        
        # Verify _handle_update_field was called
        mock_update.assert_called_once()


def test_no_infinite_loop_with_audience_command(authenticated_client):
    """Regression test: Ensure /audience [value] doesn't create infinite loop."""
    
    with patch('routes.chat_routes._handle_update_field') as mock_update:
        mock_update.return_value = {
            'response': '✅ **Target Audience updated!**',
            'action': 'profile_updated',
            'suggestions': ['Create content']
        }
        
        # Send the command once
        response = authenticated_client.post(
            '/api/chat',
            data=json.dumps({
                'message': '/audience busy entrepreneurs',
                'history': [],
                'pending_task': None
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should complete without asking again
        assert data['action'] == 'profile_updated'
        assert 'pending_task' not in data or data.get('pending_task') is None
        
        # _handle_update_field should be called exactly once
        assert mock_update.call_count == 1
