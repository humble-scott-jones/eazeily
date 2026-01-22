"""Tests for the skip profile flow in chat."""

import json
import pytest
from models import User, VoiceProfile, db


def test_explicit_content_request_with_incomplete_profile_offers_skip(client):
    """Test that explicit content requests with incomplete profile offer skip option."""
    # Create user with minimal profile (just business name, missing required fields)
    client.post('/api/signup', json={
        'email': 'skiptest@example.com',
        'password': 'testpass123'
    })
    
    # Add minimal profile
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='skiptest@example.com').first()
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business'
        )
        db.session.add(profile)
        db.session.commit()
    
    # Make explicit content request
    response = client.post('/api/chat', json={
        'message': '/post about our new product launch'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should offer skip option
    assert data['action'] == 'profile_prompt_with_skip'
    assert 'missing' in data['response'].lower() or 'profile' in data['response'].lower()
    assert 'actions' in data
    assert len(data['actions']) == 2
    
    # Check for skip and complete profile actions
    actions = {action['action']: action for action in data['actions']}
    assert 'generate_anyway' in actions
    assert 'complete_profile' in actions
    
    # Verify button texts
    assert '⚡' in actions['generate_anyway']['text'] or 'Skip' in actions['generate_anyway']['text']
    assert '✨' in actions['complete_profile']['text'] or 'Complete' in actions['complete_profile']['text']


def test_skip_generates_content_with_minimal_profile(client):
    """Test that choosing skip generates content with minimal profile data."""
    # Create user with minimal profile
    client.post('/api/signup', json={
        'email': 'skipgen@example.com',
        'password': 'testpass123'
    })
    
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='skipgen@example.com').first()
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business',
            industry='Technology'
        )
        db.session.add(profile)
        db.session.commit()
    
    # First, trigger the skip prompt
    response1 = client.post('/api/chat', json={
        'message': '/post about innovation'
    })
    
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1['action'] == 'profile_prompt_with_skip'
    
    # Get pending task
    pending_task = data1['pending_task']
    
    # Now choose to skip
    response2 = client.post('/api/chat', json={
        'message': 'generate_anyway',
        'pending_task': pending_task
    })
    
    assert response2.status_code == 200
    data2 = response2.get_json()
    
    # Should generate content
    assert data2['action'] == 'generated'
    assert 'content' in data2
    assert data2['content'] is not None


def test_complete_profile_starts_onboarding(client):
    """Test that choosing complete profile starts onboarding flow."""
    # Create user with minimal profile
    client.post('/api/signup', json={
        'email': 'completetest@example.com',
        'password': 'testpass123'
    })
    
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='completetest@example.com').first()
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business'
        )
        db.session.add(profile)
        db.session.commit()
    
    # First, trigger the skip prompt
    response1 = client.post('/api/chat', json={
        'message': 'create a post about our services'
    })
    
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1['action'] == 'profile_prompt_with_skip'
    
    # Get pending task
    pending_task = data1['pending_task']
    
    # Now choose to complete profile
    response2 = client.post('/api/chat', json={
        'message': 'complete_profile',
        'pending_task': pending_task
    })
    
    assert response2.status_code == 200
    data2 = response2.get_json()
    
    # Should continue to onboarding
    assert data2['action'] == 'continue'
    assert data2['pending_task'] is not None
    # Should ask about profile information
    assert 'industry' in data2['response'].lower() or 'business' in data2['response'].lower()


def test_explicit_request_detection_slash_commands(client):
    """Test that slash commands are detected as explicit content requests."""
    # Create user with minimal profile
    client.post('/api/signup', json={
        'email': 'slashtest@example.com',
        'password': 'testpass123'
    })
    
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='slashtest@example.com').first()
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Co'
        )
        db.session.add(profile)
        db.session.commit()
    
    slash_commands = ['/post', '/caption', '/email', '/script', '/ad']
    
    for command in slash_commands:
        response = client.post('/api/chat', json={
            'message': f'{command} test content'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        # Should offer skip since profile is incomplete
        assert data['action'] == 'profile_prompt_with_skip'


def test_explicit_request_detection_keywords(client):
    """Test that content keywords are detected as explicit content requests."""
    # Create user with minimal profile
    client.post('/api/signup', json={
        'email': 'keywordtest@example.com',
        'password': 'testpass123'
    })
    
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='keywordtest@example.com').first()
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business'
        )
        db.session.add(profile)
        db.session.commit()
    
    keyword_phrases = [
        'write a post about our product',
        'create an email for customers',
        'generate an instagram caption',
        'make a linkedin post'
    ]
    
    for phrase in keyword_phrases:
        response = client.post('/api/chat', json={
            'message': phrase
        })
        
        assert response.status_code == 200
        data = response.get_json()
        # Should offer skip since profile is incomplete
        assert data['action'] == 'profile_prompt_with_skip'


def test_no_skip_offered_without_minimal_data(client):
    """Test that skip is not offered when there's no minimal profile data."""
    # Create user with completely empty profile
    client.post('/api/signup', json={
        'email': 'noskip@example.com',
        'password': 'testpass123'
    })
    
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='noskip@example.com').first()
        # Create empty profile (no business name or industry)
        profile = VoiceProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    
    # Make explicit content request
    response = client.post('/api/chat', json={
        'message': '/post about our services'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should go straight to onboarding without skip option
    assert data['action'] == 'continue'
    assert data['pending_task'] is not None
    assert data['pending_task']['task_type'] == 'onboarding'


def test_complete_profile_skips_skip_prompt(client):
    """Test that complete profiles skip the skip prompt entirely."""
    # Create user with complete profile
    client.post('/api/signup', json={
        'email': 'complete@example.com',
        'password': 'testpass123'
    })
    
    test_app = client.application
    with test_app.app_context():
        user = User.query.filter_by(email='complete@example.com').first()
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Complete Business',
            industry='Technology',
            brand_voice='Professional and friendly',
            target_audience='Tech enthusiasts',
            key_offer='Best tech solutions'
        )
        db.session.add(profile)
        db.session.commit()
    
    # Make explicit content request
    response = client.post('/api/chat', json={
        'message': '/post about innovation'
    })
    
    # Should not get skip prompt (either generates content or missing API key error)
    # Status can be 200 (generated/continue) or 503 (missing API key)
    assert response.status_code in [200, 503]
    data = response.get_json()
    
    # Should not be a skip prompt
    assert data['action'] != 'profile_prompt_with_skip'
    
    # If successful, should be generated or continue (for content-specific questions)
    if response.status_code == 200:
        assert data['action'] in ['generated', 'continue']
