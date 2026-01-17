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
    assert data['action'] == 'onboarding'
    assert 'profile' in data['response'].lower()
    assert data['pending_task'] is None


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
    assert data['action'] == 'onboarding'


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
    
    # Create complete profile
    from models import User, VoiceProfile, db
    from app import create_app
    
    test_app = create_app()
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
        ('Write a reel script', 'reel'),
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
