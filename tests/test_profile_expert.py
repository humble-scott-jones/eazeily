"""Tests for AI-powered profile expert service."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from models import User, VoiceProfile, db


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = """1. Small business owners aged 30-50 who struggle with maintaining a consistent social media presence. They understand the importance of being online but lack the time and expertise to create engaging content regularly.

2. Marketing managers at mid-sized companies who need to scale content production without expanding their team. They're looking for efficient solutions that maintain brand consistency across multiple platforms.

3. Solopreneurs and freelancers who want to establish thought leadership in their niche. They need help crafting professional content that showcases their expertise while staying authentic to their personal brand."""
    return mock_response


@pytest.fixture
def complete_profile(authenticated_client):
    """Create a complete profile for testing."""
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        profile.business_name = "Eazeily"
        profile.industry = "Software"
        profile.brand_voice = "Friendly and helpful"
        profile.target_audience = "Small business owners"
        profile.key_offer = "AI-powered social media content"
        profile.set_writing_samples([
            "Just shipped a new feature that helps you create content 3x faster! 🚀",
            "Your brand voice is unique. We help you keep it that way across all platforms."
        ])
        db.session.commit()
    return profile


def test_profile_suggest_endpoint_requires_auth(client):
    """Test that the suggest endpoint requires authentication."""
    response = client.post('/api/profile/suggest', json={
        'field': 'target_audience'
    })
    
    # Should redirect to login or return 401
    assert response.status_code in [302, 401]


def test_profile_suggest_endpoint_requires_field(authenticated_client):
    """Test that the suggest endpoint requires a field parameter."""
    response = authenticated_client.post('/api/profile/suggest', json={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Field is required' in data['error']


def test_profile_suggest_endpoint_validates_field(authenticated_client):
    """Test that the suggest endpoint validates the field parameter."""
    response = authenticated_client.post('/api/profile/suggest', json={
        'field': 'invalid_field'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Invalid field' in data['error']


def test_profile_suggest_endpoint_valid_fields(authenticated_client):
    """Test that all expected fields are valid."""
    valid_fields = ['target_audience', 'brand_voice', 'key_offer', 'writing_samples', 'voice_rules']
    
    for field in valid_fields:
        # Mock OpenAI to avoid actual API calls
        with patch('services.profile_expert.get_client') as mock_get_client:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "1. Test suggestion"
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            response = authenticated_client.post('/api/profile/suggest', json={
                'field': field
            })
            
            # Should not return 400 for valid fields
            assert response.status_code != 400


@patch('services.profile_expert.get_client')
def test_profile_suggest_target_audience(mock_get_client, authenticated_client, complete_profile, mock_openai_response):
    """Test AI suggestion generation for target audience."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_get_client.return_value = mock_client
    
    response = authenticated_client.post('/api/profile/suggest', json={
        'field': 'target_audience'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['success'] is True
    assert data['field'] == 'target_audience'
    assert 'suggestions' in data
    assert len(data['suggestions']) > 0
    assert len(data['suggestions']) <= 3
    
    # Verify context is included
    assert 'context' in data
    assert data['context']['business_name'] == 'Eazeily'
    assert data['context']['industry'] == 'Software'
    
    # Verify OpenAI was called with correct parameters
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args
    assert call_args[1]['model'] == 'gpt-4o-mini'
    assert call_args[1]['max_tokens'] == 600
    assert call_args[1]['temperature'] == 0.7


@patch('services.profile_expert.get_client')
def test_profile_suggest_brand_voice(mock_get_client, authenticated_client, complete_profile):
    """Test AI suggestion generation for brand voice."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = """1. "Friendly, helpful, and empowering" - Matches your supportive tone while emphasizing user success

2. "Professional yet approachable" - Balances expertise with accessibility

3. "Innovative and solution-focused" - Highlights your tech-forward approach"""
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    response = authenticated_client.post('/api/profile/suggest', json={
        'field': 'brand_voice'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['success'] is True
    assert data['field'] == 'brand_voice'
    assert len(data['suggestions']) == 3


@patch('services.profile_expert.get_client')
def test_profile_suggest_handles_openai_error(mock_get_client, authenticated_client, complete_profile):
    """Test that the endpoint handles OpenAI errors gracefully."""
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("OpenAI API error")
    mock_get_client.return_value = mock_client
    
    response = authenticated_client.post('/api/profile/suggest', json={
        'field': 'target_audience'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['success'] is False
    assert 'error' in data
    assert data['suggestions'] == []


def test_profile_suggest_requires_profile(authenticated_client):
    """Test that the suggest endpoint requires a profile to exist."""
    # Delete the user's profile
    test_app = authenticated_client.application
    with test_app.app_context():
        profile = VoiceProfile.query.filter_by(user_id=1).first()
        db.session.delete(profile)
        db.session.commit()
    
    response = authenticated_client.post('/api/profile/suggest', json={
        'field': 'target_audience'
    })
    
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'No profile found' in data['error']


@patch('services.profile_expert.get_client')
def test_profile_expert_uses_full_context(mock_get_client, authenticated_client, complete_profile, mock_openai_response):
    """Test that profile expert uses full profile context in prompts."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_get_client.return_value = mock_client
    
    response = authenticated_client.post('/api/profile/suggest', json={
        'field': 'target_audience'
    })
    
    assert response.status_code == 200
    
    # Verify the prompt includes profile context
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]['messages']
    user_message = messages[1]['content']
    
    # Should include business info in the prompt
    assert 'Eazeily' in user_message
    assert 'Software' in user_message
    assert 'Friendly and helpful' in user_message
    assert 'AI-powered social media content' in user_message


def test_parse_suggestions_from_ai_response():
    """Test that suggestions are correctly parsed from AI response."""
    from services.profile_expert import parse_suggestions
    
    response_text = """1. First suggestion here
With multiple lines

2. Second suggestion
Also with details

3. Third suggestion"""
    
    suggestions = parse_suggestions(response_text)
    
    assert len(suggestions) == 3
    assert suggestions[0].startswith('First suggestion')
    assert suggestions[1].startswith('Second suggestion')
    assert suggestions[2].startswith('Third suggestion')


def test_parse_suggestions_handles_various_formats():
    """Test that parser handles different numbering formats."""
    from services.profile_expert import parse_suggestions
    
    # Test with parentheses
    response = "1) First\n2) Second\n3) Third"
    suggestions = parse_suggestions(response)
    assert len(suggestions) == 3
    
    # Test with colons
    response = "1: First\n2: Second\n3: Third"
    suggestions = parse_suggestions(response)
    assert len(suggestions) == 3


def test_build_context_handles_missing_fields():
    """Test that context builder handles missing profile fields."""
    from services.profile_expert import build_context
    
    minimal_profile = {
        'company': 'Test Co'
    }
    
    context = build_context(minimal_profile, 'target_audience')
    
    assert context['business_name'] == 'Test Co'
    assert context['industry'] == 'your industry'
    assert context['brand_voice'] == 'Not set yet'
    assert context['target_audience'] == 'Not set yet'
    assert context['key_offer'] == 'Not set yet'


def test_build_context_formats_writing_samples():
    """Test that writing samples are properly formatted in context."""
    from services.profile_expert import build_context
    
    profile = {
        'company': 'Test Co',
        'writing_samples': [
            'Sample post 1',
            'Sample post 2',
            'Sample post 3'
        ]
    }
    
    context = build_context(profile, 'brand_voice')
    
    assert 'Sample post 1' in context['writing_samples']
    assert 'Sample post 2' in context['writing_samples']
    assert '- "' in context['writing_samples']  # Check formatting


@patch('services.profile_expert.get_client')
def test_profile_suggest_key_offer(mock_get_client, authenticated_client, complete_profile):
    """Test AI suggestion generation for key offer."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = """1. AI-powered content creation that learns your brand voice and creates authentic posts in seconds.

2. Social media automation that keeps your unique voice – no more staring at blank screens or sounding robotic.

3. Transform your writing samples into unlimited on-brand content. Save 10+ hours per week on social media."""
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    response = authenticated_client.post('/api/profile/suggest', json={
        'field': 'key_offer'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['success'] is True
    assert data['field'] == 'key_offer'
    assert len(data['suggestions']) == 3
    # Key offers should be action-oriented
    assert any('AI' in s or 'content' in s for s in data['suggestions'])
