"""Social Post-Ready Pipeline - ensures outputs are copy-paste-ready.

Normalizes and validates social media outputs into stable SocialPostCard objects.
Enforces "no coaching" rules and separates notes from final captions.
"""

import logging
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


class SocialPostCard(TypedDict, total=False):
    """Post-ready social media card for a single platform.
    
    This is the stable contract for expert, copy-paste-ready outputs.
    """
    platform: str  # "instagram" | "facebook" | "linkedin" | "x"
    caption: str  # FINAL post copy only (no coaching/meta language)
    hashtags: List[str]  # Separate list, not embedded in caption
    cta: Optional[str]  # Optional call-to-action
    image_prompt: Optional[str]  # Optional image generation hint
    notes: Optional[List[str]]  # Optional strategy notes (never in caption)


# Coaching phrases that should never appear in final captions
COACHING_PHRASES = [
    'you should',
    'you could',
    'think about',
    'make sure to',
    'don\'t forget to',
    'remember to',
    'be sure to',
    'what to post',
    'here are some ideas',
    'suggestions for',
    'when posting',
    'advice:',
    'here\'s what to say',
    'talk about',
    'try to',
]

# Additional coaching patterns (word boundaries matter)
COACHING_PATTERNS = [
    r'\bconsider\s+\w+ing\b',  # "consider posting" but not "Considering"
    r'^tip:\s',  # "Tip: " at start of line (standalone tip marker)
    r'\n\s*tip:\s',  # "Tip: " on new line
]


def _contains_coaching_language(text: str) -> bool:
    """Check if text contains coaching/meta language."""
    if not text:
        return False
    
    import re
    
    text_lower = text.lower()
    
    # Check simple phrase matches
    for phrase in COACHING_PHRASES:
        if phrase in text_lower:
            return True
    
    # Check pattern matches
    for pattern in COACHING_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    
    return False


def _extract_hashtags_from_caption(caption: str) -> tuple[str, List[str]]:
    """Extract hashtags from caption text and return clean caption + hashtags list.
    
    Args:
        caption: Caption text that may contain hashtags
        
    Returns:
        Tuple of (clean_caption, hashtags_list)
    """
    lines = caption.split('\n')
    clean_lines = []
    hashtags = []
    
    for line in lines:
        # Check if line is mostly hashtags
        words = line.strip().split()
        if words and sum(1 for w in words if w.startswith('#')) / len(words) > 0.5:
            # Extract hashtags from this line
            for word in words:
                if word.startswith('#'):
                    hashtags.append(word)
        else:
            clean_lines.append(line)
    
    clean_caption = '\n'.join(clean_lines).strip()
    return clean_caption, hashtags


def _normalize_platform_name(platform: str) -> str:
    """Normalize platform names to standard format."""
    platform_map = {
        'twitter': 'x',
        'ig': 'instagram',
        'fb': 'facebook',
        'li': 'linkedin',
        'tiktok': 'x',  # Map TikTok to x for now (short form)
    }
    platform_lower = platform.lower().strip()
    return platform_map.get(platform_lower, platform_lower)


