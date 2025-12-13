"""Output validator - validates and repairs generated content."""

import logging
from typing import Any, Dict, Optional
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
