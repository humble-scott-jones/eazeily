"""Test that content generation requires a brand profile."""
import pytest
import json
import os


def test_generation_requires_profile(client, monkeypatch):
    """Test that generation returns error when profile is missing."""
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test@example.com', 'password': 'password123'})
    
    # Try to generate without a profile
    response = client.post('/api/generate', json={
        'topic': 'How to improve productivity',
        'platform': 'linkedin',
        'task_type': 'post'
    })
    
    # Should return error requiring profile
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['code'] == 'profile_required'
    assert 'profile' in data['error']['message'].lower()
    assert data['error'].get('redirect') == '/onboarding'


def test_generation_works_with_profile(client, monkeypatch):
    """Test that generation works when profile exists."""
    from unittest.mock import Mock, patch
    
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test2@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test2@example.com', 'password': 'password123'})
    
    # Create a profile
    profile_response = client.post('/api/profile', json={
        'company': 'Test Company',
        'industry': 'technology',
        'tone': 'professional',
        'brand_keywords': ['innovation', 'quality'],
        'target_audience': 'Tech professionals',
        'brand_voice': 'Thought leader',
        'key_offer': 'Best solutions'
    })
    assert profile_response.status_code == 200
    
    # Mock the voice engine to avoid needing real API key
    with patch('routes.generate_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = 'Generated professional content about productivity'
        
        # Try to generate with a profile
        response = client.post('/api/generate', json={
            'topic': 'How to improve productivity',
            'platform': 'linkedin',
            'task_type': 'post'
        })
    
    # Should succeed
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'content' in data
    assert data['task_type'] == 'post'
    assert data['platform'] == 'linkedin'


def test_profile_required_error_has_redirect(client, monkeypatch):
    """Test that profile_required error includes redirect to onboarding."""
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test3@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test3@example.com', 'password': 'password123'})
    
    # Try to generate without a profile
    response = client.post('/api/generate', json={
        'topic': 'Test',
        'platform': 'instagram',
        'task_type': 'post'
    })
    
    data = json.loads(response.data)
    assert 'redirect' in data['error']
    assert data['error']['redirect'] == '/onboarding'


def test_profile_provides_full_context_to_generation(client, monkeypatch):
    """Test that a complete profile passes all data to VoiceEngine."""
    from unittest.mock import Mock, patch, call
    
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test4@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test4@example.com', 'password': 'password123'})
    
    # Create a comprehensive profile
    profile_data = {
        'company': 'TechCorp',
        'industry': 'technology',
        'tone': 'innovative',
        'brand_keywords': ['AI', 'automation'],
        'niche_keywords': ['machine learning'],
        'customers': ['Enterprise', 'SMB'],
        'target_audience': 'CTOs and Tech Leaders',
        'brand_voice': 'Thought leader in AI',
        'key_offer': 'AI automation solutions',
        'voice_rules': 'No jargon, focus on ROI',
        'writing_samples': ['We help companies scale through automation.']
    }
    client.post('/api/profile', json=profile_data)
    
    # Mock the voice engine
    with patch('routes.generate_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = 'Generated content'
        
        # Generate content
        client.post('/api/generate', json={
            'topic': 'AI trends',
            'platform': 'linkedin',
            'task_type': 'post'
        })
        
        # Verify that generate_expert_content was called
        assert mock_engine.generate_expert_content.called
        
        # Get the call arguments
        call_args = mock_engine.generate_expert_content.call_args
        profile_arg = call_args[0][0]  # First positional argument is the profile
        
        # Verify profile has the data
        assert profile_arg.business_name == 'TechCorp'
        assert profile_arg.industry == 'technology'
        assert profile_arg.brand_voice == 'Thought leader in AI'
        assert profile_arg.target_audience == 'CTOs and Tech Leaders'
        
        # Verify profile methods work
        assert 'AI' in profile_arg.get_brand_keywords()
        assert 'machine learning' in profile_arg.get_niche_keywords()
        assert 'Enterprise' in profile_arg.get_customers()


def test_missing_api_key_returns_503_before_profile_check(client):
    """Test that API key check happens before profile check."""
    # Don't set API key
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test5@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test5@example.com', 'password': 'password123'})
    
    # Try to generate without API key (also no profile, but API key check comes first)
    response = client.post('/api/generate', json={
        'topic': 'Test',
        'platform': 'instagram',
        'task_type': 'post'
    })
    
    # Should return 503 for missing API key, not 400 for missing profile
    assert response.status_code == 503
    data = json.loads(response.data)
    assert data['error']['code'] == 'missing_api_key'
