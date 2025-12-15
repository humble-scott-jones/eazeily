"""Test that social quality gate requires structure signals."""

import pytest
from services.generation.social_quality_gate import (
    evaluate_post_quality,
    evaluate_all_posts,
    _has_structure_signal,
)


def test_numbered_list_is_structure_signal():
    """Test that numbered lists are recognized as structure signals."""
    caption_with_numbers = """
    3 steps to better content:
    
    1. Start with a strong hook
    2. Deliver clear value
    3. End with a call-to-action
    
    Try this framework today!
    """
    
    assert _has_structure_signal(caption_with_numbers)


def test_bullet_points_are_structure_signal():
    """Test that bullet points are recognized as structure signals."""
    caption_with_bullets = """
    Key takeaways from today:
    
    • Focus on value first
    • Keep it conversational
    • Always include a CTA
    
    Save this for later!
    """
    
    assert _has_structure_signal(caption_with_bullets)


def test_concrete_example_is_structure_signal():
    """Test that concrete examples are recognized as structure signals."""
    caption_with_example = """
    For example, when I started posting daily, my engagement jumped 3x.
    
    The secret? Consistency + value.
    """
    
    assert _has_structure_signal(caption_with_example)


def test_imagine_scenario_is_structure_signal():
    """Test that 'Imagine' scenarios are recognized as structure signals."""
    caption_with_imagine = """
    Imagine waking up to 100 new followers.
    
    That's what happened when I switched to this strategy.
    """
    
    assert _has_structure_signal(caption_with_imagine)


def test_myth_vs_fact_is_structure_signal():
    """Test that myth vs fact pattern is recognized."""
    caption_with_myth_fact = """
    Myth: You need 10k followers to succeed.
    Fact: Engagement matters more than follower count.
    
    Focus on building real connections.
    """
    
    assert _has_structure_signal(caption_with_myth_fact)


def test_step_markers_are_structure_signal():
    """Test that step markers (first, second, etc.) are recognized."""
    caption_with_steps = """
    First, define your audience clearly.
    Second, create content that speaks to them.
    Finally, measure and adjust.
    
    Simple but effective!
    """
    
    assert _has_structure_signal(caption_with_steps)


def test_generic_caption_fails_quality_gate():
    """Test that generic captions without structure fail quality gate."""
    generic_post = {
        'platform': 'instagram',
        'caption': 'Great tips for amazing success. Follow these awesome ideas to improve your stuff!',
        'hashtags': ['#tips', '#success']
    }
    
    result = evaluate_post_quality(generic_post)
    
    assert result['passed'] is False
    assert any('structure signal' in error.lower() for error in result['errors'])


def test_thin_caption_fails_for_instagram():
    """Test that short captions fail for Instagram."""
    thin_post = {
        'platform': 'instagram',
        'caption': 'Short post',
        'hashtags': ['#test']
    }
    
    result = evaluate_post_quality(thin_post)
    
    assert result['passed'] is False
    assert any('too short' in error.lower() for error in result['errors'])


def test_thin_caption_ok_for_twitter():
    """Test that short captions are acceptable for Twitter/X."""
    short_post = {
        'platform': 'x',
        'caption': 'Quick insight: 1. Hook 2. Value 3. CTA - simple formula for better content',
        'hashtags': ['#tips']
    }
    
    result = evaluate_post_quality(short_post)
    
    # Should pass because X allows shorter content and has structure signal
    assert result['passed'] is True


def test_rich_caption_passes_quality_gate():
    """Test that rich captions with structure pass quality gate."""
    rich_post = {
        'platform': 'instagram',
        'caption': """
        3 game-changing content tips:
        
        1. Hook in the first 3 seconds
        2. Deliver actionable value
        3. End with a clear CTA
        
        For example, my recent post used this exact framework and got 5x more engagement than usual.
        
        Save this and apply it to your next post! 🔥
        """,
        'hashtags': ['#contentcreation', '#socialmediatips']
    }
    
    result = evaluate_post_quality(rich_post)
    
    assert result['passed'] is True
    assert len(result['errors']) == 0


def test_evaluate_all_posts():
    """Test that evaluate_all_posts correctly evaluates multiple posts."""
    posts = [
        {
            'platform': 'instagram',
            'caption': """
            3 tips for better content:
            
            1. Start with a hook that stops scrolling
            2. Deliver value in every post
            3. End with a clear call-to-action
            
            These fundamentals work across all platforms. Save this for later!
            """,
            'hashtags': ['#tips']
        },
        {
            'platform': 'facebook',
            'caption': 'Short',  # Too short, no structure
            'hashtags': []
        },
        {
            'platform': 'linkedin',
            'caption': """
            First, understand your audience deeply.
            Second, create value-driven content consistently.
            Finally, engage authentically with your network.
            
            This framework transformed my LinkedIn strategy and helped me grow from 0 to 10k connections.
            """,
            'hashtags': ['#linkedin']
        }
    ]
    
    result = evaluate_all_posts(posts)
    
    assert result['passed'] is False  # One post fails
    assert len(result['results']) == 3
    assert result['results'][0]['passed'] is True  # Instagram passes
    assert result['results'][1]['passed'] is False  # Facebook fails
    assert result['results'][2]['passed'] is True  # LinkedIn passes


def test_warnings_vs_errors():
    """Test that warnings don't block but errors do."""
    post_with_warnings = {
        'platform': 'instagram',
        'caption': """
        Great tips for amazing success!
        
        1. First step is awesome
        2. Second step is incredible
        3. Third step is fantastic
        
        Try these things today!
        """,
        'hashtags': ['#tips']
    }
    
    result = evaluate_post_quality(post_with_warnings)
    
    # Should pass (has structure signal) but have warnings about generic language
    assert result['passed'] is True
    assert len(result['warnings']) > 0
    assert any('generic' in warning.lower() for warning in result['warnings'])
