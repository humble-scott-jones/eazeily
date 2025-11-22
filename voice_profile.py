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
            'suggestions': suggestions
        })
    
    return results
