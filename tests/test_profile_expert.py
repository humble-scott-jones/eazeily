"""Test the AI-powered profile expert service."""

import pytest
from unittest.mock import Mock, patch
from services.profile_expert import (
    generate_profile_suggestions,
    build_context,
    parse_suggestions,
    FIELD_EXPERT_PROMPTS
)


def test_field_expert_prompts_exist():
    """Test that prompts exist for all expected fields."""
    expected_fields = ['target_audience', 'brand_voice', 'key_offer', 'writing_samples', 'voice_rules']
    
    for field in expected_fields:
        assert field in FIELD_EXPERT_PROMPTS, f"Missing prompt for {field}"
        assert len(FIELD_EXPERT_PROMPTS[field]) > 0, f"Empty prompt for {field}"


def test_build_context_with_complete_profile():
    """Test building context from a complete profile."""
    profile = {
        'company': 'Test Company',
        'industry': 'Software',
        'tone': 'Friendly and professional',
        'target_audience': 'Small business owners',
        'key_offer': 'Easy-to-use software',
        'writing_samples': ['Sample 1', 'Sample 2', 'Sample 3']
    }
    
    context = build_context(profile, 'brand_voice')
    
    assert context['business_name'] == 'Test Company'
    assert context['industry'] == 'Software'
    assert context['brand_voice'] == 'Friendly and professional'
    assert context['target_audience'] == 'Small business owners'
    assert context['key_offer'] == 'Easy-to-use software'
    assert '- "Sample 1"' in context['writing_samples']


def test_build_context_with_minimal_profile():
    """Test building context from a minimal profile."""
    profile = {
        'business_name': 'My Business'
    }
    
    context = build_context(profile, 'brand_voice')
    
    assert context['business_name'] == 'My Business'
    assert context['industry'] == 'your industry'
    assert context['brand_voice'] == 'Not set yet'
    assert context['target_audience'] == 'Not set yet'
    assert context['key_offer'] == 'Not set yet'
    assert 'None provided yet' in context['writing_samples']


def test_build_context_handles_list_values():
    """Test that build_context properly handles list values."""
    profile = {
        'business_name': 'Test',
        'writing_samples': ['Sample 1', 'Sample 2']
    }
    
    context = build_context(profile, 'target_audience')
    
    assert '- "Sample 1"' in context['writing_samples']
    assert '- "Sample 2"' in context['writing_samples']


def test_parse_suggestions_with_numbered_list():
    """Test parsing numbered suggestions from AI response."""
    response_text = """1. First suggestion here
This continues the first one.

2. Second suggestion starts here
With more details.

3. Third and final suggestion
Also with details."""
    
    suggestions = parse_suggestions(response_text)
    
    assert len(suggestions) == 3
    assert 'First suggestion here' in suggestions[0]
    assert 'continues the first one' in suggestions[0]
    assert 'Second suggestion starts here' in suggestions[1]
    assert 'Third and final suggestion' in suggestions[2]


def test_parse_suggestions_with_mixed_formatting():
    """Test parsing suggestions with various number formats."""
    response_text = """1. First one
2) Second one
3: Third one"""
    
    suggestions = parse_suggestions(response_text)
    
    assert len(suggestions) == 3
    assert 'First one' in suggestions[0]
    assert 'Second one' in suggestions[1]


def test_parse_suggestions_limits_to_three():
    """Test that parse_suggestions returns max 3 suggestions."""
    response_text = """1. First
2. Second
3. Third
4. Fourth
5. Fifth"""
    
    suggestions = parse_suggestions(response_text)
    
    assert len(suggestions) == 3


def test_generate_profile_suggestions_invalid_field():
    """Test that invalid field returns error."""
    profile = {'business_name': 'Test'}
    
    result = generate_profile_suggestions('invalid_field', profile)
    
    assert result['success'] is False
    assert 'Unknown field' in result['error']
    assert result['suggestions'] == []


@patch('services.profile_expert.get_generative_model')
def test_generate_profile_suggestions_no_model(mock_get_model):
    """Test handling when AI service is not available."""
    mock_get_model.return_value = None
    
    profile = {'business_name': 'Test', 'industry': 'Software'}
    result = generate_profile_suggestions('brand_voice', profile)
    
    assert result['success'] is False
    assert 'AI service not configured' in result['error']
    assert result['suggestions'] == []


@patch('services.profile_expert.get_generative_model')
def test_generate_profile_suggestions_success(mock_get_model):
    """Test successful suggestion generation."""
    # Mock the AI model response
    mock_response = Mock()
    mock_response.text = """1. "Friendly and approachable" - Matches your casual writing style

2. "Professional yet warm" - Balances expertise with accessibility

3. "Conversational and helpful" - Perfect for engaging your audience"""
    
    mock_model = Mock()
    mock_model.generate_content.return_value = mock_response
    mock_get_model.return_value = mock_model
    
    profile = {
        'business_name': 'Test Company',
        'industry': 'Software',
        'tone': 'Friendly',
        'target_audience': 'Small businesses',
        'key_offer': 'Easy software',
        'writing_samples': ['We help you grow!']
    }
    
    result = generate_profile_suggestions('brand_voice', profile)
    
    assert result['success'] is True
    assert result['field'] == 'brand_voice'
    assert len(result['suggestions']) == 3
    assert 'Friendly and approachable' in result['suggestions'][0]
    assert 'Professional yet warm' in result['suggestions'][1]
    assert result['context']['business_name'] == 'Test Company'
    assert result['context']['industry'] == 'Software'


@patch('services.profile_expert.get_generative_model')
def test_generate_profile_suggestions_handles_exception(mock_get_model):
    """Test that exceptions are handled gracefully."""
    mock_model = Mock()
    mock_model.generate_content.side_effect = Exception("API error")
    mock_get_model.return_value = mock_model
    
    profile = {'business_name': 'Test'}
    result = generate_profile_suggestions('brand_voice', profile)
    
    assert result['success'] is False
    assert 'API error' in result['error']
    assert result['suggestions'] == []


def test_profile_expert_endpoint_requires_auth(client):
    """Test that the suggest endpoint requires authentication."""
    response = client.post('/api/profile/suggest', json={'field': 'brand_voice'})
    
    # Should redirect to login or return 401
    assert response.status_code in [302, 401]


def test_profile_expert_endpoint_requires_field(authenticated_client):
    """Test that field parameter is required."""
    response = authenticated_client.post('/api/profile/suggest', json={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Field is required' in data['error']


def test_profile_expert_endpoint_validates_field(authenticated_client):
    """Test that invalid fields are rejected."""
    response = authenticated_client.post('/api/profile/suggest', json={'field': 'invalid_field'})
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Invalid field' in data['error']


@patch('services.profile_expert.get_generative_model')
def test_profile_expert_endpoint_success(authenticated_client, mock_get_model):
    """Test successful profile suggestion via API endpoint."""
    # Mock the AI model response
    mock_response = Mock()
    mock_response.text = """1. First suggestion

2. Second suggestion

3. Third suggestion"""
    
    mock_model = Mock()
    mock_model.generate_content.return_value = mock_response
    mock_get_model.return_value = mock_model
    
    response = authenticated_client.post('/api/profile/suggest', json={'field': 'brand_voice'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['suggestions']) == 3
    assert 'context' in data
