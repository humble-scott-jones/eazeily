"""Output schemas for generation service responses.

Defines the expected structure of data returned from OpenAI and validators.
"""

from typing import Any, Dict, List, TypedDict, Optional


# Social Media Post Schemas
class SocialPostCard(TypedDict, total=False):
    """A single platform variant within a social media post."""
    platform: str
    caption: str
    hashtags: List[str]
    hook: Optional[str]
    cta: Optional[str]
    media_idea: Optional[str]
    alt_text: Optional[str]
    character_count: Optional[int]


class SocialPost(TypedDict):
    """A single day's social media post with multiple platform variants."""
    date: str
    pillar: str
    cards: List[SocialPostCard]
    voice_note: Optional[str]  # "why this fits your voice"


class SocialPostsOutput(TypedDict):
    """Complete output for social media generation."""
    posts: List[SocialPost]
    count: int
    summary: Optional[str]


# Reels/Video Script Schemas
class ReelBeat(TypedDict, total=False):
    """A single beat in a reel script."""
    text: str
    shot: Optional[str]
    on_screen_text: Optional[str]


class ReelScript(TypedDict):
    """A complete reel script."""
    hook: str
    beats: List[ReelBeat]
    cta: str
    caption: str
    hashtags: List[str]
    shot_list: Optional[List[str]]
    on_screen_text: Optional[List[str]]


class ReelOutput(TypedDict):
    """Complete output for reel generation."""
    script: ReelScript
    summary: Optional[str]


# Review Response Schemas
class ReviewResponseVariants(TypedDict, total=False):
    """Different length variants of a review response."""
    short: str
    medium: str
    long: str


class ReviewResponseOutput(TypedDict):
    """Complete output for review response generation."""
    responses: ReviewResponseVariants
    tone: str
    voice_applied: bool
    summary: Optional[str]


# Micro-examples for voice anchoring
class VoiceMicroExamples(TypedDict, total=False):
    """Micro-examples for voice anchoring (2-3 short examples)."""
    example_caption: str  # One short caption in their voice
    example_cta: str  # One CTA in their voice
    avoid_rewrite: Dict[str, str]  # {"bad": "...", "good": "..."}


# Generation Context Schemas
class VoiceStyleGuide(TypedDict, total=False):
    """Compact voice style guide derived from samples."""
    voice_name: Optional[str]
    tone_descriptors: List[str]
    sentence_length: str  # "short" | "medium" | "long"
    formatting: Dict[str, Any]  # line breaks, bullets, emoji frequency
    vocabulary: Dict[str, List[str]]  # top_phrases, taboo_phrases
    cta_patterns: List[str]
    signature_moves: List[str]  # e.g., "rhetorical questions", "local references"
    style_instruction: str  # natural language summary for AI
    micro_examples: Optional[VoiceMicroExamples]  # voice anchoring examples


class BrandKitV1(TypedDict, total=False):
    """Brand Kit v1 - specificity fields for better generation."""
    services: Optional[List[str]]  # What you offer
    audience_role: Optional[str]  # Who they are
    audience_pain: Optional[str]  # What problem they face
    audience_outcome: Optional[str]  # What they achieve
    audience_objection: Optional[str]  # What holds them back
    differentiators: Optional[List[str]]  # What makes you different
    proof: Optional[List[str]]  # Social proof, credentials, results
    email_signature: Optional[str]  # Sender/signoff for emails
    quote_terms: Optional[str]  # Terms for quotes (validity, deposit, etc.)


class WorkspaceContext(TypedDict, total=False):
    """Workspace profile and settings."""
    company_name: str
    industry: str
    default_tone: str
    platforms: List[str]
    offerings: Optional[str]
    audience: Optional[str]
    compliance_notes: Optional[str]
    brand_kit: Optional[BrandKitV1]
    brand_kit_tier: Optional[str]  # "minimum" | "stronger" | "best"


class GenerationContext(TypedDict, total=False):
    """Complete context for generation request."""
    workspace: WorkspaceContext
    voice_guide: Optional[VoiceStyleGuide]
    template: Optional[Dict[str, Any]]
    request: Dict[str, Any]  # request-specific toggles/params


# Standard API Response Schemas
class ErrorDetail(TypedDict):
    """Error detail structure."""
    code: str
    message: str
    details: Optional[Dict[str, Any]]


class UsedSignals(TypedDict, total=False):
    """Metadata tracking which Brand Kit signals were used in generation."""
    services_used: List[str]
    pains_used: List[str]
    outcomes_used: List[str]
    proof_used: List[str]
    differentiators_used: List[str]
    cta_used: Optional[str]
    custom_chips_used: List[str]


class SuccessResponse(TypedDict):
    """Standard success response."""
    ok: bool  # True
    request_id: str
    openai_used: bool
    fallback_used: bool
    data: Dict[str, Any]
    summary: Optional[Dict[str, Any]]
    warnings: Optional[List[str]]
    used_signals: Optional[UsedSignals]
    source: Optional[str]
    # Short mode string describing how the output was produced. Examples:
    # 'generated' (model-generated), 'fallback_suggestions' (template fallback)
    mode: Optional[str]


class ErrorResponse(TypedDict):
    """Standard error response."""
    ok: bool  # False
    request_id: str
    error: ErrorDetail
    # For easier backward compatibility some callers expect top-level source/mode
    source: Optional[str]
    mode: Optional[str]


