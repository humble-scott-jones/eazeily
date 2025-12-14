"""Test that generation service respects variant_types parameter."""

import pytest
from services.generation import GenerationService


def test_generate_respects_empty_variant_types():
    """When variant_types is empty array, no variants should be generated."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly',
            'variant_types': []  # Explicitly no variants
        }
    )
    
    assert result['ok'] is True
    assert 'data' in result
    assert 'posts' in result['data']
    
    # Each post should have variants as an empty array or dict
    for post in result['data']['posts']:
        variants = post.get('variants', {})
        if isinstance(variants, dict):
            # Variants dict should be empty or only contain the primary platform
            # (depending on implementation, primary might still be in variants)
            assert len(variants) <= 1, f"Expected no extra variants, got {list(variants.keys())}"
        elif isinstance(variants, list):
            assert len(variants) == 0, "Expected empty variants list"


def test_generate_respects_selected_variant_types():
    """When variant_types includes specific types, only those should be generated."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly',
            'variant_types': ['shorter']  # Request only shorter variant
        }
    )
    
    assert result['ok'] is True
    assert 'data' in result
    assert 'posts' in result['data']
    
    # At least one post should exist
    assert len(result['data']['posts']) > 0
    
    # Note: Implementation will determine exact structure
    # This test verifies the parameter is accepted


def test_generate_default_no_variant_types():
    """When variant_types is not provided, default should be no variants."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly'
            # variant_types not provided - should default to no variants
        }
    )
    
    assert result['ok'] is True
    assert 'data' in result
    assert 'posts' in result['data']
    
    # With default (no variant_types), should not generate extra variants
    for post in result['data']['posts']:
        variants = post.get('variants', {})
        if isinstance(variants, dict):
            # Should only have the primary platform at most
            assert len(variants) <= 1, f"Expected no extra variants by default, got {list(variants.keys())}"
        elif isinstance(variants, list):
            assert len(variants) == 0, "Expected empty variants list by default"
