"""Tests for profile expert service using Gemini."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.profile_expert import (
    build_context,
    parse_suggestions,
    generate_profile_suggestions,
    FIELD_EXPERT_PROMPTS
)


class TestBuildContext:
    """Test context building from profile data."""
    
    def test_build_context_complete_profile(self):
        """Test building context with all fields populated."""
        profile = {
            'company': 'Test Company',
            'industry': 'Technology',
            'tone': 'Professional',
            'target_audience': 'Small business owners',
            'key_offer': 'Affordable software solutions',
            'writing_samples': ['Sample 1', 'Sample 2', 'Sample 3']
        }
        
        context = build_context(profile, 'target_audience')
        
        assert context['business_name'] == 'Test Company'
        assert context['industry'] == 'Technology'
        assert context['brand_voice'] == 'Professional'
        assert context['target_audience'] == 'Small business owners'
        assert context['key_offer'] == 'Affordable software solutions'
        assert '- "Sample 1"' in context['writing_samples']
        assert '- "Sample 2"' in context['writing_samples']
    
    def test_build_context_empty_profile(self):
        """Test building context with minimal profile data."""
        profile = {}
        
        context = build_context(profile, 'brand_voice')
        
        assert context['business_name'] == 'Your business'
        assert context['industry'] == 'your industry'
        assert context['brand_voice'] == 'Not set yet'
        assert context['target_audience'] == 'Not set yet'
        assert context['key_offer'] == 'Not set yet'
        assert context['current_value'] == 'Not set'
        assert context['writing_samples'] == 'None provided yet'
    
    def test_build_context_business_name_fallback(self):
        """Test that business_name is used if company is missing."""
        profile = {
            'business_name': 'My Business',
            'industry': 'Retail'
        }
        
        context = build_context(profile, 'key_offer')
        
        assert context['business_name'] == 'My Business'
    
    def test_build_context_brand_voice_fallback(self):
        """Test that brand_voice uses tone as fallback."""
        profile = {
            'tone': 'Casual and Fun'
        }
        
        context = build_context(profile, 'target_audience')
        
        assert context['brand_voice'] == 'Casual and Fun'
    
    def test_build_context_current_value_for_field(self):
        """Test that current_value is set correctly for the requested field."""
        profile = {
            'tone': 'Professional',
            'target_audience': 'Tech enthusiasts'
        }
        
        # Test brand_voice field (maps to tone)
        context = build_context(profile, 'brand_voice')
        assert context['current_value'] == 'Professional'
        
        # Test target_audience field
        context = build_context(profile, 'target_audience')
        assert context['current_value'] == 'Tech enthusiasts'
    
    def test_build_context_writing_samples_as_string(self):
        """Test handling of writing_samples when it's a string."""
        profile = {
            'writing_samples': 'Single sample text'
        }
        
        context = build_context(profile, 'voice_rules')
        
        assert 'Single sample text' in context['writing_samples']
    
    def test_build_context_writing_samples_list(self):
        """Test handling of writing_samples list with more than 3 items."""
        profile = {
            'writing_samples': ['Sample 1', 'Sample 2', 'Sample 3', 'Sample 4', 'Sample 5']
        }
        
        context = build_context(profile, 'voice_rules')
        
        # Should only include first 3 samples
        assert '- "Sample 1"' in context['writing_samples']
        assert '- "Sample 2"' in context['writing_samples']
        assert '- "Sample 3"' in context['writing_samples']
        assert '- "Sample 4"' not in context['writing_samples']


