"""Tests for multi-profile support functionality.

This module tests:
- User.can_create_profile() method
- Profile CRUD API endpoints
- Profile switching commands
- Tier limit enforcement
"""
import pytest
from models import User, VoiceProfile, db


def test_user_can_create_profile_free_tier(client):
    """Test that free tier users can only have 1 profile."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        # Create a free tier user
        user = User(email='free@example.com', subscription_tier='free')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        # User with no profiles can create one
        assert user.can_create_profile() is True
        
        # Create a profile
        profile = VoiceProfile(user_id=user_id, business_name='Test Business', is_default=True)
        db.session.add(profile)
        db.session.commit()
        
        # User with 1 profile cannot create more (free tier limit is 1)
        user = User.query.get(user_id)
        assert user.can_create_profile() is False


def test_user_can_create_profile_pro_tier(client):
    """Test that pro tier users can have up to 3 profiles."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        # Create a pro tier user
        user = User(email='pro@example.com', subscription_tier='pro')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        # User can create first profile
        assert user.can_create_profile() is True
        
        # Create 2 profiles
        for i in range(2):
            profile = VoiceProfile(
                user_id=user_id,
                business_name=f'Business {i+1}',
                is_default=(i == 0)
            )
            db.session.add(profile)
        db.session.commit()
        
        # User can still create one more (limit is 3)
        user = User.query.get(user_id)
        assert user.can_create_profile() is True
        
        # Create third profile
        profile = VoiceProfile(user_id=user_id, business_name='Business 3')
        db.session.add(profile)
        db.session.commit()
        
        # User cannot create more (reached limit)
        user = User.query.get(user_id)
        assert user.can_create_profile() is False


def test_user_can_create_profile_team_tier(client):
    """Test that team tier users can have unlimited profiles."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        # Create a team tier user
        user = User(email='team@example.com', subscription_tier='team')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        # Create 10 profiles
        for i in range(10):
            profile = VoiceProfile(
                user_id=user_id,
                business_name=f'Business {i+1}',
                is_default=(i == 0)
            )
            db.session.add(profile)
        db.session.commit()
        
        # User can still create more (unlimited)
        user = User.query.get(user_id)
        assert user.can_create_profile() is True


def test_user_voice_profile_property_returns_default(client):
    """Test that user.voice_profile property returns the default profile."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        # Create multiple profiles
        profile1 = VoiceProfile(
            user_id=user_id,
            business_name='Business 1',
            profile_name='Profile 1',
            is_default=False
        )
        profile2 = VoiceProfile(
            user_id=user_id,
            business_name='Business 2',
            profile_name='Profile 2',
            is_default=True
        )
        db.session.add_all([profile1, profile2])
        db.session.commit()
        
        # voice_profile property should return the default
        user = User.query.get(user_id)
        assert user.voice_profile is not None
        assert user.voice_profile.id == profile2.id
        assert user.voice_profile.is_default is True


