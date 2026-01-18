"""Tests for chat-based onboarding flow with state machine."""
import pytest
from models import User, VoiceProfile, db


def test_dashboard_detects_new_user_with_no_profile(client, tmp_path, monkeypatch):
    """Test that dashboard detects users with no profile as new users."""
    from app import create_app
    
    # Set up test database
    db_file = tmp_path / "test_db.db"
    monkeypatch.setenv('TEST_DB_PATH', str(db_file))
    
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        db.create_all()
        
        # Create user without profile
        user = User(email='newuser@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Login
    with test_app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Access dashboard
        response = test_client.get('/dashboard')
        assert response.status_code == 200
        # Check that is_new_user=true is in the response
        assert b'isNewUser = true' in response.data


def test_dashboard_detects_new_user_with_incomplete_profile(client, tmp_path, monkeypatch):
    """Test that dashboard detects users with incomplete profiles as new users."""
    from app import create_app
    
    # Set up test database
    db_file = tmp_path / "test_db.db"
    monkeypatch.setenv('TEST_DB_PATH', str(db_file))
    
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        db.create_all()
        
        # Create user with incomplete profile (no business_name)
        user = User(email='incomplete@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        profile = VoiceProfile(
            user_id=user.id,
            industry='Technology',
            brand_voice='Friendly'
        )
        # Note: business_name is NOT set
        db.session.add(profile)
        db.session.commit()
        
        user_id = user.id
    
    # Login
    with test_app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Access dashboard
        response = test_client.get('/dashboard')
        assert response.status_code == 200
        # Should be marked as new user since business_name is missing
        assert b'isNewUser = true' in response.data


def test_dashboard_recognizes_existing_user_with_complete_profile(client, tmp_path, monkeypatch):
    """Test that dashboard recognizes users with complete basic profiles."""
    from app import create_app
    
    # Set up test database
    db_file = tmp_path / "test_db.db"
    monkeypatch.setenv('TEST_DB_PATH', str(db_file))
    
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        db.create_all()
        
        # Create user with complete basic profile
        user = User(email='complete@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business',  # Key field that marks as complete
            industry='Technology',
            brand_voice='Friendly'
        )
        db.session.add(profile)
        db.session.commit()
        
        user_id = user.id
    
    # Login
    with test_app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Access dashboard
        response = test_client.get('/dashboard')
        assert response.status_code == 200
        # Should NOT be marked as new user
        assert b'isNewUser = false' in response.data


def test_onboarding_profile_save_api(client, tmp_path, monkeypatch):
    """Test that profile fields can be saved via API during onboarding."""
    from app import create_app
    
    # Set up test database
    db_file = tmp_path / "test_db.db"
    monkeypatch.setenv('TEST_DB_PATH', str(db_file))
    
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        db.create_all()
        
        # Create user without profile
        user = User(email='onboarding@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Login
    with test_app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Save business_name (first onboarding step)
        response = test_client.post('/api/profile',
            json={'business_name': 'My Coffee Shop'},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        
        # Save industry (second onboarding step)
        response = test_client.post('/api/profile',
            json={'industry': 'Restaurant'},
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Save brand_voice (third onboarding step)
        response = test_client.post('/api/profile',
            json={'brand_voice': 'Friendly'},
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Verify all fields were saved
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=user_id).first()
            assert profile is not None
            assert profile.business_name == 'My Coffee Shop'
            assert profile.industry == 'Restaurant'
            assert profile.brand_voice == 'Friendly'


def test_old_onboarding_route_redirects_to_dashboard(client, tmp_path, monkeypatch):
    """Test that /onboarding redirects to dashboard."""
    from app import create_app
    
    # Set up test database
    db_file = tmp_path / "test_db.db"
    monkeypatch.setenv('TEST_DB_PATH', str(db_file))
    
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        db.create_all()
        
        # Create user
        user = User(email='redirect@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Login
    with test_app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = test_client.get('/onboarding', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard' in response.location


def test_wizard_route_redirects_to_dashboard(client, tmp_path, monkeypatch):
    """Test that /wizard redirects to dashboard."""
    from app import create_app
    
    # Set up test database
    db_file = tmp_path / "test_db.db"
    monkeypatch.setenv('TEST_DB_PATH', str(db_file))
    
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        db.create_all()
        
        # Create user
        user = User(email='wizard@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Login
    with test_app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = test_client.get('/wizard', follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard' in response.location
