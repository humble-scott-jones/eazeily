"""Gemini adapter for structured content generation.

This module provides a clean interface to Google's Gemini API for content generation,
with proper error handling, timeouts, and retry logic.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional
import time

logger = logging.getLogger(__name__)

# Import Gemini client
try:
    import google.genai as genai
except ImportError:
    genai = None

# Constants
DEFAULT_MODEL = 'gemini-1.5-flash'
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_DELAY = 1.0


def _get_client():
    """Get configured Gemini client."""
    if not genai:
        logger.error("google-genai package not available")
        return None
    
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("No API key configured for Gemini")
        return None
    
    try:
        if hasattr(genai, "Client"):
            return genai.Client(api_key=api_key)
        elif hasattr(genai, "configure"):
            genai.configure(api_key=api_key)
            return genai
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None
    
    return None


def call_gemini(
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES
) -> Optional[Dict[str, Any]]:
    """Call Gemini API with retry logic and error handling.
    
    Args:
        prompt: The prompt text to send to Gemini
        context: Optional context dictionary to include in the prompt
        model: Model name to use (default: gemini-1.5-flash)
        temperature: Generation temperature (0.0-1.0)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    
    Returns:
        Parsed JSON response from Gemini, or None on failure
    """
    client = _get_client()
    if not client:
        logger.error("Gemini client not available")
        return None
    
    # Build full prompt with context
    full_prompt = prompt
    if context:
        context_str = json.dumps(context, indent=2)
        full_prompt = f"{prompt}\n\nContext:\n{context_str}"
    
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            start_time = time.time()
            
            # Call Gemini API
            if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                # New client API
                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config={
                        'temperature': temperature,
                        'max_output_tokens': 2048,
                    }
                )
            elif hasattr(client, "GenerativeModel"):
                # Legacy API
                model_instance = client.GenerativeModel(model)
                response = model_instance.generate_content(
                    full_prompt,
                    generation_config={
                        'temperature': temperature,
                        'max_output_tokens': 2048,
                    }
                )
            else:
                logger.error("Unknown Gemini client interface")
                return None
            
            duration = time.time() - start_time
            logger.info(f"Gemini API call completed in {duration:.2f}s")
            
            # Extract text response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                if response_text.strip().startswith("```json"):
                    response_text = response_text.strip()[7:]
                if response_text.strip().startswith("```"):
                    response_text = response_text.strip()[3:]
                if response_text.strip().endswith("```"):
                    response_text = response_text.strip()[:-3]
                response_text = response_text.strip()
                
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # Return as text if not JSON
                logger.warning("Gemini response is not JSON, returning as text")
                return {'text': response_text}
        
        except Exception as e:
            last_error = e
            logger.warning(f"Gemini API call attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries:
                # Wait before retrying
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"All Gemini API retry attempts failed: {last_error}")
    
    return None


def generate_content_with_profile(
    profile: Dict[str, Any],
    content_type: str,
    topic: str,
    platform: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Generate content using profile data with Gemini.
    
    This function structures the profile data and content requirements
    into an optimal prompt for Gemini to generate high-quality content.
    
    Args:
        profile: User's brand profile including company, industry, customers, keywords, etc.
        content_type: Type of content (post, proposal, review_reply, blog_post, etc.)
        topic: Content topic or subject
        platform: Target platform (instagram, linkedin, etc.)
        additional_context: Any additional context for generation
    
    Returns:
        Generated content as a dictionary, or None on failure
    """
    # Build structured context
    context = {
        'company': profile.get('company', profile.get('business_name', '')),
        'industry': profile.get('industry', ''),
        'target_audience': profile.get('target_audience', ''),
        'customers': profile.get('customers', []),
        'brand_voice': profile.get('brand_voice', profile.get('tone', '')),
        'brand_keywords': profile.get('brand_keywords', []),
        'niche_keywords': profile.get('niche_keywords', []),
        'key_offer': profile.get('key_offer', ''),
        'scraped_meta': profile.get('scraped_meta', {}),
    }
    
    # Add additional context
    if additional_context:
        context.update(additional_context)
    
    # Build content-type-specific prompt
    prompt = _build_prompt(content_type, topic, platform, context)
    
    # Call Gemini
    return call_gemini(prompt, context=None)  # Context is already in prompt


def _build_prompt(
    content_type: str,
    topic: str,
    platform: Optional[str],
    context: Dict[str, Any]
) -> str:
    """Build content-type-specific prompt."""
    
    base_prompt = f"""You are an expert content creator. Generate high-quality content that matches the brand voice and resonates with the target audience.

Brand Context:
- Company: {context.get('company', 'N/A')}
- Industry: {context.get('industry', 'N/A')}
- Target Audience: {context.get('target_audience', 'N/A')}
- Brand Voice: {context.get('brand_voice', 'professional and friendly')}
- Brand Keywords: {', '.join(context.get('brand_keywords', []))}
- Niche Keywords: {', '.join(context.get('niche_keywords', []))}
"""
    
    # Add customer segments if available
    if context.get('customers'):
        base_prompt += f"- Key Audiences: {', '.join(context.get('customers', []))}\n"
    
    if content_type == 'proposal':
        return base_prompt + f"""
Content Type: Business Proposal
Topic: {topic}

Generate a professional business proposal with:
1. Three compelling title options
2. Executive summary (3-4 bullet points)
3. Key benefits (bullet list)
4. Clear call-to-action
5. Compelling subject line

Return as JSON with keys: titles (array), summary (string), benefits (array), cta (string), subject_line (string)
"""
    
    elif content_type == 'review_reply':
        return base_prompt + f"""
Content Type: Customer Review Reply
Review Content: {topic}

Generate a professional review response with:
1. Acknowledgment and appreciation
2. Address specific points if mentioned
3. Proposed remedy or action (if applicable)
4. Maintain brand voice

Return as JSON with keys: reply (string), short_reply (string, <140 chars)
"""
    
    elif content_type == 'blog_post':
        return base_prompt + f"""
Content Type: Blog Post
Topic: {topic}

Generate a comprehensive blog post with:
1. Three title options (engaging, SEO-friendly)
2. Meta description (150-160 characters)
3. Outline with H2 headings
4. Full draft (750-1200 words)
5. Call-to-action

Return as JSON with keys: titles (array), meta_description (string), outline (array), content (string), cta (string)
"""
    
    else:
        # Default: social media post
        platform_str = platform or 'social media'
        return base_prompt + f"""
Content Type: Social Media Post
Platform: {platform_str}
Topic: {topic}

Generate engaging social media content that:
- Matches the brand voice
- Resonates with the target audience
- Includes relevant hashtags (if appropriate)
- Has a clear message or call-to-action
- Optimized for {platform_str}

Return as JSON with keys: content (string), caption (string), hashtags (array)
"""


def validate_generated_content(
    content: Optional[Dict[str, Any]],
    content_type: str
) -> bool:
    """Validate that generated content has expected structure.
    
    Args:
        content: Generated content dictionary
        content_type: Expected content type
    
    Returns:
        True if content is valid, False otherwise
    """
    if not content or not isinstance(content, dict):
        return False
    
    # Content-type-specific validation
    if content_type == 'proposal':
        return all(k in content for k in ['titles', 'summary', 'benefits', 'cta'])
    elif content_type == 'review_reply':
        return 'reply' in content
    elif content_type == 'blog_post':
        return all(k in content for k in ['titles', 'content'])
    else:
        # For posts, accept either 'content' or 'caption'
        return 'content' in content or 'caption' in content or 'text' in content
    
    return True
