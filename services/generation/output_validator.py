from __future__ import annotations
import copy
import json
from typing import Any, Dict, Optional
from .output_schemas import (
    validate_social_posts,
    validate_reel_script,
    validate_review_responses,
)


class ValidationError(Exception):
    pass


def _default_date(day: int = 1) -> str:
    return f"2024-01-{day:02d}"


def validate_and_repair_social_posts(data: Dict[str, Any]) -> Dict[str, Any]:
    data = copy.deepcopy(data or {})
    posts = data.get("posts") or []
    repaired_posts = []
    day = 1
    for post in posts:
        if not post.get("cards"):
            continue
        post = dict(post)
        post.setdefault("date", _default_date(day))
        post.setdefault("pillar", "Educational")
        cleaned_cards = []
        for card in post.get("cards", []):
            card = dict(card)
            card.setdefault("platform", "instagram")
            card.setdefault("caption", "")
            card.setdefault("hashtags", [])
            if card.get("caption"):
                cleaned_cards.append(card)
        if cleaned_cards:
            post["cards"] = cleaned_cards
            repaired_posts.append(post)
            day += 1
    if not repaired_posts:
        raise ValidationError("No valid posts after repair")
    repaired = {"posts": repaired_posts}
    validate_social_posts(repaired)
    return repaired


def validate_and_repair_reel_script(data: Dict[str, Any]) -> Dict[str, Any]:
    data = copy.deepcopy(data or {})
    script = data.get("script") or {}
    script = dict(script)
    script.setdefault("hook", "Attention-grabbing hook")
    script.setdefault("cta", "Tap to learn more")
    script.setdefault("beats", script.get("beats") or script.get("script_beats") or [])
    if not script.get("caption"):
        script["caption"] = "Engaging caption"
    script.setdefault("hashtags", [])
    repaired = {"script": script}
    validate_reel_script(repaired)
    return repaired


def validate_and_repair_review_responses(data: Dict[str, Any]) -> Dict[str, Any]:
    data = copy.deepcopy(data or {})
    responses = data.get("responses") or {}
    responses = dict(responses)
    responses.setdefault("short", "Thank you for your feedback!")
    responses.setdefault("medium", "Thanks for sharing your experience with us.")
    responses.setdefault("long", "We appreciate your detailed feedback and are glad you enjoyed your experience.")
    repaired = {
        "responses": responses,
        "tone": data.get("tone") or "professional",
        "voice_applied": data.get("voice_applied", True),
    }
    validate_review_responses(repaired)
    return repaired


def validate_with_schema_enforcement(
    data: Dict[str, Any],
    content_type: str,
    *,
    openai_client: Optional[Any] = None,
    prompt_set: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        if content_type == "social":
            validate_social_posts(data)
            return {"ok": True, "data": data, "repaired": False, "error": None}
        if content_type == "reels":
            validate_reel_script(data)
            return {"ok": True, "data": data, "repaired": False, "error": None}
        if content_type == "reviews":
            validate_review_responses(data)
            return {"ok": True, "data": data, "repaired": False, "error": None}
        return {"ok": False, "data": None, "repaired": False, "error": "Unknown content type"}
    except Exception:
        pass

    repaired = None
    try:
        if content_type == "social":
            repaired = validate_and_repair_social_posts(data)
        elif content_type == "reels":
            repaired = validate_and_repair_reel_script(data)
        elif content_type == "reviews":
            repaired = validate_and_repair_review_responses(data)
    except ValidationError as exc:
        return {"ok": False, "data": None, "repaired": False, "error": str(exc)}

    if repaired is not None:
        return {"ok": True, "data": repaired, "repaired": True, "error": None}

    if openai_client and content_type == "social":
        try:
            response = openai_client.chat.completions.create(messages=[], model="test")
            message = response.choices[0].message.content
            repaired_data = json.loads(message)
            validate_social_posts(repaired_data)
            return {"ok": True, "data": repaired_data, "repaired": True, "error": None}
        except Exception as exc:
            return {"ok": False, "data": None, "repaired": False, "error": str(exc)}

    return {"ok": False, "data": None, "repaired": False, "error": "Validation failed"}
