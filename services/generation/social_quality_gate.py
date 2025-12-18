"""Social Quality Gate - enforces richness and detects generic outputs.

Detects:
- Coaching/meta language in captions
- Thin captions (too short for platform)
- Generic captions (lacking concrete examples or structure)

Requires at least one "structure signal" like:
- Numbered steps (1-3+)
- Checklist bullets
- Myth vs fact pattern
- Concrete example scenario
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Minimum caption lengths by platform
PLATFORM_MIN_LENGTH = {
    'instagram': 100,  # IG benefits from richer captions
    'facebook': 80,
    'linkedin': 120,  # LinkedIn expects substantial value
    'x': 40,  # X is naturally shorter (280 char limit)
}

# Generic/vague words that signal lack of specificity
GENERIC_INDICATORS = [
    'things', 'stuff', 'ways', 'tips', 'ideas',
    'something', 'anything', 'everything',
    'great', 'awesome', 'amazing', 'incredible',
    'important', 'valuable', 'useful',
]

# Structure signal patterns (at least one required for richness)
STRUCTURE_PATTERNS = [
    r'\d+[.)]\s',  # Numbered list: "1. " or "1) "
    r'[•\-*]\s',  # Bullet points
    r'(?i)myth\s*:.*?\n.*?fact\s*:',  # Myth vs fact (multiline)
    r'(?i)for example[,:]',  # Concrete example intro
    r'(?i)imagine\s',  # Scenario building
    r'(?i)step\s+\d+',  # Step-by-step
    r'(?i)(first|second|third|finally)[,:]',  # Sequential markers
]


def _check_caption_length(caption: str, platform: str) -> Optional[str]:
    """Check if caption meets minimum length for platform.
    
    Returns:
        Error message if too short, None if OK
    """
    min_length = PLATFORM_MIN_LENGTH.get(platform, 50)
    if len(caption.strip()) < min_length:
        return f"Caption too short for {platform} (min {min_length} chars)"
    return None


def _check_generic_language(caption: str) -> Optional[str]:
    """Check if caption contains too many generic/vague words.
    
    Returns:
        Warning message if too generic, None if OK
    """
    caption_lower = caption.lower()
    generic_count = sum(1 for word in GENERIC_INDICATORS if word in caption_lower)
    
    # Allow up to 2 generic words
    if generic_count > 2:
        return f"Caption contains {generic_count} generic/vague words"
    return None


def _has_structure_signal(caption: str) -> bool:
    """Check if caption contains at least one structure signal.
    
    Structure signals include:
    - Numbered steps
    - Bullet points
    - Myth vs fact
    - Concrete examples
    """
    for pattern in STRUCTURE_PATTERNS:
        # Use DOTALL for multiline patterns
        if re.search(pattern, caption, re.DOTALL):
            return True
    return False


def _check_coaching_language(caption: str) -> Optional[str]:
    """Check for coaching/instructional language.
    
    Returns:
        Error message if coaching detected, None if OK
    """
    # Import from pipeline to reuse
    from .social_post_ready_pipeline import _contains_coaching_language
    
    if _contains_coaching_language(caption):
        return "Caption contains coaching/instructional language"
    return None


def evaluate_post_quality(post_card: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate quality of a single post card.
    
    Args:
        post_card: SocialPostCard dict
        
    Returns:
        {
            'passed': bool,
            'errors': [str...],  # blocking issues
            'warnings': [str...],  # quality concerns
        }
    """
    errors = []
    warnings = []
    
    platform = post_card.get('platform', 'unknown')
    caption = post_card.get('caption', '')
    
    # Check for coaching language (blocking)
    if coaching_error := _check_coaching_language(caption):
        errors.append(coaching_error)
    
    # Check caption length (blocking for IG/LinkedIn)
    if length_error := _check_caption_length(caption, platform):
        if platform in ['instagram', 'linkedin']:
            errors.append(length_error)
        else:
            warnings.append(length_error)
    
    # Check for structure signals (blocking for quality)
    if not _has_structure_signal(caption):
        errors.append(
            "Caption lacks structure signal (no numbered steps, bullets, examples, or frameworks)"
        )
    
    # Check for generic language (warning only)
    if generic_warning := _check_generic_language(caption):
        warnings.append(generic_warning)
    
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
    }


