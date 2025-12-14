"""Test that validator enforces valid hashtag format and counts.

Rules:
- No slashes in hashtags
- No spaces in hashtags
- Instagram: 8-12 hashtags recommended
"""

import pytest
from services.generation.social_validator import (
    validate_hashtags,
    validate_post_card,
)


def test_rejects_hashtag_with_slash():
    """Test that hashtags with slashes are rejected."""
    hashtags = ['#marketing', '#social/media', '#tips']
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is not None
    assert 'slash' in error.lower()
    assert '#social/media' in error


def test_rejects_hashtag_with_space():
    """Test that hashtags with spaces are rejected."""
    hashtags = ['#marketing', '#social media', '#tips']
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is not None
    assert 'space' in error.lower()


def test_rejects_too_few_hashtags_instagram():
    """Test that Instagram posts with < 8 hashtags are flagged."""
    hashtags = ['#marketing', '#tips', '#business']
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is not None
    assert '8-12' in error or '8' in error
    assert 'instagram' in error.lower()


def test_rejects_too_many_hashtags_instagram():
    """Test that Instagram posts with > 12 hashtags are flagged."""
    hashtags = [
        '#one', '#two', '#three', '#four', '#five',
        '#six', '#seven', '#eight', '#nine', '#ten',
        '#eleven', '#twelve', '#thirteen', '#fourteen'
    ]
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is not None
    assert '8-12' in error or '12' in error
    assert 'instagram' in error.lower()


def test_accepts_valid_instagram_hashtags():
    """Test that valid Instagram hashtags (8-12) pass."""
    hashtags = [
        '#marketing', '#socialmedia', '#contentcreator', '#business',
        '#entrepreneur', '#digitalmarketing', '#growth', '#success',
        '#strategy', '#engagement'
    ]
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is None


def test_accepts_hashtags_without_hash_symbol():
    """Test that hashtags work with or without leading # symbol."""
    hashtags = [
        'marketing', 'socialmedia', 'contentcreator', 'business',
        'entrepreneur', 'digitalmarketing', 'growth', 'success',
        'strategy', 'engagement'
    ]
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is None


def test_no_count_restriction_for_facebook():
    """Test that Facebook doesn't have strict hashtag count requirements."""
    hashtags = ['#marketing', '#tips', '#business']  # Only 3
    
    error = validate_hashtags(hashtags, 'facebook')
    
    assert error is None  # Should be OK for Facebook


def test_no_count_restriction_for_linkedin():
    """Test that LinkedIn doesn't have strict hashtag count requirements."""
    hashtags = ['#marketing', '#leadership']  # Only 2
    
    error = validate_hashtags(hashtags, 'linkedin')
    
    assert error is None  # Should be OK for LinkedIn


def test_empty_hashtags_allowed():
    """Test that empty hashtags list is allowed."""
    hashtags = []
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is None  # Empty is OK (some posts don't need hashtags)


def test_post_card_fails_with_invalid_hashtags():
    """Test that post card validation fails with invalid hashtags."""
    post = {
        'platform': 'instagram',
        'caption': """
        3 proven strategies for better engagement:
        
        1. Hook that stops scrolling
        2. Clear value delivery
        3. Strong call-to-action
        
        For example, this framework doubled my engagement last week.
        """,
        'hashtags': ['#marketing', '#social/media', '#tips']  # Has slash
    }
    
    result = validate_post_card(post)
    
    assert result['passed'] is False
    assert any('slash' in error.lower() for error in result['errors'])


def test_post_card_fails_with_wrong_hashtag_count():
    """Test that Instagram post fails with wrong hashtag count."""
    post = {
        'platform': 'instagram',
        'caption': """
        3 proven strategies for better engagement:
        
        1. Hook that stops scrolling
        2. Clear value delivery
        3. Strong call-to-action
        
        For example, this framework doubled my engagement last week.
        """,
        'hashtags': ['#marketing', '#tips']  # Too few for Instagram
    }
    
    result = validate_post_card(post)
    
    assert result['passed'] is False
    assert any('instagram' in error.lower() and '8-12' in error 
              for error in result['errors'])


def test_post_card_passes_with_valid_hashtags():
    """Test that post card passes with valid hashtags."""
    post = {
        'platform': 'instagram',
        'caption': """
        3 proven strategies for better engagement:
        
        1. Hook that stops scrolling
        2. Clear value delivery
        3. Strong call-to-action
        
        For example, this framework doubled my engagement last week.
        """,
        'hashtags': [
            '#marketing', '#socialmedia', '#contentcreator', '#business',
            '#entrepreneur', '#digitalmarketing', '#growth', '#success',
            '#strategy', '#engagement'
        ]
    }
    
    result = validate_post_card(post)
    
    assert result['passed'] is True
    assert len(result['errors']) == 0


def test_validates_hashtag_type():
    """Test that non-string hashtags are rejected."""
    hashtags = ['#valid', 123, '#another']  # Has integer
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is not None
    assert 'string' in error.lower()


def test_multiple_format_issues():
    """Test detection of multiple hashtag format issues."""
    hashtags = [
        '#valid',
        '#has space',
        '#has/slash',
        '#another valid'  # Another space
    ]
    
    # Should catch the first issue encountered
    error = validate_hashtags(hashtags, 'facebook')
    
    assert error is not None
    # Should catch either space or slash
    assert 'space' in error.lower() or 'slash' in error.lower()


def test_exactly_8_hashtags_instagram():
    """Test that exactly 8 hashtags is valid for Instagram."""
    hashtags = [
        '#one', '#two', '#three', '#four',
        '#five', '#six', '#seven', '#eight'
    ]
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is None


def test_exactly_12_hashtags_instagram():
    """Test that exactly 12 hashtags is valid for Instagram."""
    hashtags = [
        '#one', '#two', '#three', '#four',
        '#five', '#six', '#seven', '#eight',
        '#nine', '#ten', '#eleven', '#twelve'
    ]
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is None


def test_hashtag_with_numbers_allowed():
    """Test that hashtags with numbers are allowed."""
    hashtags = [
        '#marketing101', '#tip2024', '#success3x', '#strategy4u',
        '#business5star', '#growth6month', '#top7tips', '#best8ways',
        '#proven9steps', '#ultimate10x'
    ]
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is None


def test_hashtag_with_underscore_allowed():
    """Test that hashtags with underscores are allowed."""
    hashtags = [
        '#social_media', '#content_creator', '#digital_marketing', '#business_growth',
        '#brand_strategy', '#online_business', '#success_tips', '#growth_hacking',
        '#marketing_tips', '#instagram_growth'
    ]
    
    error = validate_hashtags(hashtags, 'instagram')
    
    assert error is None
