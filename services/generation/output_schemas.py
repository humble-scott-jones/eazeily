from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict

SocialPostCard = Dict[str, Any]
SocialPosts = Dict[str, Any]
ReelScript = Dict[str, Any]
ReviewResponses = Dict[str, Any]


class UsedSignals(TypedDict, total=False):
    services_used: List[str]
    pains_used: List[str]
    outcomes_used: List[str]
    proof_used: List[str]
    differentiators_used: List[str]
    custom_chips_used: List[str]


class WorkspaceContext(TypedDict, total=False):
    company_name: str
    industry: str
    brand_kit: Dict[str, Any]
    brand_kit_tier: Optional[str]
    default_tone: Optional[str]
    platforms: Optional[List[str]]
    offerings: Optional[Any]
    audience: Optional[Any]
    compliance_notes: Optional[str]


BrandKitV1 = Dict[str, Any]


class SuccessResponse(TypedDict, total=False):
    ok: bool
    request_id: str
    data: Dict[str, Any]
    source: str
    mode: str
    openai_used: bool
    gemini_used: bool
    fallback_used: bool
    used_signals: UsedSignals
    summary: Optional[str]
    warnings: Optional[List[str]]


class ErrorResponse(TypedDict, total=False):
    ok: bool
    request_id: str
    error: Dict[str, Any]
    source: str
    mode: str
    openai_used: bool
    gemini_used: bool


def build_success_response(
    *,
    request_id: str,
    data: Dict[str, Any],
    source: str = "fallback",
    mode: str = "fallback_suggestions",
    openai_used: bool = False,
    gemini_used: bool = False,
    fallback_used: bool = True,
    used_signals: Optional[UsedSignals] = None,
    summary: Optional[str] = None,
    warnings: Optional[List[str]] = None,
) -> SuccessResponse:
    return {
        "ok": True,
        "request_id": request_id,
        "data": data,
        "source": source,
        "mode": mode,
        "openai_used": openai_used,
        "gemini_used": gemini_used,
        "fallback_used": fallback_used,
        "summary": summary,
        "warnings": warnings,
        "used_signals": used_signals
        or {
            "services_used": [],
            "pains_used": [],
            "outcomes_used": [],
            "proof_used": [],
            "differentiators_used": [],
            "custom_chips_used": [],
        },
    }


def build_error_response(
    *,
    request_id: str,
    code: str,
    message: str,
    source: str = "fallback",
    details: Optional[Dict[str, Any]] = None,
    gemini_used: bool = False,
    openai_used: bool = False,
) -> ErrorResponse:
    return {
        "ok": False,
        "request_id": request_id,
        "error": {"code": code, "message": message},
        "source": source,
        "mode": "error",
        "openai_used": openai_used,
        "gemini_used": gemini_used,
    }


def validate_social_posts(data: Dict[str, Any]) -> None:
    posts = data.get("posts")
    if not posts or not isinstance(posts, list):
        raise ValueError("non-empty 'posts' list is required and must contain non-empty 'posts' list")
    for post in posts:
        cards = post.get("cards")
        if not cards or not isinstance(cards, list):
            raise ValueError("posts must include cards array")
        for card in cards:
            if not card.get("platform") or not card.get("caption") or not str(card.get("caption")).strip():
                raise ValueError("platform and caption must be present and caption must be non-empty string")


def validate_reel_script(data: Dict[str, Any]) -> None:
    script = (data or {}).get("script", {})
    if not script or not script.get("hook") or not script.get("cta"):
        raise ValueError("script must include hook and cta")


def validate_review_responses(data: Dict[str, Any]) -> None:
    responses = (data or {}).get("responses", {})
    if not responses:
        raise ValueError("responses missing")

