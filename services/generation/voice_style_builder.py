from __future__ import annotations
import re
from collections import Counter
from typing import Any, Dict, List, Sequence
from .prompt_compiler import VoiceFingerprint


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[\w']+|[\u2600-\u27bf\U0001f300-\U0001f6ff\U0001f900-\U0001f9ff]", text.lower())
    return tokens


def _analyze_sentence_structure(samples: Sequence[str]) -> Dict[str, Any]:
    lengths = []
    exclamations = 0
    for sample in samples:
        tokens = _tokenize(sample)
        lengths.append(len(tokens))
        exclamations += sample.count("!")
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths) if lengths else 0
    return {"avg_length": avg_length, "variance": variance, "exclamations": exclamations}


def _extract_top_phrases(samples: Sequence[str], limit: int = 10) -> List[str]:
    bigrams = Counter()
    for sample in samples:
        tokens = _tokenize(sample)
        for i in range(len(tokens) - 1):
            phrase = f"{tokens[i]} {tokens[i+1]}"
            bigrams[phrase] += 1
    most_common = [p for p, _ in bigrams.most_common(limit)]
    return most_common


def build_voice_style_guide(samples: Sequence[str], include_phrases: Sequence[str] | None = None, avoid_phrases: Sequence[str] | None = None) -> Dict[str, Any]:
    include_phrases = list(include_phrases or [])
    avoid_phrases = list(avoid_phrases or [])

    if not samples:
        return {
            "tone_descriptors": ["professional"],
            "sentence_length": "medium",
            "formatting": "plain",
            "vocabulary": {
                "top_phrases": include_phrases,
                "taboo_phrases": avoid_phrases,
            },
            "style_instruction": "Keep it concise, structured, and audience-friendly.",
            "signature_moves": [],
            "cta_patterns": [],
        }

    structure = _analyze_sentence_structure(samples)
    tone_descriptors: List[str] = []
    if structure.get("exclamations", 0) > 1:
        tone_descriptors.append("enthusiastic")
    if not tone_descriptors:
        tone_descriptors.append("professional")

    avg_len = structure.get("avg_length", 0)
    if avg_len <= 12:
        sentence_length = "short"
    elif avg_len >= 24:
        sentence_length = "long"
    else:
        sentence_length = "medium"

    top_phrases = _extract_top_phrases(samples, limit=8)
    top_phrases.extend(include_phrases)

    signature_moves: List[str] = []
    if any("?" in sample for sample in samples):
        signature_moves.append("rhetorical questions")

    cta_patterns: List[str] = []
    CTA_TRIGGERS = ["book", "join", "try", "share", "comment", "save", "signup", "sign up"]
    for sample in samples:
        lower = sample.lower()
        for trig in CTA_TRIGGERS:
            if trig in lower:
                cta_patterns.append(trig)
    cta_patterns = list(dict.fromkeys(cta_patterns))

    guide = {
        "tone_descriptors": list(dict.fromkeys(tone_descriptors)),
        "sentence_length": sentence_length,
        "formatting": "plain",
        "vocabulary": {
            "top_phrases": list(dict.fromkeys(top_phrases)),
            "taboo_phrases": list(dict.fromkeys(avoid_phrases)),
        },
        "style_instruction": "Keep it concise, structured, and audience-friendly.",
        "signature_moves": signature_moves,
        "cta_patterns": cta_patterns,
    }
    return guide


def get_style_guide_summary(guide: Dict[str, Any]) -> str:
    tone = ", ".join(guide.get("tone_descriptors", []))
    length = guide.get("sentence_length", "medium")
    phrases = guide.get("vocabulary", {}).get("top_phrases") or []
    return f"Tone: {tone}. Sentence length: {length}. Phrases: {', '.join(phrases[:3])}" if tone else f"Sentence length: {length}."
