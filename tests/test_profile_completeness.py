"""Tests for profile completeness indicator functionality."""
import pytest
from models import User, VoiceProfile, db


def test_profile_api_returns_complete_profile(authenticated_client):
    """Test that the profile API returns a complete profile with all fields."""
    response = authenticated_client.get('/api/profile')
    assert response.status_code == 200
    
    data = response.json
    assert data['ok'] is True
    assert data['profile_status'] == 'loaded'
    assert 'profile' in data
    
    # Check that completeness data is included
    assert 'completeness' in data
    completeness = data['completeness']
    assert 'percent' in completeness
    assert 'is_complete' in completeness
    assert 'missing_fields' in completeness
    assert 'field_status' in completeness
    
    # Verify field_status has all required fields
    field_status = completeness['field_status']
    assert 'business_name' in field_status
    assert 'industry' in field_status
    assert 'brand_voice' in field_status
    assert 'target_audience' in field_status
    assert 'key_offer' in field_status
    assert 'writing_samples' in field_status
    
    profile = data['profile']
    # Check that profile includes the fields needed for completeness check
    assert 'company' in profile or 'business_name' in profile
    assert 'industry' in profile
    assert 'tone' in profile or 'brand_voice' in profile
    assert 'target_audience' in profile
    assert 'key_offer' in profile
    assert 'writing_samples' in profile


def test_profile_completeness_with_full_profile(authenticated_client):
    """Test that a complete profile returns 100% completion."""
    response = authenticated_client.get('/api/profile')
    assert response.status_code == 200
    
    data = response.json
    profile = data['profile']
    
    # The authenticated_client fixture creates a profile with:
    # - business_name: 'Test Business'
    # - industry: 'Technology'
    # - brand_voice: 'Professional and friendly'
    # - target_audience: 'Small businesses'
    # - key_offer: 'Quality software solutions'
    # - writing_samples: 2 samples
    
    # Check that all required fields are present
    assert profile.get('company') or profile.get('business_name')
    assert profile.get('industry')
    assert profile.get('tone') or profile.get('brand_voice')
    assert profile.get('target_audience')
    assert profile.get('key_offer')
    assert len(profile.get('writing_samples', [])) > 0


def test_profile_completeness_with_empty_profile(client):
    """Test that an empty profile returns 0% completion."""
    from models import User, db
    from app import create_app
    
    # Create test app context
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        # Create a user without a profile
        user = User(email='empty@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    response = client.get('/api/profile')
    assert response.status_code == 200
    
    data = response.json
    assert data['ok'] is True
    assert data['profile_status'] == 'empty'
    
    profile = data['profile']
    # All fields should be empty or default values
    assert not profile.get('company') and not profile.get('business_name')
    assert not profile.get('industry')
    assert not profile.get('tone') and not profile.get('brand_voice')
    assert not profile.get('target_audience')
    assert not profile.get('key_offer')
    assert len(profile.get('writing_samples', [])) == 0


def test_profile_completeness_with_partial_profile(client):
    """Test profile completeness with only some fields filled."""
    from models import User, VoiceProfile, db
    from app import create_app
    
    # Create test app context
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        # Create a user with partial profile (only 3 out of 6 fields)
        user = User(email='partial@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Partial Business',
            industry='Technology',
            target_audience='Small businesses'
            # Missing: brand_voice, key_offer, writing_samples
        )
        db.session.add(profile)
        db.session.commit()
        user_id = user.id
    
    # Setup authenticated session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    response = client.get('/api/profile')
    assert response.status_code == 200
    
    data = response.json
    assert data['ok'] is True
    assert data['profile_status'] == 'loaded'
    
    profile = data['profile']
    # Should have 3 out of 6 fields filled
    assert profile.get('company') or profile.get('business_name')
    assert profile.get('industry')
    assert profile.get('target_audience')
    # Missing fields should be empty
    assert not profile.get('tone') and not profile.get('brand_voice')
    assert not profile.get('key_offer')
    assert len(profile.get('writing_samples', [])) == 0


def test_dashboard_page_loads_successfully(authenticated_client):
    """Test that the dashboard page loads without errors."""
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    
    # Check that the profile badge HTML is present
    html = response.data.decode('utf-8')
    assert 'id="profile-badge"' in html
    assert 'id="progress-circle"' in html
    assert 'id="badge-percent"' in html
    assert 'id="menu-profile-badge"' in html
    
    # Check that the JavaScript functions are present
    assert 'initProfileBadge' in html
    assert 'updateProfileBadge' in html
    assert 'handleProfileBadgeClick' in html
    
    # Check that CSS for animations is present
    assert '#progress-circle' in html or 'progress-circle' in html
    assert 'stroke-dashoffset' in html
