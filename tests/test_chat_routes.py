"""Tests for the chat API endpoint."""

import json
import pytest


def test_chat_endpoint_requires_auth(client):
    """Test that /api/chat requires authentication."""
    response = client.post('/api/chat', json={
        'message': 'Hello'
    })
    # Should redirect to login or return 401
    assert response.status_code in [302, 401]


def test_chat_endpoint_validates_empty_body(authenticated_client):
    """Test that /api/chat validates empty request body."""
    response = authenticated_client.post('/api/chat', 
        data='',
        content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['action'] == 'error'
    assert 'Invalid request' in data['response']


def test_chat_endpoint_validates_missing_message(authenticated_client):
    """Test that /api/chat validates missing message field."""
    response = authenticated_client.post('/api/chat', json={
        'history': []
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['action'] == 'error'
    assert 'message' in data['response'].lower()


def test_chat_routes_to_onboarding_when_profile_missing(client):
    """Test that chat routes to onboarding when user has no profile."""
    # Create and login user without profile
    client.post('/api/signup', json={
        'email': 'nopost@example.com',
        'password': 'testpass123'
    })
    
    response = client.post('/api/chat', json={
        'message': 'Create a post for LinkedIn'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    # Now routes to continue with onboarding flow instead of static 'onboarding' action
    assert data['action'] == 'continue'
    # Should ask for business information
    assert 'response' in data
    # Should have pending onboarding task
    assert data['pending_task'] is not None
    assert data['pending_task']['task_type'] == 'onboarding'


def test_chat_routes_to_onboarding_when_profile_incomplete(client):
    """Test that chat routes to onboarding when profile is incomplete."""
    # Create user with incomplete profile (missing required fields)
    client.post('/api/signup', json={
        'email': 'incomplete@example.com',
        'password': 'testpass123'
    })
    
    # Verify signup worked and user is logged in
    # Add incomplete profile to this user directly
    from models import User, VoiceProfile, db
    from app import create_app
    
    # Get the test app that client is using
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='incomplete@example.com').first()
        assert user is not None
        
        # Create incomplete profile (missing: industry, brand_voice, target_audience, key_offer, writing_samples)
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business'
        )
        db.session.add(profile)
        db.session.commit()
    
    response = client.post('/api/chat', json={
        'message': 'Create a post'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    # Now routes to continue with onboarding flow instead of static 'onboarding' action
    assert data['action'] == 'continue'
    # Should ask for missing information
    assert 'response' in data
    # Should have pending onboarding task
    assert data['pending_task'] is not None
    assert data['pending_task']['task_type'] == 'onboarding'


def test_chat_starts_task_flow_with_complete_profile(authenticated_client):
    """Test that chat starts a task flow when profile is complete."""
    response = authenticated_client.post('/api/chat', json={
        'message': 'Create a post for LinkedIn'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    assert data['pending_task'] is not None
    assert data['pending_task']['task_type'] == 'post'
    assert 'topic' in data['response'].lower()


def test_chat_continues_pending_task(authenticated_client):
    """Test that chat continues a pending task with user's response."""
    # Start with a pending task
    response = authenticated_client.post('/api/chat', json={
        'message': 'New product launch',
        'pending_task': {
            'task_type': 'post',
            'collected': {}
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should either continue or generate based on collected fields
    assert data['action'] in ['continue', 'generated']
    
    if data['action'] == 'continue':
        assert data['pending_task'] is not None
        assert 'collected' in data['pending_task']


def test_chat_generates_content_when_fields_complete(authenticated_client):
    """Test that chat generates content when all required fields are collected."""
    # Provide a task with all required fields
    response = authenticated_client.post('/api/chat', json={
        'message': 'Sounds good',
        'pending_task': {
            'task_type': 'post',
            'collected': {
                'platform': 'LinkedIn',
                'topic': 'New product launch'
            }
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should generate content
    assert data['action'] == 'generated'
    assert data['content'] is not None
    assert len(data['content']) > 0
    assert data['pending_task'] is None


def test_chat_handles_missing_api_key(client, monkeypatch):
    """Test that chat handles missing API key gracefully."""
    # Remove API keys
    monkeypatch.delenv('GENAI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    
    # Create and login user with complete profile
    client.post('/api/signup', json={
        'email': 'apitest@example.com',
        'password': 'testpass123'
    })
    
    # Create complete profile using the client's app context
    from models import User, VoiceProfile, db
    
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='apitest@example.com').first()
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business',
            industry='Technology',
            brand_voice='Professional',
            target_audience='Developers',
            key_offer='Great software'
        )
        profile.set_writing_samples(['Sample post here.'])
        db.session.add(profile)
        db.session.commit()
    
    response = client.post('/api/chat', json={
        'message': 'Create a post'
    })
    
    assert response.status_code == 503
    data = response.get_json()
    assert data['action'] == 'error'
    assert 'AI service' in data['response'] or 'API key' in data['response']


def test_chat_response_structure(authenticated_client):
    """Test that chat response has correct structure."""
    response = authenticated_client.post('/api/chat', json={
        'message': 'Create a post'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Check required fields
    assert 'response' in data
    assert 'action' in data
    assert 'pending_task' in data
    assert 'content' in data
    assert 'suggestions' in data
    
    # Check types
    assert isinstance(data['response'], str)
    assert isinstance(data['action'], str)
    assert data['action'] in ['continue', 'generated', 'onboarding', 'error']


def test_chat_parses_different_task_types(authenticated_client):
    """Test that chat recognizes different task types from messages."""
    test_cases = [
        ('Create a caption for Instagram', 'caption'),
        ('Write a reel script', 'script'),  # reel maps to script task type
        ('Draft an email', 'email'),
        ('Make an ad', 'ad'),
        ('Write a LinkedIn post', 'post'),
    ]
    
    for message, expected_type in test_cases:
        response = authenticated_client.post('/api/chat', json={
            'message': message
        })
        
        assert response.status_code == 200
        data = response.get_json()
        if data['action'] == 'continue' and data['pending_task']:
            assert data['pending_task']['task_type'] == expected_type


def test_chat_handles_conversation_history(authenticated_client):
    """Test that chat accepts conversation history in request."""
    history = [
        {'role': 'user', 'message': 'Hello'},
        {'role': 'assistant', 'message': 'Hi! How can I help?'}
    ]
    
    response = authenticated_client.post('/api/chat', json={
        'message': 'Create a post',
        'history': history
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] in ['continue', 'onboarding']


def test_chat_logs_request_with_request_id(authenticated_client, caplog):
    """Test that chat logs requests with a request_id."""
    import logging
    
    with caplog.at_level(logging.INFO):
        response = authenticated_client.post('/api/chat', json={
            'message': 'Test message'
        })
        
        assert response.status_code == 200
        
        # Check that logs contain request_id pattern
        log_messages = [rec.message for rec in caplog.records]
        has_request_id = any('[' in msg and ']' in msg for msg in log_messages)
        assert has_request_id


def test_chat_uses_conversation_router_for_intent_parsing(authenticated_client):
    """Test that chat uses ConversationRouter to parse user intents."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/post about our new product launch'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should recognize /post command
    if data['action'] == 'continue' and data['pending_task']:
        assert data['pending_task']['task_type'] == 'post'
        assert data['pending_task'].get('flow') == 'content'
        # Should have extracted 'product launch' as topic
        if 'collected' in data['pending_task']:
            collected = data['pending_task']['collected']
            assert 'topic' in collected or data['action'] == 'continue'


def test_chat_continues_content_task_with_flow_marker(authenticated_client):
    """Test that chat continues content task and preserves flow marker."""
    response = authenticated_client.post('/api/chat', json={
        'message': 'product features',
        'pending_task': {
            'task_type': 'post',
            'collected': {'platform': 'instagram'},
            'flow': 'content'
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should either continue or generate
    assert data['action'] in ['continue', 'generated']
    
    if data['action'] == 'continue':
        assert data['pending_task'] is not None
        assert data['pending_task']['flow'] == 'content'
        assert 'collected' in data['pending_task']
        assert 'topic' in data['pending_task']['collected']


def test_chat_generates_with_all_required_fields(authenticated_client):
    """Test that chat generates content when all required fields collected."""
    response = authenticated_client.post('/api/chat', json={
        'message': 'sounds good',
        'pending_task': {
            'task_type': 'post',
            'collected': {
                'platform': 'instagram',
                'topic': 'new product launch'
            },
            'flow': 'content'
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should generate content
    assert data['action'] == 'generated'
    assert data['content'] is not None
    assert len(data['content']) > 0
    assert data['pending_task'] is None
    
    # Check formatted response includes emoji and instructions
    assert '📝' in data['response'] or 'ready' in data['response'].lower()
    assert 'regenerate' in data['response'].lower() or 'copy' in data['response'].lower()


def test_chat_supports_regeneration(authenticated_client):
    """Test that chat supports regenerating last content."""
    # First, send history with a previous content generation
    history = [
        {
            'role': 'user',
            'message': '/post about product launch',
            'pending_task': {
                'task_type': 'post',
                'collected': {'platform': 'linkedin', 'topic': 'product launch'},
                'flow': 'content'
            }
        },
        {
            'role': 'assistant',
            'message': '📝 Your post is ready!'
        }
    ]
    
    response = authenticated_client.post('/api/chat', json={
        'message': 'regenerate',
        'history': history
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should either generate new content or ask for clarification
    # If history parsing worked, should generate
    assert data['action'] in ['generated', 'continue']


def test_chat_normalizes_platform_field(authenticated_client):
    """Test that chat normalizes platform field values."""
    response = authenticated_client.post('/api/chat', json={
        'message': 'ig',  # Shorthand for instagram
        'pending_task': {
            'task_type': 'post',
            'collected': {'topic': 'product launch'},
            'flow': 'content'
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should generate content with normalized platform
    assert data['action'] == 'generated'
    assert data['content'] is not None


def test_chat_normalizes_video_length_field(authenticated_client):
    """Test that chat normalizes video_length field values."""
    response = authenticated_client.post('/api/chat', json={
        'message': '30 seconds',
        'pending_task': {
            'task_type': 'script',
            'collected': {'topic': 'product demo'},
            'flow': 'content'
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should generate content with normalized video length
    assert data['action'] == 'generated'
    assert data['content'] is not None


def test_chat_routes_onboarding_vs_content_flows(authenticated_client):
    """Test that chat correctly routes between onboarding and content flows."""
    # Test content flow with complete profile
    response = authenticated_client.post('/api/chat', json={
        'message': '/post about tech trends',
        'pending_task': None
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should start content flow
    if data['pending_task']:
        assert data['pending_task'].get('flow') == 'content'


def test_chat_provides_content_suggestions(authenticated_client):
    """Test that chat provides helpful content suggestions."""
    response = authenticated_client.post('/api/chat', json={
        'message': 'what can you do?'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should provide suggestions
    # Either in response or suggestions field
    has_suggestions = (
        data.get('suggestions') is not None or
        '/post' in data['response'] or
        '/email' in data['response']
    )
    assert has_suggestions


def test_chat_handles_slash_commands(authenticated_client):
    """Test that chat recognizes various slash commands."""
    commands = [
        ('/post', 'post'),
        ('/caption', 'caption'),
        ('/script', 'script'),
        ('/email', 'email'),
        ('/review', 'review'),
        ('/ad', 'ad'),
        ('/blog', 'blog'),
    ]
    
    for command, expected_task_type in commands:
        response = authenticated_client.post('/api/chat', json={
            'message': f'{command} about test topic'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        if data['pending_task']:
            assert data['pending_task']['task_type'] == expected_task_type
            assert data['pending_task'].get('flow') == 'content'


def test_chat_formats_generated_content_with_emoji(authenticated_client):
    """Test that generated content is formatted with appropriate emoji."""
    task_types = ['post', 'caption', 'script', 'email', 'review', 'ad', 'blog']
    emoji_map = {
        'post': '📝',
        'caption': '📸',
        'script': '🎬',
        'email': '✉️',
        'review': '⭐',
        'ad': '📢',
        'blog': '📰',
    }
    
    for task_type in task_types:
        response = authenticated_client.post('/api/chat', json={
            'message': 'done',
            'pending_task': {
                'task_type': task_type,
                'collected': {'topic': 'test topic', 'platform': 'instagram'},
                'flow': 'content'
            }
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        if data['action'] == 'generated':
            expected_emoji = emoji_map.get(task_type, '✨')
            assert expected_emoji in data['response']
