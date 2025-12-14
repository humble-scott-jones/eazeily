"""Fallback generator - wraps existing generator.py for deterministic fallback."""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

# Import existing generator functions
try:
    import generator as gen_mod
    GENERATOR_AVAILABLE = True
except ImportError:
    gen_mod = None
    GENERATOR_AVAILABLE = False


logger = logging.getLogger(__name__)


def generate_social_posts_fallback(
    session_length: int = 7,
    platforms: Optional[List[str]] = None,
    tone: str = 'professional',
    industry: str = 'business',
    company_name: str = '',
    goals: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    variant_types: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate social posts using deterministic fallback logic.
    
    Args:
        session_length: Number of days to generate (1, 7, or 30)
        platforms: List of platforms to generate for
        tone: Tone of voice
        industry: Business industry
        company_name: Company name
        goals: Content goals
        keywords: Keywords to include
        variant_types: List of variant types to generate (e.g., ['shorter', 'more_professional'])
        **kwargs: Additional params passed to generator
        
    Returns:
        Dict with 'posts' list and metadata
    """
    if not GENERATOR_AVAILABLE or not gen_mod:
        # Ultra-minimal fallback if generator module not available
        return _minimal_fallback(session_length, platforms, tone, industry)
    
    try:
        # Call existing generator.generate_posts
        posts = gen_mod.generate_posts(
            days=session_length,
            platforms=platforms or ['instagram', 'facebook', 'linkedin'],
            tone=tone,
            industry=industry,
            company=company_name,  # Fixed: use 'company' not 'company_name'
            goals=goals,
            brand_keywords=keywords,
            variant_types=variant_types,
            **{k: v for k, v in kwargs.items() if k not in ['days', 'platforms', 'tone', 'industry', 'company_name', 'company', 'goals', 'keywords', 'brand_keywords', 'variant_types']}
        )
        
        # Normalize to expected format with 'cards'
        # generator.py returns one post per platform, but we need posts grouped by day with cards array
        if not isinstance(posts, list):
            posts = []
        
        # Group posts by day_index and convert to cards format
        normalized_posts = []
        posts_by_day = {}
        
        for post in posts:
            if not isinstance(post, dict):
                continue
            
            day_index = post.get('day_index', 1)
            if day_index not in posts_by_day:
                posts_by_day[day_index] = {
                    'date': post.get('date', ''),
                    'pillar': post.get('pillar', 'Engagement'),
                    'cards': [],
                    'voice_note': post.get('voice_note')
                }
            
            # Convert post to card format
            card = {
                'platform': post.get('platform', 'instagram'),
                'caption': post.get('caption', ''),
                'hashtags': post.get('hashtags', []),
                'hook': post.get('hook'),
                'cta': post.get('cta'),
                'media_idea': post.get('image_prompt'),
                'alt_text': post.get('alt_text'),
                'warnings': post.get('warnings'),
                'thumbnail_note': post.get('thumbnail_note'),
            }
            
            # Remove None values
            card = {k: v for k, v in card.items() if v is not None}
            
            posts_by_day[day_index]['cards'].append(card)
        
        # Convert to list sorted by day
        normalized_posts = [posts_by_day[day] for day in sorted(posts_by_day.keys())]
        
        return {
            'posts': normalized_posts,
            'count': len(normalized_posts),
            'summary': f"Generated {len(normalized_posts)} posts using deterministic fallback"
        }
        
    except Exception as e:
        logger.exception(f"Fallback generator failed: {e}")
        return _minimal_fallback(session_length, platforms, tone, industry)


def generate_reel_script_fallback(
    hook_style: Optional[str] = None,
    format_type: Optional[str] = None,
    duration: int = 30,
    industry: str = 'business',
    tone: str = 'engaging',
    **kwargs
) -> Dict[str, Any]:
    """Generate reel script using deterministic fallback logic.
    
    Args:
        hook_style: Hook type (question, stat, story)
        format_type: Video format (tutorial, behind-scenes)
        duration: Target duration in seconds
        industry: Business industry
        tone: Tone of voice
        **kwargs: Additional params
        
    Returns:
        Dict with 'script' containing hook, beats, cta, etc.
    """
    # Build simple script structure
    hook = _generate_hook(hook_style, industry, tone)
    beats = _generate_beats(format_type, duration, industry)
    cta = _generate_cta(industry, tone)
    
    script = {
        'hook': hook,
        'beats': beats,
        'cta': cta,
        'caption': f"Check out this {format_type or 'content'} about {industry}! {cta}",
        'hashtags': _generate_hashtags(industry, limit=5)
    }
    
    return {
        'script': script,
        'summary': 'Generated using deterministic fallback'
    }


def generate_review_response_fallback(
    review_text: str,
    rating: Optional[int] = None,
    tone: str = 'professional',
    company_name: str = '',
    **kwargs
) -> Dict[str, Any]:
    """Generate review response using deterministic fallback logic.
    
    Args:
        review_text: The review to respond to
        rating: Star rating (1-5)
        tone: Tone of voice
        company_name: Company name
        **kwargs: Additional params
        
    Returns:
        Dict with 'responses' containing short, medium, long variants
    """
    # Determine sentiment from rating
    sentiment = 'positive' if rating and rating >= 4 else ('negative' if rating and rating <= 2 else 'neutral')
    
    # Build response templates
    if sentiment == 'positive':
        short = f"Thank you for the wonderful review! We're so glad you had a great experience."
        medium = f"Thank you so much for your kind words! We're thrilled to hear you had a positive experience with us. Your feedback means a lot to our team."
        long = f"Thank you for taking the time to share your experience! We're delighted to hear that you enjoyed {company_name or 'our service'}. Feedback like yours motivates our team to continue delivering excellent service. We look forward to serving you again soon!"
    elif sentiment == 'negative':
        short = f"We apologize for your experience. Please contact us directly so we can make this right."
        medium = f"We're sorry to hear about your experience. This is not the level of service we strive for. Please reach out to us directly so we can address your concerns and make things right."
        long = f"Thank you for bringing this to our attention. We sincerely apologize for falling short of your expectations. At {company_name or 'our company'}, customer satisfaction is our priority, and we take your feedback seriously. Please contact us directly so we can discuss this further and find a resolution. We'd appreciate the opportunity to make this right."
    else:
        short = f"Thank you for your feedback. We appreciate you taking the time to share your thoughts."
        medium = f"Thank you for your review. We appreciate all feedback as it helps us improve our service. If you have any specific concerns, please feel free to reach out to us directly."
        long = f"Thank you for taking the time to share your feedback with us. We value all input from our customers as it helps us identify areas for improvement. At {company_name or 'our company'}, we're committed to providing the best possible experience. If there's anything specific we can address, please don't hesitate to contact us directly."
    
    return {
        'responses': {
            'short': short,
            'medium': medium,
            'long': long
        },
        'tone': tone,
        'voice_applied': False,
        'summary': 'Generated using deterministic fallback'
    }


def _minimal_fallback(session_length: int, platforms: Optional[List[str]], tone: str, industry: str) -> Dict[str, Any]:
    """Ultra-minimal fallback when generator module is not available."""
    platforms = platforms or ['instagram', 'facebook', 'linkedin']
    posts = []
    
    pillars = ['Educational', 'Behind-the-Scenes', 'Testimonial', 'Product', 'Engagement', 'Story']
    
    for i in range(min(session_length, 7)):  # Cap at 7 for minimal fallback
        post_date = (date.today() + timedelta(days=i)).isoformat()
        pillar = pillars[i % len(pillars)]
        
        cards = []
        for platform in platforms[:3]:  # Limit platforms
            caption = f"Day {i+1}: {pillar} post for {industry}. Stay tuned for more!"
            cards.append({
                'platform': platform,
                'caption': caption,
                'hashtags': _generate_hashtags(industry, limit=5),
                'hook': f"Quick tip for {industry} professionals",
                'cta': 'Follow for more insights'
            })
        
        posts.append({
            'date': post_date,
            'pillar': pillar,
            'cards': cards
        })
    
    return {
        'posts': posts,
        'count': len(posts),
        'summary': 'Generated using minimal fallback'
    }


def _generate_hook(hook_style: Optional[str], industry: str, tone: str) -> str:
    """Generate a hook based on style."""
    hooks = {
        'question': f"Ever wonder how {industry} professionals do it?",
        'stat': f"Did you know? {industry} insights ahead!",
        'story': f"Here's what happened when we tried this in {industry}...",
        'default': f"Let's talk about {industry}"
    }
    return hooks.get(hook_style or 'default', hooks['default'])


def _generate_beats(format_type: Optional[str], duration: int, industry: str) -> List[Dict[str, str]]:
    """Generate script beats based on format and duration."""
    # Simple 3-beat structure
    beats = [
        {'text': f"First, understand the basics of {industry}"},
        {'text': "Then, apply what you've learned"},
        {'text': "Finally, see the results"}
    ]
    
    if duration > 45:
        # Add more beats for longer videos
        beats.insert(1, {'text': "Next, let's dive deeper"})
        beats.append({'text': "And here's the bonus tip"})
    
    return beats


def _generate_cta(industry: str, tone: str) -> str:
    """Generate a call to action."""
    ctas = [
        "Try this and let me know how it goes!",
        "Share this with someone who needs it",
        "Follow for more tips",
        "Drop a comment if you found this helpful"
    ]
    return ctas[hash(industry + tone) % len(ctas)]


def _generate_hashtags(industry: str, limit: int = 5) -> List[str]:
    """Generate relevant hashtags."""
    base_tags = [industry.lower(), 'business', 'tips', 'smallbusiness', 'entrepreneur']
    return [f"#{tag.replace(' ', '')}" for tag in base_tags[:limit]]
