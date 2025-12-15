"""Test schema validations for social output - ensure SocialPostCard contract."""

import pytest
from services.generation.social_post_ready_pipeline import (
    normalize_and_guardrail,
    SocialPostCard,
)


def test_normalizes_valid_output():
    """Test that valid output is normalized correctly."""
    raw_output = {
        'data': {
            'posts': [
                {
                    'date': 'Day 1',
                    'pillar': 'Educational',
                    'cards': [
                        {
                            'platform': 'instagram',
                            'caption': '3 steps to better content:\n\n1. Hook\n2. Value\n3. CTA',
                            'hashtags': ['#content', '#marketing'],
                            'cta': 'Save this post'
                        }
                    ]
                }
            ]
        }
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is True
    assert 'posts' in result
    assert len(result['posts']) == 1
    
    card = result['posts'][0]
    assert card['platform'] == 'instagram'
    assert card['caption'] == '3 steps to better content:\n\n1. Hook\n2. Value\n3. CTA'
    assert card['hashtags'] == ['#content', '#marketing']
    assert card['cta'] == 'Save this post'


def test_extracts_embedded_hashtags():
    """Test that hashtags embedded in caption are extracted."""
    raw_output = {
        'posts': [
            {
                'date': 'Day 1',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'Great content here\n\n#marketing #content #social',
                        'hashtags': []
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is True
    card = result['posts'][0]
    assert '#marketing' in card['hashtags']
    assert '#content' in card['hashtags']
    assert '#social' in card['hashtags']
    # Caption should be cleaned
    assert card['caption'] == 'Great content here'


def test_normalizes_platform_names():
    """Test that platform names are normalized."""
    raw_output = {
        'posts': [
            {
                'date': 'Day 1',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'Twitter',
                        'caption': 'Test post',
                        'hashtags': []
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is True
    card = result['posts'][0]
    assert card['platform'] == 'x'  # Twitter normalized to 'x'


def test_detects_coaching_language():
    """Test that coaching language is detected and warned."""
    raw_output = {
        'posts': [
            {
                'date': 'Day 1',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'You should try this amazing tip. Consider posting daily.',
                        'hashtags': []
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is True
    assert 'warnings' in result
    assert any('coaching' in w.lower() for w in result['warnings'])


def test_extracts_notes_from_voice_note():
    """Test that voice_note is extracted to notes field."""
    raw_output = {
        'posts': [
            {
                'date': 'Day 1',
                'pillar': 'Educational',
                'voice_note': 'This matches your authentic voice',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'Test post',
                        'hashtags': []
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is True
    card = result['posts'][0]
    assert 'notes' in card
    assert 'This matches your authentic voice' in card['notes']


def test_fails_on_invalid_structure():
    """Test that invalid output structure fails gracefully."""
    raw_output = {
        'posts': 'not a list'
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is False
    assert 'error' in result
    assert result['error']['code'] == 'invalid_output_format'


def test_fails_on_empty_posts():
    """Test that empty posts list fails."""
    raw_output = {
        'posts': []
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is False
    assert 'error' in result
    assert result['error']['code'] == 'no_valid_posts'


def test_handles_optional_fields():
    """Test that optional fields are included when present."""
    raw_output = {
        'posts': [
            {
                'date': 'Day 1',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'Test post',
                        'hashtags': ['#test'],
                        'cta': 'Click here',
                        'media_idea': 'Photo of sunset',
                        'notes': ['Strategy note 1']
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is True
    card = result['posts'][0]
    assert card['cta'] == 'Click here'
    assert card['image_prompt'] == 'Photo of sunset'
    assert 'Strategy note 1' in card['notes']


def test_skips_invalid_cards():
    """Test that invalid cards are skipped but valid ones are kept."""
    raw_output = {
        'posts': [
            {
                'date': 'Day 1',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': '',  # Empty caption
                        'hashtags': []
                    },
                    {
                        'platform': 'facebook',
                        'caption': 'Valid post here',
                        'hashtags': []
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok'] is True
    assert len(result['posts']) == 1
    assert result['posts'][0]['platform'] == 'facebook'
