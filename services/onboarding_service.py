"""OnboardingService - Handles conversational onboarding flow.

This service encapsulates the logic for collecting brand profile information
through conversational interactions, including URL scraping, description parsing,
and field collection via multi-turn dialogue.
"""

import logging
import re
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse

from models import VoiceProfile, db

logger = logging.getLogger(__name__)


class OnboardingService:
    """Service for managing conversational onboarding flow."""
    
    # Required fields for profile completion, in priority order
    REQUIRED_FIELDS = [
        'business_name',
        'industry',
        'target_audience',
        'brand_voice',
        'key_offer',
        'writing_samples'
    ]
    
    # Conversational prompts for each field
    FIELD_PROMPTS = {
        'business_name': "What's your business name?",
        'industry': "What industry are you in? (e.g., 'Real Estate', 'Fitness', 'Restaurant')",
        'target_audience': "Who is your ideal customer? (e.g., 'busy parents looking for healthy meal options')",
        'brand_voice': "How would you describe your brand's voice? (e.g., 'warm and friendly', 'professional and trustworthy', 'fun and playful')",
        'key_offer': "What makes your business unique? What's your main offer or value proposition?",
        'writing_samples': "Can you share a sample of your brand's writing? (e.g., a recent social post, website copy, or email)"
    }
    
    def __init__(self):
        """Initialize the onboarding service."""
        pass
    
    def process_url(self, url: str, profile: VoiceProfile) -> Dict:
        """Scrape URL and extract brand info.
        
        Args:
            url: The URL to scrape
            profile: VoiceProfile instance to update
            
        Returns:
            dict with keys:
                - success: bool
                - message: str (user-facing message)
                - extracted_fields: dict of field_name -> value
                - error: str (if failed)
        """
        try:
            from services.scraper_service import scrape_url, extract_business_info
            
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            if not parsed.hostname:
                return {
                    'success': False,
                    'error': 'Invalid URL format',
                    'message': "Hmm, that doesn't look like a valid URL. Can you double-check it?"
                }
            
            # Scrape the URL
            logger.info(f"Scraping URL for onboarding: {url}")
            scraped_text = scrape_url(url, max_length=6000)
            
            if not scraped_text:
                return {
                    'success': False,
                    'error': 'Failed to scrape URL',
                    'message': "I couldn't access that website. It might be behind a login or blocking automated access. Could you describe your brand instead?"
                }
            
            # Extract business info using AI
            business_info = extract_business_info(scraped_text, url)
            
            # Build extracted fields
            extracted_fields = {}
            
            if business_info.get('business_name'):
                extracted_fields['business_name'] = business_info['business_name']
            
            if business_info.get('industry'):
                extracted_fields['industry'] = business_info['industry']
            
            if business_info.get('key_customers'):
                extracted_fields['target_audience'] = business_info['key_customers']
            
            if business_info.get('key_offer'):
                extracted_fields['key_offer'] = business_info['key_offer']
            
            if business_info.get('voice_tone_and_style'):
                extracted_fields['brand_voice'] = business_info['voice_tone_and_style']
            
            # Use sample posts as writing samples
            if business_info.get('sample_posts'):
                extracted_fields['writing_samples'] = business_info['sample_posts']
            
            # Update profile with extracted fields
            for field, value in extracted_fields.items():
                self.update_profile_field(profile, field, value)
            
            # Build success message
            biz_name = extracted_fields.get('business_name', 'your business')
            industry = extracted_fields.get('industry', '')
            
            message_parts = [f"I found **{biz_name}**! 🎉"]
            
            if industry:
                message_parts.append(f"I see you're in the **{industry}** industry.")
            
            if extracted_fields.get('key_offer'):
                message_parts.append(f"\nYour key offer: _{extracted_fields['key_offer']}_")
            
            message_parts.append("\nHere's what I gathered:")
            for field, value in extracted_fields.items():
                if field == 'writing_samples' and isinstance(value, list):
                    message_parts.append(f"- Writing samples: {len(value)} samples extracted")
                elif field not in ['business_name', 'industry', 'key_offer']:
                    # Truncate long values for display
                    display_value = value[:100] + "..." if len(str(value)) > 100 else value
                    field_label = field.replace('_', ' ').title()
                    message_parts.append(f"- {field_label}: {display_value}")
            
            return {
                'success': True,
                'message': '\n'.join(message_parts),
                'extracted_fields': extracted_fields
            }
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': "I encountered an error reading that website. Could you describe your brand instead?"
            }
    
    def process_description(self, text: str, profile: VoiceProfile, context: Optional[str] = None) -> Dict:
        """Use Gemini to extract brand fields from description.
        
        Args:
            text: User's description text
            profile: VoiceProfile instance to update
            context: Optional context about what field we're collecting
            
        Returns:
            dict with keys:
                - success: bool
                - message: str (user-facing message)
                - extracted_fields: dict of field_name -> value
                - field_name: str (if a specific field was collected)
        """
        try:
            from services.ai_service import get_generative_model
            
            model = get_generative_model()
            if not model:
                # Fallback: try to infer from context
                if context:
                    return {
                        'success': True,
                        'message': f"Got it! I've recorded your {context.replace('_', ' ')}.",
                        'extracted_fields': {context: text},
                        'field_name': context
                    }
                return {
                    'success': False,
                    'error': 'AI service not available',
                    'message': "I need a bit more specific information. Let me ask you directly..."
                }
            
            # If we have context (collecting a specific field), just validate and store
            if context and context in self.REQUIRED_FIELDS:
                return {
                    'success': True,
                    'message': f"Perfect! I've saved your {context.replace('_', ' ')}.",
                    'extracted_fields': {context: text},
                    'field_name': context
                }
            
            # Otherwise, try to extract multiple fields from the description
            prompt = f"""Analyze this brand description and extract relevant profile information.
Return ONLY a JSON object with these keys (set to null if not found):
- business_name: The business name (string or null)
- industry: The industry category (string or null)
- target_audience: Description of ideal customers (string or null)
- brand_voice: Brand voice/tone description (string or null)
- key_offer: Main value proposition or unique offer (string or null)

User's description: "{text}"

Return only valid JSON, no markdown formatting."""
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            import json
            extracted_data = json.loads(response_text)
            
            # Filter out null values
            extracted_fields = {
                k: v for k, v in extracted_data.items() 
                if v is not None and v != "" and k in self.REQUIRED_FIELDS
            }
            
            if not extracted_fields:
                return {
                    'success': False,
                    'message': "I couldn't extract specific information from that. Let me ask you some specific questions...",
                    'extracted_fields': {}
                }
            
            # Update profile
            for field, value in extracted_fields.items():
                self.update_profile_field(profile, field, value)
            
            # Build response message
            message_parts = ["Great! Here's what I gathered:"]
            for field, value in extracted_fields.items():
                field_label = field.replace('_', ' ').title()
                display_value = value[:100] + "..." if len(str(value)) > 100 else value
                message_parts.append(f"- {field_label}: {display_value}")
            
            return {
                'success': True,
                'message': '\n'.join(message_parts),
                'extracted_fields': extracted_fields
            }
            
        except Exception as e:
            logger.error(f"Error processing description: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': "Let me ask you some specific questions to build your profile..."
            }
    
    def get_missing_fields(self, profile: VoiceProfile) -> List[str]:
        """Return list of required profile fields still missing.
        
        Args:
            profile: VoiceProfile instance to check
            
        Returns:
            List of missing field names in priority order
        """
        if not profile:
            return self.REQUIRED_FIELDS.copy()
        
        missing = []
        
        for field in self.REQUIRED_FIELDS:
            if field == 'writing_samples':
                # Check if we have at least one sample
                samples = profile.get_writing_samples()
                if not samples or len(samples) == 0:
                    missing.append(field)
            else:
                # Check if field is populated
                value = getattr(profile, field, None)
                if not value or (isinstance(value, str) and not value.strip()):
                    missing.append(field)
        
        return missing
    
    def get_next_question(self, missing_fields: List[str]) -> str:
        """Get conversational prompt for next missing field.
        
        Args:
            missing_fields: List of missing field names
            
        Returns:
            Conversational prompt string
        """
        if not missing_fields:
            return ""
        
        next_field = missing_fields[0]
        return self.FIELD_PROMPTS.get(next_field, f"Tell me about your {next_field.replace('_', ' ')}")
    
    def update_profile_field(self, profile: VoiceProfile, field: str, value: any):
        """Update a single profile field.
        
        Args:
            profile: VoiceProfile instance to update
            field: Field name to update
            value: New value for the field
        """
        if not profile:
            logger.error("Cannot update field on null profile")
            return
        
        if field == 'writing_samples':
            # Handle writing samples specially
            if isinstance(value, list):
                profile.set_writing_samples(value)
            elif isinstance(value, str):
                # Split by double newlines or treat as single sample
                if '\n\n' in value:
                    samples = [s.strip() for s in value.split('\n\n') if s.strip()]
                else:
                    samples = [value.strip()]
                profile.set_writing_samples(samples)
        elif hasattr(profile, field):
            setattr(profile, field, value)
        else:
            logger.warning(f"Unknown profile field: {field}")
    
    def is_profile_complete(self, profile: VoiceProfile) -> Tuple[bool, List[str]]:
        """Check if profile has all required fields.
        
        Args:
            profile: VoiceProfile instance to check
            
        Returns:
            Tuple of (is_complete: bool, missing_fields: list)
        """
        missing = self.get_missing_fields(profile)
        return len(missing) == 0, missing
    
    def detect_url(self, text: str) -> Optional[str]:
        """Detect if text contains a URL.
        
        Args:
            text: Text to check for URLs
            
        Returns:
            Extracted URL or None
        """
        # Pattern to match URLs
        url_pattern = r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
        match = re.search(url_pattern, text)
        
        if match:
            url = match.group(0)
            # Clean up trailing punctuation
            url = url.rstrip('.,;:!?)')
            return url
        
        return None
