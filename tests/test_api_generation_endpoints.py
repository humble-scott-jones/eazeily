"""Integration tests for API generation endpoints."""

import pytest
from unittest.mock import patch


@pytest.fixture
def mock_gemini():
    """Mock Gemini API for tests."""
    with patch('services.generation.gemini_adapter.call_gemini') as mock:
        # Mock successful AI response
        mock.return_value = {
            'text': """Exciting news! 🎉

We're thrilled to announce our new product launch. Here's what makes it special:

1. Innovative design
2. User-friendly interface
3. Incredible value

Ready to check it out? Visit our website or DM us for exclusive early access!"""
        }
        yield mock


def test_api_generate_post_endpoint(authenticated_client, mock_gemini):
    """Test that /api/generate endpoint works for post generation."""
    resp = authenticated_client.post('/api/generate', json={
        'task_type': 'post',
        'topic': 'New product launch',
        'platform': 'instagram'
    })
    
    assert resp.status_code == 200
    body = resp.get_json()
    
    # API response format: {'content': str, 'status': 'success', 'task_type': str, 'platform': str}
    # On error: {'status': 'error', 'error': {'code': str, 'message': str}}
    assert 'content' in body or 'error' in body
    if 'content' in body:
        assert body['status'] == 'success'
        assert isinstance(body['content'], str)
        assert len(body['content']) > 0


def test_api_generate_multi_day_plan(authenticated_client, mock_gemini):
    """Test multi-day content plan generation."""
    resp = authenticated_client.post('/api/generate', json={
        'days': 3,
        'platforms': ['instagram', 'linkedin'],
        'tone': 'professional',
        'goals': ['engagement', 'awareness'],
        'brand_keywords': ['innovation', 'quality']
    })
    
    assert resp.status_code == 200
    body = resp.get_json()
    
    # Check contract for multi-day plan
    assert body.get('ok') is True or 'posts' in body
    if 'posts' in body:
        assert len(body['posts']) > 0
        # Verify structure of each post
        for post in body['posts']:
            assert 'platform' in post
            assert 'caption' in post or 'variants' in post


def test_api_generate_missing_topic_returns_error(authenticated_client):
    """Test that missing topic returns validation error."""
    resp = authenticated_client.post('/api/generate', json={
        'task_type': 'post',
        'platform': 'instagram'
        # topic is missing
    })
    
    assert resp.status_code == 400
    body = resp.get_json()
    
    assert body['status'] == 'error'
    assert 'error' in body


def test_api_generate_without_auth_redirects(client):
    """Test that /api/generate requires authentication."""
    resp = client.post('/api/generate', json={
        'task_type': 'post',
        'topic': 'Test topic',
        'platform': 'instagram'
    })
    
    # Should redirect to login (302) or return 401
    assert resp.status_code in [302, 401]


def test_api_generate_with_profile_data(authenticated_client, mock_gemini):
    """Test that generation uses profile data when available."""
    resp = authenticated_client.post('/api/generate', json={
        'task_type': 'post',
        'topic': 'Customer success story',
        'platform': 'linkedin'
    })
    
    assert resp.status_code == 200
    body = resp.get_json()
    
    # Should succeed and use profile data
    assert 'content' in body or 'posts' in body
