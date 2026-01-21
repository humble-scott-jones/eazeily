"""ConversationRouter service for parsing and routing user prompts.

This service acts as the "brain" of the conversational UX, determining user intent
and managing field collection for content generation tasks.
"""

import logging
import re
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)

# Supported social media platforms with their recognized keywords
SUPPORTED_PLATFORMS = {
    'instagram': ['instagram', 'ig', 'insta'],
    'facebook': ['facebook', 'fb'],
    'linkedin': ['linkedin'],
    'twitter': ['twitter', 'x', 'tweet'],
    'tiktok': ['tiktok', 'tik tok'],
}

# Mood/Tone keywords for content generation
MOOD_KEYWORDS = {
    'excited': ['excited', 'exciting', 'thrilled', 'enthusiastic'],
    'professional': ['professional', 'formal', 'business', 'polished'],
    'casual': ['casual', 'relaxed', 'friendly', 'laid back', 'laid-back'],
    'urgent': ['urgent', 'hurry', 'limited time', 'act now', 'don\'t miss'],
    'celebratory': ['celebratory', 'celebrating', 'congrats', 'achievement', 'success'],
    'informative': ['informative', 'educational', 'learn', 'tip', 'advice', 'how to'],
    'funny': ['funny', 'humorous', 'witty', 'playful', 'fun'],
    'inspiring': ['inspiring', 'motivational', 'uplifting', 'encouraging'],
}

# Field name aliases for profile updates
FIELD_ALIASES = {
    'business_name': ['business', 'company', 'name', 'business name', 'company name'],
    'industry': ['industry', 'sector', 'field', 'niche'],
    'target_audience': ['audience', 'target', 'customers', 'target audience', 'ideal customer', 'customer'],
    'brand_voice': ['voice', 'tone', 'style', 'brand voice', 'writing style'],
    'key_offer': ['offer', 'value prop', 'unique offer', 'key offer', 'usp', 'value proposition'],
    'writing_samples': ['samples', 'examples', 'writing samples', 'copy examples'],
}

# NEW field commands that use AI-assisted completion flow
# All 8 profile field commands support two modes:
# 1. Bare command (e.g., "/keywords") triggers field_assistance with AI suggestions
# 2. Command with value (e.g., "/keywords Fresh, Local") triggers update_field for direct update
FIELD_COMMANDS = {
    '/name': 'business_name',
    '/industry': 'industry',
    '/voice': 'brand_voice',
    '/audience': 'target_audience',
    '/offer': 'key_offer',
    '/samples': 'writing_samples',
    '/keywords': 'brand_keywords',
    '/goals': 'goals',
}

# Command guidance messages for bare commands
COMMAND_GUIDANCE = {
    '/post': "📝 **What would you like to post about?**\n\nExample: `/post our weekend sale on handmade candles`",
    '/voice': "🎤 **How would you like your brand to sound?**\n\nExample: `/voice warm and professional, like a trusted friend`",
    '/audience': "🎯 **Who is your target audience?**\n\nExample: `/audience busy working parents who value convenience`",
    '/offer': "💎 **What's your main value proposition?**\n\nExample: `/offer free 30-day trial with no credit card`",
    '/email': "✉️ **What's this email about?**\n\nExample: `/email follow-up after our meeting yesterday`",
    '/review': "⭐ **Paste the review you want to respond to:**\n\nExample: `/review \"Great product but shipping was slow\"`",
    '/import': "🔗 **What URL would you like to import?**\n\nExample: `/import https://yourbusiness.com`",
    '/ad': "📢 **What product or service is this ad for?**\n\nExample: `/ad our new mobile app launch`",
    '/blog': "📰 **What topic should this blog post cover?**\n\nExample: `/blog 5 tips for better productivity`",
    '/reel': "🎬 **What's this video about?**\n\nExample: `/reel behind the scenes at our bakery`",
    '/caption': "📸 **Describe the image you're captioning:**\n\nExample: `/caption team photo at our annual retreat`",
    '/script': "🎥 **What's this video script about?**\n\nExample: `/script product demo for new features`",
    '/samples': "✍️ **Paste a writing sample from your brand:**\n\nExample: `/samples Check out our new summer collection! 🌞`",
    '/update': "✏️ **What field do you want to update?**\n\nExample: `/update voice warm and friendly`",
    '/rules': "📋 **What voice rules should I follow?**\n\nExample: `/rules always use emojis and keep it casual`",
}


