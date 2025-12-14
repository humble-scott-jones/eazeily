"""Output validator - validates and repairs generated content."""

import logging
from typing import Any, Dict, Optional, List, Tuple
from .output_schemas import (
    validate_social_posts,
    validate_reel_script,
    validate_review_responses,
    SocialPostsOutput,
    ReelOutput,
    ReviewResponseOutput
)


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when output validation fails."""
    pass


def validate_and_repair_social_posts(data: Any) -> SocialPostsOutput:
    """Validate social posts output and attempt repair if needed.
    
    Args:
        data: Output data to validate
        
    Returns:
        Validated SocialPostsOutput
        
    Raises:
        ValidationError: If validation fails and cannot be repaired
    """
    try:
        return validate_social_posts(data)
    except ValueError as e:
        logger.warning(f"Social posts validation failed: {e}, attempting repair")
        
        # Attempt repairs
        if not isinstance(data, dict):
            raise ValidationError("Output must be a dict") from e
        
        # Ensure posts array exists
        if 'posts' not in data or not isinstance(data['posts'], list):
            raise ValidationError("Output must contain 'posts' list") from e
        
        posts = data['posts']
        if not posts:
            raise ValidationError("Posts list is empty") from e
        
        # Repair individual posts
        repaired_posts = []
        for idx, post in enumerate(posts):
            if not isinstance(post, dict):
                logger.warning(f"Post {idx} is not a dict, skipping")
                continue
            
            # Ensure required fields
            if 'date' not in post:
                post['date'] = f"Day {idx + 1}"
            if 'pillar' not in post:
                post['pillar'] = "Engagement"
            
            # Ensure cards array
            if 'cards' not in post or not isinstance(post['cards'], list):
                logger.warning(f"Post {idx} has no cards, skipping")
                continue
            
            # Repair cards
            repaired_cards = []
            for card_idx, card in enumerate(post['cards']):
                if not isinstance(card, dict):
                    continue
                
                # Ensure platform and caption
                if 'platform' not in card:
                    card['platform'] = 'instagram'
                if 'caption' not in card or not card['caption']:
                    logger.warning(f"Post {idx} card {card_idx} has no caption, skipping")
                    continue
                
                # Ensure hashtags is a list
                if 'hashtags' not in card or not isinstance(card['hashtags'], list):
                    card['hashtags'] = []
                
                repaired_cards.append(card)
            
            if repaired_cards:
                post['cards'] = repaired_cards
                repaired_posts.append(post)
        
        if not repaired_posts:
            raise ValidationError("No valid posts after repair") from e
        
        # Return repaired output
        data['posts'] = repaired_posts
        return validate_social_posts(data)


def validate_and_repair_reel_script(data: Any) -> ReelOutput:
    """Validate reel script output and attempt repair if needed.
    
    Args:
        data: Output data to validate
        
    Returns:
        Validated ReelOutput
        
    Raises:
        ValidationError: If validation fails and cannot be repaired
    """
    try:
        return validate_reel_script(data)
    except ValueError as e:
        logger.warning(f"Reel script validation failed: {e}, attempting repair")
        
        if not isinstance(data, dict):
            raise ValidationError("Output must be a dict") from e
        
        script = data.get('script')
        if not isinstance(script, dict):
            raise ValidationError("Output must contain 'script' dict") from e
        
        # Ensure required fields
        if 'hook' not in script or not script['hook']:
            raise ValidationError("Script must have non-empty 'hook'") from e
        
        if 'cta' not in script or not script['cta']:
            # Provide default CTA
            script['cta'] = "Try this and let me know!"
        
        # Ensure beats is a list
        if 'beats' not in script or not isinstance(script['beats'], list):
            script['beats'] = []
        
        # Ensure caption and hashtags
        if 'caption' not in script:
            script['caption'] = ''
        if 'hashtags' not in script or not isinstance(script['hashtags'], list):
            script['hashtags'] = []
        
        data['script'] = script
        return validate_reel_script(data)


def validate_and_repair_review_responses(data: Any) -> ReviewResponseOutput:
    """Validate review responses output and attempt repair if needed.
    
    Args:
        data: Output data to validate
        
    Returns:
        Validated ReviewResponseOutput
        
    Raises:
        ValidationError: If validation fails and cannot be repaired
    """
    try:
        return validate_review_responses(data)
    except ValueError as e:
        logger.warning(f"Review responses validation failed: {e}, attempting repair")
        
        if not isinstance(data, dict):
            raise ValidationError("Output must be a dict") from e
        
        responses = data.get('responses')
        if not isinstance(responses, dict):
            raise ValidationError("Output must contain 'responses' dict") from e
        
        # Ensure at least one response variant
        valid_responses = {}
        for key in ['short', 'medium', 'long']:
            val = responses.get(key)
            if val and isinstance(val, str) and val.strip():
                valid_responses[key] = val.strip()
        
        if not valid_responses:
            raise ValidationError("At least one response variant required") from e
        
        data['responses'] = valid_responses
        
        # Ensure tone and voice_applied fields
        if 'tone' not in data:
            data['tone'] = 'professional'
        if 'voice_applied' not in data:
            data['voice_applied'] = False
        
        return validate_review_responses(data)


def detect_sensitive_content(text: str) -> Optional[str]:
    """Detect potentially sensitive content that should not be in public posts.
    
    Args:
        text: Text to scan
        
    Returns:
        Warning message if sensitive content detected, None otherwise
    """
    import re
    
    # Phone number patterns
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
        r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',  # (555) 555-5555
    ]
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Check for phone numbers
    for pattern in phone_patterns:
        if re.search(pattern, text):
            return "Phone number detected - removed from public response"
    
    # Check for emails
    if re.search(email_pattern, text):
        return "Email address detected - removed from public response"
    
    return None


def sanitize_public_content(text: str) -> str:
    """Remove sensitive content from text before public posting.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text with sensitive content removed
    """
    import re
    
    # Remove phone numbers
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',
    ]
    for pattern in phone_patterns:
        text = re.sub(pattern, '[contact info removed]', text)
    
    # Remove emails
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[contact info removed]',
        text
    )
    
    return text


# Coaching phrase detection patterns
COACHING_PHRASES = [
    r'\byou should\b',
    r'\bconsider\b',
    r'\btry to\b',
    r'\bmake sure to\b',
    r'\bdon\'t forget to\b',
    r'\bremember to\b',
    r'\bhere\'s what to say\b',
    r'\bhere\'s how\b',
    r'\bthink about\b',
    r'\bfeel free to\b',
    r'\byou could\b',
    r'\byou might want to\b',
    r'\bit\'s important to\b',
    r'\bbe sure to\b',
]


def detect_coaching_phrases(text: str) -> Optional[List[str]]:
    """Detect coaching/advisory phrases in text that should not be in final copy.
    
    Args:
        text: Text to scan for coaching phrases
        
    Returns:
        List of detected coaching phrases, or None if none found
    """
    import re
    
    detected = []
    text_lower = text.lower()
    
    for pattern in COACHING_PHRASES:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            detected.extend(matches)
    
    return detected if detected else None


def repair_coaching_caption(
    caption: str,
    openai_client: Optional[Any] = None
) -> Tuple[str, bool]:
    """Attempt to repair a caption that contains coaching phrases.
    
    Args:
        caption: Caption text to repair
        openai_client: OpenAI client for repair (optional)
        
    Returns:
        Tuple of (repaired_caption, was_repaired)
    """
    detected = detect_coaching_phrases(caption)
    if not detected:
        return caption, False
    
    if not openai_client:
        # If no client available, just return original
        logger.warning(f"Coaching phrases detected but no OpenAI client for repair: {detected}")
        return caption, False
    
    try:
        # Build repair prompt
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a content editor. "
                    "Rewrite the given text into final, paste-ready social media copy. "
                    "Remove all coaching language, advice, and meta-commentary. "
                    "Keep the core message and meaning intact. "
                    "Return ONLY the rewritten caption, nothing else."
                )
            },
            {
                "role": "user",
                "content": f"Rewrite this caption to remove coaching phrases and make it paste-ready:\n\n{caption}"
            }
        ]
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        repaired = response.choices[0].message.content.strip()
        
        # Verify repair actually removed coaching phrases
        if detect_coaching_phrases(repaired):
            logger.warning("Repair pass did not fully remove coaching phrases")
            return caption, False
        
        logger.info(f"Successfully repaired coaching caption")
        return repaired, True
        
    except Exception as e:
        logger.error(f"Failed to repair coaching caption: {e}")
        return caption, False


def validate_with_schema_enforcement(
    data: Any,
    content_type: str,
    openai_client: Optional[Any] = None,
    prompt_set: Optional[Dict[str, str]] = None,
    json_schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate output with strict schema enforcement and repair pass.
    
    This implements the requirement:
    - Validate model output against schema
    - If invalid, do one "repair pass" with the same context but stricter instruction
    - If still invalid, return error or fallback
    
    Args:
        data: Output data to validate
        content_type: Type of content ('social', 'reels', 'reviews')
        openai_client: OpenAI client for repair pass (optional)
        prompt_set: Original prompt set for repair (optional)
        json_schema: JSON schema for validation (optional)
        
    Returns:
        Dict with 'ok', 'data', 'repaired', 'error' keys
    """
    result = {'ok': False, 'repaired': False, 'data': None, 'error': None}
    
    # First validation attempt
    try:
        if content_type == 'social':
            validated = validate_and_repair_social_posts(data)
        elif content_type == 'reels':
            validated = validate_and_repair_reel_script(data)
        elif content_type == 'reviews':
            validated = validate_and_repair_review_responses(data)
        else:
            raise ValidationError(f"Unknown content type: {content_type}")
        
        result['ok'] = True
        result['data'] = validated
        return result
        
    except (ValidationError, ValueError) as e:
        logger.warning(f"Initial validation failed for {content_type}: {e}")
        result['error'] = str(e)
        
        # Try repair pass if OpenAI client and prompt available
        if openai_client and prompt_set:
            logger.info(f"Attempting repair pass for {content_type}")
            try:
                repaired_data = _attempt_repair_pass(
                    openai_client=openai_client,
                    prompt_set=prompt_set,
                    json_schema=json_schema,
                    original_error=str(e)
                )
                
                # Validate repaired output
                if content_type == 'social':
                    validated = validate_and_repair_social_posts(repaired_data)
                elif content_type == 'reels':
                    validated = validate_and_repair_reel_script(repaired_data)
                elif content_type == 'reviews':
                    validated = validate_and_repair_review_responses(repaired_data)
                
                result['ok'] = True
                result['data'] = validated
                result['repaired'] = True
                logger.info(f"Repair pass succeeded for {content_type}")
                return result
                
            except Exception as repair_error:
                logger.error(f"Repair pass failed for {content_type}: {repair_error}")
                result['error'] = f"Validation failed: {e}. Repair failed: {repair_error}"
        
        # Fallback: return error
        return result


def _attempt_repair_pass(
    openai_client: Any,
    prompt_set: Dict[str, str],
    json_schema: Optional[Dict[str, Any]],
    original_error: str
) -> Any:
    """Attempt single repair pass with stricter instructions.
    
    Args:
        openai_client: OpenAI client
        prompt_set: Original prompt set
        json_schema: JSON schema for validation
        original_error: Error from first attempt
        
    Returns:
        Repaired output data
        
    Raises:
        Exception: If repair pass fails
    """
    # Build stricter prompt
    system = prompt_set.get('system', '')
    system += (
        "\n\nIMPORTANT: Your previous output had validation errors. "
        "This is your ONE chance to fix it. "
        f"Error details: {original_error}. "
        "Return ONLY valid JSON. No extra text. No markdown. Just JSON."
    )
    
    context = prompt_set.get('context', '')
    request = prompt_set.get('request', '')
    
    if json_schema:
        request += f"\n\nSTRICT SCHEMA (must match exactly):\n{json_schema}"
    
    # Build messages
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{context}\n\n{request}"}
    ]
    
    # Call OpenAI with stricter validation
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistency
            response_format={"type": "json_object"}
        )
        
        import json
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"OpenAI repair call failed: {e}")
        raise
