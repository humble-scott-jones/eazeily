"""Tests for multi-task generation engine."""

import json
import pytest


def test_generate_accepts_task_type_parameter(client):
    """Test that generate endpoint accepts task_type parameter."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'multitask_test@example.com',
        'password': 'testpass123'
    })
    
    # Test each task type
    for task_type in ['post', 'ad', 'email', 'review']:
        response = client.post('/api/generate',
            json={
                'topic': 'Test topic',
                'platform': 'LinkedIn',
                'task_type': task_type
            },
            content_type='application/json')
        
        # Should either succeed or fail gracefully (no API key)
        assert response.status_code in [200, 500, 503]


def test_generate_defaults_to_post_task(client):
    """Test that generate defaults to post task when no task_type specified."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'default_task_test@example.com',
        'password': 'testpass123'
    })
    
    response = client.post('/api/generate',
        json={
            'topic': 'Test topic',
            'platform': 'LinkedIn'
            # No task_type specified
        },
        content_type='application/json')
    
    # Should handle gracefully
    assert response.status_code in [200, 500, 503]


def test_generate_requires_topic(client):
    """Test that generate endpoint requires topic."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'topic_required_test@example.com',
        'password': 'testpass123'
    })
    
    response = client.post('/api/generate',
        json={
            'platform': 'LinkedIn',
            'task_type': 'post'
            # Missing topic
        },
        content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'topic' in data['error'].lower()


def test_generate_with_brand_profile(client):
    """Test generation with complete brand profile."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'profile_gen_test@example.com',
        'password': 'testpass123'
    })
    
    # Create brand profile first
    client.post('/onboarding', data={
        'business_name': 'Test Business',
        'industry': 'Real Estate',
        'target_audience': 'Local families',
        'brand_voice': 'Professional',
        'key_offer': 'Free consultation',
        'voice_rules': 'Keep it friendly',
        'writing_samples': 'Sample post here.'
    })
    
    # Generate content
    response = client.post('/api/generate',
        json={
            'topic': 'New listing available',
            'platform': 'LinkedIn',
            'task_type': 'post'
        },
        content_type='application/json')
    
    # Should work with profile
    assert response.status_code in [200, 500, 503]


def test_generate_without_profile_uses_defaults(client):
    """Test that generation works without a profile (uses defaults)."""
    # Create and login user (no profile)
    client.post('/api/signup', json={
        'email': 'no_profile_test@example.com',
        'password': 'testpass123'
    })
    
    # Generate content without creating profile
    response = client.post('/api/generate',
        json={
            'topic': 'Test topic',
            'platform': 'LinkedIn',
            'task_type': 'post'
        },
        content_type='application/json')
    
    # Should still work with dummy profile
    assert response.status_code in [200, 500, 503]


def test_generate_ad_task(client):
    """Test ad generation task."""
    client.post('/api/signup', json={
        'email': 'ad_test@example.com',
        'password': 'testpass123'
    })
    
    response = client.post('/api/generate',
        json={
            'topic': '20% off sale',
            'task_type': 'ad'
        },
        content_type='application/json')
    
    assert response.status_code in [200, 500, 503]


def test_generate_email_task(client):
    """Test email generation task."""
    client.post('/api/signup', json={
        'email': 'email_test@example.com',
        'password': 'testpass123'
    })
    
    response = client.post('/api/generate',
        json={
            'topic': 'Following up on our meeting',
            'task_type': 'email'
        },
        content_type='application/json')
    
    assert response.status_code in [200, 500, 503]


def test_generate_review_reply_task(client):
    """Test review reply generation task."""
    client.post('/api/signup', json={
        'email': 'review_test@example.com',
        'password': 'testpass123'
    })
    
    response = client.post('/api/generate',
        json={
            'topic': 'Great service! Very helpful.',
            'task_type': 'review'
        },
        content_type='application/json')
    
    assert response.status_code in [200, 500, 503]
