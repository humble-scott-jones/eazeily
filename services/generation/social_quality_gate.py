from __future__ import annotations
from typing import Any, Dict, List
import re
from .social_validator import has_structure_signal, contains_banned_phrases


def _has_structure_signal(text: str) -> bool:
    # Prefer the shared validator but add a myth/fact multi-line helper
    if has_structure_signal(text):
        return True
    text = text or ""
    lower = text.lower()
    if "myth:" in lower and "fact:" in lower:
        return True
    myth_fact = re.search(r"myth:\s+.*\nfact:\s+.*", text, re.I | re.S)
    return bool(myth_fact)


def _check_coaching_language(caption: str) -> str | None:
    """Return a descriptive message if coaching language is detected."""
    reason = contains_banned_phrases(caption)
    if reason:
        return "Caption contains coaching/instructional language"
    return None


def evaluate_post_quality(post: Dict[str, Any]) -> Dict[str, Any]:
    caption = (post.get("caption") or "").strip()
    platform = (post.get("platform") or "").lower()
    errors: List[str] = []
    warnings: List[str] = []

    GENERIC_PHRASES = ["great", "amazing", "awesome", "incredible", "fantastic"]

    coaching_issue = _check_coaching_language(caption)
    if coaching_issue:
        errors.append(coaching_issue)

    if not _has_structure_signal(caption):
        errors.append("Caption lacks structure signal (numbered steps, bullets, examples)")

    # Soft warning for generic hype-y language to encourage specificity
    lower_caption = caption.lower()
    if any(phrase in lower_caption for phrase in GENERIC_PHRASES):
        warnings.append("Caption may be too generic; add specific, concrete value")

    # Minimum length checks by platform (twitter/x allows short form)
    if platform not in ("x", "twitter") and len(caption) < 40:
        errors.append(f"Caption too short for {platform or 'platform'}")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors, "warnings": warnings}


def evaluate_all_posts(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = []
    for post in posts:
        result = evaluate_post_quality(post)
        result["post"] = post
        results.append(result)
    passed = all(r.get("passed") for r in results)
    return {"passed": passed, "results": results}


def build_repair_prompt(post: Dict[str, Any], evaluation: Dict[str, Any]) -> List[Dict[str, str]]:
    platform = (post.get("platform") or "").lower()
    caption = post.get("caption") or ""
    issues = evaluation.get("errors") or []
    issues_text = "; ".join(issues) or "Improve quality"
    platform_hint = f"Platform: {platform}. Add a clear structure signal (numbered steps or bullets) and stay concise."
    system = {
        "role": "system",
        "content": (
            "You are a social copywriter. Rewrite the user's post to fix the listed issues. "
            "No meta commentary or advice. Return FINAL post copy only, no analysis."
        ),
    }
    user = {
        "role": "user",
        "content": (
            f"Original platform: {platform}. Original caption:\n{caption}\n\n"
            f"Issues to fix: {issues_text}.\n"
            "Rules: no coaching language (avoid phrases like \"you should\" or \"consider\"), "
            "include a structure signal (numbered steps or bullet points), keep the brand-safe tone, "
            "and return FINAL post copy only with hashtags if present."
        ),
    }
    return [system, user]


def attempt_repair(post: Dict[str, Any], evaluation: Dict[str, Any], openai_client: Any = None) -> Dict[str, Any]:
    if openai_client is None:
        return {"ok": False, "error": "No OpenAI client provided for repair"}

    try:
        messages = build_repair_prompt(post, evaluation)
        completion = openai_client.chat.completions.create(  # type: ignore[attr-defined]
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.4,
        )
        content = completion.choices[0].message.content if completion and completion.choices else ""
        repaired = {**post, "caption": content}
        return {"ok": True, "post": repaired}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
