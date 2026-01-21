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
from services.profile_validator import get_profile_completeness
from services.task_registry import get_task_config
from models import VoiceProfile, ContentHistory, db
import os
import logging
import uuid
import re

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)
voice_engine = VoiceEngine()
onboarding_service = OnboardingService()
conversation_router = ConversationRouter()

# Commands that should not show guidance and instead call their handlers directly
# Profile commands: handled by profile update flow
# Utility commands: handled by dedicated handlers (export, preview)
COMMANDS_WITHOUT_GUIDANCE = [
    '/update', '/profile', '/voice', '/audience', '/samples',  # Profile commands
    '/export', '/preview'  # Utility commands
]


def _check_profile_ready(profile: VoiceProfile) -> tuple[bool, list[str], int]:
    """Check if profile has minimum required fields for content generation.
    
    Args:
        profile: VoiceProfile instance to check
        
    Returns:
        Tuple of (ready: bool, missing_fields: list[str], completeness: int)
    """
    is_complete, missing_fields, completeness = get_profile_completeness(profile)
    return is_complete, missing_fields, completeness


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
        'review_reply': '⭐',
        'ad': '📢',
        'blog': '📰',
        'blog_post': '📰',
        'proposal': '📋',
        'newsletter': '📧',
        'custom': '✨',
    }
    emoji = emoji_map.get(task_type, '✨')
    
    # Use appropriate label based on task type
    task_labels = {
        'post': 'post',
        'caption': 'caption',
        'script': 'script',
        'email': 'email',
        'review': 'review response',
        'review_reply': 'review response',
        'ad': 'ad',
        'blog': 'blog post',
        'blog_post': 'blog post',
        'proposal': 'proposal',
        'newsletter': 'newsletter',
    }
    label = task_labels.get(task_type, task_type)
    
    return f"{emoji} **Your {label} is ready!**\n\n{content}\n\n---\n_Copy this content or say 'regenerate' for a new version._"


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
        # Check generation limits
        if not current_user.can_generate():
            remaining = current_user.generations_remaining()
            return _build_response(
                f"⚠️ **Monthly limit reached!**\n\n"
                f"Free accounts get 10 generations per month. "
                f"Upgrade to Pro for unlimited content creation.\n\n"
                f"Your limit resets on the 1st of next month.",
                action='limit_reached',
                suggestions=['View pricing', 'View my profile']
            )
        
        topic = params.get('topic', '')
        
        # Check if this task type requires a platform using task registry
        task_config = get_task_config(task_type)
        
        # For tasks that require platform (post, caption, ad, script), default to instagram
        # For non-social content (review, email, blog, etc.), use None
        if task_config and task_config.require_platform:
            platform = params.get('platform', 'instagram')  # Default for social content
        else:
            platform = params.get('platform')  # None for non-social content
        
        # Remove fields that are explicit parameters from params dict to avoid duplicates
        extra_context = {k: v for k, v in params.items() if k not in ['topic', 'platform']}
        
        content = voice_engine.generate_expert_content(
            user_profile=profile,
            topic=topic,
            task_type=task_type,
            platform=platform,
            **extra_context
        )
        
        # Save to history (for paid tiers)
        if current_user.get_tier_limits().get('history_days', 0) > 0:
            try:
                ContentHistory.create_from_generation(
                    user_id=current_user.id,
                    profile_id=profile.id if profile else None,
                    task_type=task_type,
                    content=content,
                    platform=platform,
                    topic=topic,
                    parameters={k: v for k, v in params.items() if k not in ['topic', 'platform']}
                )
            except (db.exc.IntegrityError, db.exc.OperationalError) as e:
                logger.warning(f"Database error saving content to history for user {current_user.id}, task_type={task_type}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error saving content to history for user {current_user.id}, task_type={task_type}: {e}", exc_info=True)
        
        # Increment generation counter
        current_user.increment_generation()
        
        # Format content
        formatted = _format_generated_content(task_type, content)
        
        # Add usage info for free tier
        remaining = current_user.generations_remaining()
        if remaining >= 0 and remaining <= 3:
            formatted += f"\n\n_({remaining} generations remaining this month)_"
        
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


