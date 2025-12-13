"""Contract tests for generation service."""

import pytest
from services.generation import GenerationService


def test_generate_social_posts_contract():
    """Test that generate_social_posts returns expected contract."""
    service = GenerationService(enable_openai=False)  # Use fallback only
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly'
        }
    )
    
    # Check success response contract
    assert 'ok' in result
    assert 'request_id' in result
    
    if result['ok']:
        # Success contract
        assert result['openai_used'] is False
        assert result['fallback_used'] is True
        assert 'data' in result
        assert 'posts' in result['data']
        assert len(result['data']['posts']) > 0
        
        # Check post structure
        post = result['data']['posts'][0]
        assert 'date' in post
        assert 'pillar' in post
        assert 'cards' in post
        assert len(post['cards']) > 0
        
        # Check card structure
        card = post['cards'][0]
        assert 'platform' in card
        assert 'caption' in card
        assert 'hashtags' in card
    else:
        # Error contract
        assert 'error' in result
        assert 'code' in result['error']
        assert 'message' in result['error']


def test_generate_reel_script_contract():
    """Test that generate_reel_script returns expected contract."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_reel_script(
        request={
            'hook_style': 'question',
            'format': 'tutorial',
            'duration': 30
        }
    )
    
    assert 'ok' in result
    assert 'request_id' in result
    
    if result['ok']:
        assert result['openai_used'] is False
        assert 'data' in result
        assert 'script' in result['data']
        
        script = result['data']['script']
        assert 'hook' in script
        assert 'beats' in script
        assert 'cta' in script
        assert 'caption' in script
        assert 'hashtags' in script
        
        # Hook and CTA should be non-empty
        assert len(script['hook']) > 0
        assert len(script['cta']) > 0
    else:
        assert 'error' in result
        assert 'code' in result['error']
        assert 'message' in result['error']


def test_generate_review_response_contract():
    """Test that generate_review_response returns expected contract."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_review_response(
        request={
            'review_text': 'Great service! Very happy with the results.',
            'rating': 5,
            'tone': 'professional'
        }
    )
    
    assert 'ok' in result
    assert 'request_id' in result
    
    if result['ok']:
        assert result['openai_used'] is False
        assert 'data' in result
        assert 'responses' in result['data']
        
        responses = result['data']['responses']
        # Should have at least one variant
        assert 'short' in responses or 'medium' in responses or 'long' in responses
        
        # All present variants should be non-empty strings
        for key in ['short', 'medium', 'long']:
            if key in responses:
                assert isinstance(responses[key], str)
                assert len(responses[key]) > 0
    else:
        assert 'error' in result
        assert 'code' in result['error']
        assert 'message' in result['error']


def test_social_posts_request_id_always_present():
    """Test that request_id is always present in response."""
    service = GenerationService(enable_openai=False)
    
    # Success case
    result = service.generate_social_posts(
        request={'session_length': 1, 'platforms': ['instagram']}
    )
    assert 'request_id' in result
    assert isinstance(result['request_id'], str)
    assert len(result['request_id']) > 0
    
    # Error case (missing review text)
    result2 = service.generate_review_response(request={})
    assert 'request_id' in result2
    assert isinstance(result2['request_id'], str)


def test_social_posts_never_returns_empty():
    """Test that social posts never returns empty posts array."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 7,
            'platforms': ['instagram', 'facebook'],
            'tone': 'professional'
        }
    )
    
    assert result['ok'] is True
    assert 'data' in result
    assert 'posts' in result['data']
    assert len(result['data']['posts']) > 0
    
    # Each post should have content
    for post in result['data']['posts']:
        assert len(post['cards']) > 0
        for card in post['cards']:
            assert len(card['caption']) > 0


def test_reel_script_never_returns_empty_hook():
    """Test that reel scripts always have non-empty hooks and CTAs."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_reel_script(
        request={'duration': 30}
    )
    
    assert result['ok'] is True
    script = result['data']['script']
    
    assert 'hook' in script
    assert len(script['hook']) > 0
    assert 'cta' in script
    assert len(script['cta']) > 0


def test_review_response_validation_error():
    """Test that missing required fields return validation error."""
    service = GenerationService(enable_openai=False)
    
    # Missing review_text
    result = service.generate_review_response(
        request={'rating': 5}
    )
    
    assert result['ok'] is False
    assert result['error']['code'] == 'validation_error'
    assert 'review text' in result['error']['message'].lower()


def test_social_posts_with_voice_samples():
    """Test social posts generation with voice samples."""
    service = GenerationService(enable_openai=False)
    
    voice_samples = [
        "We celebrate every small win with our amazing team!",
        "Quick tip: consistency beats perfection every time.",
        "Your feedback shapes our roadmap—drop ideas below!"
    ]
    
    result = service.generate_social_posts(
        request={'session_length': 1, 'platforms': ['instagram']},
        voice_samples=voice_samples
    )
    
    assert result['ok'] is True
    assert 'summary' in result
    # Voice was applied
    assert result['summary']['voice_applied'] is True


def test_review_response_with_brand_voice():
    """Test review response with brand voice enabled."""
    service = GenerationService(enable_openai=False)
    
    voice_samples = [
        "We're so grateful for your support!",
        "Your experience matters deeply to us.",
        "Thank you for being part of our community!"
    ]
    
    result = service.generate_review_response(
        request={
            'review_text': 'Amazing service!',
            'rating': 5,
            'use_brand_voice': True
        },
        voice_samples=voice_samples
    )
    
    assert result['ok'] is True
    assert 'summary' in result
    assert result['summary']['voice_applied'] is True


def test_review_response_without_brand_voice():
    """Test that voice samples are ignored when use_brand_voice=False."""
    service = GenerationService(enable_openai=False)
    
    voice_samples = ["Sample text"]
    
    result = service.generate_review_response(
        request={
            'review_text': 'Good service',
            'rating': 4,
            'use_brand_voice': False
        },
        voice_samples=voice_samples
    )
    
    assert result['ok'] is True
    assert 'summary' in result
    # Voice should NOT be applied
    assert result['summary']['voice_applied'] is False


def test_warnings_for_sensitive_content():
    """Test that sensitive content triggers warnings."""
    service = GenerationService(enable_openai=False)
    
    # Note: The fallback generator shouldn't produce sensitive content,
    # but we can test the mechanism by checking the warnings field exists
    result = service.generate_social_posts(
        request={'session_length': 1, 'platforms': ['instagram']}
    )
    
    assert result['ok'] is True
    # Warnings field should be present (even if None)
    assert 'warnings' in result
