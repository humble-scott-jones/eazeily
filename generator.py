import json
import os
import re
import time
from datetime import timedelta, date
from pathlib import Path
from typing import Optional, Any, Mapping, Sequence

PILLARS_BY_DEFAULT = [
    ("Educational", "Share a quick tip that solves a common problem for your audience."),
    ("Behind-the-Scenes", "Show a candid look at your process, team, or workspace."),
    ("Testimonial/Social Proof", "Share a short customer quote and the outcome they achieved."),
    ("Product/Offer", "Highlight one offering with benefits, price (optional), and CTA."),
    ("Engagement", "Ask a question or run a simple poll to spark comments."),
    ("Story", "Tell a brief story of a challenge → action → result."),
]

PLATFORM_HINTS = {
    "instagram": "Keep it visual, 1–2 short paragraphs, 8–12 niche hashtags.",
    "facebook": "Conversational tone, 2–3 short paragraphs. Invite replies.",
    "linkedin": "Value-forward, concise, 1–2 actionable insights, 3–6 hashtags.",
    "tiktok": "Hook in first sentence, keep lines punchy, suggest a shot list.",
    "twitter": "Short & punchy. 1–2 tweets per post; avoid walls of text.",
}

USE_OPENAI_FOR_POSTS = bool(os.getenv('OPENAI_API_KEY') or os.getenv('USE_OPENAI_FOR_POSTS'))
_openai_client = None
_TREND_MODEL = os.getenv('OPENAI_TRENDS_MODEL', 'gpt-4o-mini')
_CACHE_DIR = Path(os.getenv('TREND_CACHE_DIR') or (Path(__file__).resolve().parent / '.cache'))
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _slugify_industry(industry: str) -> str:
    if not industry:
        return 'general'
    slug = re.sub(r'[^a-z0-9]+', '-', industry.strip().lower())
    return slug.strip('-') or 'general'


def _trend_cache_path(industry: str) -> str:
    slug = _slugify_industry(industry)
    return str(_CACHE_DIR / f'trends-{slug}.json')


def _extract_openai_content(response) -> Optional[str]:
    try:
        if isinstance(response, dict):
            choices = response.get('choices') or []
        else:
            choices = getattr(response, 'choices', None)
        if not choices:
            return None
        first = choices[0]
        message = getattr(first, 'message', None)
        if message and getattr(message, 'content', None):
            return message.content  # type: ignore[attr-defined]
        if isinstance(first, dict):
            msg = first.get('message') or {}
            if isinstance(msg, dict) and msg.get('content'):
                return str(msg.get('content'))
        text = getattr(first, 'text', None)
        if text:
            return str(text)
    except Exception:
        return None
    return None


def _parse_trend_payload(raw: str) -> Optional[list[dict[str, Any]]]:
    if not raw:
        return None
    raw = raw.strip()
    candidate = raw
    if not raw.startswith('['):
        start = raw.find('[')
        end = raw.rfind(']')
        if start != -1 and end != -1 and end > start:
            candidate = raw[start:end + 1]
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        for key in ('trends', 'items', 'data'):
            val = data.get(key)
            if isinstance(val, list):
                data = val
                break
        else:
            data = [data]
    if not isinstance(data, list):
        return None
    out: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict):
            out.append(item)
        else:
            out.append({'topic': str(item)})
    return out


def _load_cached_trends(cache_path: str, ttl_hours: int) -> Optional[list[dict[str, Any]]]:
    if ttl_hours <= 0:
        return None
    if not os.path.exists(cache_path):
        return None
    age = time.time() - os.path.getmtime(cache_path)
    if age > ttl_hours * 3600:
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
            if isinstance(data, list):
                return data
    except Exception:
        return None
    return None


def _save_trend_cache(cache_path: str, payload: Sequence[Mapping[str, Any]]) -> None:
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    try:
        with open(cache_path, 'w', encoding='utf-8') as fh:
            json.dump(list(payload), fh)
    except Exception:
        pass


