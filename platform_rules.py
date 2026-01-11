"""Shared platform rules and heuristics for generating channel-specific copy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass
class PlatformRule:
    key: str
    label: str
    max_length: int
    max_hashtags: int
    cta: str
    hashtag_prefix: str = "#"
    hashtag_position: str = "end"
    link_note: str | None = None
    thumbnail_note: str | None = None


PLATFORM_RULES: dict[str, PlatformRule] = {
    "twitter": PlatformRule(
        key="twitter",
        label="X / Twitter",
        max_length=260,
        max_hashtags=3,
        cta="Reply with your take or tag a friend",
        link_note="Keep URLs short; avoid more than one link.",
        thumbnail_note="Lead with the hook in frame 1 for the preview",
    ),
    "linkedin": PlatformRule(
        key="linkedin",
        label="LinkedIn",
        max_length=1100,
        max_hashtags=5,
        cta="Add your perspective below or DM for details",
        link_note="Link after the first 1–2 lines so the intro hooks readers.",
        thumbnail_note="Use a bold headline overlay that matches the hook",
    ),
    "instagram": PlatformRule(
        key="instagram",
        label="Instagram",
        max_length=2000,
        max_hashtags=12,
        cta="Save + share if this helps; link in bio for more",
        hashtag_prefix="#",
        hashtag_position="end",
        thumbnail_note="Cover text: 3–5 words, high contrast, subject centered",
    ),
    "facebook": PlatformRule(
        key="facebook",
        label="Facebook",
        max_length=1200,
        max_hashtags=4,
        cta="Drop a comment or share with someone who needs this",
        thumbnail_note="Use a friendly face and a single bold line of text",
    ),
    "tiktok": PlatformRule(
        key="tiktok",
        label="TikTok",
        max_length=1500,
        max_hashtags=5,
        cta="Try it and tell us how it goes in the comments",
        hashtag_prefix="#",
        link_note="Keep the CTA verbal—links are less visible here.",
        thumbnail_note="Hook in 4 words max. High-contrast caption on frame 1.",
    ),
    "youtube": PlatformRule(
        key="youtube",
        label="YouTube Shorts",
        max_length=5000,
        max_hashtags=6,
        cta="Subscribe for more and check the pinned link",
        hashtag_prefix="#",
        hashtag_position="end",
        thumbnail_note="Thumbnail: bold promise + clear subject, avoid clutter",
    ),
    "short_video": PlatformRule(
        key="short_video",
        label="Reels/Shorts",
        max_length=1500,
        max_hashtags=5,
        cta="Save this and share with someone who needs it",
        hashtag_prefix="#",
        thumbnail_note="Bold hook text, high contrast, centered subject",
    ),
    # Social Ads platforms
    "facebook_ads": PlatformRule(
        key="facebook_ads",
        label="Facebook Ads",
        max_length=125,
        max_hashtags=0,
        cta="Learn more",
        link_note="Include clear CTA button text (e.g., Shop Now, Sign Up).",
        thumbnail_note="Eye-catching image with minimal text overlay",
    ),
    "instagram_ads": PlatformRule(
        key="instagram_ads",
        label="Instagram Ads",
        max_length=125,
        max_hashtags=0,
        cta="Shop now",
        link_note="Keep copy concise for mobile viewers.",
        thumbnail_note="High-quality visual with brand logo",
    ),
    "linkedin_ads": PlatformRule(
        key="linkedin_ads",
        label="LinkedIn Ads",
        max_length=150,
        max_hashtags=0,
        cta="Learn more",
        link_note="Professional tone, focus on value proposition.",
        thumbnail_note="Professional imagery, clear headline",
    ),
    "twitter_ads": PlatformRule(
        key="twitter_ads",
        label="X Ads",
        max_length=280,
        max_hashtags=2,
        cta="Click to see more",
        link_note="Concise and direct messaging.",
        thumbnail_note="Bold, simple visuals that stand out in feed",
    ),
    "tiktok_ads": PlatformRule(
        key="tiktok_ads",
        label="TikTok Ads",
        max_length=100,
        max_hashtags=0,
        cta="Watch now",
        link_note="Native feel, avoid overly promotional tone.",
        thumbnail_note="Dynamic, attention-grabbing first frame",
    ),
    # Reputation/Support
    "review_response": PlatformRule(
        key="review_response",
        label="Review Response",
        max_length=500,
        max_hashtags=0,
        cta="Thank you for your feedback",
        thumbnail_note=None,
    ),
}


DEFAULT_VARIANT_PLATFORMS: Tuple[str, ...] = (
    "twitter",
    "linkedin",
    "instagram",
    "facebook",
    "tiktok",
    "youtube",
    "short_video",
)


def truncate_with_ellipsis(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: max(limit - 1, 0)].rstrip() + "…"


def format_hashtags(raw: Iterable[str], max_count: int, prefix: str = "#") -> Tuple[List[str], bool]:
    cleaned: List[str] = []
    seen = set()
    for tag in raw:
        if not tag:
            continue
        tag_str = str(tag).strip()
        if not tag_str:
            continue
        if not tag_str.startswith(prefix):
            tag_str = f"{prefix}{tag_str}"
        tag_key = tag_str.lower()
        if tag_key in seen:
            continue
        seen.add(tag_key)
        cleaned.append(tag_str)
    trimmed = False
    if len(cleaned) > max_count:
        cleaned = cleaned[:max_count]
        trimmed = True
    return cleaned, trimmed


def apply_platform_rules(
    body: str,
    platform: str,
    hashtags: Iterable[str],
    pillar_name: str | None = None,
    goals: Iterable[str] | None = None,
    company: str | None = None,
) -> dict:
    platform_key = (platform or "").lower()
    rule = PLATFORM_RULES.get(platform_key)
    if not rule:
        rule = PlatformRule(
            key=platform_key or "default",
            label=platform or "Default",
            max_length=1500,
            max_hashtags=5,
            cta="Comment or share if this resonates",
            thumbnail_note=None,
        )

    warnings: List[str] = []
    cleaned_hashtags, trimmed = format_hashtags(hashtags, rule.max_hashtags, rule.hashtag_prefix)
    if trimmed:
        warnings.append(f"Trimmed hashtags to {rule.max_hashtags} for {rule.label}.")

    goal_hint = ", ".join(goals or [])
    cta_line = rule.cta
    if goal_hint:
        cta_line = f"{cta_line} ({goal_hint})."
    if rule.link_note:
        # Ensure there is a space after the period if needed
        if not cta_line.endswith(('.', '!', '?')):
            cta_line += '.'
        cta_line = f"{cta_line} {rule.link_note.strip()}"

    hashtag_block = " ".join(cleaned_hashtags)
    parts = [body.strip(), "", cta_line]
    if rule.hashtag_position == "end" and hashtag_block:
        parts.extend(["", hashtag_block])
    composed = "\n".join([p for p in parts if p != ""])

    if len(composed) > rule.max_length:
        # Calculate the fixed length of non-body parts (CTA, hashtags, separators)
        sep_cta = 1 if cta_line else 0  # newline before CTA
        sep_hash = 1 if (rule.hashtag_position == "end" and hashtag_block) else 0  # newline before hashtags
        # Number of newlines: between body and CTA, and between CTA and hashtags if present
        non_body_parts = ""
        if cta_line:
            non_body_parts += ("\n" if non_body_parts else "") + cta_line
        if rule.hashtag_position == "end" and hashtag_block:
            non_body_parts += "\n" + hashtag_block
        non_body_length = len(non_body_parts)
        # Also account for the newline after the body if CTA or hashtags are present
        if non_body_parts:
            non_body_length += 1  # newline after body
        allowed_body = rule.max_length - non_body_length
        if allowed_body < 0:
            allowed_body = 0
        trimmed_body = truncate_with_ellipsis(body.strip(), allowed_body)
        warnings.append(f"Trimmed copy to fit {rule.label} limit of {rule.max_length} characters.")
        parts = [trimmed_body] if trimmed_body else []
        if cta_line:
            parts.append(cta_line)
        if rule.hashtag_position == "end" and hashtag_block:
            parts.append(hashtag_block)
        composed = "\n".join(parts)
        # As a last resort, if composed is still too long (due to unexpected formatting), truncate the whole thing
        if len(composed) > rule.max_length:
            composed = truncate_with_ellipsis(composed, rule.max_length)

    variant_payload = {
        "text": composed,
        "warnings": warnings,
        "hashtags": cleaned_hashtags,
        "cta": cta_line,
        "thumbnail_note": rule.thumbnail_note,
        "platform": platform_key,
        "platform_label": rule.label,
    }

    if rule.thumbnail_note:
        context_hint = pillar_name or company
        if context_hint and "{" not in rule.thumbnail_note:
            variant_payload["thumbnail_note"] = f"{rule.thumbnail_note} ({context_hint})"

    return variant_payload

