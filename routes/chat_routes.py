"""Chat API routes for unified conversational content creation and onboarding.

This module provides the /api/chat endpoint that handles all conversational
interactions including onboarding flows and content creation tasks.

The endpoint supports multi-turn conversations through a stateless design where
all conversation state is passed in the request payload via the `pending_task`
field.

## Key Features:
- Profile readiness checking (routes to onboarding if incomplete)
- Multi-turn conversation support via pending_task state
- Intent parsing to detect task type and extract initial parameters
- Content generation via VoiceEngine integration
- Comprehensive error handling and request logging

## API Contract:

Request:
    {
        "message": "user's input text",
        "history": [{"role": "user"|"assistant", "message": "..."}],  # optional
        "pending_task": {  # optional, null for new conversations
            "task_type": "post"|"caption"|"reel"|"email"|"ad",
            "collected": {"platform": "instagram", "topic": "...", ...}
        }
    }

Response:
    {
        "response": "AI response text to display",
        "action": "continue"|"generated"|"onboarding"|"error",
        "pending_task": {...} | null,  # present if more info needed
        "content": "generated content" | null,  # present when action="generated"
        "suggestions": ["..."] | null  # optional suggestions for user
    }

## Future Enhancements:
- Replace stub intent parser with ConversationRouter AI service
- Add support for conversation history context in generation
- Add retry logic for transient API failures
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services.voice_engine import VoiceEngine
from services.onboarding_service import OnboardingService
from services.conversation_router import ConversationRouter
from models import VoiceProfile, db
import os
import logging
import uuid
import re

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)
voice_engine = VoiceEngine()
onboarding_service = OnboardingService()
conversation_router = ConversationRouter()


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


def _handle_onboarding_chat(message: str, history: list, profile: VoiceProfile, pending_task: dict = None) -> dict:
    """Handle onboarding conversation flow.
    
    Args:
        message: User's latest message
        history: Conversation history
        profile: VoiceProfile instance (may be incomplete)
        pending_task: Optional pending onboarding task state
        
    Returns:
        Response dict for the chat API
    """
    try:
        # Check if this is a continuation of field collection
        if pending_task and pending_task.get('task_type') == 'onboarding':
            collecting_field = pending_task.get('collecting_field')
            
            if collecting_field:
                # Update the specific field being collected
                onboarding_service.update_profile_field(profile, collecting_field, message)
                
                try:
                    db.session.commit()
                    logger.info(f"Updated profile field '{collecting_field}' for user {current_user.id}")
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"Database error updating profile: {db_error}", exc_info=True)
                    return _build_response(
                        "I had trouble saving that. Let me try again...",
                        action='error'
                    )
        
        # Check for URL in message
        detected_url = onboarding_service.detect_url(message)
        
        if detected_url:
            logger.info(f"Detected URL in onboarding: {detected_url}")
            result = onboarding_service.process_url(detected_url, profile)
            
            if result['success']:
                try:
                    db.session.commit()
                    logger.info(f"Saved URL-scraped profile data for user {current_user.id}")
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"Database error saving profile: {db_error}", exc_info=True)
                
                # Check if profile is now complete
                is_complete, missing = onboarding_service.is_profile_complete(profile)
                
                if is_complete:
                    return _build_response(
                        result['message'] + "\n\n✨ Your brand profile is ready! Redirecting to dashboard...",
                        action='onboarding_complete',
                        pending_task=None,
                        redirect='/dashboard'
                    )
                
                # Ask for next missing field
                next_question = onboarding_service.get_next_question(missing)
                response_message = result['message'] + f"\n\n{next_question}"
                
                return _build_response(
                    response_message,
                    action='continue',
                    pending_task={
                        'task_type': 'onboarding',
                        'collecting_field': missing[0]
                    }
                )
            else:
                # URL processing failed, ask for description
                return _build_response(
                    result['message'],
                    action='continue',
                    pending_task={'task_type': 'onboarding', 'collecting_field': None}
                )
        
        # Try to extract fields from description
        missing_fields = onboarding_service.get_missing_fields(profile)
        
        # If we know what field we're collecting, use that context
        collecting_field = None
        if pending_task and pending_task.get('task_type') == 'onboarding':
            collecting_field = pending_task.get('collecting_field')
        
        # If we're not collecting a specific field, try to extract from description
        if not collecting_field:
            result = onboarding_service.process_description(message, profile, context=None)
        else:
            # We already updated this field above, so just acknowledge
            result = {
                'success': True,
                'message': f"Got it! I've saved your {collecting_field.replace('_', ' ')}.",
                'extracted_fields': {collecting_field: message}
            }
        
        if result['success']:
            try:
                db.session.commit()
                logger.info(f"Saved profile updates for user {current_user.id}")
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error: {db_error}", exc_info=True)
        
        # Check if profile is complete
        is_complete, missing = onboarding_service.is_profile_complete(profile)
        
        if is_complete:
            return _build_response(
                result.get('message', 'Perfect!') + "\n\n🎉 Your brand profile is ready! Redirecting to dashboard...",
                action='onboarding_complete',
                pending_task=None,
                redirect='/dashboard'
            )
        
        # Ask for next missing field
        next_question = onboarding_service.get_next_question(missing)
        response_message = result.get('message', 'Thanks!') + f"\n\n{next_question}"
        
        return _build_response(
            response_message,
            action='continue',
            pending_task={
                'task_type': 'onboarding',
                'collecting_field': missing[0]
            }
        )
        
    except Exception as e:
        logger.error(f"Error in onboarding chat: {e}", exc_info=True)
        return _build_response(
            "I encountered an error. Let me ask you directly: What's your business name?",
            action='continue',
            pending_task={
                'task_type': 'onboarding',
                'collecting_field': 'business_name'
            }
        )


def _normalize_field_value(field_name: str, value: str) -> str:
    """Normalize conversational field values.
    
    Args:
        field_name: Name of the field being normalized
        value: Raw user input value
        
    Returns:
        Normalized value string
    """
    value = value.strip()
    
    if field_name == 'platform':
        platform_map = {
            'ig': 'instagram', 'insta': 'instagram',
            'fb': 'facebook',
            'x': 'twitter', 'tweet': 'twitter',
            'li': 'linkedin',
            'tt': 'tiktok',
        }
        value_lower = value.lower()
        for alias, canonical in platform_map.items():
            if alias in value_lower or canonical in value_lower:
                return canonical
        return value_lower
    
    if field_name == 'video_length':
        match = re.search(r'(\d+)', value)
        if match:
            seconds = int(match.group(1))
            if seconds in [15, 30, 60, 90]:
                return f"{seconds}s"
        return '30s'
    
    return value


def _format_generated_content(task_type: str, content: str) -> str:
    """Format generated content for chat display.
    
    Args:
        task_type: Type of content generated
        content: Raw generated content
        
    Returns:
        Formatted content string with emoji and instructions
    """
    emoji_map = {
        'post': '📝',
        'caption': '📸',
        'script': '🎬',
        'email': '✉️',
        'review': '⭐',
        'ad': '📢',
        'blog': '📰',
        'custom': '✨',
    }
    emoji = emoji_map.get(task_type, '✨')
    
    return f"{emoji} **Your {task_type} is ready!**\n\n{content}\n\n---\n_Copy this content or say 'regenerate' for a new version._"


def _get_content_suggestions() -> list:
    """Get contextual suggestions for content creation.
    
    Returns:
        List of suggestion strings
    """
    return [
        'Try /post for social media',
        'Try /email for newsletters',
        'Try /script for video content',
        'Try /review for review responses',
        'Try /custom for flexible content'
    ]


def _continue_content_task(pending_task: dict, message: str, profile: VoiceProfile) -> dict:
    """Continue collecting fields for content generation.
    
    Args:
        pending_task: Current task state with task_type and collected fields
        message: User's latest input message
        profile: User's voice profile
        
    Returns:
        Response dict with next prompt or generation result
    """
    task_type = pending_task.get('task_type', 'post')
    collected = pending_task.get('collected', {})
    
    # Get missing fields to know what we were asking for
    missing_before = conversation_router.get_missing_fields(task_type, collected)
    
    if missing_before:
        # Store the response for the first missing field
        field_name = missing_before[0]
        collected[field_name] = _normalize_field_value(field_name, message)
    
    # Check if still missing fields
    missing_after = conversation_router.get_missing_fields(task_type, collected)
    
    if missing_after:
        next_prompt = conversation_router.get_next_prompt(task_type, missing_after)
        return _build_response(
            next_prompt,
            action='continue',
            pending_task={'task_type': task_type, 'collected': collected, 'flow': 'content'}
        )
    
    # All fields collected - generate!
    return _generate_content_response(task_type, collected, profile)


def _generate_content_response(task_type: str, params: dict, profile: VoiceProfile) -> dict:
    """Generate content using VoiceEngine and return formatted response.
    
    Args:
        task_type: Type of content to generate
        params: Dictionary of collected parameters
        profile: User's voice profile
        
    Returns:
        Response dict with generated content
    """
    try:
        topic = params.get('topic', '')
        platform = params.get('platform', 'instagram')
        
        # Remove fields that are explicit parameters from params dict to avoid duplicates
        extra_context = {k: v for k, v in params.items() if k not in ['topic', 'platform']}
        
        content = voice_engine.generate_expert_content(
            user_profile=profile,
            topic=topic,
            task_type=task_type,
            platform=platform,
            **extra_context
        )
        
        formatted = _format_generated_content(task_type, content)
        
        return _build_response(
            formatted,
            action='generated',
            content=content,
            pending_task=None,
            suggestions=['Create another', 'Try /post', 'Try /email']
        )
    except Exception as e:
        logger.error(f"Content generation failed: {e}", exc_info=True)
        return _build_response(
            f"Sorry, I couldn't generate that. Please try again.",
            action='error'
        )


def _continue_task_flow(pending_task: dict, message: str, profile: VoiceProfile) -> dict:
    """Continue an in-progress task flow by collecting the next required field.
    
    This function is kept for backwards compatibility but now delegates to
    _continue_content_task for the updated implementation.
    
    Args:
        pending_task: Current task state with task_type and collected fields
        message: User's latest input message
        profile: User's voice profile
        
    Returns:
        Response dict with next prompt or generation result
    """
    # Delegate to the new implementation
    return _continue_content_task(pending_task, message, profile)


def _format_field_name(field_name: str) -> str:
    """Format field name for display.
    
    Args:
        field_name: Internal field name (e.g., 'brand_voice')
        
    Returns:
        Human-readable field name (e.g., 'Brand Voice')
    """
    return field_name.replace('_', ' ').title()


def _validate_profile_field(field_name: str, value: str) -> tuple[bool, str]:
    """Validate field value before saving.
    
    Args:
        field_name: Name of the field being validated
        value: Value to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not value or len(value.strip()) < 2:
        return False, "Please provide a more detailed value."
    
    if field_name == 'writing_samples':
        # Expect meaningful content
        if len(value) < 20:
            return False, "Writing samples should be at least a few sentences."
    
    if field_name == 'brand_voice':
        # Encourage descriptive voices
        if len(value.split()) < 2:
            return False, "Try describing your voice with 2-3 words (e.g., 'warm and friendly')."
    
    return True, ""


