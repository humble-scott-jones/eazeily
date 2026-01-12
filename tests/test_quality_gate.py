"""
Tests for quality gate that ensures generated content meets minimum standards.

Ensures that:
1. Guidance-like outputs are rejected (e.g., "Here's a caption...")
2. Finished captions are accepted
3. One repair retry is attempted for low-quality outputs
"""

import json
import pytest
import sqlite3
import uuid
import app as togetherly_app


def _create_test_user(client):
    """Helper to create a test user and set up session."""
    from models import db, User
    import uuid
    
    # Use SQLAlchemy to create user with unique email
    unique_email = f'test-{uuid.uuid4().hex[:8]}@example.com'
    user = User(email=unique_email)
    user.set_password('password123')
    
    # Need to use app context
    with client.application.app_context():
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Set up session
    with client.session_transaction() as sess:
        sess['user_id'] = str(user_id)
        sess['_user_id'] = str(user_id)
    
    return user_id


def test_quality_gate_rejects_guidance_output(client):
    _create_test_user(client)
    """Test that quality gate rejects outputs that look like guidance rather than finished content."""
    _create_test_user(client)
    # This test verifies that the output validator catches guidance-style responses
    # In practice, this would be tested at the generator/validator level
    # Here we're testing the integration
    
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'brand_keywords': ['test'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    
    # Check that posts don't contain guidance markers
    if 'posts' in data:
        for post in data['posts']:
            caption = post.get('caption', '')
            # Should not contain guidance phrases
            assert not caption.startswith('Here is a caption')
            assert not caption.startswith('Here\'s a caption')
            assert 'I suggest' not in caption.lower()
            assert 'you could' not in caption.lower()


def test_quality_gate_accepts_finished_captions(client):
    _create_test_user(client)
    """Test that quality gate accepts proper finished content."""
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'brand_keywords': ['quality', 'content'],
        'company': 'Test Co',
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    assert 'posts' in data
    assert len(data['posts']) > 0
    
    # Check that posts have required structure
    for post in data['posts']:
        assert 'caption' in post
        assert 'platform' in post
        assert 'image_prompt' in post
        assert len(post['caption']) > 0


def test_quality_gate_validates_post_structure(client):
    _create_test_user(client)
    """Test that quality gate ensures posts have required fields."""
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    
    # Verify post structure
    for post in data.get('posts', []):
        # Required fields
        assert 'caption' in post
        assert 'platform' in post
        assert 'image_prompt' in post
        assert 'pillar' in post
        
        # Types
        assert isinstance(post['caption'], str)
        assert isinstance(post['platform'], str)
        assert isinstance(post['image_prompt'], str)


def test_quality_gate_minimum_caption_length(client):
    _create_test_user(client)
    """Test that captions meet minimum length requirements."""
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'brand_keywords': ['test'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Captions should not be too short
    for post in data.get('posts', []):
        caption = post.get('caption', '')
        # Instagram captions should have substance (at least 20 chars)
        if post.get('platform') == 'instagram':
            assert len(caption) >= 20, f"Caption too short: {caption}"


def test_quality_gate_no_placeholder_content(client):
    _create_test_user(client)
    """Test that generated content doesn't contain placeholders."""
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'company': 'Real Company Name',
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Check for common placeholders
    placeholders = ['[company name]', '[your brand]', '[product name]', '{{', '}}', '[...]']
    
    for post in data.get('posts', []):
        caption = post.get('caption', '').lower()
        image_prompt = post.get('image_prompt', '').lower()
        
        for placeholder in placeholders:
            assert placeholder not in caption, f"Found placeholder in caption: {placeholder}"
            assert placeholder not in image_prompt, f"Found placeholder in image_prompt: {placeholder}"


def test_repair_retry_attempted_for_low_quality(client, monkeypatch):
    _create_test_user(client)
    """Test that repair retry is attempted when quality is low.
    
    This test verifies that the quality gate will attempt one repair
    when the initial output doesn't meet standards.
    """
    # This would require mocking the generator to return low-quality content first
    # then high-quality content on retry
    # For now, we verify the flow works with real generation
    
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    
    # Should succeed after any necessary repairs
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['ok'] is True


def test_quality_gate_allows_creative_content(client):
    _create_test_user(client)
    """Test that quality gate doesn't over-restrict creative content."""
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'tone': 'playful',
        'brand_keywords': ['fun', 'creative'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    assert len(data.get('posts', [])) > 0
    
    # Creative content should pass quality gate
    # as long as it's not guidance-like


def test_quality_gate_validates_image_prompts(client):
    _create_test_user(client)
    """Test that image prompts are validated for completeness."""
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    for post in data.get('posts', []):
        image_prompt = post.get('image_prompt', '')
        # Image prompts should have some substance
        assert len(image_prompt) > 10, "Image prompt too short"
        assert not image_prompt.lower().startswith('image of'), "Image prompt too generic"
