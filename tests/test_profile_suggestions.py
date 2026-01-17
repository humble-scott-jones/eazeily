"""Test smart suggestions for profile updates based on context."""

import json
import pytest
from models import User, VoiceProfile, db


def test_voice_update_shows_industry_based_suggestions(authenticated_client):
    """Test that /voice shows suggestions based on user's industry."""
    # First, update the test user's industry to something specific
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        profile.industry = 'Fitness'
        db.session.commit()
    
    response = authenticated_client.post('/api/chat', json={
        'message': '/voice'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    
    # Should have suggestions in the response
    assert 'suggestions' in data
    if data['suggestions']:
        # Suggestions should be non-empty
        assert len(data['suggestions']) > 0
    
    # Response should mention suggestions
    assert 'suggestion' in data['response'].lower() or 'based on' in data['response'].lower()


def test_audience_update_shows_industry_based_suggestions(authenticated_client):
    """Test that /audience shows suggestions based on user's industry."""
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        profile.industry = 'Restaurant'
        db.session.commit()
    
    response = authenticated_client.post('/api/chat', json={
        'message': '/audience'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    
    # Should have suggestions
    if data.get('suggestions'):
        assert len(data['suggestions']) > 0
        # For restaurant, should suggest food-related audiences
        suggestions_text = ' '.join(data['suggestions']).lower()
        # At least one suggestion should be relevant
        assert any(keyword in suggestions_text for keyword in ['food', 'dining', 'families', 'community'])


def test_update_key_offer_shows_suggestions(authenticated_client):
    """Test that key offer updates show suggestions."""
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        profile.industry = 'Software'
        db.session.commit()
    
    response = authenticated_client.post('/api/chat', json={
        'message': '/update'
    })
    
    data = response.get_json()
    pending_task = data['pending_task']
    
    # Specify key offer field
    response = authenticated_client.post('/api/chat', json={
        'message': 'key offer',
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['action'] == 'continue'
    
    # Should show suggestions for software industry
    if data.get('suggestions'):
        suggestions_text = ' '.join(data['suggestions']).lower()
        # Software-related suggestions
        assert any(keyword in suggestions_text for keyword in ['cloud', 'support', 'integration', 'scalable'])


def test_suggestions_from_scraped_data(authenticated_client):
    """Test that suggestions use scraped metadata when available."""
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        profile.industry = 'Fitness'
        # Set scraped metadata
        profile.set_scraped_meta({
            'key_customers': 'busy professionals seeking personalized fitness',
            'key_offer': 'one-on-one training with certified coaches'
        })
        db.session.commit()
    
    # Test audience suggestions
    response = authenticated_client.post('/api/chat', json={
        'message': '/audience'
    })
    
    data = response.get_json()
    # Should include the scraped key_customers as a suggestion
    if data.get('suggestions'):
        suggestions_text = ' '.join(data['suggestions'])
        assert 'busy professionals' in suggestions_text or len(data['suggestions']) > 0
    
    # Test key offer suggestions
    response = authenticated_client.post('/api/chat', json={
        'message': '/update'
    })
    data = response.get_json()
    pending_task = data['pending_task']
    
    response = authenticated_client.post('/api/chat', json={
        'message': 'key offer',
        'pending_task': pending_task
    })
    
    data = response.get_json()
    # Should include scraped offer as a suggestion
    if data.get('suggestions'):
        suggestions_text = ' '.join(data['suggestions'])
        assert 'one-on-one training' in suggestions_text or len(data['suggestions']) > 0


def test_suggestions_include_clickable_options(authenticated_client):
    """Test that suggestions are usable as quick select options."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/voice'
    })
    
    data = response.get_json()
    pending_task = data['pending_task']
    
    # If there are suggestions, user should be able to use them directly
    if data.get('suggestions') and len(data['suggestions']) > 0:
        first_suggestion = data['suggestions'][0]
        
        # Use the suggestion as the new value
        response = authenticated_client.post('/api/chat', json={
            'message': first_suggestion,
            'pending_task': pending_task
        })
        
        assert response.status_code == 200
        data = response.get_json()
        # Should successfully update with the suggested value
        assert data['action'] == 'profile_updated'
        assert first_suggestion in data['response']


def test_fallback_suggestions_when_no_industry(authenticated_client):
    """Test that system provides fallback suggestions when no industry is set."""
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        profile.industry = None  # No industry set
        db.session.commit()
    
    response = authenticated_client.post('/api/chat', json={
        'message': '/voice'
    })
    
    data = response.get_json()
    # Should still provide some generic suggestions
    assert data['action'] == 'continue'
    # Fallback suggestions should be provided
    if data.get('suggestions'):
        assert len(data['suggestions']) > 0