def _apply_profile_update(profile: VoiceProfile, field_name: str, new_value: str, db) -> dict:
    """Apply the update and save to database.
    
    Args:
        profile: VoiceProfile instance to update
        field_name: Field to update
        new_value: New value to set
        db: Database session
        
    Returns:
        Response dict with confirmation message
    """
    # Validate the value
    is_valid, error_msg = _validate_profile_field(field_name, new_value)
    if not is_valid:
        return _build_response(
            f"❌ {error_msg}",
            action='error'
        )
    
    # Get old value for comparison
    if field_name == 'writing_samples':
        old_samples = profile.get_writing_samples()
        old_value = f"{len(old_samples)} samples" if old_samples else "No samples"
    else:
        old_value = getattr(profile, field_name, "Not set")
        if old_value is None:
            old_value = "Not set"
    
    # Apply the update
    if field_name == 'writing_samples':
        # Handle writing samples specially
        if '\n\n' in new_value:
            samples = [s.strip() for s in new_value.split('\n\n') if s.strip()]
        else:
            samples = [new_value.strip()]
        profile.set_writing_samples(samples)
    else:
        setattr(profile, field_name, new_value)
    
    try:
        db.session.commit()
        logger.info(f"Updated profile field '{field_name}' for user {current_user.id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error updating profile: {e}", exc_info=True)
        return _build_response(
            "I had trouble saving that update. Please try again.",
            action='error'
        )
    
    # Format the new value for display
    if field_name == 'writing_samples':
        display_new_value = f"{len(samples)} samples"
    else:
        display_new_value = new_value[:100] + "..." if len(new_value) > 100 else new_value
    
    return _build_response(
        f"✅ Updated your **{_format_field_name(field_name)}**!\n\n"
        f"~~{old_value}~~ → **{display_new_value}**\n\n"
        f"Your content will now reflect this change.",
        action='profile_updated',
        suggestions=['Create content with new profile', 'Update another field', 'View full profile']
    )