class TestParseSuggestions:
    """Test parsing AI responses into suggestion lists."""
    
    def test_parse_numbered_suggestions(self):
        """Test parsing standard numbered format."""
        response = """1. First suggestion here
This continues the first suggestion.

2. Second suggestion text
More details for second.

3. Third suggestion content
Final suggestion details."""
        
        suggestions = parse_suggestions(response)
        
        assert len(suggestions) == 3
        assert suggestions[0].startswith('First suggestion')
        assert 'continues the first' in suggestions[0]
        assert suggestions[1].startswith('Second suggestion')
        assert suggestions[2].startswith('Third suggestion')
    
    def test_parse_suggestions_with_parentheses(self):
        """Test parsing with ) separator."""
        response = """1) First option
2) Second option
3) Third option"""
        
        suggestions = parse_suggestions(response)
        
        assert len(suggestions) == 3
        assert suggestions[0] == 'First option'
        assert suggestions[1] == 'Second option'
        assert suggestions[2] == 'Third option'
    
    def test_parse_suggestions_with_colon(self):
        """Test parsing with : separator."""
        response = """1: Option one text
2: Option two text
3: Option three text"""
        
        suggestions = parse_suggestions(response)
        
        assert len(suggestions) == 3
        assert suggestions[0] == 'Option one text'
    
    def test_parse_suggestions_multiline_entries(self):
        """Test parsing multi-line suggestions."""
        response = """1. "Professional and approachable" - This voice combines expertise with warmth,
making complex topics accessible to your audience.

2. "Educational yet conversational" - Perfect for sharing knowledge while
maintaining a friendly, engaging tone.

3. "Authoritative and clear" - Establishes credibility through straightforward,
confident communication."""
        
        suggestions = parse_suggestions(response)
        
        assert len(suggestions) == 3
        assert 'Professional and approachable' in suggestions[0]
        assert 'complex topics accessible' in suggestions[0]
        assert 'Educational yet conversational' in suggestions[1]
    
    def test_parse_suggestions_returns_max_three(self):
        """Test that parse_suggestions returns at most 3 items."""
        response = """1. First
2. Second
3. Third
4. Fourth
5. Fifth"""
        
        suggestions = parse_suggestions(response)
        
        assert len(suggestions) == 3
    
    def test_parse_suggestions_empty_response(self):
        """Test handling of empty response."""
        suggestions = parse_suggestions("")
        
        assert len(suggestions) == 0
    
    def test_parse_suggestions_no_numbers(self):
        """Test handling of response without numbers."""
        response = "Just some text without numbers"
        
        suggestions = parse_suggestions(response)
        
        # Should return empty list since no numbered items found
        assert len(suggestions) == 0


