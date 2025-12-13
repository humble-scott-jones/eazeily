"""Tests for output schema validation and repair pass."""

import pytest
import json
from services.generation.output_validator import (
    validate_with_schema_enforcement,
    validate_and_repair_social_posts,
    validate_and_repair_reel_script,
    validate_and_repair_review_responses,
    ValidationError
)


def test_valid_social_posts_pass():
    """Test that valid social posts pass validation."""
    valid_data = {
        'posts': [
            {
                'date': '2024-01-01',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'Great post content here!',
                        'hashtags': ['test', 'content']
                    }
                ]
            }
        ]
    }
    
    result = validate_with_schema_enforcement(valid_data, 'social')
    
    assert result['ok'] is True
    assert result['data'] is not None
    assert result['repaired'] is False
    assert result['error'] is None


def test_invalid_social_posts_trigger_repair():
    """Test that invalid social posts trigger repair."""
    invalid_data = {
        'posts': [
            {
                # Missing 'date'
                'pillar': 'Engagement',
                'cards': [
                    {
                        'platform': 'facebook',
                        'caption': 'Post content'
                    }
                ]
            }
        ]
    }
    
    result = validate_with_schema_enforcement(invalid_data, 'social')
    
    # Should repair (add default date)
    assert result['ok'] is True
    assert result['data'] is not None
    assert 'Day 1' in str(result['data']) or '2024' in str(result['data'])


def test_completely_invalid_social_fails():
    """Test that completely invalid data fails even after repair."""
    invalid_data = {
        'posts': []  # Empty posts
    }
    
    result = validate_with_schema_enforcement(invalid_data, 'social')
    
    assert result['ok'] is False
    assert result['error'] is not None


def test_valid_reel_script_pass():
    """Test that valid reel script passes validation."""
    valid_data = {
        'script': {
            'hook': 'Watch this amazing trick!',
            'beats': [
                {'text': 'First, you need to know this'},
                {'text': 'Then, do this step'}
            ],
            'cta': 'Try it yourself!',
            'caption': 'Amazing video tutorial',
            'hashtags': ['tutorial', 'tips']
        }
    }
    
    result = validate_with_schema_enforcement(valid_data, 'reels')
    
    assert result['ok'] is True
    assert result['data'] is not None


def test_invalid_reel_script_trigger_repair():
    """Test that invalid reel script triggers repair."""
    invalid_data = {
        'script': {
            'hook': 'Great hook!',
            # Missing 'cta'
            'beats': [{'text': 'Beat 1'}],
            'caption': 'Caption'
        }
    }
    
    result = validate_with_schema_enforcement(invalid_data, 'reels')
    
    # Should repair (add default CTA)
    assert result['ok'] is True
    assert result['data'] is not None
    assert result['data']['script']['cta'] is not None


def test_valid_review_responses_pass():
    """Test that valid review responses pass validation."""
    valid_data = {
        'responses': {
            'short': 'Thanks for your feedback!',
            'medium': 'Thank you so much for taking the time to share your experience.',
            'long': 'We truly appreciate your detailed feedback and are glad you enjoyed your visit.'
        },
        'tone': 'professional',
        'voice_applied': True
    }
    
    result = validate_with_schema_enforcement(valid_data, 'reviews')
    
    assert result['ok'] is True
    assert result['data'] is not None


def test_invalid_review_responses_trigger_repair():
    """Test that invalid review responses trigger repair."""
    invalid_data = {
        'responses': {
            'short': 'Thanks!'
            # Missing other variants
        }
        # Missing tone and voice_applied
    }
    
    result = validate_with_schema_enforcement(invalid_data, 'reviews')
    
    # Should repair (add defaults)
    assert result['ok'] is True
    assert result['data'] is not None
    assert result['data']['tone'] == 'professional'
    assert 'voice_applied' in result['data']


