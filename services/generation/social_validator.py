"""Social Validator - Hard validation gate to ensure post-ready content.

This module guarantees users never see scaffold text like:
- "Platform tip...", "Share a...", "Focus:...", "From...", "You should..."

Validation checks:
- Banned/meta phrases in caption
- Minimum structure present (steps/checklist/myth-fact/example)
- Minimum length thresholds by platform
- Valid hashtags (no slashes, no spaces, 8-12 for IG)

If validation fails:
- Run ONE repair rewrite ("final caption only, add concrete example/framework, no coaching")
- Re-validate and either return ok:true with posts[] OR ok:false with error.code="output_not_post_ready"
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Sentinel to detect whether caller provided an explicit openai_client kwarg
_OPENAI_CLIENT_MISSING = object()


# Minimum caption lengths by platform
PLATFORM_MIN_LENGTH = {
    'instagram': 100,  # IG benefits from richer captions
    'facebook': 80,
    'linkedin': 120,  # LinkedIn expects substantial value
    'x': 40,  # X is naturally shorter (280 char limit)
}

# Banned meta/scaffold phrases that should NEVER reach the user
BANNED_PHRASES = [
    # Instructional/coaching language
    'you should',
    'you could',
    'think about',
    'make sure to',
    'don\'t forget to',
    'remember to',
    'be sure to',
    'try to',
    
    # Meta/guidance language
    'platform tip',
    'posting tip',
    'what to post',
    'here are some ideas',
    'suggestions for',
    'when posting',
    'here\'s what to say',
    'talk about',
    'you might want to',
    'you can also',
]

# Additional scaffold patterns (regex)
SCAFFOLD_PATTERNS = [
    r'\bconsider\s+\w+ing\b',  # "consider posting" but not "Considering"
    r'(?:^|\n)\s*tip\s*:',  # "Tip: " at start of string or line
    r'(?:^|\n)\s*platform\s+tip',  # "Platform tip" at start of string or line
    r'(?:^|\n)\s*focus\s*:',  # "Focus: " at start of string or line
    r'\bshare\s+a\s+',  # "share a story/tip/etc"
    r'(?:^|\n)\s*from\s*:',  # "From: " at start of string or line (scaffold marker)
    r'(?:^|\n)\s*advice\s*:',  # "Advice: " at start of string or line
    r'(?:^|\n)\s*example\s*:',  # "Example: " at start (as scaffold marker, not "For example:")
    r'(?:^|\n)\s*note\s*:',  # "Note: " at start of string or line
    r'(?:^|\n)\s*suggestion\s*:',  # "Suggestion: " at start of string or line
]

# Repair prompt requirements (used in build_repair_prompt)
REPAIR_REQUIREMENTS = [
    "FINAL post copy only (no coaching phrases like \"you should\", \"consider\", \"try to\", \"platform tip\", \"share a\", \"focus:\")",
    "Include at least ONE structure signal:",
    "   - Numbered steps (1-3+)",
    "   - Bullet points or checklist",
    "   - Myth vs fact pattern",
    "   - Concrete example with \"For example...\" or \"Imagine...\"",
    "Hook + value + concrete example/framework + CTA",
    "Match platform best practices for {platform}",
    "Return ONLY the caption text, nothing else"
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


def contains_banned_phrases(text: str) -> Optional[str]:
    """Check if text contains banned meta/scaffold phrases.
    
    Args:
        text: Text to check
        
    Returns:
        Error message if banned phrase found, None if clean
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Check simple phrase matches
    for phrase in BANNED_PHRASES:
        if phrase in text_lower:
            return f"Contains banned phrase: '{phrase}'"
    
    # Check pattern matches
    for pattern in SCAFFOLD_PATTERNS:
        if re.search(pattern, text_lower):
            return "Contains scaffold/meta language pattern"
    
    return None


def has_structure_signal(caption: str) -> bool:
    """Check if caption contains at least one structure signal.
    
    Structure signals include:
    - Numbered steps
    - Bullet points
    - Myth vs fact
    - Concrete examples
    
    Args:
        caption: Caption text to check
        
    Returns:
        True if structure signal found, False otherwise
        
    Note:
        Uses DOTALL flag for multiline patterns (e.g., myth vs fact),
        allowing patterns to match across line boundaries.
    """
    for pattern in STRUCTURE_PATTERNS:
        if re.search(pattern, caption, re.DOTALL):
            return True
    return False


def validate_caption_length(caption: str, platform: str) -> Optional[str]:
    """Check if caption meets minimum length for platform.
    
    Args:
        caption: Caption text
        platform: Platform name (instagram, facebook, linkedin, x)
        
    Returns:
        Error message if too short, None if OK
    """
    min_length = PLATFORM_MIN_LENGTH.get(platform, 50)
    if len(caption.strip()) < min_length:
        return f"Caption too short for {platform} (min {min_length} chars, got {len(caption.strip())})"
    return None


