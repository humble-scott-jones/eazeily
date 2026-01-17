"""Tests for ConversationRouter integration with chat routes."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


def test_chat_uses_conversation_router_for_intent_parsing(authenticated_client):
    """Test that chat endpoint uses ConversationRouter.parse_intent()."""
    with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
        mock_parse.return_value = {
            'intent': 'generate',
            'task_type': 'post',
            'extracted_params': {'topic': 'new product', 'platform': 'instagram'},
            'follow_up_needed': False,
            'follow_up_question': None,
            'missing_fields': []
        }
        
        with patch('routes.chat_routes._generate_content') as mock_gen:
            mock_gen.return_value = 'Generated post content'
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/post about new product on instagram'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'generated'
            
            # Verify ConversationRouter was called
            mock_parse.assert_called_once()


def test_chat_handles_unknown_intent_with_suggestions(authenticated_client):
    """Test that unknown intent returns helpful suggestions."""
    with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
        mock_parse.return_value = {
            'intent': 'unknown',
            'task_type': None,
            'extracted_params': {},
            'follow_up_needed': True,
            'follow_up_question': "I'm not sure what you'd like to create. Try using a command like /post",
            'missing_fields': []
        }
        
        response = authenticated_client.post('/api/chat', json={
            'message': 'what is the weather today'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'continue'
        assert 'command' in data['response'].lower() or 'post' in data['response'].lower()
        assert data['suggestions'] is not None
        assert len(data['suggestions']) > 0


def test_chat_collects_missing_fields_with_conversation_router(authenticated_client):
    """Test that chat collects missing fields using ConversationRouter methods."""
    with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
        mock_parse.return_value = {
            'intent': 'generate',
            'task_type': 'post',
            'extracted_params': {'topic': 'summer sale'},
            'follow_up_needed': True,
            'follow_up_question': 'Which platform? (Instagram, Facebook, LinkedIn)',
            'missing_fields': ['platform']
        }
        
        response = authenticated_client.post('/api/chat', json={
            'message': '/post about summer sale'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'continue'
        assert 'platform' in data['response'].lower()
        assert data['pending_task'] is not None
        assert data['pending_task']['task_type'] == 'post'
        assert 'topic' in data['pending_task']['collected']


def test_chat_continues_with_conversation_router_methods(authenticated_client):
    """Test that _continue_task_flow uses ConversationRouter methods."""
    with patch('routes.chat_routes.conversation_router.get_missing_fields') as mock_missing:
        with patch('routes.chat_routes.conversation_router.get_next_prompt') as mock_prompt:
            # First call: platform is missing
            mock_missing.side_effect = [
                ['platform'],  # Before storing response
                []  # After storing response - no more missing
            ]
            
            with patch('routes.chat_routes._generate_content') as mock_gen:
                mock_gen.return_value = 'Generated post content'
                
                response = authenticated_client.post('/api/chat', json={
                    'message': 'Instagram',
                    'pending_task': {
                        'task_type': 'post',
                        'collected': {'topic': 'summer sale'}
                    }
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['action'] == 'generated'
                assert mock_missing.call_count == 2


def test_field_value_normalization_platform(authenticated_client):
    """Test that platform field values are normalized."""
    with patch('routes.chat_routes.conversation_router.get_missing_fields') as mock_missing:
        mock_missing.side_effect = [
            ['platform'],  # Before storing
            []  # After storing - complete
        ]
        
        with patch('routes.chat_routes._generate_content') as mock_gen:
            mock_gen.return_value = 'Generated content'
            
            # Test 'ig' normalizes to 'instagram'
            response = authenticated_client.post('/api/chat', json={
                'message': 'ig',
                'pending_task': {
                    'task_type': 'post',
                    'collected': {'topic': 'test'}
                }
            })
            
            assert response.status_code == 200
            # Check that generation was called with normalized platform
            mock_gen.assert_called_once()
            call_args = mock_gen.call_args
            collected = call_args[0][2]  # Third argument is collected dict
            assert collected['platform'] == 'instagram'


def test_field_value_normalization_video_length(authenticated_client):
    """Test that video_length field values are normalized."""
    with patch('routes.chat_routes.conversation_router.get_missing_fields') as mock_missing:
        mock_missing.side_effect = [
            ['video_length'],  # Before storing
            []  # After storing - complete
        ]
        
        with patch('routes.chat_routes._generate_content') as mock_gen:
            mock_gen.return_value = 'Generated script'
            
            # Test '30 seconds' normalizes to '30s'
            response = authenticated_client.post('/api/chat', json={
                'message': '30 seconds',
                'pending_task': {
                    'task_type': 'script',
                    'collected': {'topic': 'tutorial'}
                }
            })
            
            assert response.status_code == 200
            mock_gen.assert_called_once()
            call_args = mock_gen.call_args
            collected = call_args[0][2]
            assert collected['video_length'] == '30s'


def test_formatted_content_display_with_emoji(authenticated_client):
    """Test that generated content is formatted with emojis."""
    with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
        mock_parse.return_value = {
            'intent': 'generate',
            'task_type': 'post',
            'extracted_params': {'topic': 'test', 'platform': 'instagram'},
            'follow_up_needed': False,
            'follow_up_question': None,
            'missing_fields': []
        }
        
        with patch('routes.chat_routes._generate_content') as mock_gen:
            mock_gen.return_value = 'Test post content here'
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/post about test on instagram'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'generated'
            # Check for emoji in response
            assert '📝' in data['response']
            assert 'post is ready' in data['response'].lower()
            assert data['content'] == 'Test post content here'


def test_regenerate_request_detection(authenticated_client):
    """Test that regenerate requests are detected and handled."""
    # Mock history with a previous generation
    history = [
        {'role': 'user', 'message': '/post about test'},
        {'role': 'assistant', 'message': 'Here is your post', 'pending_task': {
            'task_type': 'post',
            'collected': {'topic': 'test', 'platform': 'instagram'}
        }}
    ]
    
    with patch('routes.chat_routes._generate_content') as mock_gen:
        mock_gen.return_value = 'Regenerated post content'
        
        response = authenticated_client.post('/api/chat', json={
            'message': 'regenerate',
            'history': history
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'generated'
        assert 'Regenerated post content' in data['content']


def test_suggestions_after_generation(authenticated_client):
    """Test that suggestions are provided after content generation."""
    with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
        mock_parse.return_value = {
            'intent': 'generate',
            'task_type': 'email',
            'extracted_params': {'topic': 'newsletter'},
            'follow_up_needed': False,
            'follow_up_question': None,
            'missing_fields': []
        }
        
        with patch('routes.chat_routes._generate_content') as mock_gen:
            mock_gen.return_value = 'Email content'
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/email newsletter'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'generated'
            assert data['suggestions'] is not None
            assert len(data['suggestions']) > 0


def test_multi_turn_field_collection_flow(authenticated_client):
    """Test complete multi-turn conversation flow."""
    # Step 1: Initial request with only task type
    with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
        mock_parse.return_value = {
            'intent': 'generate',
            'task_type': 'ad',
            'extracted_params': {},
            'follow_up_needed': True,
            'follow_up_question': 'What product or offer is the ad for?',
            'missing_fields': ['topic', 'platform']
        }
        
        response = authenticated_client.post('/api/chat', json={
            'message': '/ad'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'continue'
        assert data['pending_task']['task_type'] == 'ad'
        pending_task = data['pending_task']
    
    # Step 2: Provide topic
    with patch('routes.chat_routes.conversation_router.get_missing_fields') as mock_missing:
        with patch('routes.chat_routes.conversation_router.get_next_prompt') as mock_prompt:
            mock_missing.side_effect = [
                ['topic', 'platform'],  # Before storing
                ['platform']  # After storing topic
            ]
            mock_prompt.return_value = 'Which ad platform?'
            
            response = authenticated_client.post('/api/chat', json={
                'message': 'new shoes',
                'pending_task': pending_task
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'continue'
            assert 'platform' in data['response'].lower()
            pending_task = data['pending_task']
    
    # Step 3: Provide platform and generate
    with patch('routes.chat_routes.conversation_router.get_missing_fields') as mock_missing:
        mock_missing.side_effect = [
            ['platform'],  # Before storing
            []  # After storing - complete
        ]
        
        with patch('routes.chat_routes._generate_content') as mock_gen:
            mock_gen.return_value = 'Ad copy for shoes'
            
            response = authenticated_client.post('/api/chat', json={
                'message': 'facebook',
                'pending_task': pending_task
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'generated'
            assert data['content'] == 'Ad copy for shoes'


def test_slash_commands_for_all_task_types(authenticated_client):
    """Test that all slash commands are recognized."""
    task_types = ['post', 'caption', 'script', 'email', 'review', 'ad', 'blog']
    
    for task_type in task_types:
        with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
            mock_parse.return_value = {
                'intent': 'generate',
                'task_type': task_type,
                'extracted_params': {},
                'follow_up_needed': True,
                'follow_up_question': f'Tell me more about this {task_type}',
                'missing_fields': ['topic']
            }
            
            response = authenticated_client.post('/api/chat', json={
                'message': f'/{task_type}'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'continue'
            assert data['pending_task']['task_type'] == task_type


def test_error_handling_during_generation(authenticated_client):
    """Test error handling when generation fails."""
    with patch('routes.chat_routes.conversation_router.parse_intent') as mock_parse:
        mock_parse.return_value = {
            'intent': 'generate',
            'task_type': 'post',
            'extracted_params': {'topic': 'test', 'platform': 'instagram'},
            'follow_up_needed': False,
            'follow_up_question': None,
            'missing_fields': []
        }
        
        with patch('routes.chat_routes._generate_content') as mock_gen:
            mock_gen.side_effect = Exception('API error')
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/post about test on instagram'
            })
            
            assert response.status_code == 500
            data = response.get_json()
            assert data['action'] == 'error'
            assert 'couldn\'t generate' in data['response'].lower()


def test_normalize_field_value_handles_edge_cases():
    """Test _normalize_field_value helper with edge cases."""
    from routes.chat_routes import _normalize_field_value
    
    # Test platform normalization
    assert _normalize_field_value('platform', 'Instagram') == 'instagram'
    assert _normalize_field_value('platform', 'ig') == 'instagram'
    assert _normalize_field_value('platform', 'FB') == 'facebook'
    assert _normalize_field_value('platform', 'LinkedIn') == 'linkedin'
    
    # Test video_length normalization
    assert _normalize_field_value('video_length', '30') == '30s'
    assert _normalize_field_value('video_length', '60 seconds') == '60s'
    assert _normalize_field_value('video_length', '15s') == '15s'
    assert _normalize_field_value('video_length', 'invalid') == '30s'  # default
    
    # Test other fields pass through
    assert _normalize_field_value('topic', 'test topic') == 'test topic'
    assert _normalize_field_value('unknown', '  value  ') == 'value'


def test_format_generated_content_helper():
    """Test _format_generated_content helper formatting."""
    from routes.chat_routes import _format_generated_content
    
    # Test different task types
    result = _format_generated_content('post', 'Test content')
    assert '📝' in result
    assert 'post is ready' in result.lower()
    assert 'Test content' in result
    
    result = _format_generated_content('email', 'Email body')
    assert '✉️' in result
    assert 'email is ready' in result.lower()
    
    result = _format_generated_content('script', 'Video script')
    assert '🎬' in result
    
    result = _format_generated_content('unknown_type', 'Content')
    assert '✨' in result  # default emoji


def test_get_content_suggestions_helper():
    """Test _get_content_suggestions helper."""
    from routes.chat_routes import _get_content_suggestions
    
    suggestions = _get_content_suggestions()
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    assert any('/post' in s for s in suggestions)
    assert any('/email' in s for s in suggestions)
