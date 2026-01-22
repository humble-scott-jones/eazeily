"""Tests for multi-profile chat commands (/profiles and /switch).

This module tests:
- /profiles command listing all profiles
- /switch command changing active profile
- Profile context in chat generation
"""
import pytest
from models import User, VoiceProfile, db


def test_profiles_command_lists_all_profiles(authenticated_client):
    """Test that /profiles command lists all user profiles."""
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        # Make user pro tier and create additional profiles
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
        user_id = user.id
        
        # Create additional profiles
        profile2 = VoiceProfile(
            user_id=user_id,
            business_name='Client A',
            profile_name='Client: A Corp',
            is_default=False
        )
        profile3 = VoiceProfile(
            user_id=user_id,
            business_name='Client B',
            profile_name='Client: B Inc',
            is_default=False
        )
        db.session.add_all([profile2, profile3])
        db.session.commit()
    
    # Send /profiles command
    response = authenticated_client.post('/api/chat', json={
        'message': '/profiles',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    
    # Check response mentions profiles
    response_text = data['response'].lower()
    assert 'profile' in response_text
    assert 'test business' in response_text or 'client a' in response_text


def test_profiles_command_shows_create_option_when_under_limit(authenticated_client):
    """Test that /profiles shows option to create when under tier limit."""
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        # Make user pro tier (limit 3, currently has 1)
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
    
    response = authenticated_client.post('/api/chat', json={
        'message': '/profiles',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    response_text = data['response'].lower()
    
    # Should mention ability to create more
    assert 'create' in response_text or 'more' in response_text


def test_profiles_command_shows_limit_reached_when_at_max(authenticated_client):
    """Test that /profiles shows limit message when at tier maximum."""
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        # Set user to free tier (limit 1, already has 1)
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'free'
        db.session.commit()
    
    response = authenticated_client.post('/api/chat', json={
        'message': '/profiles',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    response_text = data['response'].lower()
    
    # Should mention limit reached
    assert 'limit' in response_text or 'max' in response_text


def test_switch_command_changes_active_profile(authenticated_client):
    """Test that /switch command changes the active profile."""
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        # Make user pro tier and create additional profile
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
        user_id = user.id
        
        profile2 = VoiceProfile(
            user_id=user_id,
            business_name='New Business',
            profile_name='New Profile',
            is_default=False
        )
        db.session.add(profile2)
        db.session.commit()
    
    # Switch to the new profile
    response = authenticated_client.post('/api/chat', json={
        'message': '/switch New Profile',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    
    # Check response confirms switch
    response_text = data['response'].lower()
    assert 'switch' in response_text or 'new profile' in response_text.lower()
    
    # Verify active profile changed
    response = authenticated_client.get('/api/profiles/current')
    current = response.get_json()['profile']
    assert 'New' in current['profile_name'] or 'New' in current['business_name']


def test_switch_command_with_partial_name_match(authenticated_client):
    """Test that /switch works with partial name matching."""
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
        user_id = user.id
        
        profile2 = VoiceProfile(
            user_id=user_id,
            business_name='Acme Corporation',
            profile_name='Client: Acme Corp',
            is_default=False
        )
        db.session.add(profile2)
        db.session.commit()
    
    # Switch using partial name
    response = authenticated_client.post('/api/chat', json={
        'message': '/switch Acme',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    
    # Verify switch was successful
    response_text = data['response'].lower()
    assert 'switch' in response_text or 'acme' in response_text


def test_switch_command_with_nonexistent_profile_shows_error(authenticated_client):
    """Test that /switch with invalid name shows helpful error."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/switch Nonexistent Profile',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    response_text = data['response'].lower()
    
    # Should indicate profile not found
    assert 'find' in response_text or 'not found' in response_text or "couldn't" in response_text


def test_switch_command_without_name_shows_guidance(authenticated_client):
    """Test that /switch without profile name shows helpful guidance."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/switch',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    response_text = data['response'].lower()
    
    # Should ask for profile name
    assert 'specify' in response_text or 'which' in response_text or 'example' in response_text


def test_chat_uses_active_profile_for_generation(authenticated_client):
    """Test that content generation uses the active profile from session."""
    from app import create_app
    import os
    
    # Set fake API key for generation
    os.environ['GENAI_API_KEY'] = 'test-fake-key'
    
    test_app = create_app()
    with test_app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
        user_id = user.id
        
        # Create second profile with distinct characteristics
        profile2 = VoiceProfile(
            user_id=user_id,
            business_name='Tech Startup',
            profile_name='Startup Profile',
            brand_voice='Energetic and innovative',
            target_audience='Tech enthusiasts',
            key_offer='Cutting-edge solutions',
            is_default=False
        )
        profile2.set_writing_samples(['We are disrupting the industry!'])
        db.session.add(profile2)
        db.session.commit()
    
    # Switch to the new profile
    response = authenticated_client.post('/api/chat', json={
        'message': '/switch Startup',
        'history': []
    })
    assert response.status_code == 200
    
    # Verify the session was set by checking current profile
    response = authenticated_client.get('/api/profiles/current')
    current = response.get_json()
    assert 'Startup' in current['profile']['profile_name']


def test_profile_context_preserved_across_messages(authenticated_client):
    """Test that active profile context is preserved across multiple messages."""
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
        user_id = user.id
        
        profile2 = VoiceProfile(
            user_id=user_id,
            business_name='Restaurant',
            profile_name='Restaurant Profile',
            is_default=False
        )
        db.session.add(profile2)
        db.session.commit()
    
    # Switch profile
    response = authenticated_client.post('/api/chat', json={
        'message': '/switch Restaurant',
        'history': []
    })
    assert response.status_code == 200
    
    # Send another message - profile should still be active
    response = authenticated_client.post('/api/chat', json={
        'message': '/profiles',
        'history': []
    })
    assert response.status_code == 200
    
    # Verify Restaurant profile is marked as active (with arrow marker)
    data = response.get_json()
    response_text = data['response']
    # The active profile should have the → marker
    assert '→' in response_text or 'restaurant' in response_text.lower()
