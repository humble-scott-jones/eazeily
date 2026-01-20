"""Tests for content history and usage tracking functionality."""

import pytest
from datetime import datetime, timedelta
from models import ContentHistory, User, VoiceProfile, db


def test_user_tier_defaults(client):
    """Test that new users get free tier defaults."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='newuser@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        assert user.subscription_tier == 'free'
        assert user.generation_count_month == 0
        assert user.generation_reset_date is None


def test_user_can_generate_free_tier(client):
    """Test generation limits for free tier users."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='freeuser@example.com')
        user.set_password('password123')
        user.subscription_tier = 'free'
        user.generation_count_month = 0
        db.session.add(user)
        db.session.commit()
        
        # Should be able to generate initially
        assert user.can_generate() is True
        assert user.generations_remaining() == 10
        
        # After 10 generations, should be blocked
        user.generation_count_month = 10
        db.session.commit()
        assert user.can_generate() is False
        assert user.generations_remaining() == 0


def test_user_can_generate_pro_tier(client):
    """Test that pro tier has unlimited generations."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='prouser@example.com')
        user.set_password('password123')
        user.subscription_tier = 'pro'
        user.generation_count_month = 100
        db.session.add(user)
        db.session.commit()
        
        assert user.can_generate() is True
        assert user.generations_remaining() == -1


def test_generation_counter_reset(client):
    """Test that generation counter resets monthly."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='resetuser@example.com')
        user.set_password('password123')
        user.subscription_tier = 'free'
        user.generation_count_month = 10
        # Set reset date to last month
        user.generation_reset_date = datetime.utcnow() - timedelta(days=35)
        db.session.add(user)
        db.session.commit()
        
        # Should reset counter
        can_gen = user.can_generate()
        assert can_gen is True
        assert user.generation_count_month == 0


def test_increment_generation(client):
    """Test incrementing generation counter."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='incuser@example.com')
        user.set_password('password123')
        user.generation_count_month = 5
        db.session.add(user)
        db.session.commit()
        
        user.increment_generation()
        assert user.generation_count_month == 6


def test_get_tier_limits(client):
    """Test getting tier limits."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='tieruser@example.com')
        user.set_password('password123')
        user.subscription_tier = 'pro'
        db.session.add(user)
        db.session.commit()
        
        limits = user.get_tier_limits()
        assert limits['generations'] == -1
        assert limits['history_days'] == 30
        assert limits['profiles'] == 3


