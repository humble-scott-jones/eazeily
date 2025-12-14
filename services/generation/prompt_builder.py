"""Prompt builder - constructs OpenAI prompts with context and constraints.

Builds prompts for different content types (social, reels, reviews) with:
- System message defining role and output format
- Context (workspace + voice guide)
- Request constraints (toggles, platform rules)
"""

import json
from typing import Any, Dict, List, Optional
from .output_schemas import GenerationContext, VoiceStyleGuide
from .context_builder import get_workspace_summary
from .voice_style_builder import get_style_guide_summary


# Platform-specific rules and hints
PLATFORM_RULES = {
    'instagram': {
        'max_length': 2200,
        'hashtag_count': 12,
        'style': 'Visual-first. Use line breaks, 1-2 short paragraphs. Hashtags at end.',
        'cta': 'Save + share if this helps; link in bio for more'
    },
    'facebook': {
        'max_length': 1200,
        'hashtag_count': 4,
        'style': 'Conversational, community-focused. 2-3 paragraphs. Invite comments.',
        'cta': 'Drop a comment or share with someone who needs this'
    },
    'linkedin': {
        'max_length': 1300,
        'hashtag_count': 5,
        'style': 'Professional, value-forward. 1-2 actionable insights. Concise.',
        'cta': 'Add your perspective below or DM for details'
    },
    'twitter': {
        'max_length': 280,
        'hashtag_count': 3,
        'style': 'Short, punchy. No walls of text. Thread if needed.',
        'cta': 'Reply with your take or tag a friend'
    },
    'tiktok': {
        'max_length': 1500,
        'hashtag_count': 5,
        'style': 'Hook in first 3 seconds. Short lines. Video-first mindset.',
        'cta': 'Try it and tell us how it goes in the comments'
    },
    'youtube': {
        'max_length': 5000,
        'hashtag_count': 6,
        'style': 'Hook + value promise. Clear structure. Timestamps if long.',
        'cta': 'Subscribe for more and check the pinned link'
    },
}


def _build_system_message(content_type: str) -> str:
    """Build system message defining AI role and output format."""
    base = (
        "You are Eazeily, an expert social media content generator. "
        "Generate engaging, on-brand content that sounds natural and human. "
        "CRITICAL: Never include private contact information (phone numbers, emails, addresses) in public posts. "
        "Output must be valid JSON matching the exact schema provided."
    )
    
    if content_type == 'social':
        return base + (
            "\n\nFor social media posts, create content that:\n"
            "- Matches the user's voice and tone precisely\n"
            "- Adapts to each platform's style and constraints\n"
            "- Includes relevant hashtags and CTAs\n"
            "- Provides media ideas when appropriate\n"
            "\n"
            "CRITICAL - Return FINAL post copy only:\n"
            "- Do NOT include advice, suggestions, or coaching phrases like 'you should', 'consider', 'try to'\n"
            "- Do NOT use bullet lists explaining what to do\n"
            "- The caption must be paste-ready, finished copy that can be posted immediately\n"
            "- Any strategy notes MUST go in the separate 'notes' field, never in the caption"
        )
    elif content_type == 'reels':
        return base + (
            "\n\nFor video scripts (Reels/TikTok), create content that:\n"
            "- Hooks viewers in the first 3 seconds\n"
            "- Uses short, punchy lines for on-screen text\n"
            "- Includes shot suggestions for visual storytelling\n"
            "- Ends with a clear, actionable CTA"
        )
    elif content_type == 'reviews':
        return base + (
            "\n\nFor review responses, create content that:\n"
            "- Acknowledges the reviewer's feedback\n"
            "- Matches the company's brand voice if requested\n"
            "- Stays professional regardless of review tone\n"
            "- Provides short, medium, and long response options"
        )
    else:
        return base


def _build_context_section(context: GenerationContext) -> str:
    """Build context section with workspace and voice guide."""
    parts = []
    
    # Workspace context
    if workspace_summary := get_workspace_summary(context):
        parts.append(f"WORKSPACE:\n{workspace_summary}")
    
    # Voice guide
    if voice_guide := context.get('voice_guide'):
        voice_summary = get_style_guide_summary(voice_guide)
        parts.append(f"\nVOICE STYLE:\n{voice_summary}")
        
        # Add vocabulary hints
        vocab = voice_guide.get('vocabulary', {})
        if top_phrases := vocab.get('top_phrases'):
            parts.append(f"\nInclude naturally: {', '.join(top_phrases[:5])}")
        if taboo_phrases := vocab.get('taboo_phrases'):
            parts.append(f"\nAvoid: {', '.join(taboo_phrases)}")
    
    return "\n".join(parts) if parts else ""


