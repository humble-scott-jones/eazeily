"""Tests for GenerationService integration with PromptCompiler."""

import pytest
from services.generation.generation_service import GenerationService


def test_generation_service_with_compiler_social():
    """Test social generation with PromptCompiler."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    workspace = {
        'company_name': 'Test Co',
        'industry': 'tech',
        'default_tone': 'professional',
        'platforms': ['instagram']
    }
    
    request = {
        'session_length': 7,
        'tone': 'friendly',
        'platforms': ['instagram', 'facebook'],
        'keywords': ['innovation'],
        'goals': ['engagement']
    }
    
    result = service.generate_with_compiler(
        content_type='social',
        workspace=workspace,
        request=request
    )
    
    # Should succeed
    assert result['ok'] is True
    assert result['data'] is not None
    assert 'posts' in result['data']
    assert result['summary']['prompt_compiler_used'] is True


def test_generation_service_with_compiler_reels():
    """Test reel generation with PromptCompiler."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    request = {
        'session_length': 1,
        'tone': 'energetic',
        'reel_options': {
            'hook_style': 'question',
            'duration': 30
        }
    }
    
    result = service.generate_with_compiler(
        content_type='reels',
        request=request
    )
    
    # Should succeed
    assert result['ok'] is True
    assert result['data'] is not None
    assert 'script' in result['data']


def test_generation_service_with_compiler_reviews():
    """Test review response with PromptCompiler."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    workspace = {
        'company_name': 'Happy Cafe',
        'default_tone': 'friendly'
    }
    
    request = {
        'tone': 'warm'
    }
    
    result = service.generate_with_compiler(
        content_type='reviews',
        workspace=workspace,
        request=request,
        review_text='Great coffee!',
        rating=5
    )
    
    # Should succeed
    assert result['ok'] is True
    assert result['data'] is not None
    assert 'responses' in result['data']


def test_generation_service_with_voice_samples():
    """Test generation with voice samples."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    voice_samples = [
        "Quick wins matter! Let's celebrate small victories.",
        "Your feedback helps us grow. Drop a comment below!",
        "We're here to make your life easier, one step at a time."
    ]
    
    request = {
        'session_length': 7,
        'platforms': ['instagram']
    }
    
    result = service.generate_with_compiler(
        content_type='social',
        voice_samples=voice_samples,
        include_phrases=['celebrate', 'grow'],
        avoid_phrases=['synergy'],
        request=request
    )
    
    # Should succeed with voice applied
    assert result['ok'] is True
    assert result['summary']['voice_applied'] is True


def test_generation_service_missing_review_text():
    """Test that missing review text returns error."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    result = service.generate_with_compiler(
        content_type='reviews',
        request={'tone': 'professional'}
        # Missing review_text
    )
    
    # Should return error
    assert result['ok'] is False
    assert result['error']['code'] == 'missing_parameter'


def test_generation_service_invalid_content_type():
    """Test that invalid content type returns error."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    result = service.generate_with_compiler(
        content_type='invalid_type',
        request={'session_length': 7}
    )
    
    # Should return error
    assert result['ok'] is False
    assert result['error']['code'] == 'invalid_content_type'


def test_generation_service_conversion_helpers():
    """Test that conversion helper methods work correctly."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    # Test workspace conversion
    workspace = {
        'company_name': 'Convert Test',
        'industry': 'retail',
        'default_tone': 'casual',
        'platforms': ['facebook'],
        'offerings': 'Products',
        'audience': 'Everyone'
    }
    
    profile_defaults = service._convert_to_profile_defaults(workspace)
    assert profile_defaults['company'] == 'Convert Test'
    assert profile_defaults['industry'] == 'retail'
    assert profile_defaults['signature_tone'] == 'casual'
    
    # Test request conversion
    request = {
        'session_length': 30,
        'platforms': ['instagram'],
        'tone': 'friendly',
        'keywords': ['test'],
        'goals': ['engagement']
    }
    
    run_toggles = service._convert_to_run_toggles(request)
    assert run_toggles['session_length'] == 30
    assert run_toggles['platform_focus'] == ['instagram']
    assert run_toggles['tone_override'] == 'friendly'


def test_generation_service_fallback_coverage():
    """Test fallback generation for all content types."""
    service = GenerationService(enable_openai=False, use_prompt_compiler=True)
    
    model_context = {
        'company_name': 'Fallback Test',
        'industry': 'tech',
        'tone': 'professional',
        'platforms': ['instagram'],
        'session_length': 7
    }
    
    # Social fallback
    social_data = service._generate_fallback('social', model_context)
    assert 'posts' in social_data
    
    # Reels fallback
    reels_data = service._generate_fallback('reels', model_context)
    assert 'script' in reels_data
    
    # Reviews fallback
    reviews_data = service._generate_fallback(
        'reviews',
        model_context,
        review_text='Test review',
        rating=4
    )
    assert 'responses' in reviews_data
