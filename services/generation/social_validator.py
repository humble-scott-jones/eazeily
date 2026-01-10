from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from .output_schemas import validate_social_posts

BANNED_PHRASES = [
    "you should",
    "platform tip",
    "share a",
    "focus:",
    "consider ",
    "tip:",
    "make sure to",
    "don't forget to",
    "try to",
    "what to post",
    "suggestions for",
    "advice:",
    "here's what to say",
]

STRUCTURE_PATTERNS = [
    r"\b1\.\s",
    r"\b1\)",
    r"\bfirst\b",
    r"\bsecond\b",
    r"\bfinally\b",
    r"\bfor example\b",
    r"\bimagine\b",
    r"\bmyth:\b",
    r"\bfact:\b",
    r"• ",
    r"- ",
    r"\* ",
]


def contains_banned_phrases(caption: str) -> str | None:
    text = caption.lower() if caption else ""
    for phrase in BANNED_PHRASES:
        if phrase in text:
            return f"Caption contains banned phrase: {phrase}"
    return None


def has_structure_signal(caption: str) -> bool:
    text = caption.lower() if caption else ""
    return any(re.search(pattern, text, re.I | re.M) for pattern in STRUCTURE_PATTERNS)


def validate_hashtags(hashtags: List[str], platform: str) -> Optional[str]:
    if hashtags is None:
        return None
    normalized = []
    for tag in hashtags:
        if not isinstance(tag, str):
            return "Hashtags must be strings"
        if " " in tag:
            return f"Hashtag contains space: {tag}"
        if "/" in tag:
            return f"Hashtag contains slash: {tag}"
        normalized.append(tag if tag.startswith("#") else f"#{tag}")

    if platform.lower() == "instagram" and normalized:
        if len(normalized) < 8 or len(normalized) > 12:
            return "Instagram hashtags should include 8-12 items"
    return None


def validate_post_card(card: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    caption = card.get("caption", "") or ""
    platform = (card.get("platform") or "").lower()

    banned = contains_banned_phrases(caption)
    if banned:
        errors.append(banned)
    if not has_structure_signal(caption):
        errors.append("Caption lacks structure signal")

    hashtag_error = validate_hashtags(card.get("hashtags") or [], platform)
    if hashtag_error:
        errors.append(hashtag_error)

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors, "warnings": warnings}


def validate_and_repair_posts(posts: List[Dict[str, Any]], openai_client: Any = None) -> Dict[str, Any]:
    try:
        validate_social_posts({"posts": posts})
    except Exception as exc:
        return {"ok": False, "error": {"code": "output_not_post_ready", "message": str(exc)}}
    for post in posts:
        for card in post.get("cards", []):
            check = validate_post_card(card)
            if not check["passed"]:
                return {"ok": False, "error": {"code": "output_not_post_ready", "message": ";".join(check["errors"])} }
    return {"ok": True, "posts": posts}


def build_repair_prompt(post: Dict[str, Any], evaluation: Dict[str, Any]):
    # Lightweight proxy to keep imports working; delegate to social_quality_gate
    from .social_quality_gate import build_repair_prompt as _build
    return _build(post, evaluation)


def attempt_repair(post: Dict[str, Any], evaluation: Dict[str, Any], openai_client: Any = None):
    """Proxy to social_quality_gate.attempt_repair for backward compatibility."""
    from .social_quality_gate import attempt_repair as _attempt
    return _attempt(post, evaluation, openai_client=openai_client)
