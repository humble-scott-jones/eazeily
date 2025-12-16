"""Test that voice fingerprint overrides brand inspiration when both are present."""

import pytest
from services.generation.prompt_compiler import (
    PromptCompiler, 
    ProfileDefaults, 
    VoiceFingerprint,
    RunToggles
)


def test_voice_fingerprint_overrides_inspiration_emoji():
    """Test that voice fingerprint emoji setting overrides inspiration emoji preference."""
    
    # Setup inspiration that suggests emojis
    profile = ProfileDefaults(
        company='Fun Brand',
        industry='retail',
        vibe_preset='playful_bold'  # This would normally encourage emojis
    )
    
    # Setup voice fingerprint that says "no emojis"
    voice = VoiceFingerprint(
        emoji_rate='none',
        sentence_length_band='short',
        top_phrases=['amazing', 'love it', 'check this'],
        avoid_phrases=['emoji'],
        signature_moves=['direct statements']
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice
    )
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    # Both should be applied
    assert output['model_context']['inspiration_applied'] is True
    assert output['model_context']['voice_applied'] is True
    
    # Check prompt text for precedence
    prompt_context = output['prompt_set']['context']
    
    # Voice style should appear AFTER inspiration (higher priority)
    inspiration_pos = prompt_context.find('BRAND INSPIRATION')
    voice_pos = prompt_context.find('VOICE STYLE')
    
    # Voice should come after inspiration in the context
    assert voice_pos > inspiration_pos, "Voice style should appear after inspiration to show higher priority"
    
    # Voice should mention "highest priority"
    assert 'highest priority' in prompt_context.lower() or 'personal fingerprint' in prompt_context.lower()


def test_voice_fingerprint_phrases_override_inspiration_tone():
    """Test that voice fingerprint phrases take precedence over inspiration descriptors."""
    
    # Inspiration suggests "professional" tone
    profile = ProfileDefaults(
        company='Corp',
        industry='consulting',
        brand_inspirations=[
            {'name': 'McKinsey', 'why': 'professional and formal'}
        ]
    )
    
    # Voice fingerprint has casual, friendly phrases
    voice = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['hey there', 'super excited', 'let\'s go'],
        signature_moves=['casual greeting', 'enthusiasm']
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice
    )
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    # Check that voice phrases are included
    voice_style = output['model_context']['voice_style']
    assert 'hey there' in voice_style['include_naturally']
    
    # Voice fingerprint should take precedence in the prompt
    prompt_context = output['prompt_set']['context']
    assert 'hey there' in prompt_context.lower() or 'super excited' in prompt_context.lower()


def test_inspiration_used_when_no_voice_fingerprint():
    """Test that inspiration is used normally when no voice fingerprint exists."""
    
    profile = ProfileDefaults(
        company='Brand',
        industry='retail',
        vibe_preset='friendly_modern'
    )
    
    # No voice fingerprint
    compiler = PromptCompiler(profile_defaults=profile)
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    # Inspiration should be applied
    assert output['model_context']['inspiration_applied'] is True
    # Voice should NOT be applied
    assert output['model_context']['voice_applied'] is False
    
    # Inspiration should appear in context
    prompt_context = output['prompt_set']['context']
    assert 'friendly' in prompt_context.lower() or 'modern' in prompt_context.lower()


def test_voice_avoid_phrases_override_inspiration_do():
    """Test that voice 'avoid' list overrides inspiration 'do' suggestions."""
    
    # Inspiration suggests using humor
    profile = ProfileDefaults(
        company='Fun Co',
        industry='entertainment',
        brand_inspirations=[
            {'name': 'Comedy Central', 'why': 'funny and humorous'}
        ]
    )
    
    # Voice fingerprint explicitly avoids humor
    voice = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=['professional', 'quality', 'trusted'],
        avoid_phrases=['jokes', 'humor', 'funny'],
        signature_moves=['straightforward']
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice
    )
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    # Both applied
    assert output['model_context']['inspiration_applied'] is True
    assert output['model_context']['voice_applied'] is True
    
    # Voice avoid should be in the prompt
    voice_style = output['model_context']['voice_style']
    assert any('joke' in phrase or 'humor' in phrase or 'funny' in phrase 
               for phrase in voice_style['avoid'])
    
    # Voice avoid should appear in context
    prompt_context = output['prompt_set']['context'].lower()
    assert 'avoid' in prompt_context
    assert 'jokes' in prompt_context or 'humor' in prompt_context or 'funny' in prompt_context


def test_both_empty_no_conflict():
    """Test that having neither voice nor inspiration works correctly."""
    
    profile = ProfileDefaults(
        company='Simple Co',
        industry='business'
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    run_toggles = RunToggles(session_length=7)
    output = compiler.compile_for_social(run_toggles)
    
    # Neither should be applied
    assert output['model_context']['inspiration_applied'] is False
    assert output['model_context']['voice_applied'] is False
    
    # Prompt should still work with just basic context
    prompt_set = output['prompt_set']
    assert prompt_set['system']
    assert prompt_set['context']
    assert prompt_set['request']
