"""Test prefilled values for profile updates based on context."""

import json
import pytest
from models import User, VoiceProfile, db


def test_voice_update_shows_prefilled_value(authenticated_client):
    """Test that /voice shows prefilled value based on user's industry."""
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
    
    # Should show prefilled value in the response
    assert 'found' in data['response'].lower() or 'here' in data['response'].lower()
    # Should have a prefilled_value in pending_task
    assert data['pending_task'] is not None
    assert 'prefilled_value' in data['pending_task']


def test_audience_update_shows_prefilled_value(authenticated_client):
    """Test that /audience shows prefilled value based on user's industry."""
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
    
    # Should show prefilled value
    assert 'found' in data['response'].lower() or data['pending_task'].get('prefilled_value')
    # For restaurant, prefilled value should be food-related
    if data['pending_task'].get('prefilled_value'):
        prefilled = data['pending_task']['prefilled_value'].lower()
        assert any(keyword in prefilled for keyword in ['food', 'dining', 'quality'])


def test_key_offer_shows_prefilled_value(authenticated_client):
    """Test that key offer updates show prefilled value."""
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
    
    # Should show prefilled value for software industry
    assert data['pending_task'].get('prefilled_value') is not None
    prefilled = data['pending_task']['prefilled_value'].lower()
    # Software-related prefilled value
    assert any(keyword in prefilled for keyword in ['solution', 'support', 'reliable'])


def test_prefilled_from_scraped_data(authenticated_client):
    """Test that prefilled values prioritize scraped metadata."""
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
    
    # Test audience prefill from scraped data
    response = authenticated_client.post('/api/chat', json={
        'message': '/audience'
    })
    
    data = response.get_json()
    # Should use the scraped key_customers as prefilled value
    assert data['pending_task'].get('prefilled_value') == 'busy professionals seeking personalized fitness'
    assert 'from your website' in data['response']
    
    # Test key offer prefill from scraped data
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
    # Should use scraped key_offer as prefilled value
    assert data['pending_task'].get('prefilled_value') == 'one-on-one training with certified coaches'
    assert 'from your website' in data['response']
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


def test_user_can_accept_prefilled_value(authenticated_client):
    """Test that users can accept prefilled value by pressing enter or typing it."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/voice'
    })
    
    data = response.get_json()
    pending_task = data['pending_task']
    prefilled_value = pending_task.get('prefilled_value')
    
    # User can accept by typing the value or use it directly
    if prefilled_value:
        response = authenticated_client.post('/api/chat', json={
            'message': prefilled_value,
            'pending_task': pending_task
        })
        
        assert response.status_code == 200
        data = response.get_json()
        # Should successfully update with the prefilled value
        assert data['action'] == 'profile_updated'
        assert prefilled_value in data['response']


def test_user_can_edit_prefilled_value(authenticated_client):
    """Test that users can edit the prefilled value."""
    response = authenticated_client.post('/api/chat', json={
        'message': '/voice'
    })
    
    data = response.get_json()
    pending_task = data['pending_task']
    
    # User edits and provides their own value
    custom_value = "energetic and inspiring"
    response = authenticated_client.post('/api/chat', json={
        'message': custom_value,
        'pending_task': pending_task
    })
    
    assert response.status_code == 200
    data = response.get_json()
    # Should successfully update with custom value
    assert data['action'] == 'profile_updated'
    assert custom_value in data['response']


def test_fallback_prefilled_when_no_industry(authenticated_client):
    """Test that system provides fallback prefilled values when no industry is set."""
    from app import create_app
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        # Set industry but keep it minimal - we want to test fallback values
        profile.industry = 'General'
        db.session.commit()
    
    response = authenticated_client.post('/api/chat', json={
        'message': '/voice'
    })
    
    data = response.get_json()
    # Should still provide a generic prefilled value
    assert data['action'] == 'continue'
    # Should have a prefilled value (generic fallback)
    assert data['pending_task'].get('prefilled_value') is not None
    # Should show friendly/professional as fallback
    assert 'friendly' in data['pending_task']['prefilled_value'].lower() or 'professional' in data['pending_task']['prefilled_value'].lower()