def test_user_voice_profile_property_returns_first_if_no_default(client):
    """Test that user.voice_profile returns first profile if no default is set."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        # Create profiles without default
        profile1 = VoiceProfile(
            user_id=user_id,
            business_name='Business 1',
            is_default=False
        )
        profile2 = VoiceProfile(
            user_id=user_id,
            business_name='Business 2',
            is_default=False
        )
        db.session.add_all([profile1, profile2])
        db.session.commit()
        profile1_id = profile1.id
        
        # voice_profile property should return first profile
        user = User.query.get(user_id)
        assert user.voice_profile is not None
        assert user.voice_profile.id == profile1_id


def test_list_profiles_endpoint(authenticated_client):
    """Test GET /api/profiles returns all user profiles."""
    # The authenticated_client fixture creates a user with one profile
    response = authenticated_client.get('/api/profiles')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert 'profiles' in data
    assert len(data['profiles']) >= 1
    assert data['count'] >= 1
    assert 'tier_limit' in data
    assert 'can_create_more' in data


def test_create_profile_endpoint(authenticated_client):
    """Test POST /api/profiles creates a new profile."""
    from app import create_app
    from models import User, db
    
    # First, upgrade the user to pro tier so they can have multiple profiles
    test_app = create_app()
    with test_app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
    
    response = authenticated_client.post('/api/profiles', json={
        'profile_name': 'Client: Acme Co',
        'business_name': 'Acme Corporation',
        'industry': 'Technology'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['ok'] is True
    assert 'profile' in data
    assert data['profile']['profile_name'] == 'Client: Acme Co'
    assert data['profile']['business_name'] == 'Acme Corporation'


def test_create_profile_enforces_tier_limit(authenticated_client):
    """Test that profile creation enforces tier limits."""
    from app import create_app
    from models import User, VoiceProfile, db
    
    test_app = create_app()
    with test_app.app_context():
        # Get the test user (created by authenticated_client fixture)
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'free'  # Free tier has limit of 1
        db.session.commit()
    
    # Try to create a second profile (should fail for free tier)
    response = authenticated_client.post('/api/profiles', json={
        'profile_name': 'Second Profile',
        'business_name': 'Another Business'
    })
    
    assert response.status_code == 403
    data = response.get_json()
    assert data['ok'] is False
    assert 'limit' in data['error'].lower()


def test_set_default_profile_endpoint(authenticated_client):
    """Test PUT /api/profiles/<id>/default sets a profile as default."""
    from app import create_app
    from models import User, VoiceProfile, db
    
    test_app = create_app()
    with test_app.app_context():
        # Get the test user and make them pro tier
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
    
    # Create a second profile
    response = authenticated_client.post('/api/profiles', json={
        'profile_name': 'Second Profile',
        'business_name': 'Another Business'
    })
    assert response.status_code == 201
    new_profile_id = response.get_json()['profile']['id']
    
    # Set the new profile as default
    response = authenticated_client.put(f'/api/profiles/{new_profile_id}/default')
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] is True
    
    # Verify it's now default
    response = authenticated_client.get('/api/profiles')
    profiles = response.get_json()['profiles']
    new_profile = next(p for p in profiles if p['id'] == new_profile_id)
    assert new_profile['is_default'] is True


def test_delete_profile_endpoint(authenticated_client):
    """Test DELETE /api/profiles/<id> deletes a profile."""
    from app import create_app
    from models import User, db
    
    test_app = create_app()
    with test_app.app_context():
        # Make user pro tier so they can have multiple profiles
        user = User.query.filter_by(email='test@example.com').first()
        user.subscription_tier = 'pro'
        db.session.commit()
    
    # Create a second profile
    response = authenticated_client.post('/api/profiles', json={
        'profile_name': 'Temporary Profile',
        'business_name': 'Temp Business'
    })
    assert response.status_code == 201
    profile_id = response.get_json()['profile']['id']
    
    # Delete the profile
    response = authenticated_client.delete(f'/api/profiles/{profile_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] is True
    
    # Verify it's deleted
    response = authenticated_client.get('/api/profiles')
    profiles = response.get_json()['profiles']
    assert not any(p['id'] == profile_id for p in profiles)


def test_delete_last_profile_fails(authenticated_client):
    """Test that deleting the last profile is prevented."""
    from app import create_app
    from models import VoiceProfile, db
    
    test_app = create_app()
    with test_app.app_context():
        # Get the user's only profile
        profile = VoiceProfile.query.filter_by(business_name='Test Business').first()
        profile_id = profile.id
    
    # Try to delete the only profile
    response = authenticated_client.delete(f'/api/profiles/{profile_id}')
    assert response.status_code == 400
    data = response.get_json()
    assert data['ok'] is False
    assert 'last profile' in data['error'].lower()


def test_get_current_profile_endpoint(authenticated_client):
    """Test GET /api/profiles/current returns the active profile."""
    response = authenticated_client.get('/api/profiles/current')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert 'profile' in data
    assert data['profile']['business_name'] == 'Test Business'