def _show_profile_summary(profile: VoiceProfile) -> dict:
    """Show current profile with update options.
    
    Args:
        profile: VoiceProfile instance to display
        
    Returns:
        Response dict with profile summary
    """
    writing_samples = profile.get_writing_samples()
    sample_count = len(writing_samples) if writing_samples else 0
    
    summary = f"""📋 **Your Brand Profile**

**Business:** {profile.business_name or 'Not set'}
**Industry:** {profile.industry or 'Not set'}
**Target Audience:** {profile.target_audience or 'Not set'}
**Brand Voice:** {profile.brand_voice or 'Not set'}
**Key Offer:** {profile.key_offer or 'Not set'}
**Writing Samples:** {sample_count} sample(s)

What would you like to update? You can say things like:
- "Change my brand voice to professional and authoritative"
- "Update target audience to small business owners"
- Or use `/update` to pick a field"""
    
    return _build_response(
        summary,
        action='profile_view',
        suggestions=[
            'Update brand voice',
            'Update target audience', 
            'Update key offer',
            'Back to content creation'
        ]
    )


def _continue_profile_update(pending_task: dict, message: str, profile: VoiceProfile, db) -> dict:
    """Continue a multi-turn profile update flow.
    
    Args:
        pending_task: Current task state with field_name
        message: User's latest input
        profile: VoiceProfile instance
        db: Database session
        
    Returns:
        Response dict with next prompt or confirmation
    """
    field_name = pending_task.get('field_name')
    
    if not field_name:
        # User provided field name
        normalized = conversation_router.normalize_field_name(message)
        if normalized:
            # Ask for new value
            return _build_response(
                f"What would you like to change your **{_format_field_name(normalized)}** to?",
                action='continue',
                pending_task={
                    'flow': 'profile_update',
                    'task_type': 'profile_update',
                    'field_name': normalized
                }
            )
        else:
            # Reset pending task to avoid infinite loop
            return _build_response(
                f"I don't recognize that field. Please choose from: business_name, industry, target_audience, brand_voice, key_offer, or writing_samples",
                action='continue',
                pending_task={
                    'flow': 'profile_update',
                    'task_type': 'profile_update',
                    'field_name': None  # Reset to ask again
                }
            )
    else:
        # User provided new value
        return _apply_profile_update(profile, field_name, message, db)


