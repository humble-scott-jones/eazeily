"""Test that content generation works with progressive profile data."""
import pytest
import json
import os


def test_generation_requires_profile_to_exist(client, monkeypatch):
    """Test that generation requires at least a profile record to exist."""
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test@example.com', 'password': 'password123'})
    
    # Try to generate without ANY profile
    response = client.post('/api/generate', json={
        'topic': 'How to improve productivity',
        'platform': 'linkedin',
        'task_type': 'post'
    })
    
    # Should return error requiring profile creation
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['code'] == 'profile_required'
    assert 'create your brand profile' in data['error']['message'].lower()
    assert data['error'].get('redirect') == '/onboarding'


def test_generation_requires_business_name(client, monkeypatch):
    """Test that generation requires business name at minimum."""
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test2@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test2@example.com', 'password': 'password123'})
    
    # Create profile without business name
    client.post('/api/profile', json={
        'company': '',  # Empty business name
        'industry': '',  # Empty industry
        'tone': 'professional'
    })
    
    # Try to generate
    response = client.post('/api/generate', json={
        'topic': 'Test',
        'platform': 'linkedin',
        'task_type': 'post'
    })
    
    # Should return error about missing required fields
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['code'] == 'incomplete_profile'
    assert 'business name' in data['error']['message'].lower()
    assert 'missing_fields' in data['error']
    assert 'business name' in data['error']['missing_fields']


def test_generation_works_with_minimal_profile(client, monkeypatch):
    """Test that generation works with just business name and industry."""
    from unittest.mock import Mock, patch
    
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test_min@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test_min@example.com', 'password': 'password123'})
    
    # Create minimal profile with just required fields
    profile_response = client.post('/api/profile', json={
        'company': 'Test Company',
        'industry': 'technology'
        # No brand_voice, keywords, etc.
    })
    assert profile_response.status_code == 200
    
    # Mock the voice engine
    with patch('routes.generate_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = 'Generated content with minimal context'
        
        # Try to generate with minimal profile
        response = client.post('/api/generate', json={
            'topic': 'How to improve productivity',
            'platform': 'linkedin',
            'task_type': 'post'
        })
    
    # Should succeed even with minimal profile
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'content' in data


def test_generation_works_with_complete_profile(client, monkeypatch):
    """Test that generation works great with complete profile data."""
    from unittest.mock import Mock, patch
    
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test3@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test3@example.com', 'password': 'password123'})
    
    # Create a complete profile
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


def test_incomplete_profile_error_has_redirect(client, monkeypatch):
    """Test that incomplete_profile error includes redirect to onboarding."""
    # Set API key for test
    monkeypatch.setenv('GENAI_API_KEY', 'test-api-key')
    
    # Sign up and login
    client.post('/api/signup', json={'email': 'test4@example.com', 'password': 'password123'})
    client.post('/api/login', json={'email': 'test4@example.com', 'password': 'password123'})
    
    # Create incomplete profile
    client.post('/api/profile', json={
        'company': '',  # Missing
        'industry': 'technology'
    })
    
    # Try to generate without complete profile
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