def get_command_guidance(command: str) -> Optional[str]:
    """Return guidance message for commands sent without input.
    
    Args:
        command: The bare slash command (e.g., '/post', '/voice')
        
    Returns:
        Helpful guidance message or None if no guidance needed
    """
    if not command:
        return None
    return COMMAND_GUIDANCE.get(command.lower(), None)


class ConversationRouter:
    """Routes user prompts to the correct generation flow."""
    
    # Map slash commands to task types (from task_registry.py)
    # Note: This is intentionally defined here rather than derived from task_registry
    # because it defines the conversational UX interface, not just task capabilities.
    # Not all task types need slash commands, and commands can have aliases (/reel -> script).
    COMMAND_MAP = {
        '/post': 'post',
        '/caption': 'caption',
        '/script': 'script',
        '/email': 'email',
        '/review': 'review',
        '/ad': 'ad',
        '/blog': 'blog',
        '/reel': 'script',  # alias
        '/custom': 'custom',  # flexible custom content
        '/profile': 'profile',           # View/edit profile
        '/update': 'profile_update',     # Update specific field
        '/import': 'import_profile',     # Import from URL
        '/quick': 'quick_templates',     # Show industry templates
        '/session': 'batch_session',     # Start batch generation mode
        # All 8 field commands for AI-assisted completion
        '/name': 'field_assistance',     # Business name field
        '/industry': 'field_assistance', # Industry field
        '/voice': 'field_assistance',    # Brand voice field
        '/audience': 'field_assistance', # Target audience field
        '/offer': 'field_assistance',    # Key offer field
        '/samples': 'field_assistance',  # Writing samples field
        '/keywords': 'field_assistance', # Brand keywords field
        '/goals': 'field_assistance',    # Goals field
    }
    
    # Required fields per task type (from task_registry.py patterns)
    # Note: This defines the conversational field collection flow, which is separate from
    # task_registry's generation templates. These fields drive the interactive dialogue,
    # including what questions to ask and in what order. Changes here affect UX flow.
    TASK_FIELDS = {
        'post': {
            'required': ['topic', 'platform'],
            'optional': ['mood', 'cta'],
            'prompts': {
                'topic': "What topic should this post be about? (product, tip, announcement...)",
                'platform': "Which platform? (Instagram, Facebook, LinkedIn, TikTok, Twitter)",
            }
        },
        'caption': {
            'required': ['topic'],
            'optional': ['platform', 'mood'],
            'prompts': {
                'topic': "Describe the image or what the caption should be about:",
            }
        },
        'script': {
            'required': ['topic', 'video_length'],
            'optional': ['reel_style', 'platform'],
            'prompts': {
                'topic': "What's the video about?",
                'video_length': "How long? (15s, 30s, 60s, or 90s)",
            }
        },
        'email': {
            'required': ['topic'],
            'optional': ['email_subtype', 'recipient'],
            'prompts': {
                'topic': "What's the email about?",
            }
        },
        'review': {
            'required': ['topic'],  # topic = the review text to respond to
            'optional': ['star_rating', 'desired_tone'],
            'prompts': {
                'topic': "Paste the review you want to respond to:",
            }
        },
        'ad': {
            'required': ['topic', 'platform'],
            'optional': ['ad_objective', 'target_audience'],
            'prompts': {
                'topic': "What product or offer is the ad for?",
                'platform': "Which ad platform? (Facebook, Instagram, LinkedIn, TikTok)",
            }
        },
        'blog': {
            'required': ['topic'],
            'optional': ['post_type', 'desired_length', 'seo_keywords'],
            'prompts': {
                'topic': "What's the blog post about?",
            }
        },
        'custom': {
            'required': ['content_type', 'topic', 'purpose'],
            'optional': ['target_audience', 'tone', 'format', 'length'],
            'prompts': {
                'content_type': "What type of content do you want to create? (e.g., case study, whitepaper, landing page, press release, etc.)",
                'topic': "What's the main topic or subject?",
                'purpose': "What's the purpose of this content? (e.g., educate, convert, inform, entertain)",
            }
        },
        'profile': {
            'required': [],
            'optional': ['field_to_update'],
            'prompts': {}
        },
        'profile_update': {
            'required': ['field_name', 'new_value'],
            'optional': [],
            'prompts': {
                'field_name': "Which field would you like to update? (business_name, industry, target_audience, brand_voice, key_offer, writing_samples)",
                'new_value': "What's the new value?",
            }
        },
        'update_voice': {
            'required': ['new_value'],
            'optional': [],
            'prompts': {
                'new_value': "How would you describe your new brand voice? (e.g., 'professional and authoritative', 'warm and friendly')",
            }
        },
        'update_audience': {
            'required': ['new_value'],
            'optional': [],
            'prompts': {
                'new_value': "Who is your new target audience? (e.g., 'young professionals seeking work-life balance')",
            }
        },
        'update_samples': {
            'required': ['sample_text'],
            'optional': [],
            'prompts': {
                'sample_text': "Paste a writing sample (social post, email, or website copy):",
            }
        },
        'import_profile': {
            'required': ['url'],
            'optional': [],
            'prompts': {
                'url': "Paste your website or social media URL:",
            }
        },
        'update_from_url': {
            'required': ['url'],
            'optional': [],
            'prompts': {
                'url': "Paste your website URL to update from:",
            }
        },
        'field_assistance': {
            'required': ['field'],
            'optional': [],
            'prompts': {
                'field': "Which field would you like assistance with?"
            }
        },
        'update_field': {
            'required': ['field', 'value'],
            'optional': [],
            'prompts': {
                'field': "Which field would you like to update?",
                'value': "What value would you like to set?"
            }
        },
        'quick_templates': {
            'required': ['template_selection'],
            'optional': [],
            'prompts': {
                'template_selection': "Choose a template number (1-5) or describe what you need:"
            }
        },
        'batch_session': {
            'required': ['session_action'],
            'optional': ['platform'],
            'prompts': {
                'session_action': "Type a topic to generate, 'use [platform]' to switch platforms, or 'done' to end:"
            }
        },
    }
    
    # Task type keywords for fallback classification (ordered by specificity)
    TASK_PATTERNS = [
        (['reel'], 'script'),  # Map reel to script (as per COMMAND_MAP)
        (['caption'], 'caption'),
        (['email', 'newsletter'], 'email'),
        (['review', 'respond to review', 'review response'], 'review'),
        (['ad', 'advertisement'], 'ad'),
        (['blog', 'article'], 'blog'),
        (['script', 'video'], 'script'),
        (['custom', 'flexible', 'anything'], 'custom'),
        (['post'], 'post'),  # Most generic, check last
    ]
    
    def __init__(self):
        """Initialize the conversation router."""
        self.gemini_available = self._check_gemini()
    
    def _check_gemini(self) -> bool:
        """Check if Gemini API is available."""
        try:
            from services.generation.gemini_adapter import _get_client
            client = _get_client()
            return client is not None
        except Exception as e:
            logger.warning(f"Gemini not available: {e}")
            return False
    
    def parse_intent(self, user_input: str, profile: Any) -> Dict[str, Any]:
        """
        Parse user's input into a structured intent.
        
        Args:
            user_input: The user's message or command
            profile: VoiceProfile instance with business context
        
        Returns:
            dict with keys:
                - intent: 'generate' | 'onboarding' | 'help' | 'unknown'
                - task_type: 'post' | 'caption' | etc.
                - extracted_params: {'topic': '...', 'platform': '...'}
                - follow_up_needed: bool
                - follow_up_question: str | None
                - missing_fields: ['platform', ...]
        """
        if not user_input or not user_input.strip():
            return {
                'intent': 'unknown',
                'task_type': None,
                'extracted_params': {},
                'follow_up_needed': True,
                'follow_up_question': "How can I help you create content today?",
                'missing_fields': []
            }
        
        user_input = user_input.strip()
        
        # Try parsing as slash command first
        slash_result = self._parse_slash_command(user_input)
        if slash_result:
            logger.info(f"Parsed slash command: {slash_result}")
            return self._build_response(slash_result, profile)
        
        # Try classifying with Gemini if available
        if self.gemini_available:
            gemini_result = self._classify_with_gemini(user_input, profile)
            if gemini_result:
                logger.info(f"Classified with Gemini: {gemini_result}")
                return self._build_response(gemini_result, profile)
        
        # Fallback: Try simple keyword matching
        keyword_result = self._classify_with_keywords(user_input)
        if keyword_result:
            logger.info(f"Classified with keywords: {keyword_result}")
            return self._build_response(keyword_result, profile)
        
        # Last resort: Ask user to clarify
        logger.warning(f"Could not classify user input: {user_input[:50]}")
        return {
            'intent': 'unknown',
            'task_type': None,
            'extracted_params': {},
            'follow_up_needed': True,
            'follow_up_question': (
                "I'm not sure what you'd like to create. "
                "Try using a command like /post, /caption, /script, /email, /review, /ad, or /blog"
            ),
            'missing_fields': []
        }
    
    def _classify_with_keywords(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Fallback keyword-based classification when Gemini is unavailable.
        
        Detects natural language patterns like:
        - "Write me a post about..."
        - "I need an email for..."
        - "Create a caption for..."
        - "Draft a script about..."
        
        Args:
            user_input: User's natural language message
        
        Returns:
            dict with task_type and extracted_params, or None if no match
        """
        message_lower = user_input.lower()
        
        # First check for profile update intents
        profile_intent = self.detect_profile_update_intent(user_input)
        if profile_intent:
            return profile_intent
        
        # Check for natural language patterns with task types
        natural_patterns = [
            (r'\b(?:write|create|make|draft|generate)\s+(?:me\s+)?(?:a|an)\s+post\b', 'post'),
            (r'\b(?:write|create|make|draft|generate)\s+(?:me\s+)?(?:a|an)\s+caption\b', 'caption'),
            (r'\b(?:write|create|make|draft|generate)\s+(?:me\s+)?(?:a|an)\s+script\b', 'script'),
            (r'\b(?:write|create|make|draft|generate)\s+(?:me\s+)?(?:a|an)\s+email\b', 'email'),
            (r'\b(?:write|create|make|draft|generate)\s+(?:me\s+)?(?:a|an)\s+ad\b', 'ad'),
            (r'\b(?:write|create|make|draft|generate)\s+(?:me\s+)?(?:a|an)\s+blog\b', 'blog'),
            (r'\bi need (?:a|an)\s+post\b', 'post'),
            (r'\bi need (?:a|an)\s+caption\b', 'caption'),
            (r'\bi need (?:a|an)\s+email\b', 'email'),
            (r'\bi need (?:a|an)\s+script\b', 'script'),
            (r'\bi need (?:a|an)\s+ad\b', 'ad'),
        ]
        
        task_type = None
        for pattern, ttype in natural_patterns:
            if re.search(pattern, message_lower):
                task_type = ttype
                break
        
        # If no natural pattern match, use existing keyword patterns
        if not task_type:
            for keywords, ttype in self.TASK_PATTERNS:
                if any(keyword in message_lower for keyword in keywords):
                    task_type = ttype
                    break
        
        if not task_type:
            return None
        
        # Extract parameters using existing method
        extracted_params = self._extract_params_from_text(user_input, task_type)
        
        return {
            'task_type': task_type,
            'extracted_params': extracted_params
        }
    
    def _parse_slash_command(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Parse /command syntax. Returns None if not a command.
        
        Examples:
            /post about our new product
            /caption beach sunset
            /script for new tutorial video
            /update https://example.com
            /keywords Fresh, Local (new field command with value)
            /name (new field command without value - triggers AI assistance)
        """
        if not user_input.startswith('/'):
            return None
        
        # Extract command and remainder
        parts = user_input.split(None, 1)
        command = parts[0].lower()
        remainder = parts[1] if len(parts) > 1 else ''
        
        # Check if this is a NEW field command (from FIELD_COMMANDS)
        # These take priority and use field_assistance flow
        if command in FIELD_COMMANDS:
            field = FIELD_COMMANDS[command]
            args = remainder.strip() if remainder else None
            
            if args:
                # Command with value: direct field update
                return {
                    'task_type': 'update_field',
                    'field': field,
                    'value': args
                }
            else:
                # Bare command: AI-assisted field completion
                return {
                    'task_type': 'field_assistance',
                    'field': field
                }
        
        # Check if command is valid in COMMAND_MAP (existing commands)
        if command not in self.COMMAND_MAP:
            return None
        
        # Special handling for /update with URL
        if command == '/update' and remainder.strip():
            # Check if remainder is a URL
            remainder_stripped = remainder.strip()
            if remainder_stripped.startswith('http://') or remainder_stripped.startswith('https://'):
                return {
                    'task_type': 'update_from_url',
                    'extracted_params': {'url': remainder_stripped}
                }
        
        # Check if this is a bare command that needs guidance
        # Derive list from COMMAND_GUIDANCE keys to maintain consistency
        needs_guidance = command in COMMAND_GUIDANCE and not remainder.strip()
        
        task_type = self.COMMAND_MAP[command]
        
        # Extract parameters from remainder
        extracted = self._extract_params_from_text(remainder, task_type) if remainder else {}
        
        result = {
            'task_type': task_type,
            'extracted_params': extracted
        }
        
        # Add guidance flag if needed
        if needs_guidance:
            result['needs_guidance'] = True
            result['command'] = command
        
        return result
    
    def _classify_with_gemini(self, user_input: str, profile: Any) -> Optional[Dict[str, Any]]:
        """
        Use Gemini to classify natural language intent.
        
        Args:
            user_input: User's natural language message
            profile: VoiceProfile with business context
        
        Returns:
            dict with task_type and extracted_params, or None on failure
        """
        try:
            from services.generation.gemini_adapter import call_gemini
        except ImportError:
            logger.error("Cannot import gemini_adapter")
            return None
        
        # Build context from profile
        business_name = getattr(profile, 'business_name', 'Unknown Business')
        industry = getattr(profile, 'industry', 'Unknown Industry')
        
        # Build platform list from supported platforms
        platform_list = '|'.join(sorted(SUPPORTED_PLATFORMS.keys()))
        
        # Build task type list from COMMAND_MAP to ensure consistency
        task_types = '|'.join(sorted(set(self.COMMAND_MAP.values()).union({'unknown'})))
        
        prompt = f"""Analyze this user request:

User: "{user_input}"

Business context: {business_name}, {industry}

Determine if this is:
1. Content creation (post, email, script, etc.)
2. Profile update (changing business info, voice, audience, etc.)
3. Profile view (asking about current settings)

If content creation, extract:
- task_type: post|caption|script|email|review|ad|blog|custom
- topic: the main subject/topic if mentioned
- platform: {platform_list}|null
- video_length: 15s|30s|60s|90s|null (only for script/video)
- other_params: any other relevant parameters

If profile update, extract:
- task_type: profile_update|update_voice|update_audience
- field_name: business_name|industry|target_audience|brand_voice|key_offer|writing_samples|null
- new_value: the new value they want to set

If profile view:
- task_type: profile

Return JSON:
{{
    "intent": "content|profile_update|profile_view|unknown",
    "task_type": "...",
    "topic": "..." or null,
    "platform": "..." or null,
    "video_length": "..." or null,
    "field_name": "..." or null,
    "new_value": "..." or null,
    "other_params": {{}}
}}

Rules:
- task_type must be one of: {', '.join(sorted(set(self.COMMAND_MAP.values()).union({'unknown'})))}
- For profile updates, set field_name and new_value
- Only return valid JSON, no explanation."""
        
        result = call_gemini(prompt, temperature=0.3)
        
        if not result:
            logger.warning("Gemini returned no result")
            return None
        
        # Extract intent
        intent = result.get('intent', 'unknown')
        task_type = result.get('task_type', 'unknown')
        
        if task_type == 'unknown':
            return None
        
        # Build extracted params based on intent
        extracted_params = {}
        
        if intent in ['profile_update', 'profile_view']:
            # Profile-related intent
            if result.get('field_name'):
                extracted_params['field_name'] = result['field_name']
            if result.get('new_value'):
                extracted_params['new_value'] = result['new_value']
        else:
            # Content creation intent
            if result.get('topic'):
                extracted_params['topic'] = result['topic']
            if result.get('platform'):
                extracted_params['platform'] = result['platform'].lower()
            if result.get('video_length'):
                extracted_params['video_length'] = result['video_length']
            
            # Add other params
            if result.get('other_params') and isinstance(result['other_params'], dict):
                extracted_params.update(result['other_params'])
        
        return {
            'task_type': task_type,
            'extracted_params': extracted_params
        }
    
    def _extract_params_from_text(self, text: str, task_type: str) -> Dict[str, Any]:
        """
        Extract known parameters from user's message.
        
        This does simple pattern matching for common parameters including:
        - Platform (instagram, facebook, linkedin, twitter, tiktok)
        - Mood/Tone (excited, professional, casual, urgent, etc.)
        - Video length (15s, 30s, 60s, 90s)
        - CTA (call-to-action from "with cta [text]" pattern)
        - Topic (remaining content after extracting other params)
        
        Args:
            text: User's message text
            task_type: The task type context
        
        Returns:
            dict of extracted parameters
        """
        params = {}
        text_lower = text.lower()
        
        # Extract platform using shared constant with word boundaries
        for platform, keywords in SUPPORTED_PLATFORMS.items():
            if any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in keywords):
                params['platform'] = platform
                break
        
        # Extract mood/tone using word boundaries
        # For multi-word phrases, we need to check them without word boundary on the phrase itself
        for mood, keywords in MOOD_KEYWORDS.items():
            for kw in keywords:
                # For multi-word keywords, use simple 'in' check (case-insensitive)
                # For single-word keywords, use word boundaries
                if ' ' in kw:
                    if kw in text_lower:
                        params['mood'] = mood
                        break
                else:
                    if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                        params['mood'] = mood
                        break
            if 'mood' in params:
                break
        
        # Extract CTA from "with cta [text]" pattern
        cta_pattern = r'with cta\s+["\']?([^"\']+)["\']?'
        cta_match = re.search(cta_pattern, text, re.IGNORECASE)
        if cta_match:
            params['cta'] = cta_match.group(1).strip()
            # Remove the CTA part from text for topic extraction
            text = re.sub(cta_pattern, '', text, flags=re.IGNORECASE)
        
        # Extract video length (for scripts)
        if task_type == 'script':
            # Use regex with word boundaries to avoid partial matches (e.g., '115s' matching '15s')
            length_regex_patterns = [
                (r'\b15\s*s(?:econds?)?\b', '15s'),
                (r'\b30\s*s(?:econds?)?\b', '30s'),
                (r'\b60\s*s(?:econds?)?\b', '60s'),
                (r'\b90\s*s(?:econds?)?\b', '90s'),
            ]
            for pattern, normalized in length_regex_patterns:
                if re.search(pattern, text_lower):
                    params['video_length'] = normalized
                    break
        
        # Extract topic (what remains after removing command words)
        # Remove platform names and command-related words
        topic_text = text
        for words in SUPPORTED_PLATFORMS.values():
            for word in words:
                topic_text = re.sub(r'\b' + re.escape(word) + r'\b', '', topic_text, flags=re.IGNORECASE)
        
        # Remove mood keywords from topic
        for keywords in MOOD_KEYWORDS.values():
            for word in keywords:
                topic_text = re.sub(r'\b' + re.escape(word) + r'\b', '', topic_text, flags=re.IGNORECASE)
        
        # Remove task-type related words
        task_words = ['post', 'caption', 'script', 'email', 'review', 'ad', 'blog', 'reel', 
                      'create', 'write', 'draft', 'generate', 'make', 'need', 'want',
                      'a ', 'an ', 'the ', 'i ']
        for word in task_words:
            topic_text = re.sub(r'\b' + re.escape(word.strip()) + r'\b', '', topic_text, flags=re.IGNORECASE)
        
        # Remove common filler words
        filler_words = ['about', 'for', 'on', 'regarding', 'concerning']
        for word in filler_words:
            topic_text = re.sub(r'\b' + re.escape(word) + r'\b', '', topic_text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        topic_text = ' '.join(topic_text.split()).strip()
        
        # Only add topic if there's meaningful content left (more than just whitespace or very short)
        if topic_text and len(topic_text) > 2:
            params['topic'] = topic_text
        
        return params
    
    def _build_response(self, classification: Dict[str, Any], profile: Any) -> Dict[str, Any]:
        """Build the full response structure with missing fields analysis."""
        task_type = classification['task_type']
        extracted_params = classification.get('extracted_params', {})
        
        # Get missing fields
        missing_fields = self.get_missing_fields(task_type, extracted_params)
        
        # Determine intent
        intent = 'generate'  # Default to generate intent for valid task types
        
        # Check if we need follow-up
        follow_up_needed = len(missing_fields) > 0
        follow_up_question = None
        
        if follow_up_needed:
            follow_up_question = self.get_next_prompt(task_type, missing_fields)
        
        result = {
            'intent': intent,
            'task_type': task_type,
            'extracted_params': extracted_params,
            'follow_up_needed': follow_up_needed,
            'follow_up_question': follow_up_question,
            'missing_fields': missing_fields
        }
        
        # Preserve guidance flags if present
        if classification.get('needs_guidance'):
            result['needs_guidance'] = True
        if 'command' in classification:
            result['command'] = classification['command']
        
        # Preserve field and value for new field commands
        if 'field' in classification:
            result['field'] = classification['field']
        if 'value' in classification:
            result['value'] = classification['value']
        
        return result
    
    def get_missing_fields(self, task_type: str, collected: Dict[str, Any]) -> List[str]:
        """
        Return list of required fields not yet collected.
        
        Args:
            task_type: The task type (post, caption, etc.)
            collected: Dictionary of collected parameters
        
        Returns:
            List of missing required field names
        """
        if task_type not in self.TASK_FIELDS:
            logger.warning(f"Unknown task type: {task_type}")
            return []
        
        config = self.TASK_FIELDS[task_type]
        required_fields = config.get('required', [])
        
        missing = []
        for field in required_fields:
            if field not in collected or not collected[field]:
                missing.append(field)
        
        return missing
    
    def get_next_prompt(self, task_type: str, missing_fields: List[str]) -> str:
        """
        Get the prompt for the next missing field.
        
        Args:
            task_type: The task type (post, caption, etc.)
            missing_fields: List of missing field names
        
        Returns:
            Prompt string for the next field to collect
        """
        if not missing_fields:
            return ""
        
        if task_type not in self.TASK_FIELDS:
            return "Please provide more details."
        
        config = self.TASK_FIELDS[task_type]
        prompts = config.get('prompts', {})
        
        # Get prompt for first missing field
        next_field = missing_fields[0]
        return prompts.get(next_field, f"Please provide {next_field}:")
    
    def is_ready_to_generate(self, task_type: str, collected: Dict[str, Any]) -> bool:
        """
        Check if we have all required fields to generate.
        
        Args:
            task_type: The task type (post, caption, etc.)
            collected: Dictionary of collected parameters
        
        Returns:
            True if all required fields are present, False otherwise
        """
        missing = self.get_missing_fields(task_type, collected)
        return len(missing) == 0
    
    def normalize_field_name(self, input_text: str) -> Optional[str]:
        """
        Convert user input to actual field name.
        
        Args:
            input_text: User's field reference (e.g., 'voice', 'target audience')
        
        Returns:
            Normalized field name or None if not recognized
        """
        input_lower = input_text.lower().strip()
        for field_name, aliases in FIELD_ALIASES.items():
            if input_lower in aliases or field_name in input_lower:
                return field_name
        return None
    
    def detect_profile_update_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Detect if user input is a profile update request using keywords.
        
        Args:
            user_input: User's message
        
        Returns:
            dict with task_type, field_name, new_value or None if not a profile update
        """
        message_lower = user_input.lower()
        
        # Keywords that indicate profile update intent (use word boundaries)
        update_keywords = ['change', 'update', 'modify', 'edit']
        view_keywords = ['show', 'view', 'see', 'what is my', 'current']
        
        # Check for specific phrases that indicate view vs update
        # Use word boundaries for single words, exact match for phrases
        has_view_keyword = any(
            (re.search(r'\b' + re.escape(kw) + r'\b', message_lower) if ' ' not in kw 
             else kw in message_lower)
            for kw in view_keywords
        )
        has_profile_mention = 'profile' in message_lower or 'settings' in message_lower
        is_view = has_view_keyword and has_profile_mention
        
        is_update = any(
            re.search(r'\b' + re.escape(kw) + r'\b', message_lower)
            for kw in update_keywords
        )
        
        if is_view and not is_update:
            return {
                'task_type': 'profile',
                'extracted_params': {}
            }
        
        if is_update:
            # Try to extract field name and new value
            # Pattern: "change my <field> to <value>"
            # Pattern: "update <field> to <value>"
            # Pattern: "set <field> to <value>"
            
            field_name = None
            new_value = None
            
            # Check each field alias
            for fname, aliases in FIELD_ALIASES.items():
                for alias in aliases:
                    if alias in message_lower:
                        field_name = fname
                        # Try to extract value after 'to'
                        pattern = rf'{re.escape(alias)}\s+(?:is\s+now\s+|to\s+)?(.+?)(?:\.|$)'
                        match = re.search(pattern, message_lower, re.IGNORECASE)
                        if match:
                            new_value = match.group(1).strip()
                        break
                if field_name:
                    break
            
            # Special handling for quick update shortcuts
            if 'brand voice' in message_lower or 'voice' in message_lower:
                field_name = 'brand_voice'
            elif 'target audience' in message_lower or 'audience' in message_lower:
                field_name = 'target_audience'
            
            if field_name:
                extracted_params = {'field_name': field_name}
                if new_value:
                    extracted_params['new_value'] = new_value
                
                # Determine task type based on field
                if field_name == 'brand_voice':
                    task_type = 'update_voice'
                elif field_name == 'target_audience':
                    task_type = 'update_audience'
                else:
                    task_type = 'profile_update'
                
                return {
                    'task_type': task_type,
                    'extracted_params': extracted_params
                }
            else:
                # Generic update request without specific field
                return {
                    'task_type': 'profile_update',
                    'extracted_params': {}
                }
        
        return None
