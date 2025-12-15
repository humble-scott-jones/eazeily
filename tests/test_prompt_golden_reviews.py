"""Golden tests for review response prompt compilation."""

import pytest
from services.generation.prompt_compiler import (
    PromptCompiler,
    ProfileDefaults,
    VoiceFingerprint,
    RunToggles
)


def test_golden_reviews_basic():
    """Golden test: basic review response structure."""
    profile = ProfileDefaults(
        company='Happy Restaurant',
        industry='food',
        signature_tone='friendly'
    )
    
    run_toggles = RunToggles(session_length=1)
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_reviews(
        run_toggles=run_toggles,
        review_text='Great food and service!',
        rating=5
    )
    
    # Verify model context
    context = output['model_context']
    assert context['company_name'] == 'Happy Restaurant'
    assert context['tone'] == 'friendly'
    
    # Verify schema structure
    schema = output['json_schema']
    assert 'responses' in schema['required']
    
    responses_schema = schema['properties']['responses']
    assert 'short' in responses_schema['properties']
    assert 'medium' in responses_schema['properties']
    assert 'long' in responses_schema['properties']
    assert responses_schema['minProperties'] == 1
    
    # Verify prompt includes review text
    request_text = output['prompt_set']['request']
    assert 'Great food and service!' in request_text
    assert '5/5 stars' in request_text


def test_golden_reviews_with_voice():
    """Golden test: review response with voice fingerprint."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=['appreciate', 'grateful'],
        avoid_phrases=['unfortunately'],
        typical_cta_patterns=['Visit us again soon'],
        signature_moves=['gracious']
    )
    
    profile = ProfileDefaults(
        company='Grateful Cafe',
        signature_tone='warm'
    )
    
    run_toggles = RunToggles(session_length=1)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_reviews(
        run_toggles=run_toggles,
        review_text='Loved the coffee!',
        rating=5
    )
    
    # Voice should be applied
    assert output['model_context']['voice_applied'] is True
    
    # CTA style should be included
    voice_style = output['model_context']['voice_style']
    assert 'Visit us again soon' in voice_style['cta_style']


def test_golden_reviews_trace_summary():
    """Golden test: review trace summary structure."""
    run_toggles = RunToggles(session_length=1)
    
    compiler = PromptCompiler()
    output = compiler.compile_for_reviews(
        run_toggles=run_toggles,
        review_text='Good experience',
        rating=4,
        request_id='review123'
    )
    
    trace = output['trace_summary']
    assert trace['request_id'] == 'review123'
    assert trace['content_type'] == 'reviews'
    assert 'timestamp' in trace
