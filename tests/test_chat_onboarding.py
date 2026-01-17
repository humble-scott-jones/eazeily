"""Tests for conversational onboarding flow in /api/chat endpoint."""

import pytest
import json
from unittest.mock import patch, MagicMock


def test_chat_onboarding_incomplete_profile(client):
    """Test that incomplete profile triggers onboarding flow."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'onboarding_test@example.com',
        'password': 'testpass123'
    })
    
    # Send message to chat with incomplete profile
    response = client.post('/api/chat', json={
        'message': 'I want to create a post',
        'history': []
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Should be routed to onboarding
    assert 'response' in data
    # Action should be 'continue' for onboarding flow
    assert data.get('action') in ['continue', 'onboarding']


def test_chat_onboarding_url_detection(client):
    """Test that URL in message triggers scraping during onboarding."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'url_test@example.com',
        'password': 'testpass123'
    })
    
    with patch('services.onboarding_service.scrape_url') as mock_scrape, \
         patch('services.onboarding_service.extract_business_info') as mock_extract:
        
        # Mock successful scraping
        mock_scrape.return_value = "Sample website content"
        mock_extract.return_value = {
            'business_name': 'Test Business',
            'industry': 'Software',
            'key_customers': 'Small businesses',
            'key_offer': 'Free trial',
            'voice_tone_and_style': 'Professional',
            'sample_posts': ['Post 1']
        }
        
        # Send URL in message
        response = client.post('/api/chat', json={
            'message': 'My website is https://example.com',
            'history': []
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should acknowledge the URL and extracted data
        assert 'Test Business' in data['response'] or 'found' in data['response'].lower()
        assert data.get('action') == 'continue'
        
        # Should have pending task for next field
        assert data.get('pending_task') is not None
        assert data['pending_task']['task_type'] == 'onboarding'


def test_chat_onboarding_multi_turn_conversation(client):
    """Test multi-turn conversation for collecting profile fields."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'multiturn_test@example.com',
        'password': 'testpass123'
    })
    
    # First message - start onboarding
    response1 = client.post('/api/chat', json={
        'message': 'I want to create content',
        'history': []
    })
    
    assert response1.status_code == 200
    data1 = response1.get_json()
    
    # Should ask for information
    assert data1.get('action') == 'continue'
    pending_task = data1.get('pending_task')
    assert pending_task is not None
    assert pending_task['task_type'] == 'onboarding'
    
    # Second message - provide business name
    response2 = client.post('/api/chat', json={
        'message': 'My business is called Test Corp',
        'history': [
            {'role': 'user', 'message': 'I want to create content'},
            {'role': 'assistant', 'message': data1['response']}
        ],
        'pending_task': pending_task
    })
    
    assert response2.status_code == 200
    data2 = response2.get_json()
    
    # Should acknowledge and ask for next field
    assert data2.get('action') == 'continue'
    assert data2.get('pending_task') is not None


def test_chat_onboarding_profile_complete_redirect(client):
    """Test that profile completion triggers redirect to dashboard."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'complete_test@example.com',
        'password': 'testpass123'
    })
    
    # Manually fill profile with all required fields except one
    from models import VoiceProfile, db
    from flask_login import current_user
    
    # This requires us to be in the app context with authenticated user
    # For this test, we'll mock a complete profile scenario
    
    with patch('services.onboarding_service.OnboardingService.is_profile_complete') as mock_complete:
        mock_complete.return_value = (True, [])
        
        response = client.post('/api/chat', json={
            'message': 'My last field is complete',
            'history': [],
            'pending_task': {
                'task_type': 'onboarding',
                'collecting_field': 'key_offer'
            }
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should indicate completion and provide redirect
        assert data.get('action') == 'onboarding_complete'
        assert data.get('redirect') == '/dashboard'


def test_chat_onboarding_scraping_failure_fallback(client):
    """Test graceful fallback when URL scraping fails."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'scrape_fail_test@example.com',
        'password': 'testpass123'
    })
    
    with patch('services.onboarding_service.scrape_url') as mock_scrape:
        # Mock scraping failure
        mock_scrape.return_value = None
        
        response = client.post('/api/chat', json={
            'message': 'https://blocked-website.com',
            'history': []
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should acknowledge failure and ask for alternative
        assert 'describe' in data['response'].lower() or "couldn't" in data['response'].lower()
        assert data.get('action') == 'continue'


def test_chat_onboarding_description_processing(client):
    """Test processing of brand description without URL."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'desc_test@example.com',
        'password': 'testpass123'
    })
    
    with patch('services.ai_service.get_generative_model') as mock_get_model:
        # Mock AI model
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            'business_name': 'Cool Coffee Shop',
            'industry': 'Restaurant / Café',
            'target_audience': None,
            'brand_voice': None,
            'key_offer': None
        })
        mock_model.generate_content.return_value = mock_response
        mock_get_model.return_value = mock_model
        
        response = client.post('/api/chat', json={
            'message': 'I run a coffee shop called Cool Coffee Shop',
            'history': []
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should extract info and ask for next field
        assert data.get('action') == 'continue'
        assert data.get('pending_task') is not None


def test_chat_onboarding_error_handling(client):
    """Test error handling in onboarding flow."""
    # Create and login user
    client.post('/api/signup', json={
        'email': 'error_test@example.com',
        'password': 'testpass123'
    })
    
    with patch('services.onboarding_service.OnboardingService.process_description') as mock_process:
        # Mock an exception
        mock_process.side_effect = Exception("Test error")
        
        response = client.post('/api/chat', json={
            'message': 'Some description',
            'history': []
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should handle error gracefully and continue
        assert data.get('action') in ['continue', 'error']
        assert 'response' in data
