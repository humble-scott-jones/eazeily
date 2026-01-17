"""Chat API routes for unified conversational content creation and onboarding.

This module provides the /api/chat endpoint that handles all conversational
interactions including onboarding flows and content creation tasks.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services.voice_engine import VoiceEngine
from models import VoiceProfile
import os
import logging
import uuid

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)
voice_engine = VoiceEngine()


def _check_profile_ready(profile: VoiceProfile) -> tuple[bool, list[str]]:
    """Check if profile has minimum required fields for content generation.
    
    Args:
        profile: VoiceProfile instance to check
        
    Returns:
        Tuple of (ready: bool, missing_fields: list[str])
    """
    if not profile:
        return False, ['profile']
    
    missing_fields = []
    
    # Check critical fields for content generation
    if not profile.business_name:
        missing_fields.append('business_name')
    if not profile.industry:
        missing_fields.append('industry')
    if not profile.brand_voice:
        missing_fields.append('brand_voice')
    if not profile.target_audience:
        missing_fields.append('target_audience')
    if not profile.key_offer:
        missing_fields.append('key_offer')
    
    # Check for at least one writing sample
    writing_samples = profile.get_writing_samples()
    if not writing_samples or len(writing_samples) == 0:
        missing_fields.append('writing_samples')
    
    return len(missing_fields) == 0, missing_fields


def _continue_task_flow(pending_task: dict, message: str, profile: VoiceProfile) -> dict:
    """Continue an in-progress task flow by collecting the next required field.
    
    Args:
        pending_task: Current task state with task_type and collected fields
        message: User's latest input message
        profile: User's voice profile
        
    Returns:
        Response dict with next prompt or generation result
    """
    task_type = pending_task.get('task_type', 'post')
    collected = pending_task.get('collected', {})
    
    # Define required fields per task type
    required_fields = {
        'post': ['platform', 'topic'],
        'caption': ['platform', 'topic'],
        'reel': ['topic', 'style'],
        'email': ['subject', 'goal'],
        'ad': ['platform', 'objective', 'target_audience'],
    }
    
    fields_needed = required_fields.get(task_type, ['topic', 'platform'])
    
    # Try to extract the next missing field from the message
    missing = [f for f in fields_needed if f not in collected]
    
    if missing:
        # Store the user's message as the first missing field's value
        next_field = missing[0]
        collected[next_field] = message
        
        # Check if we still need more fields
        still_missing = [f for f in fields_needed if f not in collected]
        
        if still_missing:
            # Ask for the next field
            next_prompt = _get_field_prompt(still_missing[0], task_type)
            return _build_response(
                next_prompt,
                action='continue',
                pending_task={
                    'task_type': task_type,
                    'collected': collected
                }
            )
    
    # All fields collected - generate content
    try:
        topic = collected.get('topic', message)
        platform = collected.get('platform', 'LinkedIn')
        
        # Remove fields that are explicit parameters from collected dict to avoid duplicates
        extra_context = {k: v for k, v in collected.items() if k not in ['topic', 'platform']}
        
        content = voice_engine.generate_expert_content(
            user_profile=profile,
            topic=topic,
            task_type=task_type,
            platform=platform,
            **extra_context
        )
        
        return _build_response(
            f"Here's your {task_type} for {platform}:",
            action='generated',
            content=content,
            pending_task=None
        )
    except Exception as e:
        logger.error(f"Content generation failed: {e}", exc_info=True)
        return _build_response(
            "I encountered an error generating your content. Please try again.",
            action='error',
            pending_task=None
        )


def _get_field_prompt(field: str, task_type: str) -> str:
    """Get a conversational prompt for collecting a specific field.
    
    Args:
        field: Name of the field to collect
        task_type: Type of content being created
        
    Returns:
        User-friendly prompt string
    """
    prompts = {
        'platform': f"Which platform is this {task_type} for? (e.g., Instagram, LinkedIn, Facebook)",
        'topic': f"What topic or theme should I write about for this {task_type}?",
        'subject': "What's the subject line or main topic for this email?",
        'goal': "What's the main goal of this email? (e.g., promote a sale, build relationships, announce news)",
        'style': "What style of reel? (e.g., tutorial, behind-the-scenes, storytelling)",
        'objective': "What's the objective of this ad? (e.g., drive sales, increase awareness, generate leads)",
        'target_audience': "Who is the target audience for this ad?",
    }
    
    return prompts.get(field, f"Please provide the {field} for your {task_type}")


def _build_response(message: str, action: str, **kwargs) -> dict:
    """Build a standardized response payload.
    
    Args:
        message: Main response text to display to user
        action: Action type (continue|generated|onboarding|error)
        **kwargs: Additional response fields (pending_task, content, suggestions)
        
    Returns:
        Response dictionary
    """
    response = {
        'response': message,
        'action': action,
        'pending_task': kwargs.get('pending_task'),
        'content': kwargs.get('content'),
        'suggestions': kwargs.get('suggestions'),
    }
    
    return response


def _parse_intent(message: str, history: list) -> tuple[str, dict]:
    """Stub for ConversationRouter - parse user intent from message.
    
    This is a simple placeholder until ConversationRouter is implemented.
    Looks for keywords to determine task type and extracts initial fields.
    
    Args:
        message: User's input message
        history: Conversation history
        
    Returns:
        Tuple of (task_type, initial_collected_fields)
    """
    message_lower = message.lower()
    initial_collected = {}
    
    # Extract platform mentions
    platform_map = {
        'linkedin': 'LinkedIn',
        'facebook': 'Facebook',
        'instagram': 'Instagram',
        'twitter': 'Twitter',
        'tiktok': 'TikTok',
    }
    
    for keyword, platform_name in platform_map.items():
        if keyword in message_lower:
            initial_collected['platform'] = platform_name
            break
    
    # Simple keyword matching for task type
    if 'post' in message_lower or 'linkedin' in message_lower or 'facebook' in message_lower:
        return 'post', initial_collected
    elif 'caption' in message_lower or 'instagram' in message_lower:
        return 'caption', initial_collected
    elif 'reel' in message_lower or 'tiktok' in message_lower or 'video' in message_lower:
        return 'reel', initial_collected
    elif 'email' in message_lower:
        return 'email', initial_collected
    elif 'ad' in message_lower or 'advertisement' in message_lower:
        return 'ad', initial_collected
    
    # Default to post
    return 'post', initial_collected


@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Unified conversational endpoint for all content creation and onboarding.
    
    Request body:
    {
        "message": "user's input text",
        "history": [{"role": "user"|"assistant", "message": "..."}],
        "pending_task": {
            "task_type": "post"|"caption"|etc,
            "collected": {"platform": "instagram", ...}
        } | null
    }
    
    Response:
    {
        "response": "AI response text",
        "action": "continue"|"generated"|"onboarding"|"error",
        "pending_task": {...} | null,
        "content": "generated content" | null,
        "suggestions": ["Try /post", "Create a reel"] | null
    }
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate request payload
        data = request.get_json(silent=True)
        if not data:
            logger.warning(f"[{request_id}] Empty request body")
            return jsonify(_build_response(
                "Invalid request: empty body",
                action='error'
            )), 400
        
        message = data.get('message', '').strip()
        if not message:
            logger.warning(f"[{request_id}] Missing message in request")
            return jsonify(_build_response(
                "Please provide a message",
                action='error'
            )), 400
        
        history = data.get('history', [])
        pending_task = data.get('pending_task')
        
        logger.info(
            f"[{request_id}] Chat request from user {current_user.id}: "
            f"message='{message[:50]}...', has_pending={pending_task is not None}"
        )
        
        # Get user's voice profile
        profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
        
        # Check if profile is ready for content generation
        profile_ready, missing_fields = _check_profile_ready(profile)
        
        if not profile_ready:
            # Route to onboarding - don't check API key yet since we're not generating
            logger.info(f"[{request_id}] User {current_user.id} needs onboarding - missing: {missing_fields}")
            return jsonify(_build_response(
                "I'd love to help you create amazing content! First, let's set up your brand profile. "
                "This helps me write in your unique voice and style. Click here to complete your profile setup.",
                action='onboarding',
                suggestions=['Complete your profile', 'Learn more about brand profiles']
            )), 200
        
        # Check API key configuration (only if we have a complete profile)
        api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning(f"[{request_id}] Missing API key")
            return jsonify(_build_response(
                "AI service is not configured. Please contact support or set up your API key.",
                action='error'
            )), 503
        
        # Handle pending task continuation
        if pending_task:
            logger.info(f"[{request_id}] Continuing task: {pending_task.get('task_type')}")
            result = _continue_task_flow(pending_task, message, profile)
            return jsonify(result), 200
        
        # Parse new intent from message
        task_type, initial_collected = _parse_intent(message, history)
        logger.info(f"[{request_id}] Parsed intent: task_type={task_type}, collected={initial_collected}")
        
        # Define required fields for this task type
        required_fields = {
            'post': ['platform', 'topic'],
            'caption': ['platform', 'topic'],
            'reel': ['topic', 'style'],
            'email': ['subject', 'goal'],
            'ad': ['platform', 'objective', 'target_audience'],
        }
        
        fields_needed = required_fields.get(task_type, ['topic', 'platform'])
        missing_fields = [f for f in fields_needed if f not in initial_collected]
        
        if not missing_fields:
            # We have everything we need - generate immediately
            topic = initial_collected.get('topic', message)
            platform = initial_collected.get('platform', 'LinkedIn')
            
            try:
                extra_context = {k: v for k, v in initial_collected.items() if k not in ['topic', 'platform']}
                content = voice_engine.generate_expert_content(
                    user_profile=profile,
                    topic=topic,
                    task_type=task_type,
                    platform=platform,
                    **extra_context
                )
                
                return jsonify(_build_response(
                    f"Here's your {task_type} for {platform}:",
                    action='generated',
                    content=content,
                    pending_task=None
                )), 200
            except Exception as e:
                logger.error(f"[{request_id}] Content generation failed: {e}", exc_info=True)
                return jsonify(_build_response(
                    "I encountered an error generating your content. Please try again.",
                    action='error',
                    pending_task=None
                )), 500
        
        # Ask for the first missing field
        next_prompt = _get_field_prompt(missing_fields[0], task_type)
        
        return jsonify(_build_response(
            f"I'll help you create a {task_type}. {next_prompt}",
            action='continue',
            pending_task={
                'task_type': task_type,
                'collected': initial_collected
            }
        )), 200
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        return jsonify(_build_response(
            "An unexpected error occurred. Please try again.",
            action='error'
        )), 500