class TestGenerateProfileSuggestions:
    """Test the main suggestion generation function."""
    
    def test_generate_suggestions_unknown_field(self):
        """Test handling of unknown field."""
        profile = {'company': 'Test'}
        
        result = generate_profile_suggestions('unknown_field', profile)
        
        assert result['success'] is False
        assert 'Unknown field' in result['error']
        assert result['suggestions'] == []
    
    @patch('services.profile_expert.get_generative_model')
    def test_generate_suggestions_no_model_available(self, mock_get_model):
        """Test handling when AI service is not available."""
        mock_get_model.return_value = None
        
        profile = {
            'company': 'Test Company',
            'industry': 'Technology'
        }
        
        result = generate_profile_suggestions('target_audience', profile)
        
        assert result['success'] is False
        assert 'AI service not configured' in result['error']
        assert result['suggestions'] == []
    
    @patch('services.profile_expert.get_generative_model')
    def test_generate_suggestions_successful(self, mock_get_model):
        """Test successful suggestion generation."""
        # Mock the AI model and response
        mock_response = Mock()
        mock_response.text = """1. Small business owners in the tech industry looking for affordable software solutions.

2. Startup founders who need reliable tools to scale their operations efficiently.

3. Freelance developers seeking powerful yet simple software for client projects."""
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_model.return_value = mock_model
        
        profile = {
            'company': 'Tech Solutions Inc',
            'industry': 'Technology',
            'tone': 'Professional',
            'target_audience': 'Small businesses',
            'key_offer': 'Affordable software',
            'writing_samples': ['Sample post about innovation']
        }
        
        result = generate_profile_suggestions('target_audience', profile)
        
        assert result['success'] is True
        assert result['field'] == 'target_audience'
        assert len(result['suggestions']) == 3
        assert 'Small business owners' in result['suggestions'][0]
        assert 'Startup founders' in result['suggestions'][1]
        assert 'Freelance developers' in result['suggestions'][2]
        assert result['context']['business_name'] == 'Tech Solutions Inc'
        assert result['context']['industry'] == 'Technology'
    
    @patch('services.profile_expert.get_generative_model')
    def test_generate_suggestions_with_brand_voice(self, mock_get_model):
        """Test generating brand voice suggestions."""
        mock_response = Mock()
        mock_response.text = """1. "Friendly and approachable" - Builds trust with your audience

2. "Professional yet personable" - Maintains credibility while staying relatable

3. "Energetic and inspiring" - Motivates action and engagement"""
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_model.return_value = mock_model
        
        profile = {
            'company': 'Fitness Co',
            'industry': 'Health & Fitness',
            'target_audience': 'Busy professionals'
        }
        
        result = generate_profile_suggestions('brand_voice', profile)
        
        assert result['success'] is True
        assert len(result['suggestions']) == 3
        assert 'Friendly and approachable' in result['suggestions'][0]
    
    @patch('services.profile_expert.get_generative_model')
    def test_generate_suggestions_exception_handling(self, mock_get_model):
        """Test handling of exceptions during generation."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception('API Error')
        mock_get_model.return_value = mock_model
        
        profile = {'company': 'Test'}
        
        result = generate_profile_suggestions('target_audience', profile)
        
        assert result['success'] is False
        assert 'API Error' in result['error']
        assert result['suggestions'] == []
    
    @patch('services.profile_expert.get_generative_model')
    def test_generate_suggestions_uses_system_instruction(self, mock_get_model):
        """Test that model is created with correct system instruction."""
        mock_response = Mock()
        mock_response.text = "1. Suggestion one\n2. Suggestion two\n3. Suggestion three"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_model.return_value = mock_model
        
        profile = {'company': 'Test'}
        
        generate_profile_suggestions('key_offer', profile)
        
        # Verify get_generative_model was called with system instruction
        mock_get_model.assert_called_once()
        call_kwargs = mock_get_model.call_args[1]
        assert 'system_instruction' in call_kwargs
        assert 'expert brand strategist' in call_kwargs['system_instruction']
    
    def test_all_fields_have_prompts(self):
        """Test that all valid fields have corresponding prompts."""
        valid_fields = ['target_audience', 'brand_voice', 'key_offer', 'writing_samples', 'voice_rules']
        
        for field in valid_fields:
            assert field in FIELD_EXPERT_PROMPTS, f"Missing prompt for {field}"
            assert len(FIELD_EXPERT_PROMPTS[field]) > 100, f"Prompt for {field} seems too short"


class TestProfileSuggestEndpoint:
    """Test the API endpoint for profile suggestions."""
    
    def test_suggest_endpoint_requires_auth(self, client):
        """Test that endpoint requires authentication."""
        response = client.post('/api/profile/suggest', json={'field': 'target_audience'})
        
        # Should redirect to login or return 401
        assert response.status_code in [302, 401]
    
    def test_suggest_endpoint_requires_field(self, authenticated_client):
        """Test that field parameter is required."""
        response = authenticated_client.post('/api/profile/suggest', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Field is required' in data['error']
    
    def test_suggest_endpoint_validates_field(self, authenticated_client):
        """Test that field must be one of valid options."""
        response = authenticated_client.post('/api/profile/suggest', json={'field': 'invalid_field'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid field' in data['error']
    
    @patch('services.profile_expert.get_generative_model')
    def test_suggest_endpoint_requires_profile(self, mock_get_model, authenticated_client):
        """Test that endpoint handles user without complete profile gracefully."""
        # The authenticated_client has a profile by default from conftest
        # For this test, we'll delete the profile to test the error case
        from app import create_app
        from models import VoiceProfile, db
        
        test_app = authenticated_client.application
        with test_app.app_context():
            # Delete the user's profile
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            if profile:
                db.session.delete(profile)
                db.session.commit()
        
        response = authenticated_client.post('/api/profile/suggest', json={'field': 'target_audience'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'No profile found' in data['error']
    
    @patch('services.profile_expert.get_generative_model')
    def test_suggest_endpoint_success(self, mock_get_model, authenticated_client):
        """Test successful suggestion generation via endpoint."""
        # Mock the AI response
        mock_response = Mock()
        mock_response.text = """1. Tech-savvy small business owners
2. Growing startups in need of scalable solutions
3. Enterprise teams looking for reliable tools"""
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_model.return_value = mock_model
        
        response = authenticated_client.post('/api/profile/suggest', json={'field': 'target_audience'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['field'] == 'target_audience'
        assert len(data['suggestions']) == 3
        assert 'Tech-savvy small business owners' in data['suggestions'][0]
    
    @patch('services.profile_expert.get_generative_model')
    def test_suggest_endpoint_all_valid_fields(self, mock_get_model, authenticated_client):
        """Test that endpoint works for all valid fields."""
        mock_response = Mock()
        mock_response.text = "1. Suggestion one\n2. Suggestion two\n3. Suggestion three"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_model.return_value = mock_model
        
        valid_fields = ['target_audience', 'brand_voice', 'key_offer', 'writing_samples', 'voice_rules']
        
        for field in valid_fields:
            response = authenticated_client.post('/api/profile/suggest', json={'field': field})
            
            assert response.status_code == 200, f"Failed for field: {field}"
            data = response.get_json()
            assert data['success'] is True, f"Failed for field: {field}"
            assert data['field'] == field
