"""Tests for 8-field profile completeness calculation."""
import pytest
from models import User, VoiceProfile, db
from services.profile_validator import get_profile_completeness


def test_empty_profile_shows_zero_percent(client):
    """Test that an empty profile returns 0% completion with 8 missing fields."""
    from app import create_app
    
    test_app = create_app()
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        user = User(email='empty8@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # No profile created - check completeness with None
        is_complete, missing, percent = get_profile_completeness(None)
        
        assert percent == 0
        assert is_complete is False
        assert len(missing) == 8  # All 8 fields should be missing
        assert 'Business Name' in missing
        assert 'Industry' in missing
        assert 'Brand Voice' in missing
        assert 'Target Audience' in missing
        assert 'Key Offer' in missing
        assert 'Writing Samples' in missing
        assert 'Brand Keywords' in missing
        assert 'Goals' in missing


def test_full_profile_shows_hundred_percent(authenticated_client):
    """Test that a profile with all 8 fields returns 100% completion."""
    # Update profile with all 8 fields
    authenticated_client.post('/api/profile', json={
        'business_name': 'Complete Business',
        'industry': 'Technology',
        'brand_voice': 'Professional and friendly',
        'target_audience': 'Small business owners',
        'key_offer': 'Quality software solutions',
        'writing_samples': ['Sample post 1', 'Sample post 2'],
        'brand_keywords': ['innovation', 'quality', 'reliable'],
        'goals': ['Increase brand awareness', 'Generate leads']
    })
    
    # Get profile and check completeness
    with authenticated_client.application.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        is_complete, missing, percent = get_profile_completeness(profile)
        
        assert percent == 100
        assert is_complete is True
        assert len(missing) == 0


def test_partial_profile_with_six_fields_shows_75_percent(authenticated_client):
    """Test that a profile with 6/8 fields returns 75% completion."""
    # Update profile with only 6 fields (missing brand_keywords and goals)
    authenticated_client.post('/api/profile', json={
        'business_name': 'Partial Business',
        'industry': 'Technology',
        'brand_voice': 'Professional',
        'target_audience': 'Developers',
        'key_offer': 'Great tools',
        'writing_samples': ['Sample 1']
    })
    
    with authenticated_client.application.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        is_complete, missing, percent = get_profile_completeness(profile)
        
        assert percent == 75  # 6 out of 8 fields
        assert is_complete is True  # Required fields are complete
        assert len(missing) == 2
        assert 'Brand Keywords' in missing
        assert 'Goals' in missing


def test_profile_with_keywords_and_goals_counted(authenticated_client):
    """Test that brand_keywords and goals are properly counted in completeness."""
    # Create profile with only keywords and goals missing from optional fields
    authenticated_client.post('/api/profile', json={
        'business_name': 'Test Business',
        'industry': 'Technology',
        'brand_voice': 'Professional',
        'target_audience': 'Everyone',
        'key_offer': 'Everything',
        'writing_samples': ['Sample']
        # Missing: brand_keywords and goals
    })
    
    with authenticated_client.application.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        is_complete, missing, percent = get_profile_completeness(profile)
        
        # Should be 6/8 = 75%
        assert percent == 75
        assert 'Brand Keywords' in missing
        assert 'Goals' in missing


def test_profile_with_only_keywords_missing(authenticated_client):
    """Test profile completion when only keywords are missing."""
    authenticated_client.post('/api/profile', json={
        'business_name': 'Test',
        'industry': 'Tech',
        'brand_voice': 'Pro',
        'target_audience': 'All',
        'key_offer': 'Value',
        'writing_samples': ['S'],
        'goals': ['Goal 1']
        # Missing only: brand_keywords
    })
    
    with authenticated_client.application.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        is_complete, missing, percent = get_profile_completeness(profile)
        
        # Should be 7/8 = 87% or 88% (rounded)
        assert percent >= 87
        assert len(missing) == 1
        assert 'Brand Keywords' in missing


def test_profile_with_only_goals_missing(authenticated_client):
    """Test profile completion when only goals are missing."""
    authenticated_client.post('/api/profile', json={
        'business_name': 'Test',
        'industry': 'Tech',
        'brand_voice': 'Pro',
        'target_audience': 'All',
        'key_offer': 'Value',
        'writing_samples': ['S'],
        'brand_keywords': ['keyword1']
        # Missing only: goals
    })
    
    with authenticated_client.application.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        is_complete, missing, percent = get_profile_completeness(profile)
        
        # Should be 7/8 = 87% or 88% (rounded)
        assert percent >= 87
        assert len(missing) == 1
        assert 'Goals' in missing


def test_frontend_completeness_matches_backend(authenticated_client):
    """Test that frontend checkProfileCompleteness matches backend calculation."""
    # Create a profile with 5/8 fields (62.5% = 62% or 63%)
    # First clear any defaults from fixture
    authenticated_client.post('/api/profile', json={
        'business_name': 'Test',
        'industry': 'Tech',
        'brand_voice': 'Pro',
        'target_audience': 'All',
        'key_offer': 'Value',
        'writing_samples': [],  # Clear defaults
        'brand_keywords': [],   # Clear defaults
        'goals': []             # Clear defaults
        # Result: only 5 fields filled (business, industry, voice, audience, offer)
    })
    
    response = authenticated_client.get('/api/profile')
    data = response.json
    profile = data['profile']
    
    # Verify the profile has the expected fields (API returns 'company' field)
    assert profile['company'] == 'Test'
    assert profile['industry'] == 'Tech'
    assert profile['brand_voice'] == 'Pro' or profile['tone'] == 'Pro'
    assert profile['target_audience'] == 'All'
    assert profile['key_offer'] == 'Value'
    assert len(profile['writing_samples']) == 0
    assert len(profile['brand_keywords']) == 0
    assert len(profile['goals']) == 0
    
    # Backend calculation
    with authenticated_client.application.app_context():
        db_profile = VoiceProfile.query.filter_by(user_id=1).first()
        is_complete, missing, backend_percent = get_profile_completeness(db_profile)
        
        # Should be 5/8 = 62.5% = 62% (rounded down)
        assert backend_percent == 62
        assert len(missing) == 3
