"""Tests for target audience AI processing feature."""
import pytest
from unittest.mock import patch, MagicMock
from models import User, VoiceProfile, db
from services.profile_expert import process_raw_audience_input


def test_process_raw_audience_with_url_input(authenticated_client):
    """Test that target audience with URL gets processed through AI."""
    # Mock the AI service
    with patch('services.profile_expert.get_generative_model') as mock_model:
        mock_response = MagicMock()
        mock_response.text = "Small business owners aged 30-50 who struggle with social media consistency. They're looking for an easy way to maintain their brand presence without hiring an agency."
        
        mock_gen_model = MagicMock()
        mock_gen_model.generate_content.return_value = mock_response
        mock_model.return_value = mock_gen_model
        
        # Get the user's profile
        from flask_login import current_user
        with authenticated_client.application.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            # Process a URL-based input
            result = process_raw_audience_input(
                "Look on my website https://staging.eazeily.com/ and come up with some options for me",
                profile
            )
            
            assert result['success'] is True
            assert 'Small business owners' in result['audience']
            assert result['original_input'] == "Look on my website https://staging.eazeily.com/ and come up with some options for me"


def test_process_raw_audience_without_ai_when_short(authenticated_client):
    """Test that short, direct target audience input is not processed through AI."""
    # Create a simple profile update with short input
    response = authenticated_client.post('/api/profile', json={
        'target_audience': 'Small business owners'
    })
    
    assert response.status_code == 200
    data = response.json
    assert data['ok'] is True
    
    # Verify the audience was saved as-is
    response = authenticated_client.get('/api/profile')
    data = response.json
    assert data['profile']['target_audience'] == 'Small business owners'


def test_process_raw_audience_with_long_input_triggers_ai(authenticated_client):
    """Test that long target audience input triggers AI processing."""
    long_input = "Look at my website https://example.com and analyze who my target customers are, then come up with a detailed description of my ideal customer persona"
    
    with patch('routes.profile_routes.process_raw_audience_input') as mock_process:
        mock_process.return_value = {
            'success': True,
            'audience': 'Tech-savvy entrepreneurs aged 25-45 who need automated marketing solutions.',
            'original_input': long_input
        }
        
        response = authenticated_client.post('/api/profile', json={
            'target_audience': long_input
        })
        
        assert response.status_code == 200
        # Verify AI processing was called
        mock_process.assert_called_once()


def test_process_raw_audience_fallback_on_ai_error(authenticated_client):
    """Test that target audience falls back to raw input if AI processing fails."""
    long_input = "Look at my website https://example.com and figure out my audience"
    
    with patch('routes.profile_routes.process_raw_audience_input') as mock_process:
        # Simulate AI failure
        mock_process.return_value = {
            'success': False,
            'error': 'AI service unavailable'
        }
        
        response = authenticated_client.post('/api/profile', json={
            'target_audience': long_input
        })
        
        assert response.status_code == 200
        
        # Verify the raw input was saved as fallback
        response = authenticated_client.get('/api/profile')
        data = response.json
        assert data['profile']['target_audience'] == long_input


def test_ai_processing_uses_business_context(authenticated_client):
    """Test that AI processing includes business context in the prompt."""
    with patch('services.profile_expert.get_generative_model') as mock_model:
        mock_response = MagicMock()
        mock_response.text = "Software developers building Python applications"
        
        mock_gen_model = MagicMock()
        mock_gen_model.generate_content.return_value = mock_response
        mock_model.return_value = mock_gen_model
        
        # Update profile with business info first
        authenticated_client.post('/api/profile', json={
            'business_name': 'DevTools Inc',
            'industry': 'Software Development',
            'brand_voice': 'Technical and professional'
        })
        
        # Get the profile
        with authenticated_client.application.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            result = process_raw_audience_input(
                "Check my website and suggest target audience",
                profile
            )
            
            # Verify the prompt was called with generate_content
            assert mock_gen_model.generate_content.called
            call_args = mock_gen_model.generate_content.call_args[0][0]
            
            # Verify business context is in the prompt
            assert 'DevTools Inc' in call_args or 'Test Business' in call_args
            assert 'Software Development' in call_args or 'Technology' in call_args
