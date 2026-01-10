from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, TypedDict, Tuple
from .social_validator import contains_banned_phrases, has_structure_signal


class SocialPostCard(TypedDict, total=False):
    platform: str
    caption: str
    hashtags: List[str]
    cta: Optional[str]
    media_idea: Optional[str]
    image_prompt: Optional[str]
    notes: List[str]
    date: Optional[str]
    pillar: Optional[str]


COACHING_PATTERNS = [
    "you should",
    "make sure",
    "consider ",
    "here's what to post",
    "platform tip",
    "share a",
]


def _contains_coaching_language(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(pat in lower for pat in COACHING_PATTERNS)


def _extract_hashtags(caption: str) -> Tuple[str, List[str]]:
    hashtags = re.findall(r"#\w+", caption or "")
    cleaned = re.sub(r"#\w+", "", caption or "").strip()
    return cleaned, hashtags


def _normalize_platform(name: str) -> str:
    name = (name or "").strip().lower()
    if name == "twitter":
        return "x"
    if name in ("ig", "insta"):
        return "instagram"
    return name


def normalize_and_guardrail(raw_output: Dict[str, Any]) -> Dict[str, Any]:
    warnings: List[str] = []

    # Handle wrapped response shapes {"data": {"posts": [...]}}
    posts = raw_output.get("data", {}).get("posts") if isinstance(raw_output.get("data"), dict) else raw_output.get("posts")
    if not isinstance(posts, list):
        return {
            "ok": False,
            "error": {"code": "invalid_output_format", "message": "Expected posts list"},
        }

    normalized_cards: List[SocialPostCard] = []

    for post in posts:
        if not isinstance(post, dict):
            continue
        date = post.get("date")
        pillar = post.get("pillar")
        voice_note = post.get("voice_note")

        for card in post.get("cards", []):
            if not isinstance(card, dict):
                continue
            caption_raw = card.get("caption", "") or ""
            if not caption_raw.strip():
                continue

            caption_clean, embedded_tags = _extract_hashtags(caption_raw)
            combined_hashtags_raw = card.get("hashtags") or []
            combined_hashtags = []
            for tag in list(dict.fromkeys([*(embedded_tags or []), *combined_hashtags_raw])):
                tag_str = str(tag)
                if not tag_str.startswith("#"):
                    tag_str = f"#{tag_str.lstrip('#')}"
                combined_hashtags.append(tag_str)

            if _contains_coaching_language(caption_raw):
                warnings.append("Caption contains coaching/instructional language")
            banned = contains_banned_phrases(caption_raw)
            if banned:
                warnings.append(banned)

            normalized_card: SocialPostCard = {
                "platform": _normalize_platform(card.get("platform", "")),
                "caption": caption_clean.strip(),
                "hashtags": combined_hashtags,
                "date": date,
                "pillar": pillar,
            }

            # Optional passthrough fields
            if card.get("cta"):
                normalized_card["cta"] = card["cta"]
            if card.get("media_idea"):
                normalized_card["image_prompt"] = card["media_idea"]
            if card.get("image_prompt"):
                normalized_card["image_prompt"] = card["image_prompt"]

            notes: List[str] = []
            if voice_note:
                notes.append(str(voice_note))
            raw_notes = card.get("notes")
            if isinstance(raw_notes, list):
                notes.extend([str(n) for n in raw_notes if n is not None])
            if notes:
                normalized_card["notes"] = notes

            normalized_cards.append(normalized_card)

    if not normalized_cards:
        return {"ok": False, "error": {"code": "no_valid_posts", "message": "No valid posts found"}}

    return {"ok": True, "posts": normalized_cards, "warnings": warnings}