def normalize_and_guardrail(
    raw_output: Any,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Normalize and guardrail social output into post-ready format.
    
    Args:
        raw_output: Raw output from generation (OpenAI or fallback)
        context: Optional context for logging
        request_id: Optional request ID for tracing
        
    Returns:
        Dict with normalized posts or error
        {
            'ok': True/False,
            'posts': [SocialPostCard...],  # if ok=True
            'error': {'code': str, 'message': str},  # if ok=False
            'warnings': [str...]  # optional warnings
        }
    """
    request_id = request_id or 'unknown'
    warnings = []
    
    try:
        # Validate raw output structure
        if not isinstance(raw_output, dict):
            return {
                'ok': False,
                'error': {
                    'code': 'invalid_output_format',
                    'message': 'Output must be a dictionary'
                }
            }
        
        # Extract posts data
        if 'data' in raw_output:
            # Output is wrapped in response format
            data = raw_output['data']
            if not isinstance(data, dict) or 'posts' not in data:
                return {
                    'ok': False,
                    'error': {
                        'code': 'invalid_output_format',
                        'message': 'Output data must contain posts'
                    }
                }
            posts_data = data['posts']
        elif 'posts' in raw_output:
            # Direct posts format
            posts_data = raw_output['posts']
        else:
            return {
                'ok': False,
                'error': {
                    'code': 'invalid_output_format',
                    'message': 'Output must contain posts'
                }
            }
        
        if not isinstance(posts_data, list):
            return {
                'ok': False,
                'error': {
                    'code': 'invalid_output_format',
                    'message': 'Posts must be a list'
                }
            }
        
        # Normalize each post into SocialPostCard format
        normalized_cards = []
        
        for post_idx, post in enumerate(posts_data):
            if not isinstance(post, dict):
                logger.warning(f"[{request_id}] Post {post_idx} is not a dict, skipping")
                continue
            
            # Extract cards from post
            cards = post.get('cards', [])
            if not isinstance(cards, list):
                logger.warning(f"[{request_id}] Post {post_idx} cards is not a list, skipping")
                continue
            
            for card_idx, card in enumerate(cards):
                if not isinstance(card, dict):
                    continue
                
                # Validate required fields
                platform = card.get('platform', '')
                caption = card.get('caption', '')
                
                if not platform or not caption:
                    logger.warning(
                        f"[{request_id}] Post {post_idx} card {card_idx} missing platform or caption"
                    )
                    continue
                
                # Check for coaching language in caption
                if _contains_coaching_language(caption):
                    warning = f"Coaching language detected in {platform} caption"
                    logger.warning(f"[{request_id}] {warning}")
                    warnings.append(warning)
                    
                    # Extract coaching phrases to notes
                    # For now, just flag it - repair pass should handle this
                    # In Phase 2, we could auto-extract to notes
                
                # Extract hashtags from caption if embedded
                caption_clean, extracted_hashtags = _extract_hashtags_from_caption(caption)
                
                # Get hashtags list
                hashtags = card.get('hashtags', [])
                if not isinstance(hashtags, list):
                    hashtags = []
                
                # Merge extracted hashtags
                if extracted_hashtags:
                    hashtags.extend(extracted_hashtags)
                    caption = caption_clean
                
                # Normalize platform name
                platform_normalized = _normalize_platform_name(platform)
                
                # Build SocialPostCard
                normalized_card: SocialPostCard = {
                    'platform': platform_normalized,
                    'caption': caption.strip(),
                    'hashtags': hashtags,
                }
                
                # Add optional fields if present
                if cta := card.get('cta'):
                    normalized_card['cta'] = cta
                if image_prompt := card.get('media_idea') or card.get('image_prompt'):
                    normalized_card['image_prompt'] = image_prompt
                
                # Extract notes from voice_note or notes field
                notes = []
                if voice_note := post.get('voice_note'):
                    notes.append(voice_note)
                if card_notes := card.get('notes'):
                    if isinstance(card_notes, list):
                        notes.extend(card_notes)
                    elif isinstance(card_notes, str):
                        notes.append(card_notes)
                
                if notes:
                    normalized_card['notes'] = notes
                
                normalized_cards.append(normalized_card)
        
        # Check if we have any valid cards
        if not normalized_cards:
            return {
                'ok': False,
                'error': {
                    'code': 'no_valid_posts',
                    'message': 'No valid posts could be extracted from output'
                }
            }
        
        result = {
            'ok': True,
            'posts': normalized_cards
        }
        
        if warnings:
            result['warnings'] = warnings
        
        logger.info(f"[{request_id}] Normalized {len(normalized_cards)} post cards")
        
        return result
        
    except Exception as e:
        logger.exception(f"[{request_id}] Pipeline normalization failed: {e}")
        return {
            'ok': False,
            'error': {
                'code': 'pipeline_error',
                'message': f'Failed to normalize output: {str(e)}'
            }
        }
