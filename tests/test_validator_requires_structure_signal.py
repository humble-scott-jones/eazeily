"""Test that validator requires structure signals in captions.

Structure signals include:
- Numbered steps (1-3+)
- Checklist/bullet points
- Myth vs fact pattern
- Concrete examples
"""

import pytest
from services.generation.social_validator import (
    has_structure_signal,
    validate_post_card,
)


def test_numbered_list_is_structure_signal():
    """Test that numbered lists are recognized as structure signals."""
    caption = """
    3 steps to better content:
    
    1. Start with a strong hook
    2. Deliver clear value
    3. End with a call-to-action
    
    Try this framework today!
    """
    
    assert has_structure_signal(caption)


def test_bullet_points_are_structure_signal():
    """Test that bullet points are recognized as structure signals."""
    caption = """
    Key takeaways from today:
    
    • Focus on value first
    • Keep it conversational
    • Always include a CTA
    
    Save this for later!
    """
    
    assert has_structure_signal(caption)


def test_dash_bullets_are_structure_signal():
    """Test that dash bullets are recognized as structure signals."""
    caption = """
    Key takeaways:
    
    - Focus on value first
    - Keep it conversational
    - Always include a CTA
    """
    
    assert has_structure_signal(caption)


def test_asterisk_bullets_are_structure_signal():
    """Test that asterisk bullets are recognized as structure signals."""
    caption = """
    Key takeaways:
    
    * Focus on value first
    * Keep it conversational
    * Always include a CTA
    """
    
    assert has_structure_signal(caption)


def test_concrete_example_is_structure_signal():
    """Test that concrete examples are recognized as structure signals."""
    caption = """
    For example, when I started posting daily, my engagement jumped 3x.
    
    The secret? Consistency + value.
    """
    
    assert has_structure_signal(caption)


def test_imagine_scenario_is_structure_signal():
    """Test that 'Imagine' scenarios are recognized as structure signals."""
    caption = """
    Imagine waking up to 100 new followers.
    
    That's what happened when I switched to this strategy.
    """
    
    assert has_structure_signal(caption)


def test_myth_vs_fact_is_structure_signal():
    """Test that myth vs fact pattern is recognized."""
    caption = """
    Myth: You need 10k followers to succeed.
    Fact: Engagement matters more than follower count.
    
    Focus on building real connections.
    """
    
    assert has_structure_signal(caption)


def test_step_markers_are_structure_signal():
    """Test that step markers (first, second, etc.) are recognized."""
    caption = """
    First, define your audience clearly.
    Second, create content that speaks to them.
    Finally, measure and adjust.
    
    Simple but effective!
    """
    
    assert has_structure_signal(caption)


def test_step_number_is_structure_signal():
    """Test that 'Step 1', 'Step 2' pattern is recognized."""
    caption = """
    Step 1: Define your goal
    Step 2: Create your plan
    Step 3: Execute consistently
    
    This works every time.
    """
    
    assert has_structure_signal(caption)


def test_generic_caption_has_no_structure_signal():
    """Test that generic captions without structure are detected."""
    caption = "Great tips for amazing success. Follow these awesome ideas!"
    
    assert not has_structure_signal(caption)


def test_thin_caption_has_no_structure_signal():
    """Test that thin captions have no structure signal."""
    caption = "Check out this content strategy."
    
    assert not has_structure_signal(caption)


def test_post_card_fails_without_structure():
    """Test that post card fails validation without structure signal."""
    post = {
        'platform': 'instagram',
        'caption': """
        Great tips for social media success! 
        Build amazing content that drives engagement and growth.
        Follow for more inspiration!
        """,
        'hashtags': [
            '#socialmedia', '#marketing', '#contentcreator', '#business',
            '#entrepreneur', '#success', '#tips', '#growth',
            '#strategy', '#engagement'
        ]
    }
    
    result = validate_post_card(post)
    
    assert result['passed'] is False
    assert any('structure signal' in error.lower() for error in result['errors'])


def test_post_card_passes_with_numbered_list():
    """Test that post card passes with numbered list."""
    post = {
        'platform': 'instagram',
        'caption': """
        3 proven strategies for better engagement:
        
        1. Hook that stops scrolling
        2. Clear value delivery
        3. Strong call-to-action
        
        Save this for your next post!
        """,
        'hashtags': [
            '#socialmedia', '#marketing', '#contentcreator', '#business',
            '#entrepreneur', '#success', '#tips', '#growth',
            '#strategy', '#engagement'
        ]
    }
    
    result = validate_post_card(post)
    
    assert result['passed'] is True


def test_post_card_passes_with_example():
    """Test that post card passes with concrete example."""
    post = {
        'platform': 'linkedin',
        'caption': """
        The power of consistency in content creation cannot be overstated.
        
        For example, when I committed to posting daily for 30 days, my engagement 
        increased by 300% and I gained 5,000 new followers. The key was showing up 
        every single day, even when I didn't feel like it.
        
        What's stopping you from starting your consistency journey today?
        """,
        'hashtags': [
            '#linkedin', '#contentmarketing', '#consistency', '#growth',
            '#socialmedia', '#business', '#entrepreneur', '#success'
        ]
    }
    
    result = validate_post_card(post)
    
    assert result['passed'] is True


def test_post_card_passes_with_myth_fact():
    """Test that post card passes with myth vs fact structure."""
    post = {
        'platform': 'instagram',
        'caption': """
        Let's bust a common social media myth:
        
        Myth: You need 10,000 followers to be successful on Instagram.
        Fact: Micro-influencers with 1,000-10,000 followers often have higher 
        engagement rates and more authentic connections than mega-influencers.
        
        Focus on engagement, not just follower count.
        """,
        'hashtags': [
            '#socialmedia', '#instagram', '#myths', '#facts',
            '#engagement', '#influence', '#authentic', '#growth',
            '#marketing', '#tips'
        ]
    }
    
    result = validate_post_card(post)
    
    assert result['passed'] is True


def test_parentheses_numbered_list():
    """Test that numbered list with parentheses works: 1) 2) 3)"""
    caption = """
    3 essential tips:
    
    1) Start with value
    2) Be consistent
    3) Engage authentically
    """
    
    assert has_structure_signal(caption)


def test_case_insensitive_for_example():
    """Test that 'For Example' is case-insensitive."""
    caption = "FOR EXAMPLE, I doubled my engagement by posting daily."
    
    assert has_structure_signal(caption)


def test_case_insensitive_imagine():
    """Test that 'Imagine' is case-insensitive."""
    caption = "IMAGINE waking up to 1000 new followers every morning."
    
    assert has_structure_signal(caption)


def test_case_insensitive_step_markers():
    """Test that step markers are case-insensitive."""
    caption = """
    FIRST, define your goals.
    SECOND, create your strategy.
    FINALLY, execute with consistency.
    """
    
    assert has_structure_signal(caption)