def evaluate_all_posts(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate quality of all post cards.
    
    Args:
        posts: List of SocialPostCard dicts
        
    Returns:
        {
            'passed': bool,  # True if ALL posts pass
            'results': [{'post_index': int, 'passed': bool, 'errors': [...], 'warnings': [...]}],
            'summary': str
        }
    """
    results = []
    
    for idx, post in enumerate(posts):
        evaluation = evaluate_post_quality(post)
        results.append({
            'post_index': idx,
            'platform': post.get('platform', 'unknown'),
            'passed': evaluation['passed'],
            'errors': evaluation['errors'],
            'warnings': evaluation['warnings'],
        })
    
    # Overall pass = all posts pass
    all_passed = all(r['passed'] for r in results)
    
    # Build summary
    failed_count = sum(1 for r in results if not r['passed'])
    if all_passed:
        summary = f"All {len(posts)} posts passed quality gate"
    else:
        summary = f"{failed_count}/{len(posts)} posts failed quality gate"
    
    return {
        'passed': all_passed,
        'results': results,
        'summary': summary,
    }


def build_repair_prompt(
    post_card: Dict[str, Any],
    evaluation: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """Build repair prompt to fix quality issues.
    
    Args:
        post_card: Original post card that failed
        evaluation: Quality evaluation with errors
        context: Optional context for repair
        
    Returns:
        List of messages for Gemini repair request
    """
    platform = post_card.get('platform', 'unknown')
    caption = post_card.get('caption', '')
    errors = evaluation.get('errors', [])
    
    system_msg = (
        "You are an expert social media copywriter. "
        "Your task is to rewrite the provided caption to fix specific issues. "
        "Return ONLY the final, post-ready caption. "
        "DO NOT include advice, suggestions, or meta commentary."
    )
    
    # Build issue description
    issues_text = "\n".join(f"- {error}" for error in errors)
    
    # Build repair request
    user_msg = f"""Rewrite this {platform} caption to fix these issues:

{issues_text}

Original caption:
---
{caption}
---

Requirements for the rewritten caption:
1. FINAL post copy only (no coaching phrases like "you should", "consider", "try to")
2. Include at least ONE structure signal:
   - Numbered steps (1-3+)
   - Bullet points or checklist
   - Myth vs fact pattern
   - Concrete example with "For example..." or "Imagine..."
3. Hook + value + concrete example/framework + CTA
4. Match platform best practices for {platform}
5. Return ONLY the paste-ready caption text, nothing else

Rewritten caption:"""
    
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]


def attempt_repair(
    post_card: Dict[str, Any],
    evaluation: Dict[str, Any],
    gemini_client: Optional[Any] = None,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Attempt to repair a failed post card.
    
    Args:
        post_card: Original post card that failed
        evaluation: Quality evaluation with errors
        gemini_client: Optional Gemini client for repair
        context: Optional context for repair
        request_id: Optional request ID for logging
        
    Returns:
        {
            'ok': bool,
            'repaired_card': SocialPostCard,  # if ok=True
            'error': str  # if ok=False
        }
    """
    request_id = request_id or 'unknown'
    
    if not gemini_client:
        return {
            'ok': False,
            'error': 'No Gemini client available for repair'
        }
    
    try:
        # Build repair prompt
        messages = build_repair_prompt(post_card, evaluation, context)
        
        # Call Gemini for repair
        logger.info(f"[{request_id}] Attempting repair for {post_card.get('platform')} post")
        
        response = gemini_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        repaired_caption = response.choices[0].message.content.strip()
        
        # Create repaired card
        repaired_card = post_card.copy()
        repaired_card['caption'] = repaired_caption
        
        # Re-evaluate repaired card
        new_evaluation = evaluate_post_quality(repaired_card)
        
        if new_evaluation['passed']:
            logger.info(f"[{request_id}] Repair successful for {post_card.get('platform')}")
            return {
                'ok': True,
                'repaired_card': repaired_card
            }
        else:
            logger.warning(
                f"[{request_id}] Repair failed for {post_card.get('platform')}: "
                f"{new_evaluation['errors']}"
            )
            return {
                'ok': False,
                'error': f"Repair failed: {', '.join(new_evaluation['errors'])}"
            }
    
    except Exception as e:
        logger.exception(f"[{request_id}] Repair attempt failed: {e}")
        return {
            'ok': False,
            'error': f"Repair failed: {str(e)}"
        }
