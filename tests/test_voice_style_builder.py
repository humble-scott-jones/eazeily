"""Unit tests for voice_style_builder module."""

import pytest
from services.generation.voice_style_builder import (
    build_voice_style_guide,
    get_style_guide_summary,
    _tokenize,
    _analyze_sentence_structure,
    _extract_top_phrases
)


def test_build_voice_style_guide_basic():
    """Test basic voice style guide building from samples."""
    samples = [
        "We love celebrating small wins with our crew!",
        "Quick tip: book your session early and bring questions.",
        "Posts should be punchy, helpful, and invite replies!",
        "Your ideas drive our roadmap—drop them below.",
        "Morning routine: warm tone, plenty of encouragement."
    ]
    
    guide = build_voice_style_guide(samples)
    
    assert guide is not None
    assert 'tone_descriptors' in guide
    assert 'sentence_length' in guide
    assert 'formatting' in guide
    assert 'vocabulary' in guide
    assert 'style_instruction' in guide
    
    # Check vocabulary extraction
    vocab = guide['vocabulary']
    assert 'top_phrases' in vocab
    assert 'taboo_phrases' in vocab
    assert isinstance(vocab['top_phrases'], list)


def test_build_voice_style_guide_with_include_avoid():
    """Test voice guide with specific phrases to include/avoid."""
    samples = [
        "Quick win! Let's celebrate small victories.",
        "Your feedback matters. Drop a comment below.",
        "We're here to help you succeed!"
    ]
    
    guide = build_voice_style_guide(
        samples,
        include_phrases=['celebrate', 'victory', 'success'],
        avoid_phrases=['synergy', 'leverage', 'utilize']
    )
    
    vocab = guide['vocabulary']
    # Include phrases should be in top phrases
    assert any(phrase in ' '.join(vocab['top_phrases']) for phrase in ['celebrate', 'victory', 'success'])
    # Avoid phrases should be in taboo list
    assert vocab['taboo_phrases'] == ['synergy', 'leverage', 'utilize']


def test_build_voice_style_guide_empty_samples():
    """Test handling of empty samples list."""
    guide = build_voice_style_guide([])
    
    # Should return minimal default guide
    assert guide is not None
    assert guide['sentence_length'] == 'medium'
    assert 'professional' in guide['tone_descriptors']


def test_sentence_structure_analysis():
    """Test sentence structure analysis."""
    samples = [
        "Short. Punchy. Direct.",
        "This is a longer sentence that flows naturally with more words and detail.",
        "Medium length sentence here."
    ]
    
    structure = _analyze_sentence_structure(samples)
    
    assert 'avg_length' in structure
    assert 'variance' in structure
    assert structure['avg_length'] > 0


def test_top_phrases_extraction():
    """Test extraction of common phrases."""
    samples = [
        "Quick wins matter most. Small wins add up.",
        "Win after win builds momentum. Quick wins are key.",
        "Focus on quick wins to make progress."
    ]
    
    phrases = _extract_top_phrases(samples, limit=5)
    
    # Should find "quick wins" as a repeated phrase
    assert any('quick wins' in phrase.lower() for phrase in phrases)


def test_tokenization():
    """Test text tokenization."""
    text = "Hello world! 🎉 Let's go!"
    tokens = _tokenize(text)
    
    assert 'hello' in tokens
    assert 'world' in tokens
    assert "let's" in tokens
    # Should capture emoji
    assert any(token for token in tokens if not token.isalpha())


def test_style_guide_summary():
    """Test generation of style guide summary text."""
    samples = [
        "Super excited to share this! 🎉",
        "Can't wait to see your results!",
        "This is amazing!"
    ]
    
    guide = build_voice_style_guide(samples)
    summary = get_style_guide_summary(guide)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert 'Tone:' in summary or 'Sentence length:' in summary


def test_enthusiastic_tone_detection():
    """Test detection of enthusiastic tone from punctuation."""
    samples = [
        "This is incredible! You have to try it!",
        "Amazing results! Can't believe it!",
        "So excited to share this! Wow!"
    ]
    
    guide = build_voice_style_guide(samples)
    
    # Should detect enthusiastic tone from frequent exclamations
    assert 'enthusiastic' in guide['tone_descriptors']


def test_sentence_length_classification():
    """Test sentence length classification."""
    short_samples = [
        "Quick wins. Small steps. Big impact. Start today."
    ]
    
    long_samples = [
        "This is a much longer sentence that flows with more detail and explanation about the topic at hand."
    ]
    
    short_guide = build_voice_style_guide(short_samples)
    long_guide = build_voice_style_guide(long_samples)
    
    assert short_guide['sentence_length'] == 'short'
    assert long_guide['sentence_length'] in ['medium', 'long']


def test_signature_moves_detection():
    """Test detection of writing signature moves."""
    samples = [
        "Ever wonder why this works? Here's the secret.",
        "Want to know the truth? Let me explain.",
        "Have you tried this approach? It's game-changing."
    ]
    
    guide = build_voice_style_guide(samples)
    
    # Should detect rhetorical questions as a signature move
    signature_moves = guide.get('signature_moves', [])
    assert 'rhetorical questions' in signature_moves


def test_cta_pattern_extraction():
    """Test CTA pattern extraction."""
    samples = [
        "Book your session today and let's get started!",
        "Join us for an amazing experience.",
        "Try this approach and share your results below."
    ]
    
    guide = build_voice_style_guide(samples)
    cta_patterns = guide.get('cta_patterns', [])
    
    assert len(cta_patterns) > 0
    assert any('book' in cta.lower() or 'join' in cta.lower() or 'try' in cta.lower() 
               for cta in cta_patterns)
