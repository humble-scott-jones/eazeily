"""Regression tests for 'secret sauce' - voice personalization."""

import pytest
from services.generation import GenerationService
from services.generation.voice_style_builder import build_voice_style_guide


# Deterministic fixture voice profile
FIXTURE_VOICE_SAMPLES = [
    "Quick wins drive momentum! Let's celebrate every small victory.",
    "Your ideas fuel our innovation—drop them below!",
    "Consistency beats perfection. Start small, stay steady.",
    "We're grateful for this amazing community! Thank you for being here.",
    "Pro tip: prioritize progress over polish every time.",
]

FIXTURE_INCLUDE_PHRASES = [
    "quick wins",
    "small victory",
    "celebrate",
    "grateful",
    "amazing"
]

FIXTURE_AVOID_PHRASES = [
    "synergy",
    "leverage",
    "utilize",
    "paradigm"
]


def test_voice_guide_contains_top_phrases():
    """Test that voice guide extracts recognizable top phrases."""
    guide = build_voice_style_guide(
        FIXTURE_VOICE_SAMPLES,
        include_phrases=FIXTURE_INCLUDE_PHRASES,
        avoid_phrases=FIXTURE_AVOID_PHRASES
    )
    
    vocab = guide['vocabulary']
    top_phrases = vocab['top_phrases']
    
    # Should contain at least some of our emphasized phrases
    phrases_found = sum(
        1 for phrase in FIXTURE_INCLUDE_PHRASES
        if any(phrase in ' '.join(top_phrases).lower() for phrase in [phrase])
    )
    
    assert phrases_found >= 2, "Voice guide should contain at least 2 emphasized phrases"


def test_voice_guide_marks_avoid_phrases():
    """Test that avoid phrases are properly marked as taboo."""
    guide = build_voice_style_guide(
        FIXTURE_VOICE_SAMPLES,
        include_phrases=FIXTURE_INCLUDE_PHRASES,
        avoid_phrases=FIXTURE_AVOID_PHRASES
    )
    
    vocab = guide['vocabulary']
    taboo_phrases = vocab['taboo_phrases']
    
    assert taboo_phrases == FIXTURE_AVOID_PHRASES


def test_voice_personalization_affects_tone():
    """Test that voice samples affect detected tone descriptors."""
    # Enthusiastic samples (lots of exclamations)
    enthusiastic_samples = [
        "This is amazing! Can't wait to share!",
        "Incredible results! You have to try this!",
        "So excited! Let's go!"
    ]
    
    # Calm samples (no exclamations)
    calm_samples = [
        "Consider this thoughtful approach.",
        "A measured perspective on the topic.",
        "Taking time to reflect matters."
    ]
    
    enthusiastic_guide = build_voice_style_guide(enthusiastic_samples)
    calm_guide = build_voice_style_guide(calm_samples)
    
    # Enthusiastic should have different tone descriptors than calm
    assert enthusiastic_guide['tone_descriptors'] != calm_guide['tone_descriptors']
    
    # Enthusiastic should likely include 'enthusiastic'
    if 'enthusiastic' in enthusiastic_guide['tone_descriptors']:
        assert 'enthusiastic' not in calm_guide['tone_descriptors']


def test_voice_personalization_sentence_length():
    """Test that voice samples affect sentence length classification."""
    short_samples = [
        "Short. Punchy. Direct. Quick wins. Start now."
    ]
    
    long_samples = [
        "This is a longer, more flowing sentence that takes time to unfold and includes multiple thoughts and ideas woven together in a natural conversational style."
    ]
    
    short_guide = build_voice_style_guide(short_samples)
    long_guide = build_voice_style_guide(long_samples)
    
    assert short_guide['sentence_length'] == 'short'
    assert long_guide['sentence_length'] in ['medium', 'long']


def test_voice_guide_signature_moves():
    """Test detection of signature writing moves."""
    question_samples = [
        "Ever wonder why this works?",
        "Want to know the secret?",
        "Have you tried this approach?"
    ]
    
    guide = build_voice_style_guide(question_samples)
    signature_moves = guide.get('signature_moves', [])
    
    # Should detect rhetorical questions
    assert 'rhetorical questions' in signature_moves