def _build_platform_constraints(platforms: List[str]) -> str:
    """Build platform-specific constraints section."""
    if not platforms:
        return ""
    
    parts = ["PLATFORM RULES:"]
    for platform in platforms:
        if rules := PLATFORM_RULES.get(platform.lower()):
            parts.append(
                f"\n{platform.upper()}:\n"
                f"  Style: {rules['style']}\n"
                f"  Max length: {rules['max_length']} chars\n"
                f"  Hashtags: {rules['hashtag_count']} max\n"
                f"  CTA: {rules['cta']}"
            )
    
    return "\n".join(parts)


def build_social_prompt(
    context: GenerationContext,
    session_length: int = 7,
    include_schema: bool = True
) -> List[Dict[str, str]]:
    """Build prompt messages for social media post generation.
    
    Args:
        context: Generation context with workspace, voice, request data
        session_length: Number of days to generate (1, 7, or 30)
        include_schema: Whether to include JSON schema in prompt
        
    Returns:
        List of message dicts for OpenAI chat completion
    """
    request_data = context.get('request', {})
    platforms = request_data.get('platforms', [])
    tone = request_data.get('tone', 'professional')
    goals = request_data.get('goals', [])
    keywords = request_data.get('keywords', [])
    
    # Build user message with all constraints
    user_parts = []
    
    # Context
    if context_section := _build_context_section(context):
        user_parts.append(context_section)
    
    # Request specifics
    user_parts.append(f"\nGENERATE: {session_length} social media posts")
    user_parts.append(f"TONE: {tone}")
    
    if platforms:
        user_parts.append(f"PLATFORMS: {', '.join(platforms)}")
        user_parts.append(_build_platform_constraints(platforms))
    
    if goals:
        user_parts.append(f"CONTENT GOALS: {', '.join(goals)}")
    
    if keywords:
        user_parts.append(f"KEYWORDS TO INCLUDE: {', '.join(keywords)}")
    
    # Reel options if applicable
    if reel_options := request_data.get('reel_options'):
        if 'ig_reels' in platforms or 'tiktok' in platforms:
            user_parts.append(f"\nREEL OPTIONS: {json.dumps(reel_options)}")
    
    # Schema if requested
    if include_schema:
        schema = {
            "posts": [
                {
                    "date": "YYYY-MM-DD",
                    "pillar": "Educational|Behind-the-Scenes|Testimonial|Product|Engagement|Story",
                    "cards": [
                        {
                            "platform": "platform_name",
                            "caption": "FINAL paste-ready post text with line breaks",
                            "hashtags": ["tag1", "tag2"],
                            "cta": "optional call to action line",
                            "alt_text": "optional image alt text for accessibility",
                            "image_prompt": "optional image generation prompt",
                            "notes": ["optional strategy note 1", "optional strategy note 2"]
                        }
                    ],
                    "voice_note": "why this fits your voice"
                }
            ]
        }
        
        # Add platform-specific richness guidelines
        richness_guide = "\n\nPLATFORM RICHNESS DEFAULTS:\n"
        if 'instagram' in platforms:
            richness_guide += (
                "Instagram: 1 hook line + spacing + 2-4 value lines + CTA. "
                "8-15 hashtags at end. Use line breaks for readability.\n"
            )
        if 'linkedin' in platforms:
            richness_guide += (
                "LinkedIn: Strong first line + short paragraphs + 0-3 hashtags. "
                "Professional tone, no emoji spam. Focus on value.\n"
            )
        if 'twitter' in platforms or 'x' in platforms:
            richness_guide += (
                "X/Twitter: <= 280 chars. Punchy, no walls of text. Thread if needed.\n"
            )
        if 'facebook' in platforms:
            richness_guide += (
                "Facebook: Conversational, 2-3 paragraphs. 4-8 hashtags max. Community-focused.\n"
            )
        
        user_parts.append(richness_guide)
        user_parts.append(f"\nOUTPUT FORMAT (JSON):\n{json.dumps(schema, indent=2)}")
    
    messages = [
        {"role": "system", "content": _build_system_message('social')},
        {"role": "user", "content": "\n".join(user_parts)}
    ]
    
    return messages


