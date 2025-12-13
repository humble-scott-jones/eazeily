"""Tests for voice fingerprint application in prompt compilation.

Verifies that:
- Compiled prompt includes top_phrases (bounded)
- Compiled prompt includes avoid_phrases
- Micro-examples are properly integrated
"""

import pytest
from services.generation.prompt_compiler import (
    PromptCompiler,
    ProfileDefaults,
    VoiceFingerprint,
    RunToggles,
    VoiceMicroExamples
)


def test_voice_fingerprint_top_phrases_included():
    """Test that top phrases appear in compiled prompt."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['quick wins', 'game changer', 'level up', 'let\'s go', 'crush it'],
        avoid_phrases=['synergy', 'leverage'],
        signature_moves=['direct']
    )
    
    profile = ProfileDefaults(
        company='Test Co',
        signature_tone='professional'
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Voice should be applied
    assert output['model_context']['voice_applied'] is True
    
    # Top phrases should be in voice style (bounded to 5)
    voice_style = output['model_context']['voice_style']
    assert voice_style is not None
    include = voice_style['include_naturally']
    assert len(include) <= 5  # bounded
    assert 'quick wins' in include
    
    # Should appear in prompt context
    context_text = output['prompt_set']['context']
    assert 'quick wins' in context_text.lower() or 'game changer' in context_text.lower()


def test_voice_fingerprint_avoid_phrases_included():
    """Test that avoid phrases appear in compiled prompt."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=['authentic', 'genuine'],
        avoid_phrases=['synergy', 'leverage', 'disrupt', 'revolutionize', 'paradigm'],
        signature_moves=['storytelling']
    )
    
    profile = ProfileDefaults(
        company='Authentic Co',
        signature_tone='genuine'
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Avoid phrases should be in voice style (bounded to 5)
    voice_style = output['model_context']['voice_style']
    avoid = voice_style['avoid']
    assert len(avoid) <= 5  # bounded
    assert 'synergy' in avoid
    
    # Should appear in prompt context with "AVOID" marker
    context_text = output['prompt_set']['context']
    assert 'AVOID' in context_text
    assert 'synergy' in context_text.lower() or 'leverage' in context_text.lower()


def test_voice_fingerprint_micro_examples_integrated():
    """Test that micro-examples are integrated into prompt."""
    micro_examples = VoiceMicroExamples(
        example_caption='Quick wins build momentum. Start small, go big!',
        example_cta='Drop a comment and share your story',
        avoid_rewrite={
            'bad': 'Leverage synergistic solutions',
            'good': 'Work together for better results'
        }
    )
    
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['quick wins', 'momentum'],
        avoid_phrases=['leverage', 'synergy'],
        signature_moves=['direct'],
        micro_examples=micro_examples
    )
    
    profile = ProfileDefaults(
        company='Example Co',
        signature_tone='direct'
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Micro-examples should be in voice style
    voice_style = output['model_context']['voice_style']
    assert 'micro_examples' in voice_style
    assert voice_style['micro_examples']['example_caption'] == micro_examples['example_caption']
    
    # Should appear in prompt context
    context_text = output['prompt_set']['context']
    assert 'VOICE EXAMPLES' in context_text
    assert 'Quick wins build momentum' in context_text
    assert 'Drop a comment' in context_text
    assert 'Leverage synergistic solutions' in context_text  # bad example
    assert 'Work together' in context_text  # good example


def test_voice_fingerprint_sentence_length_reflected():
    """Test that sentence length constraint is reflected."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='long',
        top_phrases=['comprehensive', 'detailed'],
        signature_moves=['storytelling']
    )
    
    compiler = PromptCompiler(voice_fingerprint=voice_fp)
    
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    voice_style = output['model_context']['voice_style']
    assert voice_style['sentence_length'] == 'long'


def test_voice_fingerprint_cta_patterns():
    """Test that CTA patterns are captured."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=['join us', 'learn more'],
        typical_cta_patterns=['Book your session today', 'Join the community'],
        signature_moves=['engaging']
    )
    
    compiler = PromptCompiler(voice_fingerprint=voice_fp)
    
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    voice_style = output['model_context']['voice_style']
    assert 'cta_style' in voice_style
    assert len(voice_style['cta_style']) <= 2  # bounded
    assert 'Book your session today' in voice_style['cta_style']


