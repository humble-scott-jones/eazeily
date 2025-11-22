import math
import re
from collections import Counter
from datetime import datetime
from typing import Iterable, Mapping


WORD_RE = re.compile(r"[a-zA-Z'][a-zA-Z']*")
STOPWORDS = {
    'the', 'and', 'a', 'to', 'of', 'in', 'for', 'on', 'with', 'is', 'it', 'this', 'that', 'at', 'by', 'an',
    'be', 'are', 'as', 'from', 'or', 'we', 'you', 'your', 'our', 'us', 'about'
}


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    return WORD_RE.findall(text.lower())


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
    cleaned = [s.strip() for s in samples if isinstance(s, str) and s.strip()]
    if not cleaned:
        return {}
    embeddings = [build_embedding(text) for text in cleaned]
    merged = merge_embeddings(embeddings)
    tokens: list[str] = []
    for text in cleaned:
        tokens.extend(_tokenize(text))
    include_phrases = _top_phrases(tokens, 7)
    avoid_phrases = [t for t in include_phrases if len(t) <= 3][:3]
    avg_length = sum(len(text.split()) for text in cleaned) / len(cleaned)
    example_lines = cleaned[:3]
    return {
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'sample_count': len(cleaned),
        'avg_length': round(avg_length, 2),
        'include_phrases': include_phrases,
        'avoid_phrases': avoid_phrases,
        'example_lines': example_lines,
        'embedding': merged,
    }


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
    """Batch evaluate multiple text samples against a voice profile.
    
    This is a convenience wrapper around assess_text that processes a list of
    prompts and returns individual assessment results for each.
    
    Args:
        profile: A voice profile dict (typically from profile_from_samples).
        prompts: List of text samples to evaluate.
        threshold: Minimum cosine similarity (0.0 to 1.0) to avoid drift.
            Default 0.72. See assess_text for details.
    
    Returns:
        A list of assessment dicts (one per prompt), each in the format returned
        by assess_text.
    """
    results = []
    for text in prompts:
        results.append(assess_text(profile, text, threshold=threshold))
    return results
