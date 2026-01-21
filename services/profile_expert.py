"""
AI-powered profile field suggestions using full profile context.
Uses Google Gemini (the project's primary AI provider).
"""
import logging
from services.ai_service import get_generative_model

logger = logging.getLogger(__name__)


def process_raw_audience_input(user_input: str, profile) -> dict:
    """
    Process raw user input about target audience through AI.
    
    Handles cases like:
    - "Look on my website https://example.com and figure it out"
    - "Check my Instagram @mybrand"
    - Long descriptions that need summarization
    
    Args:
        user_input: The raw user input about their target audience
        profile: VoiceProfile instance with current profile data
    
    Returns:
        dict with 'success', 'audience', and optional 'error'
    """
    
    # Get business context from profile
    business_name = profile.business_name or 'Your business'
    industry = profile.industry or 'your industry'
    brand_voice = profile.brand_voice or profile.tone or 'Not set yet'
    
    prompt = f"""You are analyzing user input about their target audience.

BUSINESS CONTEXT:
- Business: {business_name}
- Industry: {industry}
- Brand Voice: {brand_voice}

USER INPUT:
"{user_input}"

Your task:
1. If they referenced a URL, analyze what you know about their business
2. If they gave a vague description, make it specific
3. Return a concise, actionable target audience description (2-3 sentences max)

Format: [Demographics] who [pain point/need]. They're looking for [solution/outcome].

Example: "Small business owners aged 30-50 who struggle with social media consistency. They're looking for an easy way to maintain their brand presence without hiring an agency."

Return ONLY the target audience description, no preamble or explanation."""
    
    try:
        model = get_generative_model(
            system_instruction="You are an expert brand strategist. Provide specific, actionable target audience descriptions based on the user's actual business context."
        )
        if not model:
            return {'success': False, 'error': 'AI not configured'}
        
        response = model.generate_content(prompt)
        processed_audience = response.text.strip() if hasattr(response, 'text') else str(response).strip()
        
        # Remove any quotes or extra formatting
        processed_audience = processed_audience.strip('"').strip("'")
        
        return {
            'success': True,
            'audience': processed_audience,
            'original_input': user_input
        }
    except Exception as e:
        logger.error(f"Error processing target audience: {e}")
        return {'success': False, 'error': str(e)}


FIELD_EXPERT_PROMPTS = {
    'target_audience': """You are an expert brand strategist helping define a target audience.

CURRENT PROFILE:
- Business Name: {business_name}
- Industry: {industry}
- Brand Voice: {brand_voice}
- Key Offer: {key_offer}
- Current Target Audience: {current_value}
- Writing Samples: 
{writing_samples}

Generate exactly 3 highly specific, actionable target audience descriptions.
Each should be 2-3 sentences covering:
- Demographics (age, role, business size, or lifestyle)
- Their main pain point or challenge
- What they're actively looking for

Make them specific enough that the user could visualize this exact person.
Base your suggestions on their actual business and writing style.

Format as:
1. [First suggestion]

2. [Second suggestion]

3. [Third suggestion]
""",

    'brand_voice': """You are an expert brand voice consultant.

CURRENT PROFILE:
- Business Name: {business_name}
- Industry: {industry}
- Target Audience: {target_audience}
- Key Offer: {key_offer}
- Current Brand Voice: {current_value}
- Writing Samples:
{writing_samples}

Analyze their writing samples and business to suggest 3 brand voice options.
Each should be 3-5 descriptive words that work together, plus a brief explanation.

Format as:
1. "[Voice words]" - [Why this fits their brand]

2. "[Voice words]" - [Why this fits their brand]

3. "[Voice words]" - [Why this fits their brand]
""",

    'key_offer': """You are a value proposition expert and copywriter.

CURRENT PROFILE:
- Business Name: {business_name}
- Industry: {industry}
- Target Audience: {target_audience}
- Brand Voice: {brand_voice}
- Current Key Offer: {current_value}
- Writing Samples:
{writing_samples}

Generate 3 compelling key offer / value proposition options.
Each should clearly state:
- What they do
- Who it's for
- The main benefit or transformation

Keep each to 1-2 punchy sentences. Make them memorable and specific to their business.

Format as:
1. [First value proposition]

2. [Second value proposition]

3. [Third value proposition]
""",

    'writing_samples': """You are a social media content expert.

CURRENT PROFILE:
- Business Name: {business_name}
- Industry: {industry}
- Target Audience: {target_audience}
- Brand Voice: {brand_voice}
- Key Offer: {key_offer}

Generate 3 example social media posts they could use as writing samples.
These should match their brand voice and speak directly to their target audience.
Include appropriate emojis if their voice is casual; skip if professional.
Make each post 2-4 sentences, ready to post.

Format as:
1. [First sample post]

2. [Second sample post]

3. [Third sample post]
""",

    'voice_rules': """You are a brand guidelines expert.

CURRENT PROFILE:
- Business Name: {business_name}
- Industry: {industry}
- Target Audience: {target_audience}
- Brand Voice: {brand_voice}
- Key Offer: {key_offer}
- Writing Samples:
{writing_samples}

Suggest 3 sets of voice rules/guidelines that would help maintain consistency.
Each set should have 3-4 specific rules based on their brand voice and samples.

Format as:
1. [Rule set name]
   - [Rule 1]
   - [Rule 2]
   - [Rule 3]

2. [Rule set name]
   - [Rule 1]
   - [Rule 2]
   - [Rule 3]

3. [Rule set name]
   - [Rule 1]
   - [Rule 2]
   - [Rule 3]
"""
}


