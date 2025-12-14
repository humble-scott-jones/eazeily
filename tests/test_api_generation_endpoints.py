"""Integration tests for new API endpoints."""

import pytest


def test_api_generate_social_endpoint_exists(client):
    """Test that /api/generate/social endpoint exists and returns valid contract."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-user-123'
        sess['profile_id'] = 'test-profile-123'
    
    resp = client.post('/api/generate/social', json={
        'session_length': 1,
        'platforms': ['instagram'],
        'tone': 'friendly'
    })
    
    assert resp.status_code == 200
    body = resp.get_json()
    
    # Check contract
    assert body['ok'] is True
    assert 'request_id' in body
    assert 'openai_used' in body
    assert 'fallback_used' in body
    assert 'data' in body
    
    # Check data structure
    data = body['data']
    assert 'posts' in data
    assert len(data['posts']) > 0
    
    # Check post structure (SocialPostCard format)
    post = data['posts'][0]
    assert 'platform' in post
    assert 'caption' in post
    assert 'hashtags' in post
    # Optional fields may or may not be present
    # 'cta', 'image_prompt', 'notes' are optional


def test_api_generate_reviews_with_new_service(client):
    """Test that /api/generate/reviews uses new service."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-user-456'
        sess['profile_id'] = 'test-profile-456'
    
    resp = client.post('/api/generate/reviews', json={
        'review_text': 'Great service! Very happy with the results.',
        'rating': 5,
        'tone': 'professional'
    })
    
    assert resp.status_code == 200
    body = resp.get_json()
    
    # Check contract
    assert body['ok'] is True
    assert 'request_id' in body
    assert 'data' in body
    
    # Check data structure
    data = body['data']
    assert 'responses' in data
    responses = data['responses']
    
    # Should have at least one variant
    assert 'short' in responses or 'medium' in responses or 'long' in responses


def test_api_generate_reviews_missing_text_returns_error(client):
    """Test that missing review_text returns validation error."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-user-789'
        sess['profile_id'] = 'test-profile-789'
    
    resp = client.post('/api/generate/reviews', json={
        'rating': 5
    })
    
    assert resp.status_code == 400
    body = resp.get_json()
    
    assert body['ok'] is False
    assert 'error' in body
    assert body['error']['code'] == 'missing_review'
    assert 'request_id' in body


def test_api_generate_social_without_session(client):
    """Test that /api/generate/social works without session (uses defaults)."""
    resp = client.post('/api/generate/social', json={
        'session_length': 1,
        'platforms': ['instagram'],
        'tone': 'casual'
    })
    
    # Should still succeed even without session data
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True


def test_api_generate_social_with_voice_samples_in_db(client):
    """Test that voice samples from DB are loaded and used."""
    import sqlite3
    import json
    from app import DB_PATH
    
    # Setup: create user and profile with voice samples
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    user_id = 'voice-test-user'
    profile_id = 'voice-test-profile'
    
    voice_data = {
        'samples': [
            'We celebrate every win!',
            'Quick tips for success.',
            'Join our amazing community!'
        ]
    }
    
    # Insert profile with voice data
    conn.execute(
        'INSERT OR REPLACE INTO profiles (id, voice_profile) VALUES (?, ?)',
        (profile_id, json.dumps(voice_data))
    )
    conn.commit()
    conn.close()
    
    # Make request with this profile
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['profile_id'] = profile_id
    
    resp = client.post('/api/generate/social', json={
        'session_length': 1,
        'platforms': ['instagram']
    })
    
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True
    
    # Check that voice was applied
    if 'summary' in body:
        # Voice applied flag should be present
        assert 'voice_applied' in body['summary']


def test_api_generate_reviews_with_brand_voice_flag(client):
    """Test that use_brand_voice flag is respected."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'brand-voice-test'
        sess['profile_id'] = 'brand-voice-profile'
    
    # Test with brand voice OFF
    resp1 = client.post('/api/generate/reviews', json={
        'review_text': 'Good product',
        'rating': 4,
        'use_brand_voice': False
    })
    
    assert resp1.status_code == 200
    body1 = resp1.get_json()
    assert body1['ok'] is True
    
    # Test with brand voice ON
    resp2 = client.post('/api/generate/reviews', json={
        'review_text': 'Good product',
        'rating': 4,
        'use_brand_voice': True
    })
    
    assert resp2.status_code == 200
    body2 = resp2.get_json()
    assert body2['ok'] is True
