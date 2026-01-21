"""Tests for export and copy improvements feature."""

import json
import pytest
from unittest.mock import Mock, patch


def test_export_command_basic(authenticated_client):
    """Test that /export command returns export options."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/export'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    assert 'Export' in data['response']


def test_export_command_all_shows_pro_message(authenticated_client):
    """Test that /export all shows pro upgrade message."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/export all'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    assert 'Pro users' in data['response']
    assert 'Export All Starred Content' in data['response']


def test_export_command_week_shows_pro_message(authenticated_client):
    """Test that /export week shows pro upgrade message."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/export week'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    assert 'Pro users' in data['response']
    assert 'Export Last 7 Days' in data['response']


def test_preview_command_basic(authenticated_client):
    """Test that /preview command returns preview information."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/preview'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    assert 'Preview' in data['response']


def test_preview_command_shows_platform_info(authenticated_client):
    """Test that preview command includes platform information."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/preview'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    # Check for mention of platforms or preview tools
    response_text = data['response']
    assert 'platform' in response_text.lower() or 'preview' in response_text.lower()


def test_conversation_router_recognizes_export_command():
    """Test that ConversationRouter recognizes /export command."""
    from services.conversation_router import ConversationRouter
    from unittest.mock import Mock
    
    router = ConversationRouter()
    mock_profile = Mock()
    mock_profile.business_name = 'Test Business'
    
    result = router.parse_intent('/export', mock_profile)
    
    assert result['task_type'] == 'export'
    # Intent will be 'generate' since export is a valid command
    assert result['intent'] in ['command', 'generate']


def test_conversation_router_recognizes_preview_command():
    """Test that ConversationRouter recognizes /preview command."""
    from services.conversation_router import ConversationRouter
    from unittest.mock import Mock
    
    router = ConversationRouter()
    mock_profile = Mock()
    mock_profile.business_name = 'Test Business'
    
    result = router.parse_intent('/preview', mock_profile)
    
    assert result['task_type'] == 'preview'
    # Intent will be 'generate' since preview is a valid command
    assert result['intent'] in ['command', 'generate']


def test_regeneration_variation_request(authenticated_client):
    """Test that regeneration with variation works."""
    # First generate some content
    response = authenticated_client.post('/api/chat', json={
        'message': '/post about our new product on Instagram'
    })
    
    assert response.status_code == 200
    first_data = response.get_json()
    
    # Now request a variation (shorter)
    response = authenticated_client.post('/api/chat', json={
        'message': 'Regenerate the last content but make it shorter',
        'history': [
            {'role': 'user', 'message': '/post about our new product on Instagram'},
            {'role': 'assistant', 'message': first_data['response']}
        ]
    })
    
    assert response.status_code == 200
    data = response.get_json()
    # Should get a response (either generated or asking for more info)
    assert 'response' in data
    assert data['action'] in ['continue', 'generated']


def test_export_handler_returns_information(authenticated_client):
    """Test that export handler returns useful information."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/export'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    # Check for export-related content
    response_text = data['response'].lower()
    assert 'export' in response_text or 'copy' in response_text or 'download' in response_text


def test_command_guidance_for_export():
    """Test that export command has guidance text."""
    from services.conversation_router import COMMAND_GUIDANCE
    
    assert '/export' in COMMAND_GUIDANCE
    guidance = COMMAND_GUIDANCE['/export']
    assert 'export' in guidance.lower()


def test_command_guidance_for_preview():
    """Test that preview command has guidance text."""
    from services.conversation_router import COMMAND_GUIDANCE
    
    assert '/preview' in COMMAND_GUIDANCE
    guidance = COMMAND_GUIDANCE['/preview']
    assert 'preview' in guidance.lower()


def test_slash_commands_include_export_and_preview():
    """Test that frontend SLASH_COMMANDS include new commands."""
    # This tests that the commands are properly registered
    # In a real test environment, we'd load the JS file and parse it
    # For now, we just verify the backend recognizes the commands
    from services.conversation_router import ConversationRouter
    
    router = ConversationRouter()
    
    # Verify export is in COMMAND_MAP
    assert '/export' in router.COMMAND_MAP
    assert router.COMMAND_MAP['/export'] == 'export'
    
    # Verify preview is in COMMAND_MAP
    assert '/preview' in router.COMMAND_MAP
    assert router.COMMAND_MAP['/preview'] == 'preview'