# Validation result schemas
def validate_social_posts(data: Any) -> SocialPostsOutput:
    """Validate social posts output structure."""
    if not isinstance(data, dict):
        raise ValueError("Output must be a dict")
    
    posts = data.get('posts')
    if not isinstance(posts, list) or not posts:
        raise ValueError("Output must contain non-empty 'posts' list")
    
    for post in posts:
        if not isinstance(post, dict):
            raise ValueError("Each post must be a dict")
        if 'date' not in post or 'pillar' not in post:
            raise ValueError("Each post must have 'date' and 'pillar'")
        
        cards = post.get('cards')
        if not isinstance(cards, list) or not cards:
            raise ValueError("Each post must have non-empty 'cards' list")
        
        for card in cards:
            if not isinstance(card, dict):
                raise ValueError("Each card must be a dict")
            if 'platform' not in card or 'caption' not in card:
                raise ValueError("Each card must have 'platform' and 'caption'")
            if not isinstance(card.get('caption'), str) or not card['caption'].strip():
                raise ValueError("Card caption must be non-empty string")
    
    return {
        'posts': posts,
        'count': len(posts),
        'summary': data.get('summary')
    }


def validate_reel_script(data: Any) -> ReelOutput:
    """Validate reel script output structure."""
    if not isinstance(data, dict):
        raise ValueError("Output must be a dict")
    
    script = data.get('script')
    if not isinstance(script, dict):
        raise ValueError("Output must contain 'script' dict")
    
    if 'hook' not in script or not script['hook']:
        raise ValueError("Script must have non-empty 'hook'")
    if 'cta' not in script or not script['cta']:
        raise ValueError("Script must have non-empty 'cta'")
    
    beats = script.get('beats')
    if not isinstance(beats, list):
        raise ValueError("Script must have 'beats' list")
    
    return {
        'script': script,
        'summary': data.get('summary')
    }


def validate_review_responses(data: Any) -> ReviewResponseOutput:
    """Validate review response output structure."""
    if not isinstance(data, dict):
        raise ValueError("Output must be a dict")
    
    responses = data.get('responses')
    if not isinstance(responses, dict):
        raise ValueError("Output must contain 'responses' dict")
    
    # At least one response variant must be present
    if not any(responses.get(k) for k in ['short', 'medium', 'long']):
        raise ValueError("At least one response variant (short/medium/long) required")
    
    for key in ['short', 'medium', 'long']:
        val = responses.get(key)
        if val is not None and (not isinstance(val, str) or not val.strip()):
            raise ValueError(f"Response '{key}' must be non-empty string if present")
    
    return {
        'responses': responses,
        'tone': data.get('tone', 'professional'),
        'voice_applied': data.get('voice_applied', False),
        'summary': data.get('summary')
    }


# Canonical response builders and helpers
def build_success_response(
    request_id: str,
    data: Any,
    *,
    gemini_used: bool = False,
    openai_used: bool = False,
    summary: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    used_signals: Optional[UsedSignals] = None,
    source: Optional[str] = None,
) -> SuccessResponse:
    """Build a canonical success response for generation endpoints.

    Keeps both boolean flags and a `source` string for backward compatibility.
    """
    # Determine source if not provided
    if source is None:
        if gemini_used:
            source = 'gemini'
        elif openai_used:
            source = 'openai'
        else:
            source = 'fallback'

    fallback_used = (source == 'fallback')

    resp: SuccessResponse = {
        'ok': True,
        'request_id': request_id,
        'openai_used': bool(openai_used),
        'fallback_used': bool(fallback_used),
        'data': data,
        'summary': summary,
        'warnings': warnings,
        'used_signals': used_signals,
        'source': source,
        # Provide a small, human-friendly mode string used by tests and callers.
        # 'generated' for model-generated output, 'fallback_suggestions' for fallback templates,
        # and other values can be added as needed.
        'mode': ('generated' if source in ('openai', 'gemini') else 'fallback_suggestions' if source == 'fallback' else 'unknown'),
    }

    return resp


def build_error_response(
    request_id: str,
    code: str,
    message: str,
    *,
    source: str = 'unknown',
    details: Optional[Dict[str, Any]] = None,
    gemini_used: bool = False,
    openai_used: bool = False,
) -> ErrorResponse:
    """Build a canonical error response for generation endpoints.

    `source` should be one of 'gemini', 'openai', 'fallback', or 'unknown'.
    """
    err: ErrorDetail = {
        'code': code,
        'message': message,
        'details': details,
    }

    resp: ErrorResponse = {
        'ok': False,
        'request_id': request_id,
        'error': err,
        'source': source,
        'mode': 'error',
    }

    # For legacy callers that inspected booleans on error responses, provide
    # them via the error details to avoid changing the top-level shape.
    if details is None:
        resp['error']['details'] = {
            'gemini_used': bool(gemini_used),
            'openai_used': bool(openai_used),
            'source': source,
        }
    else:
        # If details were provided, ensure booleans/source are present for
        # easier migration for callers.
        details.setdefault('gemini_used', bool(gemini_used))
        details.setdefault('openai_used', bool(openai_used))
        details.setdefault('source', source)
        resp['error']['details'] = details

    # Add top-level source/mode for easier consumption by legacy tests/callers
    resp['source'] = source
    resp['mode'] = 'error'

    return resp


def is_success(resp: Dict[str, Any]) -> bool:
    return bool(resp and isinstance(resp, dict) and resp.get('ok') is True)


def is_error(resp: Dict[str, Any]) -> bool:
    return bool(resp and isinstance(resp, dict) and resp.get('ok') is False)