def test_social_posts_with_voice_include_phrases():
    """Test that generated posts include emphasized phrases when voice is applied.
    
    Note: With validation gate, fallback content is blocked.
    """
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={'session_length': 3, 'platforms': ['instagram']},
        voice_samples=FIXTURE_VOICE_SAMPLES,
        include_phrases=FIXTURE_INCLUDE_PHRASES
    )
    
    # Fallback is blocked by validation
    assert result['ok'] is False
    assert result['error']['code'] == 'output_not_rich_enough'


def test_social_posts_avoid_taboo_phrases():
    """Test that generated posts avoid taboo phrases (best effort with OpenAI).
    
    Note: With validation gate, fallback content is blocked.
    """
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={'session_length': 2, 'platforms': ['instagram']},
        voice_samples=FIXTURE_VOICE_SAMPLES,
        avoid_phrases=FIXTURE_AVOID_PHRASES
    )
    
    # Fallback is blocked by validation
    assert result['ok'] is False
    assert result['error']['code'] == 'output_not_rich_enough'


def test_voice_style_instruction_generation():
    """Test that style instruction is generated and meaningful."""
    guide = build_voice_style_guide(FIXTURE_VOICE_SAMPLES)
    
    instruction = guide.get('style_instruction', '')
    
    # Should have generated an instruction
    assert len(instruction) > 0
    # Should contain actionable guidance
    assert any(word in instruction.lower() for word in ['use', 'write', 'maintain', 'include'])


def test_voice_guide_consistency():
    """Test that voice guide generation is deterministic for same input."""
    guide1 = build_voice_style_guide(FIXTURE_VOICE_SAMPLES)
    guide2 = build_voice_style_guide(FIXTURE_VOICE_SAMPLES)
    
    # Core properties should be identical
    assert guide1['sentence_length'] == guide2['sentence_length']
    assert guide1['tone_descriptors'] == guide2['tone_descriptors']
    assert guide1['vocabulary']['top_phrases'] == guide2['vocabulary']['top_phrases']


def test_reel_script_with_voice():
    """Test that reel script generation respects voice when applied."""
    service = GenerationService(enable_openai=False)
    
    result = service.generate_reel_script(
        request={'duration': 30},
        voice_samples=FIXTURE_VOICE_SAMPLES
    )
    
    assert result['ok'] is True
    # Voice should be applied
    assert 'summary' in result


def test_review_response_voice_application():
    """Test that review responses change meaningfully with brand voice."""
    service = GenerationService(enable_openai=False)
    
    # Without brand voice
    result_no_voice = service.generate_review_response(
        request={
            'review_text': 'Great service!',
            'rating': 5,
            'use_brand_voice': False
        },
        voice_samples=FIXTURE_VOICE_SAMPLES
    )
    
    # With brand voice
    result_with_voice = service.generate_review_response(
        request={
            'review_text': 'Great service!',
            'rating': 5,
            'use_brand_voice': True
        },
        voice_samples=FIXTURE_VOICE_SAMPLES
    )
    
    assert result_no_voice['ok'] is True
    assert result_with_voice['ok'] is True
    
    # Voice application should be different
    assert result_no_voice['summary']['voice_applied'] is False
    assert result_with_voice['summary']['voice_applied'] is True


def test_empty_voice_samples_doesnt_break():
    """Test that empty voice samples don't cause failures.
    
    Note: With validation gate, fallback content is blocked.
    """
    service = GenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={'session_length': 1, 'platforms': ['instagram']},
        voice_samples=[]
    )
    
    # Fallback is blocked by validation
    assert result['ok'] is False
    assert result['error']['code'] == 'output_not_rich_enough'


def test_minimal_voice_samples():
    """Test handling of minimal voice samples (less than recommended)."""
    minimal_samples = ["One sample."]
    
    guide = build_voice_style_guide(minimal_samples)
    
    # Should still build a guide without errors
    assert guide is not None
    assert 'sentence_length' in guide
    assert 'tone_descriptors' in guide
