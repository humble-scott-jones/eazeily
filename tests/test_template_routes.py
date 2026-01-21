"""Integration tests for template API routes."""

import pytest
import json


def signup_and_login(client, email='test@example.com', password='testpass123'):
    """Helper to signup and login a user."""
    # Signup
    client.post('/api/signup', json={
        'email': email,
        'password': password
    })
    
    # Login
    response = client.post('/api/login', json={
        'email': email,
        'password': password
    })
    return response


def create_profile(client):
    """Helper to create a basic profile for testing."""
    from models import VoiceProfile, User, db
    from app import create_app
    
    test_app = create_app()
    with test_app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        if user:
            profile = VoiceProfile(
                user_id=user.id,
                business_name='Test Business',
                industry='restaurant',
                target_audience='Food lovers',
                brand_voice='Friendly and inviting',
                key_offer='Fresh local ingredients'
            )
            db.session.add(profile)
            db.session.commit()


class TestTemplateRoutes:
    """Test suite for template API routes."""
    
    def test_list_templates_requires_auth(self, client):
        """Test that listing templates requires authentication."""
        response = client.get('/api/templates')
        # Flask-Login redirects to login page when not authenticated
        assert response.status_code in [302, 401]
    
    def test_list_templates_authenticated(self, client):
        """Test listing templates when authenticated."""
        signup_and_login(client)
        
        response = client.get('/api/templates')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'templates' in data
        assert 'count' in data
        assert isinstance(data['templates'], list)
        assert data['count'] > 0
    
    def test_list_templates_has_expected_fields(self, client):
        """Test that each template has expected fields."""
        signup_and_login(client)
        
        response = client.get('/api/templates')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        templates = data['templates']
        
        assert len(templates) > 0
        
        # Check first template has all fields
        template = templates[0]
        assert 'id' in template
        assert 'name' in template
        assert 'description' in template
        assert 'industry' in template
        assert 'task_type' in template
        assert 'default_params' in template
        assert 'example_output' in template
    
    def test_list_templates_filter_by_industry(self, client):
        """Test filtering templates by industry."""
        signup_and_login(client)
        
        response = client.get('/api/templates?industry=restaurant')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        templates = data['templates']
        
        assert len(templates) > 0
        
        # Should include restaurant and/or general templates
        industries = {t['industry'] for t in templates}
        assert 'restaurant' in industries or 'general' in industries
    
    def test_list_templates_filter_by_task_type(self, client):
        """Test filtering templates by task type."""
        signup_and_login(client)
        
        response = client.get('/api/templates?task_type=post')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        templates = data['templates']
        
        assert len(templates) > 0
        
        # All should be posts
        assert all(t['task_type'] == 'post' for t in templates)
    
    def test_list_templates_search(self, client):
        """Test searching templates."""
        signup_and_login(client)
        
        response = client.get('/api/templates?search=motivation')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        templates = data['templates']
        
        assert len(templates) > 0
        
        # Should find templates with 'motivation' in name or description
        texts = [t['name'].lower() + ' ' + t['description'].lower() for t in templates]
        assert any('motivation' in text for text in texts)
    
    def test_get_template_by_id_requires_auth(self, client):
        """Test that getting a template by ID requires authentication."""
        response = client.get('/api/templates/restaurant_daily_special')
        # Flask-Login redirects to login page when not authenticated
        assert response.status_code in [302, 401]
    
    def test_get_template_by_id_valid(self, client):
        """Test getting a specific template by ID."""
        signup_and_login(client)
        
        response = client.get('/api/templates/restaurant_daily_special')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'template' in data
        
        template = data['template']
        assert template['id'] == 'restaurant_daily_special'
        assert template['name'] == 'Daily Special Announcement'
        assert template['industry'] == 'restaurant'
    
    def test_get_template_by_id_invalid(self, client):
        """Test getting a template with invalid ID returns 404."""
        signup_and_login(client)
        
        response = client.get('/api/templates/nonexistent_template')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_recommended_templates_requires_auth(self, client):
        """Test that getting recommended templates requires authentication."""
        response = client.get('/api/templates/recommended')
        # Flask-Login redirects to login page when not authenticated
        assert response.status_code in [302, 401]
    
    def test_get_recommended_templates_no_profile(self, client):
        """Test getting recommended templates with no profile."""
        signup_and_login(client)
        
        response = client.get('/api/templates/recommended')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'templates' in data
        assert 'count' in data
        
        # Should return all templates when no profile exists
        assert data['count'] > 0
    
    def test_get_recommended_templates_with_profile(self, client):
        """Test getting recommended templates with user profile."""
        signup_and_login(client)
        create_profile(client)
        
        response = client.get('/api/templates/recommended')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'templates' in data
        assert 'industry' in data
        
        # Should return restaurant templates since profile has restaurant industry
        templates = data['templates']
        assert len(templates) > 0
        
        # Should include restaurant or general templates
        industries = {t['industry'] for t in templates}
        assert 'restaurant' in industries or 'general' in industries
    
    def test_get_recommended_templates_with_task_type_filter(self, client):
        """Test getting recommended templates with task type filter."""
        signup_and_login(client)
        create_profile(client)
        
        response = client.get('/api/templates/recommended?task_type=post')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        templates = data['templates']
        
        assert len(templates) > 0
        # All should be posts
        assert all(t['task_type'] == 'post' for t in templates)
