"""
AI-powered profile field suggestions using full profile context.
"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
    
    # Map field to current value key
    field_to_key = {
        'target_audience': 'target_audience',
        'brand_voice': 'tone',
        'key_offer': 'key_offer',
        'writing_samples': 'writing_samples',
        'voice_rules': 'voice_rules',
    }
    
    current_key = field_to_key.get(field, field)
    current_value = profile.get(current_key, '')
    if isinstance(current_value, list):
        current_value = ', '.join(current_value) if current_value else 'Not set'
    current_value = current_value or 'Not set'
    
    return {
        'business_name': profile.get('company') or profile.get('business_name') or 'Your business',
        'industry': profile.get('industry') or 'your industry',
        'brand_voice': profile.get('tone') or profile.get('brand_voice') or 'Not set yet',
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


async def generate_profile_suggestions(field: str, profile: dict) -> dict:
    """
    Generate AI-powered suggestions for a profile field.
    
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cost-effective
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert brand strategist and copywriter. Provide specific, actionable suggestions based on the user's actual business context. Never give generic advice."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
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
        print(f"Error generating profile suggestions: {e}")
        return {
            'success': False,
            'error': str(e),
            'suggestions': []
        }


# Synchronous wrapper for non-async contexts
def generate_profile_suggestions_sync(field: str, profile: dict) -> dict:
    """Synchronous version of generate_profile_suggestions."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # For sync context, just call directly without await
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert brand strategist and copywriter. Provide specific, actionable suggestions based on the user's actual business context. Never give generic advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
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
        print(f"Error generating profile suggestions: {e}")
        return {
            'success': False,
            'error': str(e),
            'suggestions': []
        }
