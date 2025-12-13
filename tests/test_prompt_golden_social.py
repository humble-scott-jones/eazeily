"""Golden tests for social media prompt compilation.

These are snapshot/golden tests that verify the compiled prompt structure
stays consistent and predictable.
"""

import pytest
import json
from services.generation.prompt_compiler import (
    PromptCompiler,
    ProfileDefaults,
    VoiceFingerprint,
    RunToggles,
    VoiceMicroExamples
)


def test_golden_social_basic():
    """Golden test: basic social prompt structure."""
    profile = ProfileDefaults(
        company='Golden Bakery',
        industry='food',
        signature_tone='friendly',
        platforms=['instagram', 'facebook'],
        offerings='Fresh pastries and coffee',
        audience='Local community'
    )
    
    run_toggles = RunToggles(
        session_length=7,
        keywords=['fresh', 'local'],
        goals=['engagement']
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(run_toggles)
    
    # Verify model context structure (golden)
    context = output['model_context']
    assert context['company_name'] == 'Golden Bakery'
    assert context['industry'] == 'food'
    assert context['tone'] == 'friendly'
    assert context['platforms'] == ['instagram', 'facebook']
    assert context['session_length'] == 7
    assert context['keywords'] == ['fresh', 'local']
    assert context['goals'] == ['engagement']
    assert context['voice_applied'] is False
    
    # Verify prompt set structure
    prompt_set = output['prompt_set']
    assert 'system' in prompt_set
    assert 'context' in prompt_set
    assert 'request' in prompt_set
    
    # System message should have key elements
    assert 'Eazeily' in prompt_set['system']
    assert 'valid JSON' in prompt_set['system']
    
    # Context should have company and industry
    assert 'Golden Bakery' in prompt_set['context']
    assert 'food' in prompt_set['context']
    
    # Request should have session length and platforms
    assert '7' in prompt_set['request']
    assert 'instagram' in prompt_set['request'].lower()
    assert 'fresh' in prompt_set['request']


def test_golden_social_with_voice():
    """Golden test: social prompt with voice fingerprint."""
    micro_examples = VoiceMicroExamples(
        example_caption='Fresh bread daily. No shortcuts. Just love.',
        example_cta='Stop by and taste the difference',
        avoid_rewrite={
            'bad': 'Leverage our artisanal bread solutions',
            'good': 'Try our handmade bread'
        }
    )
    
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['fresh daily', 'handmade', 'community'],
        avoid_phrases=['leverage', 'synergy'],
        typical_cta_patterns=['Stop by today', 'Grab yours now'],
        signature_moves=['direct', 'warm'],
        micro_examples=micro_examples
    )
    
    profile = ProfileDefaults(
        company='Artisan Bakery',
        industry='food',
        signature_tone='warm',
        platforms=['instagram']
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Verify voice is applied
    context = output['model_context']
    assert context['voice_applied'] is True
    
    voice_style = context['voice_style']
    assert voice_style['sentence_length'] == 'short'
    assert 'fresh daily' in voice_style['include_naturally']
    assert 'leverage' in voice_style['avoid']
    assert 'Stop by today' in voice_style['cta_style']
    assert voice_style['micro_examples'] is not None
    
    # Verify prompt includes voice examples
    prompt_context = output['prompt_set']['context']
    assert 'VOICE STYLE' in prompt_context
    assert 'VOICE EXAMPLES' in prompt_context
    assert 'Fresh bread daily' in prompt_context
    assert 'Stop by and taste' in prompt_context
    assert 'Leverage our artisanal' in prompt_context  # bad example
    assert 'Try our handmade' in prompt_context  # good example


def test_golden_social_json_schema():
    """Golden test: verify JSON schema structure for social."""
    compiler = PromptCompiler()
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    schema = output['json_schema']
    
    # Verify schema structure (golden)
    assert schema['type'] == 'object'
    assert 'posts' in schema['required']
    
    posts_schema = schema['properties']['posts']
    assert posts_schema['type'] == 'array'
    
    post_item = posts_schema['items']
    assert 'date' in post_item['required']
    assert 'pillar' in post_item['required']
    assert 'cards' in post_item['required']
    
    # Pillar enum should have specific values
    pillar_enum = post_item['properties']['pillar']['enum']
    assert 'Educational' in pillar_enum
    assert 'Engagement' in pillar_enum
    
    # Cards schema
    cards_schema = post_item['properties']['cards']
    assert cards_schema['type'] == 'array'
    assert cards_schema['minItems'] == 1
    
    card_item = cards_schema['items']
    assert 'platform' in card_item['required']
    assert 'caption' in card_item['required']
    assert card_item['properties']['caption']['minLength'] == 1


def test_golden_social_trace_summary():
    """Golden test: verify trace summary structure."""
    profile = ProfileDefaults(
        company='Test Co',
        industry='tech',
        signature_tone='professional'
    )
    
    voice_fp = VoiceFingerprint(
        top_phrases=['innovative'],
        avoid_phrases=['boring']
    )
    
    run_toggles = RunToggles(
        session_length=7,
        keywords=['tech'],
        goals=['growth']
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_social(run_toggles, request_id='test123')
    
    trace = output['trace_summary']
    
    # Verify trace structure (golden)
    assert trace['request_id'] == 'test123'
    assert trace['content_type'] == 'social'
    assert 'timestamp' in trace
    
    selections = trace['selections']
    assert selections['tone'] == 'professional'
    assert selections['session_length'] == 7
    assert selections['goals_count'] == 1
    assert selections['keywords_count'] == 1
    
    assert trace['voice_fingerprint_applied'] is True
    assert 'token_budget_estimate' in trace
    assert trace['token_budget_estimate'] > 0


def test_golden_social_platform_rules():
    """Golden test: verify platform-specific rules in prompt."""
    profile = ProfileDefaults(
        company='Multi Platform Co',
        signature_tone='professional'
    )
    
    run_toggles = RunToggles(
        session_length=7,
        platform_focus=['instagram', 'linkedin', 'twitter']
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(run_toggles)
    
    request_text = output['prompt_set']['request']
    
    # Verify platform rules are included
    assert 'PLATFORM RULES' in request_text
    assert 'INSTAGRAM' in request_text
    assert '2200 chars' in request_text  # Instagram limit
    assert 'LINKEDIN' in request_text
    assert '1300 chars' in request_text  # LinkedIn limit
    assert 'TWITTER' in request_text
    assert '280 chars' in request_text  # Twitter limit


def test_golden_social_minimal_profile():
    """Golden test: minimal profile still produces valid output."""
    run_toggles = RunToggles(
        session_length=1,
        tone_override='casual'
    )
    
    compiler = PromptCompiler()  # No profile
    output = compiler.compile_for_social(run_toggles)
    
    # Should still have valid structure
    assert output['model_context']['tone'] == 'casual'
    assert output['model_context']['session_length'] == 1
    assert output['model_context']['industry'] == 'business'  # default
    
    # Should have all three components
    assert 'system' in output['prompt_set']
    assert 'context' in output['prompt_set']
    assert 'request' in output['prompt_set']
    
    # Schema should be valid
    assert 'posts' in output['json_schema']['properties']


def test_golden_social_token_estimate():
    """Golden test: token estimate is reasonable."""
    profile = ProfileDefaults(
        company='Token Test Co',
        industry='tech',
        signature_tone='professional',
        offerings='Software products',
        audience='Developers'
    )
    
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=['innovative', 'cutting edge', 'next level'],
        avoid_phrases=['old school', 'legacy']
    )
    
    run_toggles = RunToggles(
        session_length=30,
        platform_focus=['instagram', 'facebook', 'linkedin'],
        keywords=['tech', 'innovation', 'future'],
        goals=['engagement', 'growth', 'awareness']
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    token_estimate = output['trace_summary']['token_budget_estimate']
    
    # Token estimate should be reasonable (not 0, not crazy high)
    assert token_estimate > 100  # At least some tokens
    assert token_estimate < 10000  # Not excessive
    
    # Rough sanity check: more content = more tokens
    # With voice, platforms, keywords, goals, should be several hundred
    assert token_estimate > 200


def test_golden_social_consistent_output():
    """Golden test: same inputs produce consistent structure."""
    profile = ProfileDefaults(
        company='Consistent Co',
        industry='retail',
        signature_tone='friendly'
    )
    
    run_toggles = RunToggles(
        session_length=7,
        keywords=['quality']
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    
    # Compile twice
    output1 = compiler.compile_for_social(run_toggles)
    output2 = compiler.compile_for_social(run_toggles)
    
    # Structure should be identical (excluding timestamp and request_id)
    assert output1['model_context']['company_name'] == output2['model_context']['company_name']
    assert output1['model_context']['tone'] == output2['model_context']['tone']
    assert output1['json_schema'] == output2['json_schema']
    
    # Prompt structure should be the same
    assert len(output1['prompt_set']['system']) == len(output2['prompt_set']['system'])
    assert output1['prompt_set']['system'] == output2['prompt_set']['system']