def test_voice_fingerprint_not_washed_out_by_template():
    """Test that voice fingerprint persists when template is applied.
    
    This is a critical requirement: templates change structure, not voice identity.
    """
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['no fluff', 'straight talk'],
        avoid_phrases=['corporate speak'],
        signature_moves=['direct']
    )
    
    from services.generation.prompt_compiler import TemplatePreset
    template = TemplatePreset(
        name='Marketing Template',
        preferred_tone='professional',
        structure_preference='list'
    )
    
    profile = ProfileDefaults(
        company='Direct Co',
        signature_tone='casual'
    )
    
    run_toggles = RunToggles(session_length=7)
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp,
        template_preset=template
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Template should be applied
    assert output['model_context']['template_applied'] is True
    
    # Voice should STILL be applied (not washed out)
    assert output['model_context']['voice_applied'] is True
    
    # Voice characteristics should be present
    voice_style = output['model_context']['voice_style']
    assert 'no fluff' in voice_style['include_naturally']
    assert 'corporate speak' in voice_style['avoid']
    
    # Prompt should include both template and voice
    context_text = output['prompt_set']['context']
    assert 'VOICE STYLE' in context_text


def test_voice_fingerprint_without_micro_examples():
    """Test voice fingerprint without micro-examples still works."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=['authentic', 'real'],
        avoid_phrases=['fake'],
        signature_moves=['genuine']
    )
    
    compiler = PromptCompiler(voice_fingerprint=voice_fp)
    
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    # Should still work without micro_examples
    assert output['model_context']['voice_applied'] is True
    voice_style = output['model_context']['voice_style']
    assert 'micro_examples' not in voice_style or voice_style.get('micro_examples') is None


def test_voice_fingerprint_bounded_to_reasonable_limits():
    """Test that voice fingerprint data is bounded for prompt size."""
    # Create voice with many phrases
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=[f'phrase_{i}' for i in range(20)],  # 20 phrases
        avoid_phrases=[f'avoid_{i}' for i in range(20)],  # 20 avoid phrases
        typical_cta_patterns=[f'CTA {i}' for i in range(10)],  # 10 CTAs
        signature_moves=['move1', 'move2', 'move3', 'move4']
    )
    
    compiler = PromptCompiler(voice_fingerprint=voice_fp)
    
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    voice_style = output['model_context']['voice_style']
    
    # Should be bounded
    assert len(voice_style['include_naturally']) <= 5
    assert len(voice_style['avoid']) <= 5
    assert len(voice_style['cta_style']) <= 2
    assert len(voice_style['tone_markers']) <= 3


def test_voice_fingerprint_in_reels_compilation():
    """Test that voice fingerprint is applied in reels compilation too."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        top_phrases=['quick tip', 'watch this'],
        avoid_phrases=['boring'],
        signature_moves=['hooks']
    )
    
    compiler = PromptCompiler(voice_fingerprint=voice_fp)
    
    output = compiler.compile_for_reels(RunToggles(session_length=1))
    
    # Voice should be applied
    assert output['model_context']['voice_applied'] is True
    
    # Should appear in prompt
    context_text = output['prompt_set']['context']
    assert 'Voice style' in context_text or 'Include' in context_text


def test_voice_fingerprint_in_reviews_compilation():
    """Test that voice fingerprint is applied in review responses."""
    voice_fp = VoiceFingerprint(
        sentence_length_band='medium',
        top_phrases=['appreciate', 'feedback'],
        avoid_phrases=['sorry not sorry'],
        typical_cta_patterns=['Visit us again'],
        signature_moves=['gracious']
    )
    
    profile = ProfileDefaults(
        company='Review Co',
        signature_tone='professional'
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_reviews(
        run_toggles=RunToggles(session_length=1),
        review_text='Great service!',
        rating=5
    )
    
    # Voice should be applied
    assert output['model_context']['voice_applied'] is True
    
    # CTA style should be in voice
    voice_style = output['model_context']['voice_style']
    assert 'Visit us again' in voice_style['cta_style']


def test_voice_fingerprint_empty_still_compiles():
    """Test that empty voice fingerprint doesn't break compilation."""
    voice_fp = VoiceFingerprint()  # Empty
    
    compiler = PromptCompiler(voice_fingerprint=voice_fp)
    
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    # Should not be applied (no meaningful data)
    assert output['model_context']['voice_applied'] is False
    assert output['model_context']['voice_style'] is None
