"""Tests for output schema enforcing post-ready format.

Verifies that:
1. Captions contain ONLY final copy (no coaching/guidance)
2. Strategy notes are separated into notes[] field
3. Output schema includes all required fields
"""

import pytest
from services.generation.output_schemas import (
    SocialPostCard,
    validate_social_posts,
    UsedSignals
)
from services.generation.social_post_ready_pipeline import (
    normalize_and_guardrail,
    _contains_coaching_language
)


def test_caption_has_no_coaching_language():
    """Test that valid captions don't trigger coaching detection."""
    good_captions = [
        "Transform your look with our expert color services. Book today! 💇",
        "Here's what makes our salon different: certified stylists, premium products, personalized service.",
        "Ready for a change? Our team specializes in dramatic transformations.",
        "3 signs you need a hair consultation:\n1. Split ends\n2. Dull color\n3. Flat, lifeless hair"
    ]
    
    for caption in good_captions:
        assert not _contains_coaching_language(caption), f"False positive on: {caption}"


def test_coaching_language_detected():
    """Test that coaching/guidance language is properly detected."""
    bad_captions = [
        "You should post about your hair transformation journey.",
        "Make sure to mention your stylist's credentials.",
        "Here are some ideas for your next post about hair care.",
        "Consider posting before/after photos.",
        "Don't forget to include a call to action.",
        "Tip: Always show the process behind your work."
    ]
    
    for caption in bad_captions:
        assert _contains_coaching_language(caption), f"Missed coaching language in: {caption}"


def test_social_post_card_schema():
    """Test that SocialPostCard has required structure."""
    card: SocialPostCard = {
        'platform': 'instagram',
        'caption': 'Ready for a hair transformation? Book your consultation today!',
        'hashtags': ['#HairTransformation', '#SalonLife'],
        'cta': 'Book now',
        'notes': ['Educational angle works well for this audience']
    }
    
    # Required fields
    assert 'platform' in card
    assert 'caption' in card
    assert 'hashtags' in card
    
    # Optional fields
    assert 'cta' in card
    assert 'notes' in card
    
    # Caption should be paste-ready
    assert not _contains_coaching_language(card['caption'])


def test_notes_separate_from_caption():
    """Test that notes are kept separate from caption."""
    raw_output = {
        'posts': [
            {
                'date': '2024-01-15',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'Transform your look! Book today.',
                        'hashtags': ['#Salon']
                    }
                ],
                'voice_note': 'This educational angle resonates with first-time clients'
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok']
    assert len(result['posts']) > 0
    
    first_card = result['posts'][0]
    # Caption should be clean
    assert 'Transform your look! Book today.' in first_card['caption']
    # Notes should be preserved separately
    assert 'notes' in first_card
    assert 'educational angle' in first_card['notes'][0].lower()


def test_validate_social_posts_requires_posts():
    """Test that validation requires non-empty posts list."""
    with pytest.raises(ValueError, match="non-empty 'posts' list"):
        validate_social_posts({'posts': []})
    
    with pytest.raises(ValueError, match="contain non-empty 'posts' list"):
        validate_social_posts({})


def test_validate_social_posts_requires_card_fields():
    """Test that validation requires platform and caption in each card."""
    invalid_data = {
        'posts': [
            {
                'date': '2024-01-15',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram'
                        # Missing caption
                    }
                ]
            }
        ]
    }
    
    with pytest.raises(ValueError, match="platform.*caption"):
        validate_social_posts(invalid_data)


def test_validate_social_posts_rejects_empty_captions():
    """Test that validation rejects empty or whitespace-only captions."""
    invalid_data = {
        'posts': [
            {
                'date': '2024-01-15',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': '   '  # Whitespace only
                    }
                ]
            }
        ]
    }
    
    with pytest.raises(ValueError, match="non-empty string"):
        validate_social_posts(invalid_data)


def test_used_signals_includes_custom_chips():
    """Test that UsedSignals schema includes custom_chips_used field."""
    signals: UsedSignals = {
        'services_used': ['Haircuts', 'Color'],
        'pains_used': ['Finding trusted stylist'],
        'outcomes_used': ['Healthy hair'],
        'proof_used': ['10+ years'],
        'differentiators_used': ['Certified team'],
        'custom_chips_used': ['VIP Package']
    }
    
    # All fields should be present
    assert 'services_used' in signals
    assert 'custom_chips_used' in signals
    assert len(signals['custom_chips_used']) == 1


def test_normalize_extracts_hashtags_from_caption():
    """Test that embedded hashtags are extracted to separate field."""
    raw_output = {
        'posts': [
            {
                'date': '2024-01-15',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'instagram',
                        'caption': 'Transform your look today!\n\n#HairTransformation #SalonLife #BeautyTips',
                        'hashtags': []
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok']
    card = result['posts'][0]
    
    # Caption should not contain hashtag line
    assert '#HairTransformation' not in card['caption']
    
    # Hashtags should be in separate list
    assert len(card['hashtags']) > 0
    assert '#HairTransformation' in card['hashtags']


def test_platform_names_normalized():
    """Test that platform names are normalized to standard format."""
    raw_output = {
        'posts': [
            {
                'date': '2024-01-15',
                'pillar': 'Educational',
                'cards': [
                    {
                        'platform': 'Twitter',  # Should become 'x'
                        'caption': 'Quick tip!',
                        'hashtags': []
                    },
                    {
                        'platform': 'IG',  # Should become 'instagram'
                        'caption': 'Transform today!',
                        'hashtags': []
                    }
                ]
            }
        ]
    }
    
    result = normalize_and_guardrail(raw_output)
    
    assert result['ok']
    assert len(result['posts']) == 2
    
    platforms = [card['platform'] for card in result['posts']]
    assert 'x' in platforms
    assert 'instagram' in platforms
    assert 'Twitter' not in platforms
    assert 'IG' not in platforms