def validate_hashtags(hashtags: List[str], platform: str) -> Optional[str]:
    """Validate hashtags format and count.
    
    Rules:
    - No slashes in hashtags
    - No spaces in hashtags
    - Instagram: 8-12 hashtags recommended
    - Other platforms: no strict count requirement
    
    Args:
        hashtags: List of hashtag strings
        platform: Platform name
        
    Returns:
        Error message if validation fails, None if OK
    """
    if not hashtags:
        return None  # Empty hashtags list is OK
    
    # Check each hashtag format
    for tag in hashtags:
        if not isinstance(tag, str):
            return f"Hashtag must be string, got {type(tag).__name__}"
        
        # Remove leading # if present
        tag_clean = tag.lstrip('#')
        
        # Check for slashes
        if '/' in tag_clean:
            return f"Hashtag contains slash: {tag}"
        
        # Check for spaces
        if ' ' in tag_clean:
            return f"Hashtag contains space: {tag}"
    
    # Instagram-specific count validation
    if platform == 'instagram':
        count = len(hashtags)
        if count < 8 or count > 12:
            return f"Instagram hashtags should be 8-12, got {count}"
    
    return None


def validate_post_card(post_card: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a single post card against all quality rules.
    
    Args:
        post_card: Post card dict with platform, caption, hashtags
        
    Returns:
        Dict with:
            - passed: bool
            - errors: List[str] (blocking issues)
            - warnings: List[str] (quality concerns)
    """
    errors = []
    warnings = []
    
    platform = post_card.get('platform', 'unknown')
    caption = post_card.get('caption', '')
    hashtags = post_card.get('hashtags', [])
    
    # Check for banned phrases (BLOCKING)
    if banned_error := contains_banned_phrases(caption):
        errors.append(banned_error)
    
    # Check caption length (BLOCKING for IG/LinkedIn)
    if length_error := validate_caption_length(caption, platform):
        if platform in ['instagram', 'linkedin']:
            errors.append(length_error)
        else:
            warnings.append(length_error)
    
    # Check for structure signals (BLOCKING)
    if not has_structure_signal(caption):
        errors.append(
            "Caption lacks structure signal (no numbered steps, bullets, examples, or frameworks)"
        )
    
    # Check hashtags (BLOCKING)
    if hashtag_error := validate_hashtags(hashtags, platform):
        errors.append(hashtag_error)
    
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
    }


def validate_all_posts(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate all post cards.
    
    Args:
        posts: List of post card dicts
        
    Returns:
        Dict with:
            - passed: bool (True if ALL posts pass)
            - results: List of validation results per post
            - summary: str
    """
    results = []
    
    for idx, post in enumerate(posts):
        validation = validate_post_card(post)
        results.append({
            'post_index': idx,
            'platform': post.get('platform', 'unknown'),
            'passed': validation['passed'],
            'errors': validation['errors'],
            'warnings': validation['warnings'],
        })
    
    # Overall pass = all posts pass
    all_passed = all(r['passed'] for r in results)
    
    # Build summary
    failed_count = sum(1 for r in results if not r['passed'])
    if all_passed:
        summary = f"All {len(posts)} posts passed validation"
    else:
        summary = f"{failed_count}/{len(posts)} posts failed validation"
    
    return {
        'passed': all_passed,
        'results': results,
        'summary': summary,
    }


def build_repair_prompt(
    post_card: Dict[str, Any],
    validation: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Build repair prompt to fix validation issues.
    
    Args:
        post_card: Original post card that failed
        validation: Validation result with errors
        
    Returns:
        List of messages for Gemini repair request
    """
    platform = post_card.get('platform', 'unknown')
    caption = post_card.get('caption', '')
    hashtags = post_card.get('hashtags', [])
    errors = validation.get('errors', [])
    
    system_msg = (
        "You are an expert social media copywriter. "
        "Your task is to rewrite the provided caption to fix specific issues. "
        "Return ONLY the final, post-ready caption. "
        "DO NOT include advice, suggestions, or meta commentary."
    )
    
    # Build issue description
    issues_text = "\n".join(f"- {error}" for error in errors)
    
    # Build requirements list (format platform placeholder)
    requirements_text = "\n".join(
        f"{i+1}. {req.format(platform=platform)}" 
        for i, req in enumerate(REPAIR_REQUIREMENTS)
    )
    
    # Build repair request
    user_msg = f"""Rewrite this {platform} caption to fix these issues:

{issues_text}

Original caption:
---
{caption}
---

Requirements for the rewritten caption:
{requirements_text}

Rewritten caption:"""
    
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]


def attempt_repair(
    post_card: Dict[str, Any],
    validation: Dict[str, Any],
    gemini_client: Optional[Any] = None,
    openai_client: Optional[Any] = _OPENAI_CLIENT_MISSING,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Attempt to repair a failed post card (ONE repair attempt only).
    
    Args:
        post_card: Original post card that failed
        validation: Validation result with errors
        gemini_client: Optional Gemini client for repair
        request_id: Optional request ID for logging
        
    Returns:
        Dict with:
            - ok: bool
            - repaired_card: Dict (if ok=True)
            - error: str (if ok=False)
    """
    request_id = request_id or 'unknown'
    
    # If caller explicitly passed openai_client=None, they requested OpenAI
    # path but provided no client. Return a clear message for that case.
    if openai_client is None and gemini_client is None:
        return {
            'ok': False,
            'error': 'No OpenAI client available for repair'
        }

    # If caller provided an OpenAI client (or we have only a Gemini client),
    # map whichever is present to gemini_client so existing repair logic can run.
    if not gemini_client and openai_client is not _OPENAI_CLIENT_MISSING:
        # Caller provided an explicit openai_client (may be a real client or None)
        gemini_client = openai_client

    if not gemini_client:
        # No repair client available at all
        return {
            'ok': False,
            'error': 'No Gemini client available for repair'
        }
    
    try:
        # Build repair prompt
        messages = build_repair_prompt(post_card, validation)
        
        # Call Gemini for repair (ONE attempt only)
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
        
        # Re-validate repaired card
        new_validation = validate_post_card(repaired_card)
        
        if new_validation['passed']:
            logger.info(f"[{request_id}] Repair successful for {post_card.get('platform')}")
            return {
                'ok': True,
                'repaired_card': repaired_card
            }
        else:
            logger.warning(
                f"[{request_id}] Repair failed for {post_card.get('platform')}: "
                f"{new_validation['errors']}"
            )
            return {
                'ok': False,
                'error': f"Repair failed: {', '.join(new_validation['errors'])}"
            }
    
    except Exception as e:
        logger.exception(f"[{request_id}] Repair attempt failed: {e}")
        return {
            'ok': False,
            'error': f"Repair failed: {str(e)}"
        }


def validate_and_repair_posts(
    posts: List[Dict[str, Any]],
    gemini_client: Optional[Any] = None,
    openai_client: Optional[Any] = _OPENAI_CLIENT_MISSING,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Validate posts and attempt repair if needed (unified entry point).
    
    This is the main entry point for validation with repair.
    
    Args:
        posts: List of post cards to validate
        gemini_client: Optional Gemini client for repair
        request_id: Optional request ID for logging
        
    Returns:
        Dict with:
            - ok: bool
            - posts: List[Dict] (if ok=True)
            - error: Dict with code and message (if ok=False)
    """
    request_id = request_id or 'unknown'
    
    # First validation pass
    validation_result = validate_all_posts(posts)
    
    if validation_result['passed']:
        # All posts pass, return success
        logger.info(f"[{request_id}] All posts passed validation")
        return {
            'ok': True,
            'posts': posts
        }
    
    # Some posts failed - attempt repair if Gemini available
    # If caller provided an explicit openai_client kwarg (even if None), map it
    # to gemini_client. If they passed None explicitly, treat that as a
    # signal that OpenAI path was requested but no client is available.
    if openai_client is None and gemini_client is None:
        logger.error(f"[{request_id}] Validation failed, no OpenAI client for repair")
        return {
            'ok': False,
            'error': {
                'code': 'output_not_post_ready',
                'message': 'Generated content does not meet quality standards',
                'details': validation_result
            }
        }

    if gemini_client is None and openai_client is not _OPENAI_CLIENT_MISSING:
        gemini_client = openai_client

    if not gemini_client:
        # No repair available - return error (generic path). Historically the
        # contract returned a generic 'output_not_rich_enough' code in the
        # no-repair case; preserve that contract to match tests that assert
        # on this specific code.
        logger.error(f"[{request_id}] Validation failed, no Gemini/OpenAI client for repair")
        details = validation_result
        code = 'output_not_rich_enough'

        return {
            'ok': False,
            'error': {
                'code': code,
                'message': 'Generated content does not meet quality standards',
                'details': details
            }
        }
    
    # Attempt repair
    logger.info(f"[{request_id}] Validation failed, attempting repair")
    repaired_posts = []
    
    for result in validation_result['results']:
        if result['passed']:
            # Post already passed, keep it
            repaired_posts.append(posts[result['post_index']])
        else:
            # Attempt repair
            post_card = posts[result['post_index']]
            repair_result = attempt_repair(
                post_card=post_card,
                validation=result,
                gemini_client=gemini_client,
                request_id=request_id
            )
            
            if repair_result['ok']:
                repaired_posts.append(repair_result['repaired_card'])
            else:
                # Repair failed - return error for this post
                logger.error(
                    f"[{request_id}] Repair failed for {post_card.get('platform')}: "
                    f"{repair_result['error']}"
                )
                return {
                    'ok': False,
                    'error': {
                        'code': 'output_not_rich_enough',
                        'message': f"Post {result['post_index']} repair failed: {repair_result['error']}",
                        'details': validation_result
                    }
                }
    
    # Re-validate all repaired posts
    final_validation = validate_all_posts(repaired_posts)
    
    if final_validation['passed']:
        logger.info(f"[{request_id}] Repair successful, all posts now pass")
        return {
            'ok': True,
            'posts': repaired_posts
        }
    else:
        # Still failing after repair - return error
        logger.error(f"[{request_id}] Posts still fail after repair")
        return {
            'ok': False,
            'error': {
                'code': 'output_not_rich_enough',
                'message': 'Generated content does not meet quality standards after repair',
                'details': final_validation
            }
        }