def _get_prefilled_value_for_field(field_name: str, profile: VoiceProfile) -> tuple[str | None, str]:
    """Get pre-filled value and source description for a field based on profile data.
    
    Args:
        field_name: The field being updated
        profile: User's VoiceProfile with context data
        
    Returns:
        Tuple of (prefilled_value, source_description)
        - prefilled_value: The best value we found, or None
        - source_description: Where it came from (e.g., "from your website", "based on your industry")
    """
    try:
        # Get context data
        industry = profile.industry
        scraped_meta = profile.get_scraped_meta() if hasattr(profile, 'get_scraped_meta') else {}
        
        # Priority: scraped data > industry defaults > generic
        
        if field_name == 'brand_voice':
            # Check scraped data first
            if scraped_meta.get('voice_tone_and_style'):
                return scraped_meta['voice_tone_and_style'], "from your website"
            
            # Use industry defaults
            if industry:
                try:
                    import json
                    industry_key = industry.lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
                    industry_file = f'industry_packs/v1/{industry_key}.json'
                    
                    if os.path.exists(industry_file):
                        with open(industry_file, 'r') as f:
                            industry_data = json.load(f)
                            keywords = industry_data.get('keyword_banks', {}).get('seed_keywords', [])
                            if len(keywords) > 6:
                                value = f"{keywords[3]} and {keywords[4]}"
                                return value, f"based on typical {industry} businesses"
                except:
                    pass
            
            # Generic default
            return "professional and friendly", "a common starting point"
        
        elif field_name == 'target_audience':
            # Check scraped data first
            if scraped_meta.get('key_customers'):
                return scraped_meta['key_customers'], "from your website"
            
            # Industry defaults
            if industry:
                industry_audiences = {
                    'fitness': 'health-conscious individuals seeking results',
                    'restaurant': 'food lovers looking for quality dining experiences',
                    'software': 'businesses seeking reliable tech solutions',
                    'realtor': 'individuals and families looking for their dream home',
                    'salon': 'people who value self-care and looking their best',
                    'healthcare': 'patients and families seeking quality care',
                    'coach': 'individuals ready for personal or professional growth',
                }
                industry_lower = industry.lower()
                for key, audience in industry_audiences.items():
                    if key in industry_lower:
                        return audience, f"typical for {industry} businesses"
            
            return "busy professionals and families", "a common audience"
        
        elif field_name == 'key_offer':
            # Check scraped data first
            if scraped_meta.get('key_offer'):
                return scraped_meta['key_offer'], "from your website"
            
            # Industry defaults
            if industry:
                industry_offers = {
                    'fitness': 'personalized training programs that deliver real results',
                    'restaurant': 'fresh, quality food in a welcoming atmosphere',
                    'software': 'reliable solutions with outstanding support',
                    'realtor': 'expert guidance through every step of your real estate journey',
                    'salon': 'personalized beauty services that make you feel amazing',
                }
                industry_lower = industry.lower()
                for key, offer in industry_offers.items():
                    if key in industry_lower:
                        return offer, f"common for {industry} businesses"
            
            return "exceptional service and quality", "a solid foundation"
        
        elif field_name == 'business_name':
            if scraped_meta.get('business_name'):
                return scraped_meta['business_name'], "from your website"
            return None, ""
        
        elif field_name == 'industry':
            # Don't pre-fill industry - let them choose
            return None, ""
    
    except Exception as e:
        logger.warning(f"Error getting prefilled value: {e}")
    
    return None, ""


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
        f"Perfect! I've updated your **{_format_field_name(field_name)}** to:\n\n"
        f"**{display_new_value}**\n\n"
        f"This will help me create content that feels more authentically you. Ready to create something?",
        action='profile_updated',
        suggestions=['Create content', 'Update another field', 'View my profile']
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
    
    summary = f"""Here's your brand profile:\n\n"""
    summary += f"**Business:** {profile.business_name or 'Not set'}\n"
    summary += f"**Industry:** {profile.industry or 'Not set'}\n"
    summary += f"**Target Audience:** {profile.target_audience or 'Not set'}\n"
    summary += f"**Brand Voice:** {profile.brand_voice or 'Not set'}\n"
    summary += f"**Key Offer:** {profile.key_offer or 'Not set'}\n"
    summary += f"**Writing Samples:** {sample_count} sample(s)\n\n"
    summary += "Want to update something? Just tell me which part, like:"
    summary += '- "I want to update my brand voice"\n'
    summary += '- "Change my target audience"\n'
    summary += '- Or just type `/update`'
    
    return _build_response(
        summary,
        action='profile_view',
        suggestions=[
            'Update brand voice',
            'Update target audience', 
            'Update key offer',
            'Create content'
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
    # Handle writing samples collection
    if pending_task.get('collecting') == 'writing_samples':
        # Check if user is done
        if message.lower().strip() in ['done', 'finished', 'complete', 'stop']:
            current_count = len(profile.get_writing_samples() or [])
            return _build_response(
                f"Perfect! You now have {current_count} writing sample(s) saved. "
                f"I'll use these to match your style when creating content.\n\n"
                f"Ready to create something?",
                action='profile_updated',
                suggestions=['Create content', 'View my profile']
            )
        
        # Add the sample
        current_samples = profile.get_writing_samples() or []
        current_samples.append(message)
        profile.set_writing_samples(current_samples)
        
        try:
            db.session.commit()
            logger.info(f"Added writing sample for user {current_user.id}")
            
            return _build_response(
                f"Great sample! I've saved it ({len(current_samples)} total).\n\n"
                f"Want to add another? Just paste it, or say 'done' to finish.",
                action='continue',
                pending_task={
                    'flow': 'profile_update',
                    'task_type': 'update_samples',
                    'collecting': 'writing_samples'
                }
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving writing sample: {e}", exc_info=True)
            return _build_response(
                "I had trouble saving that sample. Please try again.",
                action='error'
            )
    
    field_name = pending_task.get('field_name')
    
    if not field_name:
        # User provided field name
        normalized = conversation_router.normalize_field_name(message)
        if normalized:
            # Get prefilled value for this field
            prefilled_value, source = _get_prefilled_value_for_field(normalized, profile)
            
            # Build prompt showing what we found
            field_display = _format_field_name(normalized)
            
            if prefilled_value:
                # We have data - show it and let them edit or accept
                prompt = f"Great! Here's what I found for your **{field_display}** {source}:\n\n"
                prompt += f"**{prefilled_value}**\n\n"
                prompt += "Does this capture your brand? You can edit it or just hit enter to keep it as is."
                
                # Store the prefilled value in pending task
                return _build_response(
                    prompt,
                    action='continue',
                    pending_task={
                        'flow': 'profile_update',
                        'task_type': 'profile_update',
                        'field_name': normalized,
                        'prefilled_value': prefilled_value
                    }
                )
            else:
                # No data found - guide them to define it
                prompts_by_field = {
                    'business_name': "What's the name of your business?",
                    'industry': "What industry are you in? This helps me understand your audience and create better content for you.",
                    'target_audience': "Who are you trying to reach? Tell me about your ideal customers - who they are, what they need, and what matters to them.",
                    'brand_voice': "How would you describe your brand's personality? Think about how you want to sound when talking to your customers.",
                    'key_offer': "What makes your business special? What's the main value you provide that sets you apart?",
                    'writing_samples': "Share a few examples of your writing - social posts, emails, or website copy. This helps me match your style."
                }
                
                prompt = prompts_by_field.get(normalized, f"What would you like for your {field_display}?")
                
                return _build_response(
                    prompt,
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
                "I don't recognize that field. Which one would you like to update? You can choose from business name, industry, target audience, brand voice, key offer, or writing samples.",
                action='continue',
                pending_task={
                    'flow': 'profile_update',
                    'task_type': 'profile_update',
                    'field_name': None  # Reset to ask again
                }
            )
    else:
        # User provided new value (or accepted prefilled by hitting enter)
        prefilled = pending_task.get('prefilled_value')
        allow_skip = pending_task.get('allow_skip', False)
        
        # Check if user wants to skip (for business name confirmation)
        if allow_skip and message.lower().strip() in ['keep it', 'keep', 'no', 'skip', 'continue']:
            value_to_save = profile.business_name  # Keep existing
        elif not message.strip() and prefilled:
            value_to_save = prefilled
        else:
            value_to_save = message
        
        # Apply the profile update
        result = _apply_profile_update(profile, field_name, value_to_save, db)
        
        # Check if this was part of an import flow
        imported_url = pending_task.get('imported_url')
        extracted_data = pending_task.get('extracted_data')
        
        if imported_url and extracted_data and field_name == 'business_name':
            # We were in an import flow and just got/confirmed the business name
            # Now continue with the smart merge using the extracted data
            extracted_data['business_name'] = value_to_save  # Add the user-provided/confirmed name
            
            # Build comparisons with the complete data
            comparisons = []
            fields_to_compare = [
                ('business_name', 'Business Name', profile.business_name),
                ('industry', 'Industry', profile.industry),
                ('target_audience', 'Target Audience', profile.target_audience),
                ('brand_voice', 'Brand Voice', profile.brand_voice),
                ('key_offer', 'Key Offer', profile.key_offer),
                ('brand_keywords', 'Brand Keywords', profile.get_brand_keywords()),
                ('goals', 'Goals', profile.get_goals()),
            ]
            
            for field_key, field_label, current_value in fields_to_compare:
                # Map extracted field names to profile field names
                if field_key == 'target_audience':
                    new_value = extracted_data.get('key_customers')
                elif field_key == 'brand_voice':
                    new_value = extracted_data.get('voice_tone_and_style')
                elif field_key == 'brand_keywords':
                    new_value = extracted_data.get('brand_keywords', [])
                elif field_key == 'goals':
                    new_value = extracted_data.get('content_goals_ai', [])
                else:
                    new_value = extracted_data.get(field_key)
                
                # Format for display
                current_display = _format_field_value(current_value)
                new_display = _format_field_value(new_value)
                
                # Determine suggestion and status
                if current_value and new_value:
                    # Both have values - generate merge suggestion
                    suggestion = _generate_merge_suggestion(field_key, current_value, new_value, profile)
                    status = 'both'
                elif current_value:
                    suggestion = current_value  # Keep current
                    status = 'keep_current'
                elif new_value:
                    suggestion = new_value  # Use new
                    status = 'use_new'
                else:
                    suggestion = None
                    status = 'empty'
                
                comparisons.append({
                    'field': field_key,
                    'label': field_label,
                    'current': current_display,
                    'new': new_display,
                    'suggestion': _format_field_value(suggestion) if suggestion else "(needs input)",
                    'suggestion_value': suggestion,
                    'status': status,
                })
            
            # Build message
            message_text = f"✅ Got it! Business name saved as **{value_to_save}**.\n\n"
            message_text += f"🔍 **Here's what else I found on {imported_url}:**\n\n"
            
            has_changes = False
            for comp in comparisons:
                # Only show fields that have changes or new data (excluding business_name we just set)
                if comp['status'] in ['both', 'use_new'] and comp['field'] != 'business_name':
                    has_changes = True
                    icon = {
                        'both': '🔀',
                        'use_new': '🆕',
                    }.get(comp['status'], '📋')
                    
                    message_text += f"{icon} **{comp['label']}**\n"
                    message_text += f"   • Current: {comp['current']}\n"
                    message_text += f"   • Website: {comp['new']}\n"
                    if comp['status'] == 'both':
                        message_text += f"   • 💡 Suggested: {comp['suggestion']}\n"
                    message_text += "\n"
            
            if not has_changes:
                return _build_response(
                    f"✅ Got it! Business name saved as **{value_to_save}**.\n\n"
                    f"I checked {imported_url} and didn't find any other new information. Your profile is up to date!",
                    action='continue',
                    suggestions=['Create content', 'View my profile']
                )
            
            message_text += "---\n**What would you like to do?**"
            
            return _build_response(
                message_text,
                action='continue',
                pending_task={
                    'flow': 'import_merge',
                    'task_type': 'import_merge',
                    'comparisons': comparisons,
                    'url': imported_url,
                },
                suggestions=['Accept all suggestions', 'Review each field', 'Cancel']
            )
        
        return result




def _format_field_value(value) -> str:
    """Format a field value for display in merge comparison.
    
    Args:
        value: The value to format (string, list, or None)
        
    Returns:
        Formatted string for display
    """
    if value is None:
        return "(empty)"
    
    if isinstance(value, list):
        if not value:
            return "(empty)"
        # Format list items
        if len(value) <= 3:
            return ", ".join(str(v) for v in value)
        else:
            return ", ".join(str(v) for v in value[:3]) + f" (+{len(value)-3} more)"
    
    if isinstance(value, str):
        if not value.strip():
            return "(empty)"
        # Truncate long strings
        if len(value) > 150:
            return value[:150] + "..."
        return value
    
    return str(value)


# Constants for merge suggestion limits
MAX_BRAND_KEYWORDS = 10
MAX_GOALS = 5
MAX_VOICE_DESCRIPTORS = 5


def _text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity ratio using word overlap.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Float between 0.0 and 1.0 representing Jaccard similarity
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity (intersection / union)
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def _fallback_text_merge(field: str, current: str, new: str) -> str:
    """Fallback merge when AI is unavailable.
    
    Args:
        field: Field name being merged
        current: Current value
        new: New value
        
    Returns:
        Merged text value
    """
    # Check similarity
    similarity = _text_similarity(current, new)
    
    # If very similar (>80% overlap), keep longer one
    if similarity > 0.8:
        return new if len(new) > len(current) else current
    
    # Special handling by field type
    if field == 'brand_voice':
        # For brand voice, combine descriptors with comma
        # Remove common words like "and", "but", "or"
        current_words = [w.strip() for w in current.replace(',', ' ').split() if w.lower() not in ['and', 'but', 'or', 'with']]
        new_words = [w.strip() for w in new.replace(',', ' ').split() if w.lower() not in ['and', 'but', 'or', 'with']]
        
        # Combine unique words
        combined_words = []
        seen = set()
        for word in current_words + new_words:
            if word.lower() not in seen:
                combined_words.append(word)
                seen.add(word.lower())
        
        return ', '.join(combined_words[:MAX_VOICE_DESCRIPTORS])
    
    if field in ['target_audience', 'key_offer']:
        # For target audience and key offer, combine first sentences if similar length
        current_sentences = current.split('.')
        new_sentences = new.split('.')
        
        if len(current_sentences) > 0 and len(new_sentences) > 0:
            current_first = current_sentences[0].strip()
            new_first = new_sentences[0].strip()
            
            # If both are similar length, combine them
            if abs(len(current_first) - len(new_first)) < 50:
                return f"{current_first}. {new_first}."
        
        # Otherwise prefer longer value
        return new if len(new) > len(current) else current
    
    # Default: prefer longer value
    return new if len(new) > len(current) else current


def _generate_merge_suggestion(field: str, current, new, profile: VoiceProfile):
    """Use AI or heuristics to suggest best merge of current and new values.
    
    Args:
        field: Field name being merged
        current: Current value in profile
        new: New value from scraper
        profile: VoiceProfile instance for context
        
    Returns:
        Suggested merged value
    """
    # Handle None values at the start
    if not current and not new:
        return None
    if not current:
        return new
    if not new:
        return current
    
    # For list fields, merge and dedupe
    if field in ['brand_keywords', 'goals']:
        current_list = current if isinstance(current, list) else ([current] if current else [])
        new_list = new if isinstance(new, list) else ([new] if new else [])
        # Dedupe while preserving order (case-insensitive)
        combined = []
        seen = set()
        for item in current_list + new_list:
            item_lower = str(item).lower()
            if item_lower not in seen:
                combined.append(item)
                seen.add(item_lower)
        return combined[:MAX_BRAND_KEYWORDS] if field == 'brand_keywords' else combined[:MAX_GOALS]
    
    # For text fields, try to merge intelligently
    if isinstance(current, str) and isinstance(new, str):
        # Check if values are very similar (>80% word overlap)
        similarity = _text_similarity(current, new)
        if similarity > 0.8:
            # Keep longer one
            return new if len(new) > len(current) else current
        
        # Try AI-assisted merge if available
        try:
            from services.ai_service import get_generative_model
            model = get_generative_model()
            
            if model:
                prompt = f"""Combine these two descriptions into one that captures the best of both.

Current: {current}
New from website: {new}

Return ONLY the combined description (under 200 characters), no explanation."""
                
                response = model.generate_content(prompt)
                if response and response.text:
                    merged = response.text.strip()
                    # Clean any markdown formatting
                    if merged.startswith('```'):
                        merged = merged.split('\n', 1)[1] if '\n' in merged else merged
                    if merged.endswith('```'):
                        merged = merged.rsplit('\n', 1)[0] if '\n' in merged else merged
                    return merged.strip()
        except Exception as e:
            logger.warning(f"AI merge failed for {field}: {e}")
        
        # Fall back to heuristic merge
        return _fallback_text_merge(field, current, new)
    
    # Fallback: prefer new if longer/more detailed, otherwise current
    return new if new else current


def _handle_url_import_with_merge(url: str, profile: VoiceProfile) -> dict:
    """Import from URL with smart merge to existing profile.
    
    Shows a comparison between current profile data and scraped data,
    with AI-powered suggestions for merging both.
    
    Args:
        url: The URL to scrape
        profile: VoiceProfile instance with existing data
        
    Returns:
        Response dict with comparison and action buttons
    """
    try:
        from services.scraper_service import scrape_url, extract_business_info
        
        # Scrape and extract
        scraped_text = scrape_url(url, max_length=6000)
        if not scraped_text:
            return _build_response(
                '❌ Could not access that URL. Please check the URL and try again.',
                action='error'
            )
        
        extracted = extract_business_info(scraped_text, url)
        
        # Check if business_name was not found by the scraper
        scraped_business_name = extracted.get('business_name')
        if not scraped_business_name:
            # Scraper couldn't find business name - ask user to provide it
            if profile.business_name:
                # Profile has one, but let's confirm/update it
                return _build_response(
                    f"🔍 I scanned {url} but couldn't find the business name.\n\n"
                    f"I have **{profile.business_name}** in your profile. Is that correct, or would you like to update it?\n\n"
                    f"Reply with the correct business name, or say 'keep it' to proceed with what you have.",
                    action='continue',
                    pending_task={
                        'flow': 'profile_update',
                        'task_type': 'profile_update',
                        'field_name': 'business_name',
                        'imported_url': url,
                        'extracted_data': extracted,
                        'allow_skip': True  # User can say 'keep it' to skip
                    }
                )
            else:
                # No business name in profile either - must provide
                return _build_response(
                    f"🔍 I scanned {url} but couldn't find the business name.\n\n"
                    f"What's the name of your business?",
                    action='continue',
                    pending_task={
                        'flow': 'profile_update',
                        'task_type': 'profile_update',
                        'field_name': 'business_name',
                        'imported_url': url,
                        'extracted_data': extracted
                    }
                )
        
        # Build comparison for each field
        comparisons = []
        fields_to_compare = [
            ('business_name', 'Business Name', profile.business_name),
            ('industry', 'Industry', profile.industry),
            ('target_audience', 'Target Audience', profile.target_audience),
            ('brand_voice', 'Brand Voice', profile.brand_voice),
            ('key_offer', 'Key Offer', profile.key_offer),
            ('brand_keywords', 'Brand Keywords', profile.get_brand_keywords()),
            ('goals', 'Goals', profile.get_goals()),
        ]
        
        for field_key, field_label, current_value in fields_to_compare:
            # Map extracted field names to profile field names
            if field_key == 'target_audience':
                new_value = extracted.get('key_customers')
            elif field_key == 'brand_voice':
                new_value = extracted.get('voice_tone_and_style')
            elif field_key == 'brand_keywords':
                new_value = extracted.get('brand_keywords', [])
            elif field_key == 'goals':
                new_value = extracted.get('content_goals_ai', [])
            else:
                new_value = extracted.get(field_key)
            
            # Format for display
            current_display = _format_field_value(current_value)
            new_display = _format_field_value(new_value)
            
            # Determine suggestion and status
            if current_value and new_value:
                # Both have values - generate merge suggestion
                suggestion = _generate_merge_suggestion(field_key, current_value, new_value, profile)
                status = 'both'
            elif current_value:
                suggestion = current_value  # Keep current
                status = 'keep_current'
            elif new_value:
                suggestion = new_value  # Use new
                status = 'use_new'
            else:
                suggestion = None
                status = 'empty'
            
            comparisons.append({
                'field': field_key,
                'label': field_label,
                'current': current_display,
                'new': new_display,
                'suggestion': _format_field_value(suggestion) if suggestion else "(needs input)",
                'suggestion_value': suggestion,  # Store actual value for later
                'status': status,
            })
        
        # Build message
        message = f"🔍 **Comparing your profile with {url}**\n\n"
        
        has_changes = False
        for comp in comparisons:
            # Only show fields that have changes or new data
            if comp['status'] in ['both', 'use_new']:
                has_changes = True
                icon = {
                    'both': '🔀',
                    'use_new': '🆕',
                }.get(comp['status'], '📋')
                
                message += f"{icon} **{comp['label']}**\n"
                message += f"   • Current: {comp['current']}\n"
                message += f"   • Website: {comp['new']}\n"
                if comp['status'] == 'both':
                    message += f"   • 💡 Suggested: {comp['suggestion']}\n"
                message += "\n"
        
        if not has_changes:
            return _build_response(
                f"✅ I checked {url} and your profile is already up to date!\n\n"
                f"No new information found. Your existing profile data looks good.",
                action='continue',
                suggestions=['Create content', 'View my profile']
            )
        
        message += "---\n**What would you like to do?**"
        
        return _build_response(
            message,
            action='continue',
            pending_task={
                'flow': 'import_merge',
                'task_type': 'import_merge',
                'comparisons': comparisons,
                'url': url,
            },
            suggestions=['Accept all suggestions', 'Review each field', 'Cancel']
        )
        
    except Exception as e:
        logger.error(f"Error in URL import with merge: {e}", exc_info=True)
        return _build_response(
            f"I had trouble processing that URL. Error: {str(e)}",
            action='error'
        )


def _handle_url_update(url: str, profile: VoiceProfile, db) -> dict:
    """Handle updating profile from a URL by scraping and showing changes.
    
    Args:
        url: The URL to scrape
        profile: VoiceProfile instance to update
        db: Database session
        
    Returns:
        Response dict with changes preview or error
    """
    try:
        # Use the onboarding service to scrape the URL
        from services.onboarding_service import OnboardingService
        onboarding_service = OnboardingService()
        
        # Show scanning message
        logger.info(f"Scanning URL for profile update: {url}")
        
        # Scrape the URL (don't update profile yet)
        result = onboarding_service.process_url(url, profile)
        
        if not result['success']:
            return _build_response(
                result['message'],
                action='error'
            )
        
        extracted_fields = result.get('extracted_fields', {})
        
        if not extracted_fields:
            return _build_response(
                f"🔍 I scanned {url} but couldn't find any new information to update.\n\n"
                f"Your profile is already up to date! ✨",
                action='continue',
                suggestions=['Update a field manually', 'Create content', 'View my profile']
            )
        
        # Build a list of changes (old value -> new value)
        changes = []
        field_labels = {
            'business_name': 'Business Name',
            'industry': 'Industry',
            'target_audience': 'Target Audience',
            'brand_voice': 'Brand Voice',
            'key_offer': 'Key Offer',
            'writing_samples': 'Writing Samples'
        }
        
        for field_name, new_value in extracted_fields.items():
            if field_name not in field_labels:
                continue
                
            # Get old value
            if field_name == 'writing_samples':
                old_samples = profile.get_writing_samples()
                old_value = f"{len(old_samples)} samples" if old_samples else None
                new_display = f"{len(new_value)} samples" if isinstance(new_value, list) else "1 sample"
            else:
                old_value = getattr(profile, field_name, None)
                # Truncate for display
                new_display = new_value[:80] + "..." if len(str(new_value)) > 80 else new_value
            
            # Only include if different from current value
            if old_value != new_value:
                changes.append({
                    'field_name': field_name,
                    'field_label': field_labels[field_name],
                    'old_value': old_value,
                    'new_value': new_value,
                    'new_display': new_display
                })
        
        if not changes:
            return _build_response(
                f"🔍 I scanned {url} and found the same information that's already in your profile.\n\n"
                f"Your profile is up to date! ✨",
                action='continue',
                suggestions=['Update a field manually', 'Create content', 'View my profile']
            )
        
        # Build confirmation message
        message_parts = [f"✨ **Found updates from {url}!**\n"]
        
        for change in changes:
            field_label = change['field_label']
            old_value = change['old_value']
            new_display = change['new_display']
            
            if old_value:
                old_display = old_value[:50] + "..." if len(str(old_value)) > 50 else old_value
                message_parts.append(f"📋 **{field_label}:** ~~{old_display}~~ → {new_display}")
            else:
                message_parts.append(f"📋 **{field_label}:** Added \"{new_display}\"")
        
        message_parts.append("\n---\n✅ Apply these changes?")
        
        # Store changes in pending task for confirmation
        return _build_response(
            '\n'.join(message_parts),
            action='continue',
            pending_task={
                'flow': 'url_update_confirmation',
                'task_type': 'update_from_url',
                'changes': changes,
                'url': url
            },
            suggestions=['Yes, apply all', 'No, cancel']
        )
        
    except Exception as e:
        logger.error(f"Error handling URL update: {e}", exc_info=True)
        return _build_response(
            f"I had trouble accessing that website. Please try again or update fields manually.",
            action='error'
        )


def _apply_url_update_changes(changes: list, profile: VoiceProfile, db) -> dict:
    """Apply the changes from URL update to the profile.
    
    Args:
        changes: List of change dicts with field_name, new_value
        profile: VoiceProfile instance to update
        db: Database session
        
    Returns:
        Response dict with confirmation message
    """
    try:
        applied_count = 0
        
        for change in changes:
            field_name = change['field_name']
            new_value = change['new_value']
            
            if field_name == 'writing_samples':
                if isinstance(new_value, list):
                    profile.set_writing_samples(new_value)
                    applied_count += 1
            elif hasattr(profile, field_name):
                setattr(profile, field_name, new_value)
                applied_count += 1
        
        db.session.commit()
        logger.info(f"Applied {applied_count} field updates from URL for user {current_user.id}")
        
        return _build_response(
            f"✅ **Profile updated!**\n\n"
            f"I've updated {applied_count} field(s) from your website.\n\n"
            f"Your profile now reflects your latest brand information. Ready to create something?",
            action='profile_updated',
            suggestions=['Create content', 'View my profile', 'Update another field']
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying URL updates: {e}", exc_info=True)
        return _build_response(
            "I had trouble saving those updates. Please try again.",
            action='error'
        )


def _apply_import_merge_suggestions(comparisons: list, profile: VoiceProfile, db) -> dict:
    """Apply the merge suggestions to the profile.
    
    Args:
        comparisons: List of comparison dicts with field, suggestion_value
        profile: VoiceProfile instance to update
        db: Database session
        
    Returns:
        Response dict with confirmation message
    """
    try:
        applied_count = 0
        
        for comp in comparisons:
            field = comp['field']
            suggestion = comp.get('suggestion_value')
            
            # Skip if no suggestion or if keeping current (status: keep_current)
            if not suggestion or comp['status'] == 'keep_current':
                continue
            
            # Apply the suggestion based on field type
            if field == 'brand_keywords':
                if isinstance(suggestion, list):
                    profile.set_brand_keywords(suggestion)
                    applied_count += 1
            elif field == 'goals':
                if isinstance(suggestion, list):
                    profile.set_goals(suggestion)
                    applied_count += 1
            elif hasattr(profile, field):
                setattr(profile, field, suggestion)
                applied_count += 1
        
        db.session.commit()
        logger.info(f"Applied {applied_count} merge suggestions for user {current_user.id}")
        
        return _build_response(
            f"✅ **Profile updated with smart merge!**\n\n"
            f"I've updated {applied_count} field(s) by combining your existing data with what I found on the website.\n\n"
            f"Your profile now has the best of both worlds. Ready to create something?",
            action='profile_updated',
            suggestions=['Create content', 'View my profile']
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying merge suggestions: {e}", exc_info=True)
        return _build_response(
            "I had trouble saving those updates. Please try again.",
            action='error'
        )


def _handle_field_assistance(field: str, profile: VoiceProfile) -> dict:
    """Handle AI-assisted field completion with suggestions.
    
    This is called when user sends a bare field command like `/keywords`
    or existing commands like `/voice` without providing a value. 
    The system should provide AI-generated suggestions based on their profile data.
    
    Args:
        field: The field name (e.g., 'brand_keywords', 'goals', 'brand_voice', 'target_audience')
        profile: VoiceProfile instance with business context
        
    Returns:
        Response dict with AI suggestions
    """
    try:
        # Map internal field names to user-friendly names
        field_display_names = {
            'business_name': 'Business Name',
            'industry': 'Industry',
            'brand_keywords': 'Brand Keywords',
            'goals': 'Goals',
            'key_offer': 'Key Offer',
            'brand_voice': 'Brand Voice',
            'target_audience': 'Target Audience',
            'writing_samples': 'Writing Samples',
        }
        
        field_display = field_display_names.get(field, field.replace('_', ' ').title())
        
        # For now, provide guidance to enter the value directly
        # In the future, this could use AI to generate suggestions
        prompts_by_field = {
            'business_name': "What's the name of your business?",
            'industry': "What industry are you in? (e.g., Restaurant, Fitness, Software, Healthcare)",
            'brand_keywords': "What keywords describe your brand? (e.g., Fresh, Local, Organic)",
            'goals': "What are your main business goals? (e.g., Increase awareness, Drive sales, Build community)",
            'key_offer': "What's your main value proposition? What makes you unique?",
            'brand_voice': "How would you describe your brand's personality? Think about how you want to sound when talking to your customers.",
            'target_audience': "Who are you trying to reach? Tell me about your ideal customers - who they are, what they need, and what matters to them.",
            'writing_samples': "Share a few examples of your writing - social posts, emails, or website copy. This helps me match your style.",
        }
        
        prompt = prompts_by_field.get(field, f"What would you like for your {field_display}?")
        
        return _build_response(
            f"Let's set up your **{field_display}**.\n\n{prompt}",
            action='continue',
            pending_task={
                'flow': 'field_update',
                'task_type': 'field_assistance',
                'field': field
            }
        )
        
    except Exception as e:
        logger.error(f"Error in field assistance: {e}", exc_info=True)
        return _build_response(
            "I had trouble with that. Please try again.",
            action='error'
        )


def _handle_update_field(field: str, value: str, profile: VoiceProfile, db) -> dict:
    """Handle direct field update with provided value.
    
    This is called when user sends a field command with a value,
    like `/keywords Fresh, Local, Organic` or `/voice warm and friendly`.
    
    Args:
        field: The field name (e.g., 'brand_keywords', 'goals', 'brand_voice', 'target_audience')
        value: The value to set
        profile: VoiceProfile instance
        db: Database session
        
    Returns:
        Response dict with confirmation
    """
    try:
        # Map field names to profile attributes
        # Include both NEW fields and EXISTING fields
        field_mapping = {
            'business_name': 'business_name',
            'industry': 'industry',
            'key_offer': 'key_offer',
            'brand_keywords': 'brand_keywords',  # May need to add this field
            'goals': 'goals',  # May need to add this field
            'brand_voice': 'brand_voice',  # EXISTING field
            'target_audience': 'target_audience',  # EXISTING field
        }
        
        # Special handling for writing_samples
        if field == 'writing_samples':
            current_samples = profile.get_writing_samples() or []
            current_samples.append(value.strip())
            profile.set_writing_samples(current_samples)
            
            try:
                db.session.commit()
                logger.info(f"Added writing sample via field command")
                
                return _build_response(
                    f"✅ **Writing Sample added!**\n\n"
                    f"I've saved your sample ({len(current_samples)} total).\n\n"
                    f"This will help me match your style when creating content. Ready to create something?",
                    action='profile_updated',
                    suggestions=['Create content', 'Add another sample', 'View my profile']
                )
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error saving writing sample: {db_error}", exc_info=True)
                return _build_response(
                    "I had trouble saving that sample. Please try again.",
                    action='error'
                )
        
        profile_field = field_mapping.get(field)
        
        if not profile_field:
            return _build_response(
                f"I don't know how to update the field '{field}' yet. Please use the existing profile update commands.",
                action='error'
            )
        
        # Check if profile has this attribute
        if not hasattr(profile, profile_field):
            logger.warning(f"Profile does not have field '{profile_field}' - would need schema update")
            return _build_response(
                f"The '{field}' field isn't available yet. Please use existing profile fields like business name, industry, or key offer.",
                action='continue',
                suggestions=['Update brand voice', 'Update target audience', 'View my profile']
            )
        
        # Validate the value
        if not value or len(value.strip()) < 2:
            return _build_response(
                "Please provide a more detailed value.",
                action='error'
            )
        
        # Set the field value
        setattr(profile, profile_field, value.strip())
        
        try:
            db.session.commit()
            logger.info(f"Updated field '{profile_field}' via field command")
            
            field_display = field.replace('_', ' ').title()
            
            return _build_response(
                f"✅ **{field_display} updated!**\n\n"
                f"I've saved: {value[:100]}{'...' if len(value) > 100 else ''}\n\n"
                f"This will help me create better content for you. Ready to create something?",
                action='profile_updated',
                suggestions=['Create content', 'Update another field', 'View my profile']
            )
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error updating field: {db_error}", exc_info=True)
            return _build_response(
                "I had trouble saving that update. Please try again.",
                action='error'
            )
        
    except Exception as e:
        logger.error(f"Error updating field: {e}", exc_info=True)
        return _build_response(
            "I had trouble updating that field. Please try again.",
            action='error'
        )


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
    # Handle import merge confirmation
    if pending_task and pending_task.get('flow') == 'import_merge':
        message_lower = message.lower().strip()
        
        # Check for affirmative responses (accept suggestions)
        if any(word in message_lower for word in ['yes', 'accept', 'apply', 'confirm', 'ok', 'sure', 'do it', 'all']):
            comparisons = pending_task.get('comparisons', [])
            return _apply_import_merge_suggestions(comparisons, profile, db)
        
        # Check for negative responses
        if any(word in message_lower for word in ['no', 'cancel', 'skip', 'nevermind']):
            return _build_response(
                "No problem! Your profile hasn't been changed.\n\n"
                "Want to try importing from a different URL?",
                action='continue',
                suggestions=['Try another URL', 'View my profile', 'Create content']
            )
        
        # Check for review request
        if any(word in message_lower for word in ['review', 'check', 'each', 'field', 'one']):
            return _build_response(
                "Field-by-field review isn't implemented yet. For now, you can:\n\n"
                "• **Accept all** suggestions to merge your profile\n"
                "• **Cancel** and keep your current profile\n"
                "• Update specific fields manually using `/update`\n\n"
                "What would you like to do?",
                action='continue',
                pending_task=pending_task,
                suggestions=['Accept all suggestions', 'Cancel']
            )
        
        # Ambiguous response - ask again
        return _build_response(
            "Would you like me to apply these merge suggestions?\n\n"
            "Reply 'accept all' to apply the suggested changes, or 'cancel' to keep your current profile.",
            action='continue',
            pending_task=pending_task
        )
    
    # Handle URL update confirmation
    if pending_task and pending_task.get('flow') == 'url_update_confirmation':
        message_lower = message.lower().strip()
        
        # Check for affirmative responses
        if any(word in message_lower for word in ['yes', 'apply', 'confirm', 'ok', 'sure', 'do it']):
            changes = pending_task.get('changes', [])
            return _apply_url_update_changes(changes, profile, db)
        
        # Check for negative responses
        if any(word in message_lower for word in ['no', 'cancel', 'skip', 'nevermind']):
            return _build_response(
                "No problem! Your profile hasn't been changed.\n\n"
                "Want to update a specific field instead?",
                action='continue',
                suggestions=['Update brand voice', 'Update target audience', 'View my profile']
            )
        
        # Ambiguous response - ask again
        return _build_response(
            "Would you like me to apply these updates?\n\n"
            "Reply 'yes' to apply all changes, or 'no' to cancel.",
            action='continue',
            pending_task=pending_task
        )
    
    if pending_task and pending_task.get('flow') == 'profile_update':
        return _continue_profile_update(pending_task, message, profile, db)
    
    # Parse the intent for profile updates
    intent_result = conversation_router.parse_intent(message, profile)
    
    # Note: guidance_needed is handled at a higher level now, so we don't need to check here
    
    if intent_result['task_type'] == 'profile':
        # Show profile summary
        return _show_profile_summary(profile)
    
    # Handle writing samples collection
    if intent_result['task_type'] == 'update_samples':
        extracted = intent_result.get('extracted_params', {})
        sample_text = extracted.get('sample_text')
        
        if sample_text:
            # Direct update - use field update handler for consistency
            return _handle_update_field('writing_samples', sample_text, profile, db)
        else:
            # No value provided - use NEW field assistance flow
            return _handle_field_assistance('writing_samples', profile)
    
    # Handle URL import (note: actual import is handled client-side via /onboarding/social-style)
    if intent_result['task_type'] == 'import_profile':
        extracted = intent_result.get('extracted_params', {})
        url = extracted.get('url')
        
        if url:
            # Return message indicating client should handle this
            return _build_response(
                f"Please use the `/import {url}` command in the chat interface to import from that URL.",
                action='continue',
                suggestions=['Try the /import command']
            )
        else:
            return _build_response(
                "Please provide a URL to import from:\n\n"
                "Example: `/import https://yourwebsite.com`",
                action='continue'
            )
    
    # Handle URL update - use smart merge flow
    if intent_result['task_type'] == 'update_from_url':
        extracted = intent_result.get('extracted_params', {})
        url = extracted.get('url')
        
        if url:
            # Use the new smart merge flow instead of simple overwrite
            return _handle_url_import_with_merge(url, profile)
        else:
            return _build_response(
                "Please provide a URL to update from:\n\n"
                "Example: `/update https://yourwebsite.com`",
                action='continue'
            )
    
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
            # Use the NEW field assistance flow for existing commands when no value provided
            # This integrates AI-powered suggestions into existing /voice and /audience commands
            return _handle_field_assistance(field_name, profile)
        
        # No field specified - ask which field
        return _build_response(
            "Which part of your profile would you like to update? I can help you with:\n\n"
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


def _handle_export(message: str, profile: VoiceProfile) -> dict:
    """Handle export command to download generated content.
    
    Args:
        message: User's message containing export command
        profile: User's voice profile
        
    Returns:
        Response dictionary with export options
    """
    from datetime import datetime, timedelta
    import json
    
    message_lower = message.lower().strip()
    
    # Check for batch export options (future feature for paid tier)
    if 'all' in message_lower:
        return _build_response(
            "💾 **Export All Starred Content**\n\nThis feature is available for Pro users. "
            "Upgrade your account to export all starred content in one file.\n\n"
            "Meanwhile, you can export your last generated content with `/export`.",
            action='continue'
        )
    
    if 'week' in message_lower:
        return _build_response(
            "💾 **Export Last 7 Days**\n\nThis feature is available for Pro users. "
            "Upgrade your account to export content from the last week.\n\n"
            "Meanwhile, you can export your last generated content with `/export`.",
            action='continue'
        )
    
    # For basic export, we need the last generated content
    # In a real implementation, we'd fetch this from session or database
    # For now, we'll provide instructions for the user
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Create export metadata
    export_data = {
        'date': current_date,
        'business_name': profile.business_name if profile else 'Unknown',
        'platform': 'N/A',  # Would be populated from last generation
        'content_note': 'Export your last generated content by clicking Copy, then save to a file.'
    }
    
    response_text = f"""💾 **Export Content**

**Export Options:**
- Copy the generated content above and save it to a file
- Use the Copy button to get the content to clipboard
- Format: Plain text (.txt) or Markdown (.md)

**Metadata:**
- Date: {export_data['date']}
- Business: {export_data['business_name']}

_Pro tip: Save exports with descriptive filenames like `instagram-post-{current_date}.txt`_

**Coming Soon:**
- `/export all` - Export all starred content
- `/export week` - Export last 7 days
- Automatic download feature"""
    
    return _build_response(
        response_text,
        action='continue',
        suggestions=['Create new content', 'Try /post', 'Try /caption']
    )


def _handle_preview(profile: VoiceProfile) -> dict:
    """Handle preview command to show content mockup.
    
    Args:
        profile: User's voice profile
        
    Returns:
        Response dictionary with preview
    """
    # For now, provide information about the preview feature
    response_text = """👁️ **Content Preview**

**How to Preview:**
1. Generate your content (post, caption, email, etc.)
2. Use the Copy button to copy it
3. Preview in your platform's composer or use a preview tool

**Platform-Specific Preview Tools:**
- Instagram: Use Stories drafts or preview in Creator Studio
- LinkedIn: Post composer has built-in preview
- Facebook: Business Suite preview feature
- Twitter/X: Character counter in composer

**Coming Soon:**
- Live platform previews directly in Eazeily
- Character count and hashtag validation
- Visual mockups for different platforms
- Preview how content looks on mobile vs desktop

_Try generating content with `/post`, `/caption`, or `/email` to see it in action!_"""
    
    return _build_response(
        response_text,
        action='continue',
        suggestions=['Create a post', 'Try /post', 'Try /caption']
    )


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
        profile_ready, missing_fields, completeness = _check_profile_ready(profile)
        
        # Handle pending task based on flow type
        if pending_task:
            task_type = pending_task.get('task_type')
            flow = pending_task.get('flow')
            
            # Auto-detect flow if not specified based on task_type
            if not flow:
                if task_type == 'onboarding':
                    flow = 'onboarding'
                elif task_type in ['profile', 'profile_update', 'update_voice', 'update_audience', 'update_from_url']:
                    flow = 'profile_update'
                else:
                    # If profile is complete and task_type is a content type, assume content flow
                    content_task_types = ['post', 'caption', 'script', 'email', 'review', 'ad', 'blog', 'reel', 'custom']
                    if profile_ready and task_type in content_task_types:
                        flow = 'content'
                    else:
                        flow = 'onboarding'
            
            logger.info(f"[{request_id}] Continuing {flow} flow for task: {task_type}")
            
            if flow in ['profile_update', 'url_update_confirmation', 'import_merge']:
                # Continue profile update flow (includes import merge)
                result = _handle_profile_update(message, pending_task, profile, db)
                return jsonify(result), 200
            elif flow == 'field_update':
                # Continue field update flow (for new FIELD_COMMANDS)
                field = pending_task.get('field')
                if field:
                    result = _handle_update_field(field, message, profile, db)
                    return jsonify(result), 200
                else:
                    return jsonify(_build_response(
                        "I lost track of which field we were updating. Please try again.",
                        action='error'
                    )), 500
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
        
        # Check if this command needs guidance (bare command without arguments)
        # Show guidance but don't stop processing - continue to the actual handler
        if intent_result.get('needs_guidance'):
            from services.conversation_router import get_command_guidance
            command = intent_result.get('command')
            if command:
                guidance = get_command_guidance(command)
                # For commands in COMMANDS_WITHOUT_GUIDANCE, let their handlers provide guidance
                if guidance and command not in COMMANDS_WITHOUT_GUIDANCE:
                    return jsonify(_build_response(guidance, action='continue')), 200
        
        # Handle profile-related intents (including new commands)
        if intent_result['task_type'] in ['profile', 'profile_update', 'update_voice', 'update_audience', 'update_samples', 'import_profile', 'update_from_url']:
            logger.info(f"[{request_id}] Handling profile update request")
            result = _handle_profile_update(message, None, profile, db)
            return jsonify(result), 200
        
        # Handle NEW field assistance flow (from FIELD_COMMANDS)
        if intent_result['task_type'] == 'field_assistance':
            logger.info(f"[{request_id}] Handling field assistance request")
            field = intent_result.get('field')
            if field:
                result = _handle_field_assistance(field, profile)
                return jsonify(result), 200
            else:
                return jsonify(_build_response(
                    "I'm not sure which field you want to update. Try using a command like /keywords or /goals.",
                    action='error'
                )), 400
        
        # Handle NEW direct field update (from FIELD_COMMANDS with value)
        if intent_result['task_type'] == 'update_field':
            logger.info(f"[{request_id}] Handling direct field update")
            field = intent_result.get('field')
            value = intent_result.get('value')
            if field and value:
                result = _handle_update_field(field, value, profile, db)
                return jsonify(result), 200
            else:
                return jsonify(_build_response(
                    "I need both a field name and a value to update. Try using /keywords Fresh, Local.",
                    action='error'
                )), 400
        
        # Handle export command
        if intent_result['task_type'] == 'export':
            logger.info(f"[{request_id}] Handling export request")
            result = _handle_export(message, profile)
            return jsonify(result), 200
        
        # Handle preview command
        if intent_result['task_type'] == 'preview':
            logger.info(f"[{request_id}] Handling preview request")
            result = _handle_preview(profile)
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
