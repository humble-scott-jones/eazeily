import math
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Iterable, Mapping


# Regex to capture words (including contractions) AND emojis/symbols commonly used in social
# This is a broad pattern: words OR non-whitespace/non-punctuation symbols (emojis)
TOKEN_RE = re.compile(r"[a-zA-Z'][a-zA-Z']*|[^\w\s\.,\"';:?!]+")

def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    # Find words and emojis, ignore standard punctuation for token counts
    return TOKEN_RE.findall(text.lower())


def _analyze_structure(samples: list[str]) -> dict:
    """Analyze sentence structure and punctuation habits."""
    if not samples:
        return {}
    
    sentence_lengths = []
    punctuation_counts = Counter()
    
    for text in samples:
        # Rough sentence splitting
        sentences = re.split(r'[.!?]+', text)
        for s in sentences:
            words = s.strip().split()
            if words:
                sentence_lengths.append(len(words))
        
        # Count expressive punctuation
        punctuation_counts['!'] += text.count('!')
        punctuation_counts['?'] += text.count('?')
        punctuation_counts['...'] += text.count('...')
    
    avg_len = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    # Calculate variance (standard deviation)
    variance = 0
    if len(sentence_lengths) > 1:
        variance = math.sqrt(sum((x - avg_len) ** 2 for x in sentence_lengths) / len(sentence_lengths))
        
    return {
        'avg_sentence_len': round(avg_len, 1),
        'sentence_variance': round(variance, 1),
        'punctuation_profile': dict(punctuation_counts)
    }


def _generate_style_instruction(profile: dict) -> str:
    """Synthesize a natural language instruction for the AI based on stats."""
    parts = []
    
    # 1. Length/Pacing
    avg_len = profile.get('avg_length', 15)
    variance = profile.get('structure', {}).get('sentence_variance', 0)
    
    if avg_len < 10:
        parts.append("Use short, punchy sentences.")
    elif avg_len > 25:
        parts.append("Use longer, narrative-style sentences.")
        
    if variance > 5:
        parts.append("Vary sentence length to sound conversational.")
        
    # 2. Energy/Punctuation
    punc = profile.get('structure', {}).get('punctuation_profile', {})
    exclamations = punc.get('!', 0)
    ellipses = punc.get('...', 0)
    sample_count = profile.get('sample_count', 1)
    
    if exclamations / sample_count > 1.5:
        parts.append("Maintain a high-energy, enthusiastic tone (use '!' frequently).")
    elif ellipses / sample_count > 0.5:
        parts.append("Use a thoughtful, pausing style (use '...' occasionally).")
        
    # 3. Vocabulary
    phrases = profile.get('include_phrases', [])
    if phrases:
        parts.append(f"Naturally weave in words like: {', '.join(phrases[:5])}.")
        
    return " ".join(parts)



def build_embedding(text: str) -> dict[str, float]:
    tokens = _tokenize(text)
    counts = Counter(tokens)
    total = float(sum(counts.values()) or 1.0)
    return {token: count / total for token, count in counts.items()}


def merge_embeddings(embeddings: Iterable[Mapping[str, float]]) -> dict[str, float]:
    accumulator: Counter[str] = Counter()
    total = 0
    for emb in embeddings:
        for token, weight in (emb or {}).items():
            accumulator[token] += float(weight)
            total += float(weight)
    if not total:
        return {}
    return {token: weight / total for token, weight in accumulator.items()}


