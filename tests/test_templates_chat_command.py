"""Integration tests for /templates chat command."""

import pytest
import json
from unittest.mock import patch, MagicMock


def signup_and_login(client, email='test@example.com', password='testpass123'):
    """Helper to signup and login a user."""
    client.post('/api/signup', json={'email': email, 'password': password})
    client.post('/api/login', json={'email': email, 'password': password})


def create_complete_profile(client):
    """Helper to create a complete profile for testing."""
    from models import VoiceProfile, User, db
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        if user:
            profile = VoiceProfile(
                user_id=user.id,
                business_name='Test Restaurant',
                industry='restaurant',
                target_audience='Food lovers and families',
                brand_voice='Warm and inviting',
                key_offer='Fresh homemade pasta daily'
            )
            profile.set_writing_samples(['Check out our new summer menu!', 'Join us for happy hour!'])
            db.session.add(profile)
            db.session.commit()


class TestTemplatesChatCommand:
    """Test suite for /templates chat command."""
    
    def test_templates_command_requires_auth(self, client):
        """Test that /templates command requires authentication."""
        response = client.post('/api/chat', json={
            'message': '/templates'
        })
        assert response.status_code == 401
    
    def test_templates_command_lists_templates(self, client, monkeypatch):
        """Test that /templates command lists available templates."""
        signup_and_login(client)
        create_complete_profile(client)
        
        response = client.post('/api/chat', json={
            'message': '/templates'
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['action'] == 'continue'
        assert 'response' in data
        
        # Should show template list
        response_text = data['response']
        assert 'Content Templates' in response_text
        assert '1.' in response_text  # Numbered list
        assert 'Preview:' in response_text
    
    def test_templates_command_includes_suggestions(self, client):
        """Test that /templates command includes suggestions."""
        signup_and_login(client)
        create_complete_profile(client)
        
        response = client.post('/api/chat', json={
            'message': '/templates'
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'suggestions' in data
        assert isinstance(data['suggestions'], list)
    
    def test_templates_command_with_incomplete_profile(self, client):
        """Test /templates with incomplete profile routes to onboarding."""
        signup_and_login(client)
        # Don't create profile - should route to onboarding
        
        response = client.post('/api/chat', json={
            'message': '/templates'
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should ask for profile info first
        assert 'action' in data
    
    def test_template_selection_by_number(self, client, monkeypatch):
        """Test selecting a template by number."""
        # Mock the generation to avoid API calls
        monkeypatch.setenv('GENAI_API_KEY', 'test-key')
        
        with patch('services.voice_engine.VoiceEngine.generate') as mock_generate:
            mock_generate.return_value = {
                'content': 'Test generated content',
                'source': 'gemini'
            }
            
            signup_and_login(client)
            create_complete_profile(client)
            
            # First, get the templates list
            response1 = client.post('/api/chat', json={
                'message': '/templates'
            })
            assert response1.status_code == 200
            
            data1 = json.loads(response1.data)
            assert 'pending_task' in data1
            pending_task = data1['pending_task']
            
            # Now select template #1
            response2 = client.post('/api/chat', json={
                'message': '1',
                'pending_task': pending_task
            })
            assert response2.status_code == 200
            
            data2 = json.loads(response2.data)
            # Should generate content
            assert 'content' in data2 or data2['action'] == 'generated'
    
    def test_template_selection_use_template_format(self, client, monkeypatch):
        """Test selecting a template with 'use template X' format."""
        monkeypatch.setenv('GENAI_API_KEY', 'test-key')
        
        with patch('services.voice_engine.VoiceEngine.generate') as mock_generate:
            mock_generate.return_value = {
                'content': 'Test generated content',
                'source': 'gemini'
            }
            
            signup_and_login(client)
            create_complete_profile(client)
            
            # Get templates list
            response1 = client.post('/api/chat', json={
                'message': '/templates'
            })
            data1 = json.loads(response1.data)
            pending_task = data1['pending_task']
            
            # Select with 'use template 2' format
            response2 = client.post('/api/chat', json={
                'message': 'use template 2',
                'pending_task': pending_task
            })
            assert response2.status_code == 200
            
            data2 = json.loads(response2.data)
            # Should generate content
            assert 'content' in data2 or data2['action'] == 'generated'
    
    def test_template_selection_invalid_number(self, client):
        """Test selecting a template with invalid number."""
        signup_and_login(client)
        create_complete_profile(client)
        
        # Get templates list
        response1 = client.post('/api/chat', json={
            'message': '/templates'
        })
        data1 = json.loads(response1.data)
        pending_task = data1['pending_task']
        
        # Try to select out of range
        response2 = client.post('/api/chat', json={
            'message': '999',
            'pending_task': pending_task
        })
        assert response2.status_code == 200
        
        data2 = json.loads(response2.data)
        # Should ask to choose valid number
        assert 'response' in data2
        assert 'between' in data2['response'].lower()
    
    def test_template_selection_non_numeric(self, client):
        """Test selecting a template with non-numeric input."""
        signup_and_login(client)
        create_complete_profile(client)
        
        # Get templates list
        response1 = client.post('/api/chat', json={
            'message': '/templates'
        })
        data1 = json.loads(response1.data)
        pending_task = data1['pending_task']
        
        # Try non-numeric input
        response2 = client.post('/api/chat', json={
            'message': 'random text',
            'pending_task': pending_task
        })
        assert response2.status_code == 200
        
        data2 = json.loads(response2.data)
        # Should ask for valid input
        assert 'response' in data2
    
    def test_templates_show_industry_relevant(self, client):
        """Test that templates show industry-relevant options."""
        signup_and_login(client)
        create_complete_profile(client)  # Restaurant industry
        
        response = client.post('/api/chat', json={
            'message': '/templates'
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        response_text = data['response']
        
        # Should include restaurant-specific templates
        # Check for some restaurant template names
        assert 'Daily Special' in response_text or 'Weekend Brunch' in response_text or 'Menu' in response_text
    
    def test_template_pending_task_structure(self, client):
        """Test that /templates creates correct pending_task structure."""
        signup_and_login(client)
        create_complete_profile(client)
        
        response = client.post('/api/chat', json={
            'message': '/templates'
        })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'pending_task' in data
        
        pending_task = data['pending_task']
        assert pending_task['task_type'] == 'templates'
        assert pending_task['flow'] == 'template_selection'
        assert 'template_ids' in pending_task
        assert isinstance(pending_task['template_ids'], list)
        assert len(pending_task['template_ids']) > 0
