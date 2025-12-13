"""Tests for prompt compiler precedence logic.

Verifies that merge precedence is correct for every key:
RunToggles > TemplatePreset > VoiceFingerprint > ProfileDefaults
"""

import pytest
from services.generation.prompt_compiler import (
    PromptCompiler,
    ProfileDefaults,
    VoiceFingerprint,
    TemplatePreset,
    RunToggles
)


def test_precedence_tone_override():
    """Test that tone follows correct precedence."""
    profile = ProfileDefaults(
        company='Test Co',
        industry='tech',
        signature_tone='professional',
        platforms=['linkedin']
    )
    
    template = TemplatePreset(
        name='Marketing Template',
        preferred_tone='playful'
    )
    
    run_toggles = RunToggles(
        tone_override='inspirational',
        session_length=7
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        template_preset=template
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # RunToggles should override template and profile
    assert output['model_context']['tone'] == 'inspirational'


def test_precedence_tone_template_over_profile():
    """Test that template tone overrides profile when no run toggle."""
    profile = ProfileDefaults(
        signature_tone='professional',
        platforms=['linkedin']
    )
    
    template = TemplatePreset(
        name='Template',
        preferred_tone='casual'
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        template_preset=template
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Template should override profile
    assert output['model_context']['tone'] == 'casual'


def test_precedence_platforms():
    """Test platform precedence."""
    profile = ProfileDefaults(
        signature_tone='professional',
        platforms=['linkedin', 'twitter']
    )
    
    template = TemplatePreset(
        name='Template',
        preferred_platforms=['instagram', 'facebook']
    )
    
    run_toggles = RunToggles(
        platform_focus=['tiktok'],
        session_length=7
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        template_preset=template
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # RunToggles platform_focus should override all
    assert output['model_context']['platforms'] == ['tiktok']


def test_precedence_platforms_template_over_profile():
    """Test that template platforms override profile."""
    profile = ProfileDefaults(
        signature_tone='professional',
        platforms=['linkedin']
    )
    
    template = TemplatePreset(
        name='Template',
        preferred_platforms=['instagram']
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        template_preset=template
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Template platforms should override profile
    assert output['model_context']['platforms'] == ['instagram']


def test_precedence_keywords_goals():
    """Test that keywords and goals come from run toggles."""
    profile = ProfileDefaults(
        company='Test Co',
        industry='tech',
        signature_tone='professional'
    )
    
    run_toggles = RunToggles(
        session_length=7,
        keywords=['innovation', 'growth'],
        goals=['engagement', 'awareness']
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    output = compiler.compile_for_social(run_toggles)
    
    # Keywords and goals should be from run toggles
    assert output['model_context']['keywords'] == ['innovation', 'growth']
    assert output['model_context']['goals'] == ['engagement', 'awareness']


def test_precedence_session_length():
    """Test session length from run toggles."""
    profile = ProfileDefaults(
        signature_tone='professional',
        platforms=['instagram']
    )
    
    run_toggles = RunToggles(session_length=30)
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    output = compiler.compile_for_social(run_toggles)
    
    # Session length should be from run toggles
    assert output['model_context']['session_length'] == 30


def test_precedence_voice_fingerprint_not_overridden():
    """Test that voice fingerprint is applied as constraints, not overridden."""
    profile = ProfileDefaults(
        company='Test Co',
        signature_tone='professional',
        platforms=['instagram']
    )
    
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['quick wins', 'let\'s go'],
        avoid_phrases=['synergy', 'leverage'],
        signature_moves=['rhetorical questions']
    )
    
    template = TemplatePreset(
        name='Template',
        preferred_tone='playful'
    )
    
    run_toggles = RunToggles(
        tone_override='casual',
        session_length=7
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp,
        template_preset=template
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Tone should be from run toggle (highest priority)
    assert output['model_context']['tone'] == 'casual'
    
    # Voice fingerprint should be applied (not overridden)
    assert output['model_context']['voice_applied'] is True
    assert output['model_context']['voice_style'] is not None
    assert 'quick wins' in output['model_context']['voice_style']['include_naturally']
    assert 'synergy' in output['model_context']['voice_style']['avoid']


def test_precedence_profile_defaults_baseline():
    """Test that profile defaults are used as baseline."""
    profile = ProfileDefaults(
        company='Baseline Corp',
        industry='retail',
        signature_tone='friendly',
        platforms=['facebook'],
        offerings='Product line',
        audience='Young adults'
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    output = compiler.compile_for_social(run_toggles)
    
    # All profile defaults should be in model context
    assert output['model_context']['company_name'] == 'Baseline Corp'
    assert output['model_context']['industry'] == 'retail'
    assert output['model_context']['tone'] == 'friendly'
    assert output['model_context']['platforms'] == ['facebook']
    assert output['model_context']['offerings'] == 'Product line'
    assert output['model_context']['audience'] == 'Young adults'


def test_precedence_empty_inputs():
    """Test compiler with minimal inputs."""
    run_toggles = RunToggles(
        session_length=7,
        tone_override='professional'
    )
    
    compiler = PromptCompiler()  # No profile, voice, or template
    
    output = compiler.compile_for_social(run_toggles)
    
    # Should use defaults
    assert output['model_context']['tone'] == 'professional'
    assert output['model_context']['session_length'] == 7
    assert output['model_context']['voice_applied'] is False


def test_precedence_reel_toggles():
    """Test that reel toggles are preserved."""
    profile = ProfileDefaults(
        company='Video Co',
        signature_tone='energetic'
    )
    
    run_toggles = RunToggles(
        session_length=1,
        reel_toggles={
            'hook_style': 'question',
            'duration': 45,
            'include_shot_list': True
        }
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    output = compiler.compile_for_reels(run_toggles)
    
    # Reel toggles should be used in schema and prompt
    assert 'script' in output['json_schema']['properties']
    assert 'shot_list' in output['json_schema']['properties']['script']['properties']


def test_precedence_complete_layers():
    """Test all four layers with complete data."""
    profile = ProfileDefaults(
        company='Full Stack Co',
        industry='tech',
        signature_tone='professional',
        platforms=['linkedin', 'twitter'],
        offerings='SaaS platform',
        audience='Developers',
        taboo_topics=['politics', 'religion']
    )
    
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        emoji_rate='low',
        top_phrases=['game changer', 'level up'],
        avoid_phrases=['disrupt', 'revolutionize'],
        typical_cta_patterns=['Join us today', 'Learn more'],
        signature_moves=['storytelling']
    )
    
    template = TemplatePreset(
        name='Weekly Update',
        preferred_tone='friendly',
        preferred_platforms=['instagram', 'facebook']
    )
    
    run_toggles = RunToggles(
        session_length=7,
        tone_override='inspiring',
        platform_focus=['tiktok', 'youtube'],
        keywords=['innovation', 'future'],
        goals=['engagement']
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp,
        template_preset=template
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Verify final precedence results
    assert output['model_context']['company_name'] == 'Full Stack Co'  # from profile
    assert output['model_context']['industry'] == 'tech'  # from profile
    assert output['model_context']['tone'] == 'inspiring'  # from run toggles (highest)
    assert output['model_context']['platforms'] == ['tiktok', 'youtube']  # from run toggles
    assert output['model_context']['keywords'] == ['innovation', 'future']  # from run toggles
    assert output['model_context']['goals'] == ['engagement']  # from run toggles
    assert output['model_context']['offerings'] == 'SaaS platform'  # from profile
    assert output['model_context']['audience'] == 'Developers'  # from profile
    assert output['model_context']['voice_applied'] is True  # voice fingerprint present
    assert output['model_context']['template_applied'] is True  # template present
    
    # Voice style should be present
    voice_style = output['model_context']['voice_style']
    assert voice_style is not None
    assert 'game changer' in voice_style['include_naturally']
    assert 'disrupt' in voice_style['avoid']