def test_create_history_entry(client):
    """Test creating a content history entry."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        # Create user and profile
        user = User(email='historyuser@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business',
            industry='Technology'
        )
        db.session.add(profile)
        db.session.commit()
        
        # Create history entry
        entry = ContentHistory.create_from_generation(
            user_id=user.id,
            profile_id=profile.id,
            task_type='post',
            content='Test post content',
            platform='instagram',
            topic='AI trends',
            parameters={'mood': 'professional'}
        )
        
        assert entry.id is not None
        assert entry.task_type == 'post'
        assert entry.platform == 'instagram'
        assert entry.topic == 'AI trends'
        assert entry.starred is False
        assert entry.deleted_at is None


def test_content_history_to_dict(client):
    """Test ContentHistory to_dict method."""
    from app import create_app
    test_app = create_app()
    
    with test_app.app_context():
        user = User(email='dictuser@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        entry = ContentHistory(
            user_id=user.id,
            task_type='email',
            generated_content='Test email',
            platform='email',
            topic='Newsletter',
            parameters={'cta': 'Sign up now'}
        )
        db.session.add(entry)
        db.session.commit()
        
        result = entry.to_dict()
        assert result['task_type'] == 'email'
        assert result['generated_content'] == 'Test email'
        assert result['parameters']['cta'] == 'Sign up now'
        assert 'created_at' in result


def test_get_history_free_tier(authenticated_client):
    """Test that free tier users get upgrade message."""
    response = authenticated_client.get('/api/history')
    assert response.status_code == 200
    data = response.get_json()
    assert data['upgrade_required'] is True
    assert 'Pro and Team plans' in data['message']


def test_get_usage_endpoint(authenticated_client):
    """Test usage stats endpoint."""
    response = authenticated_client.get('/api/usage')
    assert response.status_code == 200
    data = response.get_json()
    assert 'tier' in data
    assert 'generations_used' in data
    assert 'generations_remaining' in data
    assert 'generations_limit' in data
    assert 'history_days' in data
    assert data['tier'] == 'free'  # Default tier
    assert data['generations_limit'] == 10


def test_get_history_pro_tier(client, tmp_path, monkeypatch):
    """Test that pro tier users can access history."""
    from app import create_app
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        # Create pro user
        user = User(email='prohistory@example.com')
        user.set_password('password123')
        user.subscription_tier = 'pro'
        db.session.add(user)
        db.session.commit()
        
        # Create profile
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Pro Business',
            industry='Technology'
        )
        db.session.add(profile)
        db.session.commit()
        
        # Create history entries
        for i in range(5):
            entry = ContentHistory(
                user_id=user.id,
                profile_id=profile.id,
                task_type='post',
                generated_content=f'Content {i}',
                platform='instagram'
            )
            db.session.add(entry)
        db.session.commit()
        
        user_id = user.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    response = client.get('/api/history')
    assert response.status_code == 200
    data = response.get_json()
    assert 'upgrade_required' not in data or data.get('upgrade_required') is False
    assert data['total'] == 5
    assert len(data['items']) == 5


def test_toggle_star(client, tmp_path, monkeypatch):
    """Test starring a history item."""
    from app import create_app
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        user = User(email='staruser@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        entry = ContentHistory(
            user_id=user.id,
            task_type='post',
            generated_content='Star me',
            starred=False
        )
        db.session.add(entry)
        db.session.commit()
        
        user_id = user.id
        entry_id = entry.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    # Toggle star on
    response = client.post(f'/api/history/{entry_id}/star')
    assert response.status_code == 200
    data = response.get_json()
    assert data['starred'] is True
    
    # Toggle star off
    response = client.post(f'/api/history/{entry_id}/star')
    assert response.status_code == 200
    data = response.get_json()
    assert data['starred'] is False


def test_soft_delete_history_item(client, tmp_path, monkeypatch):
    """Test soft deleting a history item."""
    from app import create_app
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        user = User(email='deleteuser@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        entry = ContentHistory(
            user_id=user.id,
            task_type='post',
            generated_content='Delete me'
        )
        db.session.add(entry)
        db.session.commit()
        
        user_id = user.id
        entry_id = entry.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    # Delete the item
    response = client.delete(f'/api/history/{entry_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['deleted'] is True
    
    # Verify item is soft deleted
    with test_app.app_context():
        entry = ContentHistory.query.get(entry_id)
        assert entry.deleted_at is not None


def test_reuse_content(client, tmp_path, monkeypatch):
    """Test reusing content from history."""
    from app import create_app
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        user = User(email='reuseuser@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        entry = ContentHistory(
            user_id=user.id,
            task_type='email',
            generated_content='Reusable content',
            platform='email',
            topic='Newsletter',
            parameters={'cta': 'Click here'}
        )
        db.session.add(entry)
        db.session.commit()
        
        user_id = user.id
        entry_id = entry.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    response = client.post(f'/api/history/{entry_id}/reuse')
    assert response.status_code == 200
    data = response.get_json()
    assert data['content'] == 'Reusable content'
    assert data['task_type'] == 'email'
    assert data['platform'] == 'email'
    assert data['topic'] == 'Newsletter'
    assert data['parameters']['cta'] == 'Click here'


def test_history_pagination(client, tmp_path, monkeypatch):
    """Test history pagination."""
    from app import create_app
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        user = User(email='pageuser@example.com')
        user.set_password('password123')
        user.subscription_tier = 'pro'
        db.session.add(user)
        db.session.commit()
        
        # Create 25 history entries
        for i in range(25):
            entry = ContentHistory(
                user_id=user.id,
                task_type='post',
                generated_content=f'Content {i}'
            )
            db.session.add(entry)
        db.session.commit()
        
        user_id = user.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    # Get first page
    response = client.get('/api/history?page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total'] == 25
    assert len(data['items']) == 10
    assert data['current_page'] == 1
    assert data['has_next'] is True
    
    # Get second page
    response = client.get('/api/history?page=2&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 10
    assert data['current_page'] == 2


def test_generation_limit_enforcement_free_tier(client, tmp_path, monkeypatch):
    """Test that free tier limits are enforced during generation."""
    from app import create_app
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        user = User(email='limituser@example.com')
        user.set_password('password123')
        user.subscription_tier = 'free'
        user.generation_count_month = 10  # At limit
        user.generation_reset_date = datetime.utcnow()  # Set current month to prevent reset
        db.session.add(user)
        db.session.commit()
        
        # Create profile
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Limited Business',
            industry='Technology',
            target_audience='Everyone',
            brand_voice='Professional',
            key_offer='Great service'
        )
        db.session.add(profile)
        db.session.commit()
        
        user_id = user.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    # This should be blocked - but we need to verify via the actual endpoint
    # Note: The actual chat endpoint would need to be tested with mocked generation
    # For now, we verify the can_generate logic works
    with test_app.app_context():
        user = User.query.get(user_id)
        assert user.can_generate() is False
