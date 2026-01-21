"""Template service for industry-specific content generation templates.

This service provides quick-start templates organized by industry to help users
generate content faster with pre-configured topics and moods.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Industry-specific templates for quick content generation
INDUSTRY_TEMPLATES = {
    'restaurant': [
        {'name': 'Daily Special', 'topic': "today's special dish", 'mood': 'excited'},
        {'name': 'Weekend Promo', 'topic': 'weekend dining special', 'mood': 'urgent'},
        {'name': 'Behind the Kitchen', 'topic': 'behind the scenes in our kitchen', 'mood': 'casual'},
        {'name': 'Customer Spotlight', 'topic': 'featuring a happy customer', 'mood': 'celebratory'},
        {'name': 'New Menu Item', 'topic': 'announcing a new menu item', 'mood': 'excited'},
    ],
    'fitness': [
        {'name': 'Monday Motivation', 'topic': 'motivational fitness message', 'mood': 'inspiring'},
        {'name': 'Workout Tip', 'topic': 'quick fitness tip', 'mood': 'professional'},
        {'name': 'Transformation Story', 'topic': 'client success story', 'mood': 'celebratory'},
        {'name': 'Class Schedule', 'topic': 'this week\'s class schedule', 'mood': 'excited'},
        {'name': 'Nutrition Advice', 'topic': 'healthy eating tip', 'mood': 'informative'},
    ],
    'retail': [
        {'name': 'Flash Sale', 'topic': 'limited time sale announcement', 'mood': 'urgent'},
        {'name': 'New Arrivals', 'topic': 'showcasing new products', 'mood': 'excited'},
        {'name': 'Styling Tips', 'topic': 'how to style our products', 'mood': 'casual'},
        {'name': 'Customer Review', 'topic': 'featuring customer testimonial', 'mood': 'celebratory'},
        {'name': 'Gift Guide', 'topic': 'gift ideas for the season', 'mood': 'informative'},
    ],
    'salon': [
        {'name': 'Before & After', 'topic': 'stunning transformation showcase', 'mood': 'excited'},
        {'name': 'Hair Care Tip', 'topic': 'professional hair care advice', 'mood': 'informative'},
        {'name': 'Special Offer', 'topic': 'limited time service discount', 'mood': 'urgent'},
        {'name': 'Trending Style', 'topic': 'latest hair or beauty trend', 'mood': 'professional'},
        {'name': 'Client Love', 'topic': 'happy client testimonial', 'mood': 'celebratory'},
    ],
    'software': [
        {'name': 'Feature Announcement', 'topic': 'new product feature launch', 'mood': 'excited'},
        {'name': 'Quick Tutorial', 'topic': 'how to use a key feature', 'mood': 'informative'},
        {'name': 'Customer Success', 'topic': 'customer achievement story', 'mood': 'celebratory'},
        {'name': 'Tech Tip', 'topic': 'productivity tip for users', 'mood': 'professional'},
        {'name': 'Product Update', 'topic': 'latest improvements and fixes', 'mood': 'informative'},
    ],
    'default': [
        {'name': 'Weekly Update', 'topic': 'what\'s happening this week', 'mood': 'casual'},
        {'name': 'Special Announcement', 'topic': 'important business update', 'mood': 'professional'},
        {'name': 'Customer Appreciation', 'topic': 'thanking our customers', 'mood': 'celebratory'},
        {'name': 'Behind the Scenes', 'topic': 'day in the life at our business', 'mood': 'casual'},
        {'name': 'Limited Offer', 'topic': 'exclusive limited time offer', 'mood': 'urgent'},
    ],
}


def get_templates_for_industry(industry: Optional[str]) -> List[Dict[str, str]]:
    """Get templates for a specific industry.
    
    Args:
        industry: Industry name (e.g., 'restaurant', 'fitness')
                 If None or unknown, returns default templates
    
    Returns:
        List of template dictionaries with 'name', 'topic', and 'mood' keys
    """
    if not industry:
        return INDUSTRY_TEMPLATES['default']
    
    # Normalize industry name (lowercase, strip whitespace)
    industry_normalized = industry.lower().strip()
    
    # Return templates for the industry, or default if not found
    return INDUSTRY_TEMPLATES.get(industry_normalized, INDUSTRY_TEMPLATES['default'])


def get_template_by_index(industry: Optional[str], index: int) -> Optional[Dict[str, str]]:
    """Get a specific template by its index (1-based).
    
    Args:
        industry: Industry name
        index: Template index (1-5)
    
    Returns:
        Template dictionary or None if index is out of range
    """
    templates = get_templates_for_industry(industry)
    
    if index < 1 or index > len(templates):
        return None
    
    return templates[index - 1]


def format_template_list(industry: Optional[str]) -> str:
    """Format templates as a numbered list for display.
    
    Args:
        industry: Industry name
    
    Returns:
        Formatted string with numbered template list
    """
    templates = get_templates_for_industry(industry)
    
    lines = ["**Quick Templates:**\n"]
    for i, template in enumerate(templates, 1):
        lines.append(f"{i}. **{template['name']}** - {template['topic']}")
    
    lines.append("\n_Reply with a number (1-5) to use a template, or describe what you need._")
    
    return "\n".join(lines)


def get_available_industries() -> List[str]:
    """Get list of all available industries with templates.
    
    Returns:
        List of industry names
    """
    return [ind for ind in INDUSTRY_TEMPLATES.keys() if ind != 'default']
