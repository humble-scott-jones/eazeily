"""Tests for improved profile update flow with AI suggestions.

Tests the enhanced profile update features including:
- AI suggestions for bare commands
- Numeric selection from suggestions
- Profile dashboard with field selection
- Guided profile completion flow
- Progress bar display
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAISuggestions:
    """Test AI suggestions for profile fields."""
    
    def test_bare_voice_command_shows_ai_suggestions(self, authenticated_client, profile):
        """Test that /voice without value shows AI suggestions."""
        with patch('routes.chat_routes.generate_profile_suggestions') as mock_gen:
            mock_gen.return_value = {
                'success': True,
                'suggestions': [
                    'Professional and authoritative',
                    'Warm and friendly',
                    'Casual and energetic'
                ]
            }
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/voice'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'continue'
            assert 'suggestions' in data['pending_task']
            assert len(data['pending_task']['suggestions']) == 3
            assert '1.' in data['response']  # Numbered options
            assert '2.' in data['response']
            assert '3.' in data['response']
    
    def test_bare_audience_command_shows_ai_suggestions(self, authenticated_client, profile):
        """Test that /audience without value shows AI suggestions."""
        with patch('routes.chat_routes.generate_profile_suggestions') as mock_gen:
            mock_gen.return_value = {
                'success': True,
                'suggestions': [
                    'Small business owners aged 30-50',
                    'Tech startup founders',
                    'Marketing professionals'
                ]
            }
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/audience'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'continue'
            assert 'suggestions' in data['pending_task']
            assert '1.' in data['response']
    
    def test_bare_offer_command_shows_ai_suggestions(self, authenticated_client, profile):
        """Test that /offer without value shows AI suggestions."""
        with patch('routes.chat_routes.generate_profile_suggestions') as mock_gen:
            mock_gen.return_value = {
                'success': True,
                'suggestions': [
                    'Fast delivery in 24 hours',
                    'Expert support included',
                    'Money-back guarantee'
                ]
            }
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/offer'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['action'] == 'continue'
            assert 'suggestions' in data['pending_task']


class TestSuggestionSelection:
    """Test numeric selection from AI suggestions."""
    
    def test_select_first_suggestion(self, authenticated_client, profile):
        """Test selecting option 1 from suggestions."""
        # First, trigger suggestions
        with patch('routes.chat_routes.generate_profile_suggestions') as mock_gen:
            mock_gen.return_value = {
                'success': True,
                'suggestions': [
                    'Professional and authoritative',
                    'Warm and friendly',
                    'Casual and energetic'
                ]
            }
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/voice'
            })
            pending_task = response.get_json()['pending_task']
        
        # Then select option 1
        response = authenticated_client.post('/api/chat', json={
            'message': '1',
            'pending_task': pending_task
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'profile_updated'
        assert 'Professional and authoritative' in data['response']
    
    def test_select_custom_option(self, authenticated_client, profile):
        """Test writing custom value instead of selecting."""
        # First, trigger suggestions
        with patch('routes.chat_routes.generate_profile_suggestions') as mock_gen:
            mock_gen.return_value = {
                'success': True,
                'suggestions': [
                    'Professional and authoritative',
                    'Warm and friendly',
                    'Casual and energetic'
                ]
            }
            
            response = authenticated_client.post('/api/chat', json={
                'message': '/voice'
            })
            pending_task = response.get_json()['pending_task']
        
        # Then provide custom value
        response = authenticated_client.post('/api/chat', json={
            'message': 'Bold and innovative',
            'pending_task': pending_task
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'profile_updated'
        assert 'Bold and innovative' in data['response']


class TestProfileDashboard:
    """Test profile dashboard with field selection."""
    
    def test_profile_command_shows_dashboard(self, authenticated_client, profile):
        """Test /profile shows interactive dashboard."""
        response = authenticated_client.post('/api/chat', json={
            'message': '/profile'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'profile_view'
        assert 'pending_task' in data
        assert data['pending_task']['flow'] == 'profile_dashboard'
        # Should show numbered fields
        assert '1.' in data['response']
        assert '2.' in data['response']
        # Should show status icons
        assert '✅' in data['response'] or '❌' in data['response']
        # Should show progress bar
        assert '📊 Profile:' in data['response']
    
    def test_select_field_by_number(self, authenticated_client, profile):
        """Test selecting field 3 (brand_voice) from dashboard."""
        # First show dashboard
        response = authenticated_client.post('/api/chat', json={
            'message': '/profile'
        })
        pending_task = response.get_json()['pending_task']
        
        # Then select field 3
        with patch('routes.chat_routes.generate_profile_suggestions') as mock_gen:
            mock_gen.return_value = {
                'success': True,
                'suggestions': ['Option 1', 'Option 2', 'Option 3']
            }
            
            response = authenticated_client.post('/api/chat', json={
                'message': '3',
                'pending_task': pending_task
            })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'continue'
        assert 'Brand Voice' in data['response']


class TestGuidedCompletion:
    """Test guided profile completion flow."""
    
    def test_complete_command_starts_flow(self, client, monkeypatch):
        """Test /complete starts guided completion with incomplete profile."""
        # Set fake API key for test
        monkeypatch.setenv('GENAI_API_KEY', 'test-fake-api-key')
        
        from models import User, VoiceProfile, db
        from app import create_app
        
        # Create a user with incomplete profile
        test_app = create_app()
        test_app.config['TESTING'] = True
        
        with test_app.app_context():
            user = User(email='incomplete@example.com')
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            
            # Create incomplete profile (missing target_audience and key_offer)
            profile = VoiceProfile(
                user_id=user.id,
                business_name='Test Business',
                industry='Technology',
                brand_voice='Professional'
            )
            db.session.add(profile)
            db.session.commit()
            
            user_id = user.id
        
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.post('/api/chat', json={
            'message': '/complete'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'continue'
        assert 'pending_task' in data
        assert data['pending_task']['task_type'] == 'guided_completion'
        # Should show progress
        assert '📊 Profile:' in data['response']
        # Should show skip option
        assert 'skip' in data['response'].lower()
    
    def test_answer_first_field_continues(self, client, monkeypatch):
        """Test answering first field continues to next."""
        # Set fake API key for test
        monkeypatch.setenv('GENAI_API_KEY', 'test-fake-api-key')
        
        from models import User, VoiceProfile, db
        from app import create_app
        
        # Create a user with incomplete profile
        test_app = create_app()
        test_app.config['TESTING'] = True
        
        with test_app.app_context():
            user = User(email='incomplete2@example.com')
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            
            # Create incomplete profile
            profile = VoiceProfile(
                user_id=user.id,
                business_name='Test Business',
                industry='Technology'
            )
            db.session.add(profile)
            db.session.commit()
            
            user_id = user.id
        
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Start guided completion
        response = client.post('/api/chat', json={
            'message': '/complete'
        })
        pending_task = response.get_json()['pending_task']
        
        # Answer the first field
        response = client.post('/api/chat', json={
            'message': 'Professional and friendly',
            'pending_task': pending_task
        })
        
        assert response.status_code == 200
        data = response.get_json()
        # Should continue to next field or complete
        assert data['action'] in ['continue', 'profile_complete']
    
    def test_skip_field_moves_to_next(self, client, monkeypatch):
        """Test skip moves to next field."""
        # Set fake API key for test
        monkeypatch.setenv('GENAI_API_KEY', 'test-fake-api-key')
        
        from models import User, VoiceProfile, db
        from app import create_app
        
        # Create a user with incomplete profile
        test_app = create_app()
        test_app.config['TESTING'] = True
        
        with test_app.app_context():
            user = User(email='incomplete3@example.com')
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            
            # Create incomplete profile
            profile = VoiceProfile(
                user_id=user.id,
                business_name='Test Business',
                industry='Technology'
            )
            db.session.add(profile)
            db.session.commit()
            
            user_id = user.id
        
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Start guided completion
        response = client.post('/api/chat', json={
            'message': '/complete'
        })
        pending_task = response.get_json()['pending_task']
        
        # Skip the field
        response = client.post('/api/chat', json={
            'message': 'skip',
            'pending_task': pending_task
        })
        
        assert response.status_code == 200
        data = response.get_json()
        # Should continue to next field or complete
        assert data['action'] in ['continue', 'profile_complete']
    
    def test_complete_profile_shows_celebration(self, authenticated_client, complete_profile):
        """Test completing profile shows celebration message."""
        response = authenticated_client.post('/api/chat', json={
            'message': '/complete'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'profile_complete'
        assert '🎉' in data['response'] or '🎊' in data['response']


class TestProgressBar:
    """Test progress bar display."""
    
    def test_progress_bar_after_update(self, authenticated_client, profile):
        """Test progress bar shows after field update."""
        response = authenticated_client.post('/api/chat', json={
            'message': '/voice warm and friendly'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert '📊 Profile:' in data['response']
        assert '%' in data['response']
    
    def test_progress_bar_shows_percentage(self, authenticated_client, profile):
        """Test progress bar shows correct percentage."""
        response = authenticated_client.post('/api/chat', json={
            'message': '/voice warm and friendly'
        })
        
        data = response.get_json()
        # Should show a percentage (any number followed by %)
        import re
        assert re.search(r'\d+%', data['response'])


class TestValidationMessages:
    """Test field-specific validation messages."""
    
    def test_business_name_validation_message(self, authenticated_client, profile):
        """Test business_name validation has specific message."""
        response = authenticated_client.post('/api/chat', json={
            'message': '/name a'  # Too short
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'error'
        assert 'Business names should be at least 2 characters' in data['response']
    
    def test_brand_voice_validation_message(self, authenticated_client, profile):
        """Test brand_voice validation has specific message."""
        response = authenticated_client.post('/api/chat', json={
            'message': '/voice a'  # Too short
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['action'] == 'error'
        assert '2-3 words' in data['response']
