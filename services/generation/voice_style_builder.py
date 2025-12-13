"""Voice style builder - extracts compact voice style guide from samples.

This module analyzes user-provided text samples to derive a VoiceStyleGuide
that captures "how they write" without stuffing all samples into prompts.
"""

import re
import math
from collections import Counter
from typing import List, Dict, Any, Optional
from .output_schemas import VoiceStyleGuide


# Token pattern: words (including contractions) and emojis/symbols
TOKEN_RE = re.compile(r"[a-zA-Z'][a-zA-Z']*|[^\w\s\.,\"';:?!]+")


def _tokenize(text: str) -> List[str]:
    """Extract words and emoji tokens from text."""
    if not text:
        return []
    return TOKEN_RE.findall(text.lower())


def _analyze_sentence_structure(samples: List[str]) -> Dict[str, Any]:
    """Analyze sentence lengths and patterns."""
    if not samples:
        return {}
    
    sentence_lengths = []
    for text in samples:
        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)
        for s in sentences:
            words = s.strip().split()
            if words:
                sentence_lengths.append(len(words))
    
    if not sentence_lengths:
        return {'avg_length': 0, 'variance': 0}
    
    avg_len = sum(sentence_lengths) / len(sentence_lengths)
    
    variance = 0
    if len(sentence_lengths) > 1:
        variance = math.sqrt(
            sum((x - avg_len) ** 2 for x in sentence_lengths) / len(sentence_lengths)
        )
    
    return {
        'avg_length': round(avg_len, 1),
        'variance': round(variance, 1),
        'lengths': sentence_lengths
    }


def _analyze_punctuation(samples: List[str]) -> Dict[str, int]:
    """Count expressive punctuation usage."""
    counts = Counter()
    for text in samples:
        counts['!'] += text.count('!')
        counts['?'] += text.count('?')
        counts['...'] += text.count('...')
        counts['emoji'] += len([c for c in text if ord(c) > 127 and ord(c) < 0x10FFFF])
    return dict(counts)


def _extract_top_phrases(samples: List[str], limit: int = 10) -> List[str]:
    """Extract most common meaningful phrases (2-3 word sequences)."""
    # Collect 2-3 word phrases
    all_phrases = []
    for text in samples:
        words = text.lower().split()
        # 2-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 5:  # skip very short phrases
                all_phrases.append(phrase)
        # 3-word phrases
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            if len(phrase) > 8:
                all_phrases.append(phrase)
    
    # Count and return top phrases
    phrase_counts = Counter(all_phrases)
    # Filter out single-occurrence phrases
    common_phrases = [p for p, count in phrase_counts.most_common(limit * 2) if count > 1]
    return common_phrases[:limit]


def _extract_cta_patterns(samples: List[str]) -> List[str]:
    """Extract call-to-action patterns from samples."""
    cta_keywords = ['book', 'call', 'visit', 'learn', 'join', 'get', 'try', 
                    'check', 'follow', 'subscribe', 'share', 'comment', 'drop']
    ctas = []
    
    for text in samples:
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            lower = sentence.lower()
            # Look for sentences with CTA keywords
            if any(keyword in lower for keyword in cta_keywords):
                cleaned = sentence.strip()
                if cleaned and len(cleaned) < 100:  # reasonable CTA length
                    ctas.append(cleaned)
    
    # Return up to 3 unique CTAs
    unique_ctas = []
    for cta in ctas:
        if cta not in unique_ctas:
            unique_ctas.append(cta)
        if len(unique_ctas) >= 3:
            break
    
    return unique_ctas


def _detect_signature_moves(samples: List[str], structure: Dict[str, Any]) -> List[str]:
    """Detect characteristic writing patterns (signature moves)."""
    moves = []
    
    # Check for rhetorical questions
    question_count = sum(text.count('?') for text in samples)
    if question_count >= len(samples) * 0.5:  # at least 1 question per 2 samples
        moves.append("rhetorical questions")
    
    # Check for storytelling (past tense verbs, narrative markers)
    storytelling_markers = ['was', 'were', 'had', 'when', 'then', 'after', 'before']
    story_score = sum(
        sum(1 for marker in storytelling_markers if marker in text.lower())
        for text in samples
    )
    if story_score > len(samples) * 2:
        moves.append("storytelling")
    
    # Check for line breaks (short paragraphs)
    line_break_count = sum(text.count('\n') for text in samples)
    if line_break_count >= len(samples):  # average 1+ breaks per sample
        moves.append("frequent line breaks")
    
    # Check for lists/bullets
    list_markers = ['•', '–', '- ', '* ', '1.', '2.', '3.']
    if any(marker in text for text in samples for marker in list_markers):
        moves.append("bullet lists")
    
    # Check for emphasis (caps, bold markers)
    if any(word.isupper() and len(word) > 2 for text in samples for word in text.split()):
        moves.append("emphasis (caps)")
    
    return moves


def _classify_sentence_length(avg_length: float) -> str:
    """Classify average sentence length."""
    if avg_length < 10:
        return "short"
    elif avg_length > 20:
        return "long"
    else:
        return "medium"


