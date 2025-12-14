"""Test that generator never returns coaching language in captions."""

import pytest
from services.generation import GenerationService
from services.generation.social_post_ready_pipeline import _contains_coaching_language


def test_fallback_generator_no_coaching_phrases():
    """Test that fallback generator does not include coaching phrases in captions."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram', 'linkedin'],
            'tone': 'professional',
        }
    )
    
    assert result['ok'] is True
    assert 'data' in result
    
    posts = result['data'].get('posts', [])
    assert len(posts) > 0, "Should generate at least one post"
    
    # Check each caption for coaching language
    for post in posts:
        caption = post.get('caption', '')
        assert not _contains_coaching_language(caption), (
            f"Caption contains coaching language: {caption}"
        )


def test_coaching_phrases_detected():
    """Test that our coaching detection catches common phrases."""
    coaching_examples = [
        "You should post daily to grow your audience",
        "Consider adding more hashtags to your posts",
        "Here's what to say when promoting your product",
        "Try to engage with your followers every day",
        "Make sure to include a call-to-action",
        "Don't forget to tag relevant accounts",
    ]
    
    for example in coaching_examples:
        assert _contains_coaching_language(example), (
            f"Failed to detect coaching in: {example}"
        )


def test_non_coaching_phrases_pass():
    """Test that normal post content doesn't trigger false positives."""
    normal_examples = [
        "Here's my top 3 tips for better content:\n1. Hook\n2. Value\n3. CTA",
        "I should have started this years ago! Game-changing results.",
        "Considering a rebrand? Here's what worked for us.",
        "Try this simple framework: Problem → Solution → Action",
    ]
    
    for example in normal_examples:
        assert not _contains_coaching_language(example), (
            f"False positive for: {example}"
        )


def test_quality_gate_rejects_coaching():
    """Test that quality gate rejects posts with coaching language."""
    from services.generation.social_quality_gate import evaluate_post_quality
    
    post_with_coaching = {
        'platform': 'instagram',
        'caption': 'You should try these tips. Consider posting daily. Make sure to engage.',
        'hashtags': ['#tips']
    }
    
    result = evaluate_post_quality(post_with_coaching)
    
    assert result['passed'] is False
    assert any('coaching' in error.lower() for error in result['errors'])


def test_multiple_platforms_no_coaching():
    """Test that coaching is avoided across all platforms."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram', 'facebook', 'linkedin', 'x'],
            'tone': 'friendly',
        }
    )
    
    assert result['ok'] is True
    posts = result['data'].get('posts', [])
    
    for post in posts:
        platform = post.get('platform', 'unknown')
        caption = post.get('caption', '')
        
        assert not _contains_coaching_language(caption), (
            f"{platform} caption contains coaching language: {caption}"
        )
