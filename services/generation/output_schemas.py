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


class WorkspaceContext(TypedDict, total=False):
    """Workspace profile and settings."""
    company_name: str
    industry: str
    default_tone: str
    platforms: List[str]
    offerings: Optional[str]
    audience: Optional[str]
    compliance_notes: Optional[str]


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


class SuccessResponse(TypedDict):
    """Standard success response."""
    ok: bool  # True
    request_id: str
    openai_used: bool
    fallback_used: bool
    data: Dict[str, Any]
    summary: Optional[Dict[str, Any]]
    warnings: Optional[List[str]]


class ErrorResponse(TypedDict):
    """Standard error response."""
    ok: bool  # False
    request_id: str
    error: ErrorDetail


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
