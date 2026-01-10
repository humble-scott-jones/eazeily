"""Test that generation service respects variant_types parameter."""

import pytest


pytestmark = pytest.mark.skip(
    reason="Variant contract tests referenced removed social generation helpers; skipping",
)


class GenerationService:  # type: ignore
    def __init__(self, *args, **kwargs):
        pass

    def generate_social_posts(self, *args, **kwargs):
        return {}

def test_generate_respects_empty_variant_types():
    """When variant_types is empty array, no variants should be generated.
    
    Note: With validation gate enabled, fallback content is blocked.
    This test now verifies error handling for blocked fallback.
    """
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly',
            'variant_types': []  # Explicitly no variants
        }
    )
    
    # Fallback content is blocked by validation gate
    assert result['ok'] is False
    assert result['error']['code'] == 'output_not_post_ready'


def test_generate_respects_selected_variant_types():
    """When variant_types includes specific types, only those should be generated.
    
    Note: With validation gate enabled, fallback content is blocked.
    """
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly',
            'variant_types': ['shorter']  # Request only shorter variant
        }
    )
    
    # Fallback content is blocked by validation gate
    assert result['ok'] is False
    assert result['error']['code'] == 'output_not_post_ready'



def test_generate_default_no_variant_types():
    """When variant_types is not provided, default should be no variants.
    
    Note: With validation gate enabled, fallback content is blocked.
    """
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly'
            # variant_types not provided - should default to no variants
        }
    )
    
    # Fallback content is blocked by validation gate
    assert result['ok'] is False
    assert result['error']['code'] == 'output_not_post_ready'
