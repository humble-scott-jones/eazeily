"""Social post ready pipeline - normalizes and validates social post outputs.

Responsibilities:
- Validate/normalize raw model output into SocialPostCard objects
- Enforce "final copy only" rules (no coaching/meta language)
- Separate notes from captions
- Ensure proper structure for copy-paste-ready output
"""

import logging
from typing import Any, Dict, List, Optional

from .output_schemas import SocialPostCard, SocialPost
from .social_quality_gate import quality_gate_check

logger = logging.getLogger(__name__)


def normalize_post_card(card: Dict[str, Any]) -> SocialPostCard:
    """Normalize a raw post card into SocialPostCard schema.
    
    Args:
        card: Raw card dict from model output
        
    Returns:
        Normalized SocialPostCard
    """
    normalized: SocialPostCard = {
        'platform': card.get('platform', 'instagram'),
        'caption': card.get('caption', ''),
        'hashtags': card.get('hashtags', [])
    }
    
    # Optional fields
    if 'hook' in card:
        normalized['hook'] = card['hook']
    
    if 'cta' in card:
        normalized['cta'] = card['cta']
    
    if 'media_idea' in card or 'image_prompt' in card:
        normalized['media_idea'] = card.get('media_idea') or card.get('image_prompt')
    
    if 'alt_text' in card:
        normalized['alt_text'] = card['alt_text']
    
    if 'character_count' in card:
        normalized['character_count'] = card['character_count']
    elif 'caption' in card:
        # Calculate character count if not provided
        normalized['character_count'] = len(card['caption'])
    
    return normalized


def extract_notes_from_caption(card: Dict[str, Any]) -> Dict[str, Any]:
    """Extract strategy notes from caption if they exist.
    
    Looks for patterns that indicate notes mixed into caption and separates them.
    
    Args:
        card: Post card dict
        
    Returns:
        Card with notes extracted and caption cleaned
    """
    caption = card.get('caption', '')
    
    # Patterns that indicate notes/meta commentary
    note_indicators = [
        r'\(Note:.*?\)',
        r'\(Strategy:.*?\)',
        r'\(Why this works:.*?\)',
        r'\[Note:.*?\]',
        r'\[Strategy:.*?\]',
    ]
    
    import re
    
    notes = []
    cleaned_caption = caption
    
    for pattern in note_indicators:
        matches = re.findall(pattern, cleaned_caption, re.IGNORECASE | re.DOTALL)
        if matches:
            notes.extend(matches)
            cleaned_caption = re.sub(pattern, '', cleaned_caption, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up extra whitespace
    cleaned_caption = re.sub(r'\n{3,}', '\n\n', cleaned_caption)
    cleaned_caption = cleaned_caption.strip()
    
    if notes:
        card['caption'] = cleaned_caption
        card['notes'] = notes
        logger.info(f"Extracted {len(notes)} notes from {card.get('platform')} caption")
    
    return card


def validate_hashtags(hashtags: List[str]) -> List[str]:
    """Validate and clean hashtags.
    
    Args:
        hashtags: List of hashtag strings
        
    Returns:
        Cleaned list of hashtags
    """
    cleaned = []
    
    for tag in hashtags:
        if not tag:
            continue
        
        # Remove # prefix if present
        tag = tag.strip()
        if tag.startswith('#'):
            tag = tag[1:]
        
        # Remove spaces and invalid characters
        tag = tag.replace(' ', '')
        
        # Only keep if non-empty
        if tag:
            cleaned.append(tag)
    
    return cleaned


def normalize_social_post(post: Dict[str, Any]) -> SocialPost:
    """Normalize a raw social post into SocialPost schema.
    
    Args:
        post: Raw post dict from model output
        
    Returns:
        Normalized SocialPost
    """
    cards = post.get('cards', [])
    
    # Normalize each card
    normalized_cards = []
    for card in cards:
        # Extract notes from caption first
        card = extract_notes_from_caption(card)
        
        # Normalize card structure
        normalized_card = normalize_post_card(card)
        
        # Validate and clean hashtags
        normalized_card['hashtags'] = validate_hashtags(normalized_card.get('hashtags', []))
        
        normalized_cards.append(normalized_card)
    
    normalized_post: SocialPost = {
        'date': post.get('date', 'TBD'),
        'pillar': post.get('pillar', 'Engagement'),
        'cards': normalized_cards
    }
    
    # Optional voice note
    if 'voice_note' in post:
        normalized_post['voice_note'] = post['voice_note']
    
    return normalized_post


def normalize_and_guardrail(
    data: Dict[str, Any],
    openai_client: Optional[Any] = None,
    allow_repair: bool = True
) -> Dict[str, Any]:
    """Main pipeline: normalize output and apply quality guardrails.
    
    Args:
        data: Raw output from model
        openai_client: Optional OpenAI client for repair pass
        allow_repair: Whether to allow repair attempts
        
    Returns:
        Dict with 'ok', 'posts', 'errors', 'warnings' keys
    """
    try:
        # Step 1: Normalize structure
        raw_posts = data.get('posts', [])
        
        if not raw_posts:
            return {
                'ok': False,
                'error': {
                    'code': 'empty_output',
                    'message': 'No posts in output'
                }
            }
        
        normalized_posts = []
        for post in raw_posts:
            try:
                normalized_post = normalize_social_post(post)
                
                # Skip posts with no cards
                if normalized_post['cards']:
                    normalized_posts.append(normalized_post)
            except Exception as e:
                logger.warning(f"Failed to normalize post: {e}")
                continue
        
        if not normalized_posts:
            return {
                'ok': False,
                'error': {
                    'code': 'normalization_failed',
                    'message': 'All posts failed normalization'
                }
            }
        
        # Step 2: Apply quality gate
        gate_result = quality_gate_check(
            normalized_posts,
            openai_client=openai_client,
            allow_repair=allow_repair
        )
        
        if not gate_result['ok']:
            # Quality gate failed even after repair
            error_summary = []
            for error in gate_result.get('errors', []):
                if isinstance(error, dict):
                    error_summary.append(
                        f"{error.get('platform', 'unknown')}: {', '.join(error.get('errors', []))}"
                    )
                else:
                    error_summary.append(str(error))
            
            return {
                'ok': False,
                'error': {
                    'code': 'output_not_post_ready',
                    'message': 'Generated content does not meet quality standards for copy-paste-ready posts',
                    'details': {
                        'errors': error_summary,
                        'warnings': gate_result.get('warnings', [])
                    }
                }
            }
        
        # Success!
        return {
            'ok': True,
            'posts': gate_result['posts'],
            'warnings': gate_result.get('warnings', [])
        }
        
    except Exception as e:
        logger.exception(f"Pipeline error: {e}")
        return {
            'ok': False,
            'error': {
                'code': 'pipeline_error',
                'message': f'Pipeline processing failed: {str(e)}'
            }
        }