def _handle_profile_update(message: str, pending_task: dict, profile: VoiceProfile, db) -> dict:
    """Handle profile field updates.
    
    Args:
        message: User's input message
        pending_task: Optional pending task state
        profile: VoiceProfile instance
        db: Database session
        
    Returns:
        Response dict with next step or confirmation
    """
    if pending_task and pending_task.get('flow') == 'profile_update':
        return _continue_profile_update(pending_task, message, profile, db)
    
    # Parse the intent for profile updates
    intent_result = conversation_router.parse_intent(message, profile)
    
    if intent_result['task_type'] == 'profile':
        # Show profile summary
        return _show_profile_summary(profile)
    
    if intent_result['task_type'] in ['profile_update', 'update_voice', 'update_audience']:
        extracted = intent_result.get('extracted_params', {})
        field_name = extracted.get('field_name')
        new_value = extracted.get('new_value')
        
        # Handle quick shortcuts
        if intent_result['task_type'] == 'update_voice':
            field_name = 'brand_voice'
        elif intent_result['task_type'] == 'update_audience':
            field_name = 'target_audience'
        
        if field_name and new_value:
            # Direct update - we have both field and value
            return _apply_profile_update(profile, field_name, new_value, db)
        
        if field_name:
            # Ask for new value
            return _build_response(
                f"What would you like to change your **{_format_field_name(field_name)}** to?",
                action='continue',
                pending_task={
                    'flow': 'profile_update',
                    'task_type': intent_result['task_type'],
                    'field_name': field_name
                }
            )
        
        # No field specified - ask which field
        return _build_response(
            "Which field would you like to update?\n\n"
            "• **Business Name**\n"
            "• **Industry**\n"
            "• **Target Audience**\n"
            "• **Brand Voice**\n"
            "• **Key Offer**\n"
            "• **Writing Samples**",
            action='continue',
            pending_task={
                'flow': 'profile_update',
                'task_type': 'profile_update',
                'field_name': None
            }
        )
    
    # Not a profile update - should not reach here
    return _build_response(
        "I'm not sure what you'd like to do. Try saying 'update my profile' or '/profile'",
        action='error'
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
        action: Action type (continue|generated|onboarding|onboarding_complete|error)
        **kwargs: Additional response fields (pending_task, content, suggestions, redirect)
        
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
    
    # Add redirect if provided
    if 'redirect' in kwargs:
        response['redirect'] = kwargs['redirect']
    
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
    
    # Check for more specific patterns first to avoid false matches
    # Order matters: check specific patterns before generic ones
    if 'reel' in message_lower or 'tiktok' in message_lower or 'video' in message_lower:
        return 'reel', initial_collected
    elif 'caption' in message_lower or ('instagram' in message_lower and 'post' not in message_lower):
        return 'caption', initial_collected
    elif 'email' in message_lower:
        return 'email', initial_collected
    elif 'ad' in message_lower or 'advertisement' in message_lower:
        return 'ad', initial_collected
    elif 'post' in message_lower or 'linkedin' in message_lower or 'facebook' in message_lower:
        return 'post', initial_collected
    
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
            "collected": {"platform": "instagram", ...},
            "flow": "content"|"onboarding"
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
        
        # Handle pending task based on flow type
        if pending_task:
            task_type = pending_task.get('task_type')
            flow = pending_task.get('flow')
            
            # Auto-detect flow if not specified based on task_type
            if not flow:
                if task_type == 'onboarding':
                    flow = 'onboarding'
                elif task_type in ['profile', 'profile_update', 'update_voice', 'update_audience']:
                    flow = 'profile_update'
                else:
                    # If profile is complete and task_type is a content type, assume content flow
                    content_task_types = ['post', 'caption', 'script', 'email', 'review', 'ad', 'blog', 'reel', 'custom']
                    if profile_ready and task_type in content_task_types:
                        flow = 'content'
                    else:
                        flow = 'onboarding'
            
            logger.info(f"[{request_id}] Continuing {flow} flow for task: {task_type}")
            
            if flow == 'profile_update':
                # Continue profile update flow
                result = _handle_profile_update(message, pending_task, profile, db)
                return jsonify(result), 200
            elif flow == 'content':
                # Continue content generation flow
                result = _continue_content_task(pending_task, message, profile)
                return jsonify(result), 200
            else:
                # Continue onboarding flow
                result = _handle_onboarding_chat(message, history, profile, pending_task)
                return jsonify(result), 200
        
        # Route based on profile completeness
        if not profile_ready:
            # Route to onboarding flow
            logger.info(f"[{request_id}] User {current_user.id} needs onboarding - missing: {missing_fields}")
            
            # Get or create profile if needed
            if not profile:
                logger.info(f"Creating new VoiceProfile for user {current_user.id}")
                profile = VoiceProfile(user_id=current_user.id)
                db.session.add(profile)
                try:
                    db.session.commit()
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"Failed to create profile: {db_error}", exc_info=True)
                    return jsonify(_build_response(
                        "I had trouble setting up your profile. Please try again.",
                        action='error'
                    )), 500
            
            # Handle onboarding conversation
            result = _handle_onboarding_chat(message, history, profile, pending_task)
            return jsonify(result), 200
        
        # Profile complete - check API key configuration
        api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning(f"[{request_id}] Missing API key")
            return jsonify(_build_response(
                "AI service is not configured. Please contact support or set up your API key.",
                action='error'
            )), 503
        
        # Check for regeneration request
        message_lower = message.lower().strip()
        if message_lower in ['regenerate', 'try again', 'new version', 'another']:
            # Check history for last generated content
            if history:
                for msg in reversed(history):
                    if msg.get('pending_task') and msg['pending_task'].get('flow') == 'content':
                        last_task = msg['pending_task']
                        logger.info(f"[{request_id}] Regenerating content for task: {last_task.get('task_type')}")
                        return jsonify(_generate_content_response(
                            last_task['task_type'], 
                            last_task.get('collected', {}), 
                            profile
                        )), 200
            return jsonify(_build_response(
                "What would you like me to create?",
                action='continue',
                suggestions=_get_content_suggestions()
            )), 200
        
        # Parse new intent using ConversationRouter
        intent_result = conversation_router.parse_intent(message, profile)
        logger.info(f"[{request_id}] Parsed intent: {intent_result['intent']}, task_type={intent_result.get('task_type')}")
        
        # Handle profile-related intents
        if intent_result['task_type'] in ['profile', 'profile_update', 'update_voice', 'update_audience']:
            logger.info(f"[{request_id}] Handling profile update request")
            result = _handle_profile_update(message, None, profile, db)
            return jsonify(result), 200
        
        if intent_result['intent'] == 'unknown':
            return jsonify(_build_response(
                intent_result['follow_up_question'],
                action='continue',
                suggestions=_get_content_suggestions()
            )), 200
        
        if intent_result['follow_up_needed']:
            return jsonify(_build_response(
                intent_result['follow_up_question'],
                action='continue',
                pending_task={
                    'task_type': intent_result['task_type'],
                    'collected': intent_result['extracted_params'],
                    'flow': 'content'  # Distinguish from onboarding flow
                }
            )), 200
        
        # Ready to generate - all required fields collected
        logger.info(f"[{request_id}] Generating content immediately for task: {intent_result['task_type']}")
        result = _generate_content_response(
            intent_result['task_type'], 
            intent_result['extracted_params'], 
            profile
        )
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        return jsonify(_build_response(
            "An unexpected error occurred. Please try again.",
            action='error'
        )), 500
