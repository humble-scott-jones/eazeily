"""Social quality gate - validates post quality and performs repair pass.

Checks:
- Coaching detection: ensures no coaching/meta language in captions
- Richness check: ensures posts have actionable content (steps, examples, etc.)
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Coaching phrases that indicate meta/advice language (not final copy)
COACHING_PATTERNS = [
    r'\byou should\b',
    r'\bconsider adding\b',
    r'\bconsider including\b',
    r'\bhere\'?s what to say\b',
    r'\btalk about\b',
    r'\bmake sure to\b',
    r'\bdon\'?t forget to\b',
    r'\btry saying\b',
    r'\byou could mention\b',
    r'\byou might want to\b',
    r'\bit\'?s important to say\b',
    r'\bremember to tell them\b',
    r'\bexplain that\b',
    r'\bshare about\b',
    r'\btell your audience\b',
    r'\blet them know that\b',
    r'\bhint at\b',
    r'\bsuggest that\b',
    r'\bbe sure to mention\b',
]

# Compiled patterns for efficiency
COACHING_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in COACHING_PATTERNS]


def detect_coaching_language(text: str) -> Optional[str]:
    """Detect coaching/meta language in text.
    
    Args:
        text: The text to check
        
    Returns:
        Error message if coaching detected, None otherwise
    """
    if not text:
        return None
    
    for pattern in COACHING_REGEX:
        match = pattern.search(text)
        if match:
            matched_phrase = match.group(0)
            return f"Coaching language detected: '{matched_phrase}'"
    
    return None


def check_richness(caption: str, platform: str = 'instagram') -> Tuple[bool, Optional[str]]:
    """Check if caption has rich, actionable content.
    
    A caption passes richness check if it includes at least ONE of:
    - Numbered steps (1-3+)
    - Checklist bullets
    - Myth vs fact structure
    - Concrete example scenario with context
    
    Args:
        caption: The caption text to check
        platform: Platform name (affects length requirements)
        
    Returns:
        Tuple of (passes_check, error_message)
    """
    if not caption:
        return False, "Caption is empty"
    
    # Minimum length thresholds by platform
    min_lengths = {
        'instagram': 150,
        'linkedin': 150,
        'facebook': 100,
        'twitter': 50,
        'tiktok': 80,
    }
    
    min_length = min_lengths.get(platform.lower(), 100)
    
    if len(caption) < min_length:
        return False, f"Caption too short for {platform} (min: {min_length} chars)"
    
    # Check for numbered steps (e.g., "1.", "2.", or "1)", "2)")
    numbered_steps = re.findall(r'(?:^|\n)\s*\d+[\.)]\s+', caption, re.MULTILINE)
    if len(numbered_steps) >= 3:
        return True, None
    
    # Check for checklist bullets (✓, ✔, ☑, •, -, *)
    bullet_points = re.findall(r'(?:^|\n)\s*[✓✔☑•\-\*]\s+', caption, re.MULTILINE)
    if len(bullet_points) >= 3:
        return True, None
    
    # Check for myth vs fact structure
    myth_fact_indicators = [
        r'\bmyth\b.*\bfact\b',
        r'\bwrong\b.*\bright\b',
        r'\bbefore\b.*\bafter\b',
    ]
    for pattern in myth_fact_indicators:
        if re.search(pattern, caption, re.IGNORECASE):
            return True, None
    
    # Check for concrete example scenarios
    example_indicators = [
        r'\bfor example\b',
        r'\bimagine\b',
        r'\bpicture this\b',
        r'\blet\'?s say\b',
        r'\btake.*for instance\b',
        r'\bconsider.*scenario\b',
    ]
    for pattern in example_indicators:
        if re.search(pattern, caption, re.IGNORECASE):
            # Example should be substantial (not just the phrase)
            if len(caption) > min_length * 1.5:
                return True, None
    
    return False, "Caption lacks rich structure (needs steps, bullets, myth/fact, or concrete examples)"


def validate_post_card(card: Dict[str, Any], platform: Optional[str] = None) -> Dict[str, Any]:
    """Validate a single post card for quality.
    
    Args:
        card: SocialPostCard dict
        platform: Optional platform override
        
    Returns:
        Dict with 'ok', 'card', 'errors' keys
    """
    errors = []
    
    platform = platform or card.get('platform', 'instagram')
    caption = card.get('caption', '')
    
    # Check for coaching language
    if coaching_error := detect_coaching_language(caption):
        errors.append(coaching_error)
    
    # Check richness
    is_rich, richness_error = check_richness(caption, platform)
    if not is_rich and richness_error:
        errors.append(richness_error)
    
    # Check that notes are not in caption
    notes = card.get('notes', [])
    if notes and isinstance(notes, list):
        for note in notes:
            if note and note.lower() in caption.lower():
                errors.append(f"Note text found in caption: '{note[:50]}...'")
    
    return {
        'ok': len(errors) == 0,
        'card': card,
        'errors': errors
    }


def validate_social_posts_quality(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate quality of all social posts.
    
    Args:
        posts: List of SocialPost dicts
        
    Returns:
        Dict with 'ok', 'posts', 'errors' keys
    """
    all_errors = []
    
    for post_idx, post in enumerate(posts):
        cards = post.get('cards', [])
        
        for card_idx, card in enumerate(cards):
            result = validate_post_card(card)
            
            if not result['ok']:
                for error in result['errors']:
                    all_errors.append({
                        'post_idx': post_idx,
                        'card_idx': card_idx,
                        'platform': card.get('platform'),
                        'error': error
                    })
    
    return {
        'ok': len(all_errors) == 0,
        'posts': posts,
        'errors': all_errors
    }