def _build_style_instruction(voice_guide: Dict[str, Any]) -> str:
    """Generate natural language instruction from style guide."""
    parts = []
    
    # Length and pacing
    sentence_length = voice_guide.get('sentence_length', 'medium')
    if sentence_length == 'short':
        parts.append("Use short, punchy sentences.")
    elif sentence_length == 'long':
        parts.append("Use longer, flowing sentences.")
    
    # Punctuation energy
    formatting = voice_guide.get('formatting', {})
    punctuation = formatting.get('punctuation', {})
    sample_count = max(len(voice_guide.get('_samples', [])), 1)
    
    exclamations = punctuation.get('!', 0)
    if exclamations / sample_count > 1.5:
        parts.append("Maintain high energy with frequent exclamation points.")
    
    ellipses = punctuation.get('...', 0)
    if ellipses / sample_count > 0.5:
        parts.append("Use thoughtful pauses with ellipses.")
    
    # Vocabulary
    vocab = voice_guide.get('vocabulary', {})
    top_phrases = vocab.get('top_phrases', [])
    if top_phrases:
        parts.append(f"Incorporate phrases like: {', '.join(top_phrases[:3])}.")
    
    # Signature moves
    signature_moves = voice_guide.get('signature_moves', [])
    if 'rhetorical questions' in signature_moves:
        parts.append("Use rhetorical questions to engage.")
    if 'storytelling' in signature_moves:
        parts.append("Tell brief stories with clear outcomes.")
    
    return " ".join(parts) if parts else "Write in a clear, engaging style."


def build_voice_style_guide(
    samples: List[str],
    include_phrases: Optional[List[str]] = None,
    avoid_phrases: Optional[List[str]] = None,
    voice_name: Optional[str] = None
) -> VoiceStyleGuide:
    """Build a compact voice style guide from text samples.
    
    Args:
        samples: List of text samples (5-10 posts)
        include_phrases: Optional list of phrases to emphasize
        avoid_phrases: Optional list of phrases to avoid
        voice_name: Optional name for this voice
        
    Returns:
        VoiceStyleGuide with derived style characteristics
    """
    if not samples:
        # Return minimal default guide
        return VoiceStyleGuide(
            tone_descriptors=['professional'],
            sentence_length='medium',
            formatting={},
            vocabulary={'top_phrases': [], 'taboo_phrases': []},
            cta_patterns=[],
            signature_moves=[],
            style_instruction="Write in a clear, professional style."
        )
    
    # Analyze structure
    structure = _analyze_sentence_structure(samples)
    punctuation = _analyze_punctuation(samples)
    
    # Extract patterns
    top_phrases = _extract_top_phrases(samples)
    if include_phrases:
        # Merge user-specified phrases with discovered ones
        top_phrases = list(set(include_phrases + top_phrases))[:10]
    
    cta_patterns = _extract_cta_patterns(samples)
    signature_moves = _detect_signature_moves(samples, structure)
    
    # Build formatting profile
    formatting = {
        'line_breaks': 'frequent' if sum(s.count('\n') for s in samples) >= len(samples) else 'sparse',
        'bullet_usage': 'yes' if any('•' in s or '- ' in s for s in samples) else 'no',
        'emoji_frequency': 'high' if punctuation.get('emoji', 0) > len(samples) * 2 else 'low',
        'punctuation': punctuation
    }
    
    # Classify sentence length
    avg_length = structure.get('avg_length', 15)
    sentence_length = _classify_sentence_length(avg_length)
    
    # Build vocabulary section
    vocabulary = {
        'top_phrases': top_phrases,
        'taboo_phrases': avoid_phrases or []
    }
    
    # Determine tone descriptors
    tone_descriptors = []
    if exclamations := punctuation.get('!', 0):
        if exclamations > len(samples) * 2:
            tone_descriptors.append('enthusiastic')
    if punctuation.get('?', 0) > len(samples):
        tone_descriptors.append('engaging')
    if sentence_length == 'short':
        tone_descriptors.append('direct')
    if not tone_descriptors:
        tone_descriptors = ['professional', 'clear']
    
    # Build the guide
    guide = VoiceStyleGuide(
        voice_name=voice_name,
        tone_descriptors=tone_descriptors,
        sentence_length=sentence_length,
        formatting=formatting,
        vocabulary=vocabulary,
        cta_patterns=cta_patterns,
        signature_moves=signature_moves,
        style_instruction='',  # will be filled below
        _samples=samples  # temp storage for instruction builder
    )
    
    # Generate natural language instruction
    guide['style_instruction'] = _build_style_instruction(guide)
    
    # Remove temp storage
    if '_samples' in guide:
        del guide['_samples']
    
    return guide


def get_style_guide_summary(voice_guide: VoiceStyleGuide) -> str:
    """Get a compact text summary of a voice style guide for prompt injection."""
    parts = []
    
    if voice_name := voice_guide.get('voice_name'):
        parts.append(f"Voice: {voice_name}")
    
    tone = ', '.join(voice_guide.get('tone_descriptors', []))
    if tone:
        parts.append(f"Tone: {tone}")
    
    parts.append(f"Sentence length: {voice_guide.get('sentence_length', 'medium')}")
    
    if instruction := voice_guide.get('style_instruction'):
        parts.append(instruction)
    
    return ". ".join(parts) + "."
