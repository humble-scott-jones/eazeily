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
                'topic': "What's this post about? (product, tip, announcement...)",
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
    }
    
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
        
        # Fallback: Ask user to clarify
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
    
    def _parse_slash_command(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Parse /command syntax. Returns None if not a command.
        
        Examples:
            /post about our new product
            /caption beach sunset
            /script for new tutorial video
        """
        if not user_input.startswith('/'):
            return None
        
        # Extract command and remainder
        parts = user_input.split(None, 1)
        command = parts[0].lower()
        remainder = parts[1] if len(parts) > 1 else ''
        
        # Check if command is valid
        if command not in self.COMMAND_MAP:
            return None
        
        task_type = self.COMMAND_MAP[command]
        
        # Extract parameters from remainder
        extracted = self._extract_params_from_text(remainder, task_type) if remainder else {}
        
        return {
            'task_type': task_type,
            'extracted_params': extracted
        }
    
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
        
        prompt = f"""Analyze this user request for content creation:

User: "{user_input}"

Business context: {business_name}, {industry}

Extract and return as JSON:
{{
    "task_type": "post|caption|script|email|review|ad|blog|unknown",
    "topic": "the main subject/topic if mentioned",
    "platform": "{platform_list}|null",
    "video_length": "15s|30s|60s|90s|null",
    "other_params": {{}}
}}

Rules:
- task_type must be one of: post, caption, script, email, review, ad, blog, or unknown
- Set platform to null if not mentioned
- Set video_length to null if not mentioned (only for script/video requests)
- Include any other relevant parameters in other_params
- Only return valid JSON, no explanation."""

        result = call_gemini(prompt, temperature=0.3)
        
        if not result:
            logger.warning("Gemini returned no result")
            return None
        
        # Extract fields
        task_type = result.get('task_type', 'unknown')
        if task_type == 'unknown':
            return None
        
        # Build extracted params
        extracted_params = {}
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
        
        This does simple pattern matching for common parameters.
        
        Args:
            text: User's message text
            task_type: The task type context
        
        Returns:
            dict of extracted parameters
        """
        params = {}
        text_lower = text.lower()
        
        # Extract platform using shared constant
        for platform, keywords in SUPPORTED_PLATFORMS.items():
            if any(kw in text_lower for kw in keywords):
                params['platform'] = platform
                break
        
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
        
        # Remove common filler words
        filler_words = ['about', 'for', 'on', 'regarding', 'concerning']
        for word in filler_words:
            topic_text = re.sub(r'\b' + re.escape(word) + r'\b', '', topic_text, flags=re.IGNORECASE)
        
        topic_text = topic_text.strip()
        if topic_text:
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
        
        return {
            'intent': intent,
            'task_type': task_type,
            'extracted_params': extracted_params,
            'follow_up_needed': follow_up_needed,
            'follow_up_question': follow_up_question,
            'missing_fields': missing_fields
        }
    
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
