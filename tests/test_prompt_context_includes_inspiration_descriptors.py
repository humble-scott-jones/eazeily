"""Test that prompt compiler includes brand inspiration descriptors in context."""

import pytest
from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles


def test_prompt_includes_inspiration_descriptors():
    """Test that brand inspirations are converted to descriptors in prompt context."""
    
    # Setup profile with brand inspirations
    profile = ProfileDefaults(
        company='Test Corp',
        industry='retail',
        signature_tone='friendly',
        platforms=['instagram'],
        brand_inspirations=[
            {'name': 'Apple', 'why': 'clean and minimal design'},
            {'name': 'Nike', 'why': 'bold and confident messaging'}
        ],
        brand_anti_inspirations=[
            {'name': 'Pushy Corp', 'why': 'too salesy and aggressive'}
        ]
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    # Compile for social
    run_toggles = RunToggles(
        session_length=7,
        platform_focus=['instagram'],
        keywords=['summer', 'sale']
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Verify inspiration is applied
    assert output['model_context']['inspiration_applied'] is True
    assert output['model_context']['inspiration_style'] is not None
    
    inspiration_style = output['model_context']['inspiration_style']
    
    # Verify descriptors were extracted
    assert 'descriptors' in inspiration_style
    assert len(inspiration_style['descriptors']) > 0
    
    # Should extract "simple" or "minimal" from "clean and minimal"
    descriptors_str = ' '.join(inspiration_style['descriptors'])
    assert 'simple' in descriptors_str or 'minimal' in descriptors_str or 'clean' in descriptors_str
    
    # Should extract "confident" or "bold" from "bold and confident"
    assert 'confident' in descriptors_str or 'bold' in descriptors_str
    
    # Verify do/dont lists exist
    assert 'do' in inspiration_style
    assert len(inspiration_style['do']) > 0
    
    assert 'dont' in inspiration_style
    assert len(inspiration_style['dont']) > 0
    
    # Verify anti-pattern was captured
    dont_str = ' '.join(inspiration_style['dont']).lower()
    assert 'aggressive' in dont_str or 'sales' in dont_str or 'salesy' in dont_str
    
    # Verify prompt set includes inspiration
    prompt_set = output['prompt_set']
    context_text = prompt_set['context'].lower()
    
    assert 'brand inspiration' in context_text or 'inspiration' in context_text


def test_vibe_preset_generates_descriptors():
    """Test that vibe presets generate appropriate descriptors."""
    
    profile = ProfileDefaults(
        company='Health Clinic',
        industry='healthcare',
        signature_tone='professional',
        vibe_preset='clinical_trustworthy'
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    assert output['model_context']['inspiration_applied'] is True
    inspiration_style = output['model_context']['inspiration_style']
    
    # Verify clinical_trustworthy preset descriptors
    descriptors = inspiration_style['descriptors']
    descriptors_str = ' '.join(descriptors).lower()
    
    assert 'professional' in descriptors_str or 'trustworthy' in descriptors_str or 'authoritative' in descriptors_str
    
    # Should have "don't be casual" or similar
    dont_list = inspiration_style['dont']
    dont_str = ' '.join(dont_list).lower()
    assert 'casual' in dont_str or 'emoji' in dont_str


def test_no_inspirations_no_context():
    """Test that without inspirations, inspiration_applied is False."""
    
    profile = ProfileDefaults(
        company='Test Corp',
        industry='retail',
        signature_tone='friendly'
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    # Should not apply inspiration when none provided
    assert output['model_context']['inspiration_applied'] is False
    assert output['model_context']['inspiration_style'] is None


def test_playful_bold_vibe_preset():
    """Test playful_bold vibe preset generates correct descriptors."""
    
    profile = ProfileDefaults(
        company='Fun Brand',
        industry='fitness',
        vibe_preset='playful_bold'
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    inspiration_style = output['model_context']['inspiration_style']
    descriptors_str = ' '.join(inspiration_style['descriptors']).lower()
    
    assert 'playful' in descriptors_str or 'bold' in descriptors_str or 'energetic' in descriptors_str


def test_no_emojis_direct_vibe_preset():
    """Test no_emojis_direct preset includes emoji restriction."""
    
    profile = ProfileDefaults(
        company='Business Co',
        industry='consulting',
        vibe_preset='no_emojis_direct'
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    inspiration_style = output['model_context']['inspiration_style']
    
    # Should have direct/straightforward descriptors
    descriptors_str = ' '.join(inspiration_style['descriptors']).lower()
    assert 'direct' in descriptors_str or 'straightforward' in descriptors_str
    
    # Should explicitly avoid emojis
    dont_str = ' '.join(inspiration_style['dont']).lower()
    assert 'emoji' in dont_str