def build_context(profile: dict, field: str) -> dict:
    """Build context dictionary from profile for prompt formatting."""
    
    # Get writing samples as formatted string
    samples = profile.get('writing_samples', [])
    if isinstance(samples, list):
        samples_text = '\n'.join([f'- "{s}"' for s in samples[:3]]) if samples else 'None provided yet'
    else:
        samples_text = str(samples) if samples else 'None provided yet'
    
    # Map field to current value key - handles both 'tone' and 'brand_voice' for compatibility
    field_to_key = {
        'target_audience': 'target_audience',
        'brand_voice': 'brand_voice',
        'key_offer': 'key_offer',
        'writing_samples': 'writing_samples',
        'voice_rules': 'voice_rules',
    }
    
    current_key = field_to_key.get(field, field)
    current_value = profile.get(current_key, '')
    if isinstance(current_value, list):
        current_value = ', '.join(current_value) if current_value else 'Not set'
    current_value = current_value or 'Not set'
    
    # Use brand_voice field consistently (profile dict should have this normalized)
    brand_voice = profile.get('brand_voice') or profile.get('tone') or 'Not set yet'
    
    return {
        'business_name': profile.get('company') or profile.get('business_name') or 'Your business',
        'industry': profile.get('industry') or 'your industry',
        'brand_voice': brand_voice,
        'target_audience': profile.get('target_audience') or 'Not set yet',
        'key_offer': profile.get('key_offer') or 'Not set yet',
        'current_value': current_value,
        'writing_samples': samples_text,
    }


def parse_suggestions(response_text: str) -> list:
    """Parse numbered suggestions from AI response."""
    suggestions = []
    lines = response_text.strip().split('\n')
    current = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a new numbered item
        if line and len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            # Save previous suggestion if exists
            if current:
                suggestions.append('\n'.join(current).strip())
            current = [line[2:].strip()]  # Start new suggestion without number
        elif current:
            current.append(line)
    
    # Don't forget last suggestion
    if current:
        suggestions.append('\n'.join(current).strip())
    
    return suggestions[:3]  # Return max 3


def generate_profile_suggestions(field: str, profile: dict) -> dict:
    """
    Generate AI-powered suggestions for a profile field using Gemini.
    
    Args:
        field: The profile field to generate suggestions for
        profile: The user's current profile data
        
    Returns:
        dict with 'suggestions' list and 'context' info
    """
    
    prompt_template = FIELD_EXPERT_PROMPTS.get(field)
    if not prompt_template:
        return {
            'success': False,
            'error': f'Unknown field: {field}',
            'suggestions': []
        }
    
    context = build_context(profile, field)
    prompt = prompt_template.format(**context)
    
    try:
        # Use the existing Gemini infrastructure
        model = get_generative_model(
            system_instruction="You are an expert brand strategist and copywriter. Provide specific, actionable suggestions based on the user's actual business context. Never give generic advice."
        )
        
        if not model:
            logger.error("AI service not available for profile suggestions")
            return {
                'success': False,
                'error': 'AI service not configured',
                'suggestions': []
            }
        
        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        suggestions = parse_suggestions(response_text)
        
        return {
            'success': True,
            'field': field,
            'suggestions': suggestions,
            'context': {
                'business_name': context['business_name'],
                'industry': context['industry'],
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating profile suggestions: {e}")
        return {
            'success': False,
            'error': str(e),
            'suggestions': []
        }


def suggest_brand_voices(profile: dict) -> dict:
    """Convenience function to generate brand voice suggestions."""
    return generate_profile_suggestions('brand_voice', profile)


def suggest_target_audiences(profile: dict) -> dict:
    """Convenience function to generate target audience suggestions."""
    return generate_profile_suggestions('target_audience', profile)


def suggest_key_offers(profile: dict) -> dict:
    """Convenience function to generate key offer suggestions."""
    return generate_profile_suggestions('key_offer', profile)
