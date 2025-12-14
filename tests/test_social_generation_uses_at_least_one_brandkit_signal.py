"""Tests that social generation incorporates Brand Kit signals as required.

Tests verify that when Brand Kit is present (services, audience, proof, differentiators),
the prompt compiler includes these signals in prompts with explicit MUST USE rules:
- Each post MUST include at least ONE: service mention OR differentiator OR proof point
- Each post MUST include at least ONE: pain/outcome reference OR audience callout

Also tests tier evaluation, backward compatibility, and integration with brand inspiration.
"""

import pytest
from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles


def test_prompt_includes_brand_kit_services():
    """Test that social prompt includes Brand Kit services when present."""
    profile_defaults: ProfileDefaults = {
        'company': 'Growth Agency',
        'industry': 'marketing',
        'signature_tone': 'professional',
        'platforms': ['instagram'],
        'brand_kit': {
            'services': ['SEO consulting', 'Content strategy', 'Link building'],
            'audience_role': 'Small business owners'
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    
    run_toggles: RunToggles = {
        'session_length': 7,
        'platform_focus': ['instagram']
    }
    
    output = compiler.compile_for_social(run_toggles)
    
    # Check that brand_kit is in model context
    assert output['model_context']['brand_kit_applied'] is True
    assert output['model_context']['brand_kit'] is not None
    assert 'services' in output['model_context']['brand_kit']
    
    # Check that prompt includes services
    context_section = output['prompt_set']['context']
    assert 'SEO consulting' in context_section
    assert 'Content strategy' in context_section


def test_prompt_includes_brand_kit_audience_signals():
    """Test that social prompt includes audience signals (pain/outcome)."""
    profile_defaults: ProfileDefaults = {
        'company': 'Fit Studio',
        'industry': 'fitness',
        'signature_tone': 'energetic',
        'platforms': ['instagram'],
        'brand_kit': {
            'services': ['Personal training'],
            'audience_role': 'Busy professionals',
            'audience_pain': 'No time for gym',
            'audience_outcome': 'Get fit in 30 min/day'
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    
    run_toggles: RunToggles = {
        'session_length': 7
    }
    
    output = compiler.compile_for_social(run_toggles)
    
    # Check prompt includes audience signals
    context_section = output['prompt_set']['context']
    assert 'Busy professionals' in context_section
    assert 'No time for gym' in context_section
    assert 'Get fit in 30 min/day' in context_section


def test_prompt_includes_brand_kit_proof():
    """Test that social prompt includes proof points."""
    profile_defaults: ProfileDefaults = {
        'company': 'Law Firm',
        'industry': 'legal',
        'signature_tone': 'professional',
        'platforms': ['linkedin'],
        'brand_kit': {
            'services': ['Business law', 'Contract review'],
            'proof': ['20 years experience', '500+ clients served', 'AV-rated']
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    
    run_toggles: RunToggles = {
        'session_length': 7
    }
    
    output = compiler.compile_for_social(run_toggles)
    
    # Check prompt includes proof
    context_section = output['prompt_set']['context']
    assert '20 years experience' in context_section
    assert '500+ clients served' in context_section


def test_prompt_includes_brand_kit_differentiators():
    """Test that social prompt includes differentiators."""
    profile_defaults: ProfileDefaults = {
        'company': 'Design Studio',
        'industry': 'design',
        'signature_tone': 'creative',
        'platforms': ['instagram'],
        'brand_kit': {
            'services': ['Brand design', 'Web design'],
            'differentiators': ['Award-winning team', 'Fast turnaround', 'Unlimited revisions']
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    
    run_toggles: RunToggles = {
        'session_length': 7
    }
    
    output = compiler.compile_for_social(run_toggles)
    
    # Check prompt includes differentiators
    context_section = output['prompt_set']['context']
    assert 'Award-winning team' in context_section
    assert 'Fast turnaround' in context_section


def test_prompt_includes_must_use_rules():
    """Test that prompt includes MUST USE content requirements."""
    profile_defaults: ProfileDefaults = {
        'company': 'Consulting Co',
        'industry': 'business',
        'signature_tone': 'professional',
        'platforms': ['linkedin'],
        'brand_kit': {
            'services': ['Strategy consulting'],
            'audience_role': 'CEOs',
            'audience_pain': 'Unclear growth path',
            'proof': ['Forbes Top 100']
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    
    run_toggles: RunToggles = {
        'session_length': 7
    }
    
    output = compiler.compile_for_social(run_toggles)
    
    # Check prompt includes MUST USE rules
    context_section = output['prompt_set']['context']
    assert 'BRAND KIT (MUST USE in every post)' in context_section
    assert 'CONTENT REQUIREMENTS (each post MUST include)' in context_section
    assert 'At least ONE: service mention OR differentiator OR proof point' in context_section
    assert 'At least ONE: pain/outcome reference OR audience callout' in context_section


def test_brand_kit_tier_in_model_context():
    """Test that brand_kit_tier is included in model context."""
    # Test with "best" tier (services + audience + proof)
    profile_defaults: ProfileDefaults = {
        'company': 'Agency',
        'industry': 'marketing',
        'signature_tone': 'professional',
        'platforms': ['instagram'],
        'brand_kit': {
            'services': ['Marketing'],
            'audience_role': 'Businesses',
            'proof': ['100+ clients']
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    output = compiler.compile_for_social({'session_length': 7})
    
    assert output['model_context']['brand_kit_tier'] == 'best'


def test_minimum_tier_brand_kit():
    """Test prompt with minimum tier brand kit (services only)."""
    profile_defaults: ProfileDefaults = {
        'company': 'Simple Co',
        'industry': 'business',
        'signature_tone': 'professional',
        'platforms': ['facebook'],
        'brand_kit': {
            'services': ['Consulting']
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    output = compiler.compile_for_social({'session_length': 7})
    
    assert output['model_context']['brand_kit_tier'] == 'minimum'
    assert output['model_context']['brand_kit_applied'] is True


def test_no_brand_kit_still_works():
    """Test that generation still works without brand_kit (backward compatibility)."""
    profile_defaults: ProfileDefaults = {
        'company': 'Old Co',
        'industry': 'business',
        'signature_tone': 'professional',
        'platforms': ['facebook']
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    output = compiler.compile_for_social({'session_length': 7})
    
    # Should work fine
    assert output['model_context']['brand_kit_applied'] is False
    assert output['model_context'].get('brand_kit') is None
    assert output['model_context'].get('brand_kit_tier') is None
    
    # Prompt should not include brand kit section
    context_section = output['prompt_set']['context']
    assert 'BRAND KIT' not in context_section


def test_brand_kit_with_brand_inspiration():
    """Test that brand_kit works alongside brand_inspiration."""
    profile_defaults: ProfileDefaults = {
        'company': 'Creative Co',
        'industry': 'design',
        'signature_tone': 'creative',
        'platforms': ['instagram'],
        'brand_inspirations': [
            {'name': 'Apple', 'why': 'Clean and minimal'}
        ],
        'vibe_preset': 'premium_minimal',
        'brand_kit': {
            'services': ['Brand design', 'Logo design'],
            'audience_role': 'Startups'
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    output = compiler.compile_for_social({'session_length': 7})
    
    # Both should be applied
    assert output['model_context']['brand_kit_applied'] is True
    assert output['model_context']['inspiration_applied'] is True
    
    # Prompt should include both
    context_section = output['prompt_set']['context']
    assert 'BRAND KIT' in context_section
    assert 'BRAND INSPIRATION' in context_section


def test_brand_kit_with_voice_fingerprint():
    """Test that brand_kit works with voice fingerprint."""
    profile_defaults: ProfileDefaults = {
        'company': 'Voice Co',
        'industry': 'business',
        'signature_tone': 'professional',
        'platforms': ['linkedin'],
        'brand_kit': {
            'services': ['Consulting'],
            'audience_role': 'Executives'
        }
    }
    
    voice_fingerprint = {
        'sentence_length_band': 'short',
        'top_phrases': ['game-changer', 'level up'],
        'avoid_phrases': ['synergy', 'circle back']
    }
    
    compiler = PromptCompiler(
        profile_defaults=profile_defaults,
        voice_fingerprint=voice_fingerprint
    )
    
    output = compiler.compile_for_social({'session_length': 7})
    
    # Both should be applied
    assert output['model_context']['brand_kit_applied'] is True
    assert output['model_context']['voice_applied'] is True
    
    # Prompt should include both
    context_section = output['prompt_set']['context']
    assert 'BRAND KIT' in context_section
    assert 'VOICE STYLE' in context_section


def test_brand_kit_limits_items_in_prompt():
    """Test that brand_kit limits the number of items shown in prompt."""
    profile_defaults: ProfileDefaults = {
        'company': 'Many Services Co',
        'industry': 'business',
        'signature_tone': 'professional',
        'platforms': ['facebook'],
        'brand_kit': {
            'services': ['Service 1', 'Service 2', 'Service 3', 'Service 4', 
                        'Service 5', 'Service 6', 'Service 7'],
            'proof': ['Proof 1', 'Proof 2', 'Proof 3', 'Proof 4', 'Proof 5'],
            'differentiators': ['Diff 1', 'Diff 2', 'Diff 3', 'Diff 4']
        }
    }
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    output = compiler.compile_for_social({'session_length': 7})
    
    context_section = output['prompt_set']['context']
    
    # Check that brand kit section exists
    assert 'BRAND KIT' in context_section
    
    # Check that services are included (implementation shows first 5)
    services_lines = [line for line in context_section.split('\n') if 'Services:' in line]
    assert len(services_lines) > 0, "Services line should exist in context"
    
    services_line = services_lines[0]
    # Count commas to see how many services are listed (5 services = 4 commas)
    # Note: The implementation uses [:5] slicing, so max 5 services
    service_items = services_line.split('Services:')[1].strip().split(',')
    assert len(service_items) <= 5
    
    # Verify MUST USE rules are present
    assert 'CONTENT REQUIREMENTS' in context_section
