"""Golden tests for reel/video prompt compilation."""

import pytest
from services.generation.prompt_compiler import (
    PromptCompiler,
    ProfileDefaults,
    VoiceFingerprint,
    RunToggles
)


def test_golden_reels_basic():
    """Golden test: basic reel prompt structure."""
    profile = ProfileDefaults(
        company='Video Creator Co',
        industry='media',
        signature_tone='energetic'
    )
    
    run_toggles = RunToggles(
        session_length=1,
        reel_toggles={
            'hook_style': 'question',
            'duration': 30
        }
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_reels(run_toggles)
    
    # Verify model context
    context = output['model_context']
    assert context['company_name'] == 'Video Creator Co'
    assert context['industry'] == 'media'
    assert context['tone'] == 'energetic'
    
    # Verify schema structure
    schema = output['json_schema']
    assert schema['type'] == 'object'
    assert 'script' in schema['required']
    
    script_schema = schema['properties']['script']
    assert 'hook' in script_schema['required']
    assert 'beats' in script_schema['required']
    assert 'cta' in script_schema['required']
    assert 'caption' in script_schema['required']
    assert 'hashtags' in script_schema['required']
    
    # Verify prompt structure
    prompt_set = output['prompt_set']
    assert 'system' in prompt_set
    assert 'video content creator' in prompt_set['system'].lower()
    assert 'Hook viewers in first 3 seconds' in prompt_set['system']
    
    # Request should mention reel specifics
    assert 'Video Creator Co' in prompt_set['context']
    assert 'question' in prompt_set['request']
    assert '30 seconds' in prompt_set['request']


def test_golden_reels_with_shot_list():
    """Golden test: reel with shot list toggle."""
    run_toggles = RunToggles(
        session_length=1,
        reel_toggles={
            'hook_style': 'stat',
            'duration': 45,
            'include_shot_list': True
        }
    )
    
    compiler = PromptCompiler()
    output = compiler.compile_for_reels(run_toggles)
    
    # Schema should include shot_list
    script_schema = output['json_schema']['properties']['script']
    assert 'shot_list' in script_schema['properties']
    assert script_schema['properties']['shot_list']['type'] == 'array'


def test_golden_reels_with_voice():
    """Golden test: reel with voice fingerprint."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['watch this', 'game changer'],
        avoid_phrases=['boring'],
        signature_moves=['hooks']
    )
    
    profile = ProfileDefaults(
        company='Hook Masters',
        industry='education',
        signature_tone='exciting'
    )
    
    run_toggles = RunToggles(
        session_length=1,
        reel_toggles={'duration': 30}
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_reels(run_toggles)
    
    # Voice should be applied
    assert output['model_context']['voice_applied'] is True
    
    # Context should mention voice style
    context_text = output['prompt_set']['context']
    assert 'Voice style' in context_text or 'short' in context_text


def test_golden_reels_trace_summary():
    """Golden test: reel trace summary structure."""
    run_toggles = RunToggles(
        session_length=1,
        reel_toggles={'hook_style': 'story', 'duration': 60}
    )
    
    compiler = PromptCompiler()
    output = compiler.compile_for_reels(run_toggles, request_id='reel123')
    
    trace = output['trace_summary']
    assert trace['request_id'] == 'reel123'
    assert trace['content_type'] == 'reels'
    assert 'timestamp' in trace