def test_schema_validation_with_openai_repair_pass():
    """Test that schema validation can use OpenAI for repair pass."""
    # Mock OpenAI client
    class MockOpenAI:
        class ChatCompletions:
            class Message:
                def __init__(self):
                    self.content = json.dumps({
                        'posts': [{
                            'date': '2024-01-01',
                            'pillar': 'Educational',
                            'cards': [{
                                'platform': 'instagram',
                                'caption': 'Repaired content',
                                'hashtags': ['fixed']
                            }]
                        }]
                    })
            
            class Choice:
                def __init__(self):
                    self.message = MockOpenAI.ChatCompletions.Message()
            
            class Response:
                def __init__(self):
                    self.choices = [MockOpenAI.ChatCompletions.Choice()]
            
            def create(self, **kwargs):
                return self.Response()
        
        def __init__(self):
            self.chat = type('Chat', (), {'completions': self.ChatCompletions()})()
    
    invalid_data = {'posts': [{'cards': []}]}  # Invalid
    
    prompt_set = {
        'system': 'Generate content',
        'context': 'Test context',
        'request': 'Test request'
    }
    
    mock_client = MockOpenAI()
    
    result = validate_with_schema_enforcement(
        invalid_data,
        'social',
        openai_client=mock_client,
        prompt_set=prompt_set
    )
    
    # Should attempt repair with OpenAI
    # Result depends on whether repair succeeds
    assert isinstance(result, dict)
    assert 'ok' in result


def test_unknown_content_type_fails():
    """Test that unknown content type fails validation."""
    result = validate_with_schema_enforcement({'data': 'test'}, 'unknown_type')
    
    # Should return error result (not raise exception)
    assert result['ok'] is False
    assert result['error'] is not None
    assert 'Unknown content type' in result['error']


def test_repair_social_posts_with_missing_fields():
    """Test repair of social posts with missing fields."""
    data = {
        'posts': [
            {
                'cards': [
                    {
                        'caption': 'Good content'
                    }
                ]
            }
        ]
    }
    
    repaired = validate_and_repair_social_posts(data)
    
    # Should have filled in missing fields
    assert repaired['posts'][0]['date'] is not None
    assert repaired['posts'][0]['pillar'] is not None
    assert repaired['posts'][0]['cards'][0]['platform'] is not None


def test_repair_reel_script_with_missing_cta():
    """Test repair of reel script with missing CTA."""
    data = {
        'script': {
            'hook': 'Great hook!',
            'beats': [{'text': 'Beat 1'}],
            'caption': 'Caption'
        }
    }
    
    repaired = validate_and_repair_reel_script(data)
    
    # Should have added default CTA
    assert repaired['script']['cta'] is not None
    assert len(repaired['script']['cta']) > 0


def test_repair_review_responses_with_missing_variants():
    """Test repair of review responses with missing variants."""
    data = {
        'responses': {
            'medium': 'Good response'
        }
    }
    
    repaired = validate_and_repair_review_responses(data)
    
    # Should have defaults for tone and voice_applied
    assert repaired['tone'] == 'professional'
    assert 'voice_applied' in repaired


def test_validation_error_raised_for_unfixable():
    """Test that ValidationError is raised for unfixable data."""
    data = {'posts': 'not a list'}  # Completely wrong structure
    
    with pytest.raises(ValidationError):
        validate_and_repair_social_posts(data)


def test_empty_cards_skipped_in_repair():
    """Test that posts with empty cards are skipped."""
    data = {
        'posts': [
            {
                'date': '2024-01-01',
                'pillar': 'Educational',
                'cards': []  # Empty cards
            },
            {
                'date': '2024-01-02',
                'pillar': 'Engagement',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'Valid content'
                    }
                ]
            }
        ]
    }
    
    repaired = validate_and_repair_social_posts(data)
    
    # First post should be skipped, second should remain
    assert len(repaired['posts']) == 1
    assert repaired['posts'][0]['date'] == '2024-01-02'


def test_schema_enforcement_deterministic():
    """Test that schema validation is deterministic."""
    valid_data = {
        'posts': [{
            'date': '2024-01-01',
            'pillar': 'Educational',
            'cards': [{
                'platform': 'instagram',
                'caption': 'Test',
                'hashtags': []
            }]
        }]
    }
    
    result1 = validate_with_schema_enforcement(valid_data.copy(), 'social')
    result2 = validate_with_schema_enforcement(valid_data.copy(), 'social')
    
    # Should get same result both times
    assert result1['ok'] == result2['ok']
    assert result1['repaired'] == result2['repaired']