def generate_repair_prompt(card: Dict[str, Any], errors: List[str]) -> str:
    """Generate a repair prompt for a failed post card.
    
    Args:
        card: The post card that failed validation
        errors: List of error messages
        
    Returns:
        Repair prompt string
    """
    platform = card.get('platform', 'instagram')
    caption = card.get('caption', '')
    
    error_summary = "; ".join(errors)
    
    prompt = f"""REPAIR REQUEST: The following {platform} caption failed quality checks.

ORIGINAL CAPTION:
{caption}

ISSUES FOUND:
{error_summary}

REQUIREMENTS:
1. Rewrite into FINAL caption only (no coaching/meta language)
2. Make it rich and specific with ONE of these frameworks:
   - 3+ numbered steps
   - 3+ checklist bullets
   - Myth vs fact structure
   - Concrete example scenario with industry context
3. Include a clear, actionable CTA
4. Match the platform style for {platform}
5. No advice language like "you should", "consider adding", etc.

Return ONLY the rewritten caption as final copy, ready to paste."""
    
    return prompt


def attempt_repair_with_openai(
    card: Dict[str, Any],
    errors: List[str],
    openai_client: Optional[Any] = None
) -> Optional[Dict[str, Any]]:
    """Attempt to repair a post card using OpenAI.
    
    Args:
        card: The post card to repair
        errors: List of validation errors
        openai_client: Optional OpenAI client
        
    Returns:
        Repaired card dict if successful, None otherwise
    """
    if not openai_client:
        logger.warning("No OpenAI client available for repair")
        return None
    
    try:
        repair_prompt = generate_repair_prompt(card, errors)
        
        # Call OpenAI with repair prompt
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert social media content writer. Fix the content according to requirements."
                },
                {
                    "role": "user",
                    "content": repair_prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        repaired_caption = response.choices[0].message.content.strip()
        
        # Create repaired card
        repaired_card = card.copy()
        repaired_card['caption'] = repaired_caption
        repaired_card['_repaired'] = True
        
        # Validate repair
        validation = validate_post_card(repaired_card)
        
        if validation['ok']:
            logger.info(f"Successfully repaired {card.get('platform')} post")
            return repaired_card
        else:
            logger.warning(f"Repair failed validation: {validation['errors']}")
            return None
            
    except Exception as e:
        logger.error(f"Error during repair attempt: {e}")
        return None


def quality_gate_check(
    posts: List[Dict[str, Any]],
    openai_client: Optional[Any] = None,
    allow_repair: bool = True
) -> Dict[str, Any]:
    """Main quality gate check with optional repair.
    
    Args:
        posts: List of SocialPost dicts
        openai_client: Optional OpenAI client for repairs
        allow_repair: Whether to attempt repairs
        
    Returns:
        Dict with 'ok', 'posts', 'errors', 'warnings' keys
    """
    # Initial validation
    validation = validate_social_posts_quality(posts)
    
    if validation['ok']:
        return {
            'ok': True,
            'posts': posts,
            'errors': [],
            'warnings': []
        }
    
    # If validation failed and repair is allowed
    if allow_repair and openai_client:
        logger.info(f"Quality gate failed with {len(validation['errors'])} errors, attempting repair")
        
        repaired_posts = []
        repair_warnings = []
        remaining_errors = []
        
        for post in posts:
            repaired_post = post.copy()
            repaired_cards = []
            
            for card in post.get('cards', []):
                # Check if this card has errors
                card_validation = validate_post_card(card)
                
                if card_validation['ok']:
                    repaired_cards.append(card)
                else:
                    # Attempt repair
                    repaired_card = attempt_repair_with_openai(
                        card,
                        card_validation['errors'],
                        openai_client
                    )
                    
                    if repaired_card:
                        repaired_cards.append(repaired_card)
                        repair_warnings.append(
                            f"Repaired {card.get('platform')} post (issues: {', '.join(card_validation['errors'][:2])})"
                        )
                    else:
                        # Repair failed, keep original but note error
                        repaired_cards.append(card)
                        remaining_errors.append({
                            'platform': card.get('platform'),
                            'errors': card_validation['errors']
                        })
            
            repaired_post['cards'] = repaired_cards
            repaired_posts.append(repaired_post)
        
        # If repair fixed all issues
        if not remaining_errors:
            return {
                'ok': True,
                'posts': repaired_posts,
                'errors': [],
                'warnings': repair_warnings
            }
        
        # If some issues remain after repair
        return {
            'ok': False,
            'posts': repaired_posts,
            'errors': remaining_errors,
            'warnings': repair_warnings
        }
    
    # No repair or repair not available
    return {
        'ok': False,
        'posts': posts,
        'errors': validation['errors'],
        'warnings': ['Quality gate failed - no repair attempted']
    }