def _fallback_trends(industry: str) -> list[dict[str, str]]:
    focus = (industry or 'local business').strip() or 'local business'
    title = focus.title()
    return [
        {'topic': f'{title} customer stories', 'rationale': 'Spotlight authentic wins to build trust', 'confidence': 'medium'},
        {'topic': f'Behind-the-scenes of {title}', 'rationale': 'Show process and people for transparency', 'confidence': 'medium'},
        {'topic': f'{title} seasonal offers', 'rationale': 'Tie promos to timely moments for urgency', 'confidence': 'medium'}
    ]


def fetch_trend_context(industry: str, ttl_hours: int = 6) -> list[dict[str, Any]]:
    cache_path = _trend_cache_path(industry or 'general')
    cached = _load_cached_trends(cache_path, ttl_hours)
    if cached is not None:
        return cached

    if USE_OPENAI_FOR_POSTS and _openai_client:
        try:
            prompt = (
                "List three emerging content trends for the {industry} industry. "
                "Respond ONLY with a JSON array where each item has 'topic', 'rationale', and 'confidence'."
            ).format(industry=industry or 'local business')
            response = _openai_client.chat.completions.create(  # type: ignore[attr-defined]
                model=_TREND_MODEL,
                messages=[
                    {'role': 'system', 'content': 'You are a marketing strategist.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.4
            )
            content = _extract_openai_content(response)
            parsed = _parse_trend_payload(content or '')
            if parsed:
                _save_trend_cache(cache_path, parsed)
                return parsed
        except Exception:
            return []

    fallback = _fallback_trends(industry)
    _save_trend_cache(cache_path, fallback)
    return fallback

def default_hashtags(industry: str, niche_keywords: list[str]):
    base = [f"#{industry.replace(' ', '')[:18]}", "#SmallBusiness", "#LocalBiz", "#BehindTheScenes", "#Tips"]
    extra = [f"#{k.strip().replace(' ', '')[:18]}" for k in niche_keywords if k.strip()]
    seen = set()
    tags = []
    for t in base + extra:
        t_low = t.lower()
        if t_low not in seen:
            tags.append(t)
            seen.add(t_low)
    return tags[:12]

def to_sentence_case(s: str):
    if not s:
        return s
    return s[0].upper() + s[1:]

def make_caption(industry: str, tone: str, pillar_name: str, pillar_hint: str,
                 platform: str, brand_keywords: list[str], hashtags: list[str], goals: list[str], company: str = "", theme: Optional[str] = None):
    tone_blurb = {
        "friendly": "Warm, encouraging, and conversational.",
        "professional": "Clear, confident, and value-focused.",
        "playful": "Upbeat, witty, and a bit cheeky.",
        "inspirational": "Uplifting, thoughtful, and mission-driven."
    }.get(tone.lower(), "Conversational and helpful.")

    platform_hint = PLATFORM_HINTS.get(platform.lower(), "Make it concise and useful.")
    brand_line = f" ({', '.join(brand_keywords)})" if brand_keywords else ""
    goal_line = f"Focus: {', '.join(goals)}." if goals else ""

    company_line = f"From {company}." if company else ""
    theme_line = f"Theme: {theme}." if theme else ""
    body = (
        f"{pillar_name} • {industry}{brand_line}\n"
        f"{pillar_hint}\n\n"
        f"{company_line}\n"
        f"{theme_line}\n"
        f"{goal_line}\n"
        f"Tone: {tone_blurb}\n"
        f"Platform tip: {platform_hint}\n\n"
        f"CTA: Tell us what you think below 👇"
    )

    tags = " ".join(hashtags)
    return f"{body}\n\n{tags}"

def make_full_post(industry: str, tone: str, pillar_name: str, pillar_hint: str,
                   platform: str, brand_keywords: list[str], hashtags: list[str], goals: list[str], company: str = "", theme: Optional[str] = None):
    """Legacy function for backward compatibility with tests."""
    caption = make_caption(industry, tone, pillar_name, pillar_hint, platform, brand_keywords, hashtags, goals, company, theme)
    return {
        'caption': caption,
        'theme': theme
    }

def image_prompt(industry: str, pillar_name: str, brand_keywords: list[str], company: str = ""):
    kw = ", ".join(brand_keywords) if brand_keywords else "on-brand colors"
    company_part = f"Company: {company}. " if company else ""
    return (f"High-quality photo for social post. {company_part}Industry: {industry}. "
            f"Content pillar: {pillar_name}. Style: natural light, minimal background, {kw}.")

def make_reel_plan(industry: str, pillar_name: str, brand_keywords: list[str], tone: str, company: str = "", reel_style: Optional[str] = None, goals: Optional[list[str]] = None, niche_keywords: Optional[list[str]] = None, length_seconds: int = 30, production_tier: str = "solo"):
    # structured reel plan; tailor suggestions by industry and an optional `reel_style` preference
    style = (reel_style or "Face-camera tips")
    goals = goals or []
    niche_keywords = niche_keywords or []
    length_seconds = int(length_seconds or 30)

    # industry-specific modifiers to make outputs more relevant to the professional
    industry_key = (industry or "").lower()
    industry_mods = {
        "realtor": {
            "cta": "Schedule a showing or DM for details.",
            "thumb_extra": "Show a room or exterior with bold feature text",
            "hook_pfx": "House tip:"
        },
        "restaurant": {
            "cta": "Reserve a table or check the menu link.",
            "thumb_extra": "Close-up of dish with appetizing colors",
            "hook_pfx": "Chef's secret:"
        },
        "retail": {
            "cta": "Shop now or visit us in-store.",
            "thumb_extra": "Product shot with clear price/text",
            "hook_pfx": "New in:"
        },
        "fitness": {
            "cta": "Try this move & tag us in your video.",
            "thumb_extra": "Action shot with energetic typography",
            "hook_pfx": "Quick workout:"
        },
        "artisan": {
            "cta": "Shop the collection or visit the studio.",
            "thumb_extra": "Close-up of hands at work",
            "hook_pfx": "Behind the craft:"
        },
        "coach": {
            "cta": "Book a consult or grab the free worksheet.",
            "thumb_extra": "Headshot with clear value statement",
            "hook_pfx": "Quick tip:"
        },
        "nonprofit": {
            "cta": "Learn how to help or donate today.",
            "thumb_extra": "Impact photo with short stat overlay",
            "hook_pfx": "Impact story:"
        },
        "home_services": {
            "cta": "Book an estimate or ask for a quote.",
            "thumb_extra": "Before/after split with clear label",
            "hook_pfx": "Before & after:"
        },
        "healthcare": {
            "cta": "Book a consult or learn more on our site.",
            "thumb_extra": "Friendly staff or clinic photo with clear text",
            "hook_pfx": "Health tip:"
        }
    }

    mods = industry_mods.get(industry_key, {"cta": "Comment / DM / Link in bio", "thumb_extra": "Clean bold text, subject centered", "hook_pfx": "Quick tip:"})

    # pick some hooks based on style
    hooks_map = {
        "Face-camera tips": [
            "3 mistakes costing you customers 👇",
            "Try this before your next post…",
            "The 30-second fix for engagement"
        ],
        "Property b-roll + captions": [
            f"Inside this {industry} feature in 30s 🏡",
            "3 features you’ll miss if you scroll fast…",
            "Before/After: tiny changes, big feel"
        ],
        "Product b-roll + captions": [
            f"Check out this {pillar_name} in 30s ✨",
            "3 reasons customers love this…",
            "Quick tour: what makes it special"
        ],
        "Local hotspot montage": [
            f"Spend a perfect morning in {pillar_name} ☀️",
            "Hidden gem you’ve gotta try…",
            "Locals know this trick 🤫"
        ],
        "Story + before/after": [
            "From idea → launch in 30s",
            "We almost gave up—then this happened",
            "Tiny change → big result"
        ],
        "Workout montage": [
            "Quick 3-move sequence to level up your routine",
            "Try this superset for max results",
            "Short challenge: do 3 rounds"
        ]
    }

    # allow fallback to a style-agnostic set if exact match not found
    chosen_hooks = hooks_map.get(style) or hooks_map.get("Face-camera tips")
    if not chosen_hooks:
        chosen_hooks = hooks_map["Face-camera tips"]
    # produce ranked hooks (industry-prefixed variants) and alternates
    ranked_hooks = [f"{mods.get('hook_pfx','Quick tip:')} {h}" for h in chosen_hooks]
    # add short alternates
    for h in chosen_hooks[:2]:
        short = h.replace('…', '').split(' - ')[0].strip()
        if short and short not in ranked_hooks:
            ranked_hooks.append(short)
    hook = ranked_hooks[0]

    # script beats: timestamps for the requested length_seconds
    total = max(10, length_seconds)
    # percentage allocation for Hook, Problem, Tip, Example, CTA
    slots = [0.12, 0.25, 0.35, 0.18, 0.10]
    bounds = []
    acc = 0.0
    for pct in slots:
        start = int(acc * total)
        acc += pct
        end = int(acc * total)
        bounds.append((start, end))

    problem_line = "A common pain point your audience has and why it matters."
    if goals:
        problem_line = f"Pain point related to: {', '.join(goals[:2])}."
    tip_line = "One actionable tip the viewer can try right away."
    example_line = f"Quick example or result — mention {company} if relevant." if company else "Quick example or result to make it real."
    cta_line = mods.get('cta')

    beats = [
        {"start_s": bounds[0][0], "end_s": bounds[0][1], "osd": "Hook", "line": hook},
        {"start_s": bounds[1][0], "end_s": bounds[1][1], "osd": "Problem", "line": problem_line},
        {"start_s": bounds[2][0], "end_s": bounds[2][1], "osd": "Tip", "line": tip_line},
        {"start_s": bounds[3][0], "end_s": bounds[3][1], "osd": "Example", "line": example_line},
        {"start_s": bounds[4][0], "end_s": bounds[4][1], "osd": "CTA", "line": cta_line}
    ]

    # combine style-based shot guidance with industry-specific suggestions
    shot_map = {
        "Face-camera tips": [
            "Front-facing A-roll, eye-level, natural light",
            "Cutaways: screen recording, product close-up",
            "End with CTA text overlay"
        ],
        "Property b-roll + captions": [
            "Exterior wide → entry → kitchen → feature highlight",
            "Quick pans, 0.8x speed ramp between rooms",
            "On-screen captions for each highlight"
        ],
        "Product b-roll + captions": [
            "Wide shot → detail close-ups → demo",
            "Match edits to beat; short clips per feature",
            "Add caption overlays for key specs"
        ],
        "Local hotspot montage": [
            "Sign → interior → hero item → smiling staff → crowd",
            "Match cuts to beat; 0.5s–1.0s per clip",
            "End with text: name + location"
        ],
        "Story + before/after": [
            "Talking head intro",
            "B-roll: before clip/photos",
            "After reveal with text overlay"
        ],
        "Workout montage": [
            "Demonstration A-roll",
            "Close-ups on form",
            "Speed ramps and finishing CTA"
        ]
    }

    style_shots = shot_map.get(style, ["Talking head + a few cutaways, end with CTA"])
    # add industry-specific shot hints to the start of the list where helpful
    industry_shots = []
    if industry_key == 'realtor':
        industry_shots = ["Start with exterior wide, show hero room, highlight value props"]
    elif industry_key == 'restaurant':
        industry_shots = ["Close-up of dish, plating, hands prepping"]
    elif industry_key == 'fitness':
        industry_shots = ["Full-body demo shot, side view for form"]
    elif industry_key == 'artisan':
        industry_shots = ["Hands-on process close-ups, product reveal"]

    # convert simple descriptions into structured shots aligned to beats
    shot_list = []
    combined_shots = industry_shots + style_shots
    for idx, b in enumerate(beats):
        base = combined_shots[idx % max(1, len(combined_shots))]
        shot_list.append({
            "start_s": b["start_s"],
            "end_s": b["end_s"],
            "shot_type": base,
            "duration_s": b["end_s"] - b["start_s"],
            "notes": "Match cuts to spoken lines; stable framing; consider jump cuts for energy."
        })

    hashtags_all = default_hashtags(industry, brand_keywords + niche_keywords)
    hashtags = {"primary": hashtags_all[:3], "optional": hashtags_all[3:8]}
    thumb_prompt = f"Portrait thumbnail: {industry} • {style}. {mods.get('thumb_extra')}"

    # generate SRT text from beats
    def fmt_ts(s):
        ms = int(s * 1000)
        h = ms // 3600000
        ms -= h * 3600000
        m = ms // 60000
        ms -= m * 60000
        sec = ms // 1000
        ms = ms % 1000
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    srt_lines = []
    for i, b in enumerate(beats, start=1):
        start = fmt_ts(b["start_s"])
        end = fmt_ts(b["end_s"])
        text = b["line"]
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    srt_text = "\n".join(srt_lines)

    # music suggestion mapping by tone
    mood_map = {
        "friendly": "acoustic upbeat, 90-110 BPM",
        "professional": "minimal ambient, 60-80 BPM",
        "playful": "funky pop, 100-125 BPM",
        "inspirational": "uplifting cinematic, 70-100 BPM"
    }
    music = mood_map.get(tone.lower(), "neutral upbeat, 90 BPM")

    cta_variants = [{"type": "primary", "text": cta_line}, {"type": "soft", "text": "Learn more / link in bio"}, {"type": "engage", "text": "Comment your favorite"}]

    return {
        "style": style,
        "length_seconds": length_seconds,
        "ranked_hooks": ranked_hooks,
        "hook": hook,
        "beats": beats,
        "script_beats": [b.get('line') for b in beats],
        "shot_list": shot_list,
        "on_screen_text": [b.get('osd') for b in beats],
        "hashtags": hashtags,
        "cta": cta_line,
        "cta_variants": cta_variants,
        "thumbnail_prompt": thumb_prompt,
        "srt": srt_text,
        "music_suggestion": music,
        "production_tier": production_tier
    }

def unsplash_link(industry: str, pillar_name: str):
    q = f"{industry} {pillar_name}".replace(" ", "+")
    return f"https://source.unsplash.com/featured/?{q}"

def rolling_pillars():
    while True:
        for name, hint in PILLARS_BY_DEFAULT:
            yield (name, hint)

def generate_review_response(review_text: str, tone: str = "professional", company_name: str = "", industry: str = "") -> dict:
    """
    Generate a professional response to a customer review.
    
    Args:
        review_text: The customer's review text
        tone: Response tone ('professional', 'grateful', 'apologetic', 'friendly')
        company_name: Optional company name to include
        industry: Optional industry for tailored responses
        
    Returns:
        dict with 'response', 'method', and optionally 'detected_sentiment'
    """
    if not review_text or not review_text.strip():
        raise ValueError("Review text is required")
    
    review_text = review_text.strip()
    
    # Simple sentiment detection
    positive_words = ['great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'perfect', 'best', 'awesome', 'thank', 'appreciate', 'enjoyed', 'beautiful', 'clean', 'comfortable', 'helpful', 'friendly']
    negative_words = ['terrible', 'awful', 'horrible', 'worst', 'disappointed', 'disappointing', 'bad', 'poor', 'rude', 'dirty', 'uncomfortable', 'unhelpful', 'problem', 'issue', 'complaint', 'never', 'waste']
    
    review_lower = review_text.lower()
    positive_count = sum(1 for word in positive_words if word in review_lower)
    negative_count = sum(1 for word in negative_words if word in review_lower)
    
    if positive_count > negative_count:
        detected_sentiment = "positive"
    elif negative_count > positive_count:
        detected_sentiment = "negative"
    else:
        detected_sentiment = "neutral"
    
    # Industry-specific response templates
    industry_templates = {
        "house_host": {
            "positive": {
                "professional": "Thank you for choosing to stay with us! We're delighted to hear that you had a wonderful experience at {company}. We hope to welcome you back soon.",
                "grateful": "We're so grateful for your kind words about your stay at {company}! It means the world to us that you enjoyed your time here. Come back and visit us again soon!",
                "friendly": "Thanks so much for the lovely review of your stay at {company}! We're thrilled you had such a great time. Hope to see you back here again soon! 😊",
                "apologetic": "Thank you for your positive feedback about your stay at {company}. We're grateful for guests like you who appreciate the comforts of home."
            },
            "negative": {
                "professional": "We're sorry to hear about your experience at {company}. We take all feedback seriously and would like to discuss this further to ensure future stays are better. Please contact us directly so we can make this right.",
                "grateful": "Thank you for bringing this to our attention regarding your stay at {company}. We truly appreciate your feedback as it helps us improve. We'd love to speak with you personally to address your concerns.",
                "friendly": "Oh no, we're so sorry to hear about the issues during your stay at {company}! We really want to make this right. Can you please reach out to us directly so we can chat about how to improve your experience?",
                "apologetic": "We sincerely apologize for the difficulties you experienced during your stay at {company}. This is not the experience we strive to provide. Please contact us so we can discuss how to make amends."
            },
            "neutral": {
                "professional": "Thank you for staying with us at {company}. We appreciate you taking the time to share your feedback. We hope to have the opportunity to host you again in the future.",
                "grateful": "Thank you for choosing {company} for your stay. We value your feedback and are always working to improve. We hope to welcome you back soon!",
                "friendly": "Thanks for staying with us at {company}! We appreciate you sharing your thoughts. Hope we get to host you again sometime! 👍",
                "apologetic": "Thank you for your feedback about your stay at {company}. We're sorry if we fell short of your expectations and would welcome the chance to improve."
            }
        }
    }
    
    # Default templates for other industries
    default_templates = {
        "positive": {
            "professional": "Thank you for your positive feedback{company_part}! We appreciate you taking the time to share your experience with us.",
            "grateful": "We're so grateful for your kind words{company_part}! Thank you for choosing us and for sharing your positive experience.",
            "friendly": "Thanks so much for the great review{company_part}! We're thrilled you had a wonderful experience. 😊",
            "apologetic": "Thank you for your positive feedback{company_part}. We're grateful for customers like you who appreciate our service."
        },
        "negative": {
            "professional": "We're sorry to hear about your experience{company_part}. We take all feedback seriously and would like to discuss this further to ensure we can better serve you in the future.",
            "grateful": "Thank you for bringing this to our attention{company_part}. We truly appreciate your feedback as it helps us improve our service.",
            "friendly": "Oh no, we're so sorry to hear about this{company_part}! We really want to make this right. Can you please reach out to us directly?",
            "apologetic": "We sincerely apologize for any inconvenience or disappointment you experienced{company_part}. This is not the level of service we strive to provide."
        },
        "neutral": {
            "professional": "Thank you for your feedback{company_part}. We appreciate you taking the time to share your thoughts with us.",
            "grateful": "Thank you for your feedback{company_part}. We value all input from our customers as it helps us continue to improve.",
            "friendly": "Thanks for sharing your thoughts{company_part}! We appreciate you taking the time to leave feedback. 👍",
            "apologetic": "Thank you for your feedback{company_part}. We're sorry if we fell short of your expectations."
        }
    }
    
    # Get templates based on industry
    templates = industry_templates.get(industry.lower(), default_templates)
    
    # Get the appropriate template
    template = templates.get(detected_sentiment, templates["neutral"]).get(tone.lower(), templates["neutral"]["professional"])
    
    # Format company name
    company_part = f" about {company_name}" if company_name else ""
    
    # Generate response
    response = template.format(company=company_name or "our property", company_part=company_part)
    
    return {
        "response": response,
        "method": "template",
        "detected_sentiment": detected_sentiment
    }


def _coerce_start_day(value: Any) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    # fallback: treat anything else as "today"
    return date.today()


def generate_posts(
    profile: Optional[Mapping[str, Any]] = None,
    *,
    days: Optional[int] = None,
    start_day: Optional[date] = None,
    industry: str = "Business",
    tone: str = "friendly",
    platforms: Optional[list[str]] = None,
    brand_keywords: Optional[list[str]] = None,
    include_images: bool = True,
    niche_keywords: Optional[list[str]] = None,
    goals: Optional[list[str]] = None,
    company: str = "",
    details: Optional[Mapping[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Generate a list of posts for the requested period.

    Supports both keyword arguments and a single profile mapping. The mapping
    may contain keys like days, start_day, industry, tone, platforms, etc.
    """

    if isinstance(profile, Mapping):
        default = profile
        days = days or default.get("days") or default.get("plan_days")
        start_day = start_day or default.get("start_day")
        industry = default.get("industry", industry)
        tone = default.get("tone", tone)
        platforms = default.get("platforms", platforms)
        brand_keywords = default.get("brand_keywords", brand_keywords)
        include_images = default.get("include_images", include_images)
        niche_keywords = default.get("niche_keywords", niche_keywords)
        goals = default.get("goals", goals)
        company = default.get("company", company)
        details = default.get("details", details)

    days = int(days or 7)
    start_day = _coerce_start_day(start_day)
    industry = (industry or "Business").strip() or "Business"
    tone = tone or "friendly"
    platforms = list(platforms or ["instagram"])
    if not platforms:
        platforms = ["instagram"]
    brand_keywords = list(brand_keywords or [])
    niche_keywords = list(niche_keywords or [])
    goals = list(goals or [])
    details = dict(details or {})
    company = company or ""

    posts: list[dict[str, Any]] = []
    pillar_stream = rolling_pillars()
    hashtags = default_hashtags(industry, niche_keywords)

    for i in range(days):
        day = start_day + timedelta(days=i)
        pillar_name, pillar_hint = next(pillar_stream)

        # Generate platform-specific variants for this day
        variants = {}
        for p in platforms:
            caption = make_caption(
                industry=to_sentence_case(industry),
                tone=tone,
                pillar_name=pillar_name,
                pillar_hint=pillar_hint,
                platform=p,
                brand_keywords=brand_keywords,
                hashtags=hashtags,
                goals=goals,
                company=company,
                theme=details.get("note")
            )
            variants[p] = caption

        # Create one post per platform (maintains backward compatibility)
        for p in platforms:
            caption = variants[p]
            iprompt = image_prompt(industry, pillar_name, brand_keywords, company)
            img_url = unsplash_link(industry, pillar_name) if include_images else None

            reel_obj = None
            if p.lower() in ["instagram", "tiktok", "short_video"]:
                reel_style = details.get('reel_style')
                raw_length = details.get('reel_length')
                try:
                    reel_length = int(raw_length) if raw_length not in (None, "") else 30
                except (TypeError, ValueError):
                    reel_length = 30
                production_tier = details.get('production_tier') or 'solo'
                reel_obj = make_reel_plan(
                    industry,
                    pillar_name,
                    brand_keywords,
                    tone,
                    company,
                    reel_style,
                    goals=goals,
                    niche_keywords=niche_keywords,
                    length_seconds=reel_length,
                    production_tier=production_tier or 'solo'
                )

            posts.append({
                "date": day.isoformat(),
                "day_index": i + 1,
                "platform": p,
                "pillar": pillar_name,
                "caption": caption,
                "image_prompt": iprompt,
                "image_url": img_url,
                "reel": reel_obj,
                "variants": variants if len(platforms) > 1 else None
            })

    return posts