def cosine_similarity(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for token, aval in a.items():
        bval = b.get(token)
        if bval:
            dot += float(aval) * float(bval)
    a_norm = math.sqrt(sum(float(v) ** 2 for v in a.values()))
    b_norm = math.sqrt(sum(float(v) ** 2 for v in b.values()))
    if not a_norm or not b_norm:
        return 0.0
    return dot / (a_norm * b_norm)


def _top_phrases(tokens: list[str], n: int = 5) -> list[str]:
    counts = Counter([t for t in tokens if t not in STOPWORDS])
    return [token for token, _ in counts.most_common(n)]


def profile_from_samples(samples: list[str]) -> dict:
    """Build a voice profile from a collection of sample text strings.

    Analyzes the provided samples to extract linguistic patterns, common phrases,
    and stylistic characteristics that define a unique "voice". The resulting profile
    can be used to assess whether new content aligns with the established voice.

    Args:
        samples: A list of text strings representing the voice to profile. Each sample
                should be a complete post, message, or content snippet that exemplifies
                the desired tone and style. Empty or whitespace-only strings are ignored.

    Returns:
        A dictionary containing the voice profile with the following structure:
        {
            'created_at': str,           # ISO 8601 timestamp (UTC) when profile was created
            'sample_count': int,         # Number of valid samples analyzed
            'avg_length': float,         # Average word count across all samples
            'include_phrases': list[str], # Top 7 most frequent non-stopword tokens
            'avoid_phrases': list[str],  # Up to 3 short (≤3 chars) frequent tokens to avoid overusing
            'example_lines': list[str],  # First 3 sample texts for reference
            'embedding': dict[str, float] # Merged token frequency embeddings (token → normalized weight)
        }
        
        Returns an empty dict if no valid samples are provided.

    Example:
        >>> samples = [
        ...     "We love celebrating small wins with our crew.",
        ...     "Friendly reminder: book your session early!",
        ... ]
        >>> profile = profile_from_samples(samples)
        >>> profile['sample_count']
        2
        >>> 'embedding' in profile
        True
    """
    cleaned = [s.strip() for s in samples if isinstance(s, str) and s.strip()]
    if not cleaned:
        return {}
    
    embeddings = [build_embedding(text) for text in cleaned]
    merged = merge_embeddings(embeddings)
    
    tokens: list[str] = []
    for text in cleaned:
        tokens.extend(_tokenize(text))
        
    include_phrases = _top_phrases(tokens, 7)
    avoid_phrases = []
    
    # New structural analysis
    structure = _analyze_structure(cleaned)
    avg_length = sum(len(text.split()) for text in cleaned) / len(cleaned)
    example_lines = cleaned[:3]
    
    profile = {
        'created_at': datetime.now(timezone.utc).isoformat() + 'Z',
        'sample_count': len(cleaned),
        'avg_length': round(avg_length, 2),
        'structure': structure,
        'include_phrases': include_phrases,
        'avoid_phrases': avoid_phrases,
        'example_lines': example_lines,
        'embedding': merged,
    }
    
    # Generate the "North Star" instruction
    profile['style_instruction'] = _generate_style_instruction(profile)
    
    return profile


def assess_text(profile: Mapping[str, object], text: str, *, threshold: float = 0.72) -> dict:
    """Evaluate how well a text sample matches the given voice profile.
    
    This function performs drift detection by comparing the text's word-frequency
    embedding against the profile's baseline embedding using cosine similarity.
    When the similarity falls below the threshold, the text is flagged as drifting
    from the expected voice.
    
    Args:
        profile: A voice profile dict containing 'embedding', 'include_phrases',
            and 'avoid_phrases' keys (typically from profile_from_samples).
        text: The text sample to evaluate against the profile.
        threshold: Minimum cosine similarity (0.0 to 1.0) required to avoid drift.
            Default 0.72 is calibrated for typical brand voice detection.
            Lower values are more permissive; higher values are stricter.
    
    Returns:
        A dict with keys:
            - 'score': Cosine similarity score between 0.0 and 1.0.
            - 'drift': Boolean indicating if score < threshold (voice drift detected).
            - 'message': A hint for how to realign with the voice (or None if no drift).
            - 'suggestions': List of phrase recommendations based on profile data.
    """
    embedding = profile.get('embedding') if isinstance(profile, Mapping) else None
    score = cosine_similarity(embedding or {}, build_embedding(text))
    include_phrases = list(profile.get('include_phrases') or []) if isinstance(profile, Mapping) else []
    suggestions = []
    if include_phrases:
        suggestions.append(f"Lean on phrases like: {', '.join(include_phrases[:3])}.")
    avoid_phrases = list(profile.get('avoid_phrases') or []) if isinstance(profile, Mapping) else []
    if avoid_phrases:
        suggestions.append(f"Avoid overusing: {', '.join(avoid_phrases[:2])}.")
    drift = score < threshold
    message = None
    if drift:
        message = "Closer to your voice: tighten cadence and reuse your go-to phrases."
    return {
        'score': round(score, 4),
        'drift': drift,
        'message': message,
        'suggestions': suggestions
    }


def evaluate_prompts(profile: Mapping[str, object], prompts: list[str], *, threshold: float = 0.72) -> list[dict]:
    if not prompts:
        return []
    
    # Batch build embeddings for all prompts upfront to avoid redundant work
    prompt_embeddings = [build_embedding(text) for text in prompts]
    
    # Extract profile data once
    profile_embedding = profile.get('embedding') if isinstance(profile, Mapping) else None
    include_phrases = list(profile.get('include_phrases') or []) if isinstance(profile, Mapping) else []
    avoid_phrases = list(profile.get('avoid_phrases') or []) if isinstance(profile, Mapping) else []
    
    # Build suggestions once since they're the same for all prompts
    suggestions = []
    if include_phrases:
        suggestions.append(f"Lean on phrases like: {', '.join(include_phrases[:3])}.")
    if avoid_phrases:
        suggestions.append(f"Avoid overusing: {', '.join(avoid_phrases[:2])}.")
    
    results = []
    for text_embedding in prompt_embeddings:
        score = cosine_similarity(profile_embedding or {}, text_embedding)
        drift = score < threshold
        message = None
        if drift:
            message = "Closer to your voice: tighten cadence and reuse your go-to phrases."
        results.append({
            'score': round(score, 4),
            'drift': drift,
            'message': message,
            'suggestions': suggestions.copy()
        })
    
    return results

def analyze_samples(samples: list[str]) -> dict:
    """
    Analyze a list of text samples to build a voice profile.
    Returns a dictionary containing the voice profile data.
    """
    if not samples:
        return {}
        
    # Basic analysis
    structure = _analyze_structure(samples)
    
    # Tokenize all samples
    all_tokens = []
    for s in samples:
        all_tokens.extend(_tokenize(s))
        
    # Word frequency
    word_counts = Counter(all_tokens)
    total_words = len(all_tokens)
    
    # Extract common phrases/words (simplified)
    common_words = [w for w, c in word_counts.most_common(20) if len(w) > 3] # Filter short words
    
    return {
        'samples': samples,
        'structure': structure,
        'common_words': common_words,
        'analyzed_at': datetime.now(timezone.utc).isoformat(),
        'sample_count': len(samples)
    }

STOPWORDS = {
    'the', 'and', 'a', 'to', 'of', 'in', 'i', 'is', 'that', 'it', 'on', 'you', 'this', 'for', 'but', 'with', 'are', 'have', 'be', 'at', 'or', 'as', 'was', 'so', 'if', 'out', 'not', 'an', 'my', 'we', 'they', 'just', 'do', 'can', 'from', 'by', 'about', 'what', 'all', 'your', 'me', 'up', 'one', 'no', 'when', 'like', 'time', 'has', 'will', 'there', 'go', 'get', 'how', 'know', 'take', 'make', 'see', 'come', 'think', 'look', 'want', 'give', 'use', 'find', 'tell', 'ask', 'work', 'seem', 'feel', 'try', 'leave', 'call'
}