def build_reel_prompt(
    context: GenerationContext,
    hook_style: Optional[str] = None,
    format_type: Optional[str] = None,
    duration: Optional[int] = None,
    include_shot_list: bool = False,
    include_on_screen_text: bool = False,
    include_schema: bool = True
) -> List[Dict[str, str]]:
    """Build prompt messages for reel/video script generation.
    
    Args:
        context: Generation context
        hook_style: Hook type (question, stat, story, etc.)
        format_type: Video format (tutorial, behind-scenes, etc.)
        duration: Target duration in seconds
        include_shot_list: Whether to include shot list
        include_on_screen_text: Whether to include on-screen text suggestions
        include_schema: Whether to include JSON schema
        
    Returns:
        List of message dicts for OpenAI chat completion
    """
    request_data = context.get('request', {})
    
    user_parts = []
    
    # Context
    if context_section := _build_context_section(context):
        user_parts.append(context_section)
    
    # Request specifics
    user_parts.append("\nGENERATE: Video script (Reel/TikTok/Short)")
    
    if hook_style:
        user_parts.append(f"HOOK STYLE: {hook_style}")
    if format_type:
        user_parts.append(f"FORMAT: {format_type}")
    if duration:
        user_parts.append(f"DURATION: ~{duration} seconds")
    
    user_parts.append(
        "\nKEY REQUIREMENTS:\n"
        "- Hook viewers in first 3 seconds\n"
        "- Use short, punchy lines (5-8 words each)\n"
        "- Clear visual progression\n"
        "- Strong CTA at end"
    )
    
    if include_shot_list:
        user_parts.append("- Include shot list with camera angles/movements")
    if include_on_screen_text:
        user_parts.append("- Include on-screen text suggestions for each beat")
    
    # Schema
    if include_schema:
        schema = {
            "script": {
                "hook": "opening hook (3 seconds)",
                "beats": [
                    {
                        "text": "voiceover text",
                        "shot": "camera shot description" if include_shot_list else None,
                        "on_screen_text": "text overlay" if include_on_screen_text else None
                    }
                ],
                "cta": "call to action",
                "caption": "post caption for the video",
                "hashtags": ["tag1", "tag2"],
                "shot_list": ["shot 1", "shot 2"] if include_shot_list else None
            }
        }
        # Remove None values
        schema['script'] = {k: v for k, v in schema['script'].items() if v is not None}
        user_parts.append(f"\nOUTPUT FORMAT (JSON):\n{json.dumps(schema, indent=2)}")
    
    messages = [
        {"role": "system", "content": _build_system_message('reels')},
        {"role": "user", "content": "\n".join(user_parts)}
    ]
    
    return messages


def build_review_response_prompt(
    context: GenerationContext,
    review_text: str,
    rating: Optional[int] = None,
    channel: Optional[str] = None,
    response_length: str = 'medium',
    use_brand_voice: bool = False,
    include_schema: bool = True
) -> List[Dict[str, str]]:
    """Build prompt messages for review response generation.
    
    Args:
        context: Generation context
        review_text: The review to respond to
        rating: Star rating (1-5)
        channel: Review platform (google, yelp, facebook, etc.)
        response_length: Target length (short, medium, long)
        use_brand_voice: Whether to apply voice style guide
        include_schema: Whether to include JSON schema
        
    Returns:
        List of message dicts for OpenAI chat completion
    """
    request_data = context.get('request', {})
    tone = request_data.get('tone', 'professional')
    
    user_parts = []
    
    # Context (only if using brand voice)
    if use_brand_voice:
        if context_section := _build_context_section(context):
            user_parts.append(context_section)
    
    # Request specifics
    user_parts.append(f"\nGENERATE: Response to customer review")
    user_parts.append(f"TONE: {tone}")
    
    if rating:
        user_parts.append(f"RATING: {rating}/5 stars")
    if channel:
        user_parts.append(f"PLATFORM: {channel}")
    
    user_parts.append(f"\nREVIEW TEXT:\n{review_text}")
    
    user_parts.append(
        "\nRESPONSE GUIDELINES:\n"
        "- Acknowledge their specific feedback\n"
        "- Stay professional and gracious\n"
        "- Be genuine, not generic\n"
        "- Never include contact info (phone/email)\n"
        "- Provide 3 variants: short (~50 words), medium (~100 words), long (~150 words)"
    )
    
    if use_brand_voice:
        user_parts.append("- Match the company's brand voice precisely")
    
    # Schema
    if include_schema:
        schema = {
            "responses": {
                "short": "~50 word response",
                "medium": "~100 word response",
                "long": "~150 word response"
            },
            "tone": tone,
            "voice_applied": use_brand_voice
        }
        user_parts.append(f"\nOUTPUT FORMAT (JSON):\n{json.dumps(schema, indent=2)}")
    
    messages = [
        {"role": "system", "content": _build_system_message('reviews')},
        {"role": "user", "content": "\n".join(user_parts)}
    ]
    
    return messages
