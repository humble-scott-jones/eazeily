from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.voice_engine import VoiceEngine
from services.task_registry import get_task_config, list_task_types
from services.profile_validator import get_profile_completeness, format_missing_fields_message
from models import VoiceProfile
import os
import logging

logger = logging.getLogger(__name__)
generate_bp = Blueprint('generate', __name__)
voice_engine = VoiceEngine()

@generate_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Dashboard route with new user detection for chat-based onboarding."""
    # Check if user is new (no profile or incomplete basic info)
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    is_new_user = profile is None or not profile.business_name
    
    return render_template('dashboard.html', is_new_user=is_new_user, profile=profile)

@generate_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """Settings page - redirects to profile editing form."""
    from flask import redirect, url_for
    return redirect(url_for('profile.profile_page'))


@generate_bp.route('/api/model-ready', methods=['GET'])
def model_ready():
    """Health check endpoint to verify AI model/provider is configured.
    
    Returns:
    - 200 if model is ready
    - 503 if model is not configured
    """
    genai_key = os.getenv("GENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    if not genai_key and not google_key:
        return jsonify({
            "ok": False,
            "ready": False,
            "error": "AI service is not configured. Set GENAI_API_KEY or GOOGLE_API_KEY environment variable."
        }), 503
    
    # Determine which provider is configured
    provider = "gemini" if genai_key else "google"
    
    return jsonify({
        "ok": True,
        "ready": True,
        "provider": provider
    }), 200


def _missing(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _error_response(code: str, message: str, http_status: int = 400, **extra):
    payload = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
        }
    }
    if extra:
        payload["error"].update(extra)
    return jsonify(payload), http_status


def _handle_multi_day_generation(data):
    """Handle multi-day content plan generation.
    
    Expected payload:
    - days: number of days to generate
    - platforms: list of platform keys
    - tone: brand tone
    - goals: list of marketing goals
    - brand_keywords: list of brand keywords
    - niche_keywords: list of niche keywords (optional)
    - details: dict of additional details (e.g., reel_style, reel_length)
    - company: company name
    - industry: industry/vertical
    - include_images: bool
    - variant_types: list (optional)
    - image_data_url: base64 image data (optional)
    - image_context: description of image (optional)
    """
    import uuid
    request_id = str(uuid.uuid4())
    
    logger.info(
        "multi_day_generation.start",
        extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "days": data.get('days', 1),
            "platforms": data.get('platforms', []),
        }
    )
    
    # Check if API key is configured
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning(
            "multi_day_generation.missing_api_key",
            extra={"request_id": request_id, "user_id": current_user.id}
        )
        return _error_response(
            "missing_api_key",
            "AI service is not configured. Set GENAI_API_KEY or GOOGLE_API_KEY environment variable.",
            503,
        )
    
    # Extract and validate required fields
    days = data.get('days', 1)
    platforms = data.get('platforms', [])
    
    if not platforms or len(platforms) == 0:
        logger.warning(
            "multi_day_generation.missing_platforms",
            extra={"request_id": request_id, "user_id": current_user.id}
        )
        return _error_response(
            "missing_platforms",
            "At least one platform is required.",
            400,
        )
    
    # Build complete payload with defaults
    from datetime import date
    from generator import generate_posts
    
    # Get user profile for defaults
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    
    # Check if profile exists
    if not profile:
        logger.warning(
            "multi_day_generation.missing_profile",
            extra={"request_id": request_id, "user_id": current_user.id}
        )
        return _error_response(
            "profile_missing",
            "Please complete your brand profile before generating content.",
            400,
            redirect="/profile"
        )
    
    # Check profile completeness
    is_complete, missing_fields, completeness = get_profile_completeness(profile)
    
    # If profile is incomplete (missing required fields), block generation
    if not is_complete:
        logger.warning(
            "multi_day_generation.incomplete_profile",
            extra={
                "request_id": request_id,
                "user_id": current_user.id,
                "missing_fields": missing_fields,
                "completeness": completeness
            }
        )
        return _error_response(
            "profile_incomplete",
            f"Your profile is missing: {format_missing_fields_message(missing_fields)}. Please complete your profile for better content.",
            400,
            missing_fields=missing_fields,
            completeness=completeness,
            redirect="/profile"
        )
    
    try:
        # Call generator with complete payload
        posts = generate_posts(
            days=days,
            start_day=date.today(),
            industry=data.get('industry') or (profile.industry if profile else 'Business'),
            tone=data.get('tone') or (profile.brand_voice if profile else 'friendly'),
            platforms=platforms,
            brand_keywords=data.get('brand_keywords', []),
            include_images=data.get('include_images', False),
            niche_keywords=data.get('niche_keywords', []),
            goals=data.get('goals', []),
            details=data.get('details', {}),
            company=data.get('company') or (profile.business_name if profile else ''),
            voice_profile=profile.get_defaults() if profile else None,
            profile=profile,
            variant_types=data.get('variant_types', [])
        )
        
        logger.info(
            "multi_day_generation.success",
            extra={
                "request_id": request_id,
                "user_id": current_user.id,
                "posts_generated": len(posts),
            }
        )
        
        # Build response
        response = {
            "ok": True,
            "count": len(posts),
            "posts": posts,
            "days": days,
            "platforms": platforms,
            "request_id": request_id,
        }
        
        # Add warning for low profile completeness
        if completeness < 80:
            response['warnings'] = [{
                'code': 'low_profile_completeness',
                'message': f'Your profile is {completeness}% complete. Add {format_missing_fields_message(missing_fields)} for better results.',
                'missing_fields': missing_fields
            }]
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(
            "multi_day_generation.failed",
            extra={
                "request_id": request_id,
                "user_id": current_user.id,
                "error": str(e),
            },
            exc_info=True
        )
        return _error_response(
            "generation_failed",
            f"Content generation failed: {str(e)}",
            500,
        )


def _handle_generate(task_type, data):
    """Handle content generation with optimized database access and structured API calls.
    
    This function:
    1. Validates inputs efficiently
    2. Fetches profile data in a single optimized query
    3. Structures context data for the AI model
    4. Returns clean, copy-paste-ready content
    """
    task_cfg = get_task_config(task_type)
    if not task_cfg:
        return _error_response(
            "invalid_task_type",
            f"Unsupported task_type '{task_type}'.",
            400,
            allowed=list_task_types(),
        )

    topic = (data.get('topic') or '').strip()
    platform = (data.get('platform') or '').strip()

    if _missing(topic):
        return _error_response("missing_topic", "Topic is required.")

    if task_cfg.require_platform and _missing(platform):
        return _error_response("platform_required", "Platform is required for this task.")

    # Check if API key is configured
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return _error_response(
            "missing_api_key",
            "AI service is not configured. Set GENAI_API_KEY or GOOGLE_API_KEY.",
            503,
        )

    # OPTIMIZED: Fetch user profile with all needed data in a single query
    # Using select load to ensure all profile fields are loaded efficiently
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    
    # Check if profile exists
    if not profile:
        logger.warning(f"User {current_user.id} attempted generation without a brand profile")
        return _error_response(
            "profile_missing",
            "Please complete your brand profile before generating content.",
            400,
            redirect="/profile"
        )
    
    # Check profile completeness
    is_complete, missing_fields, completeness = get_profile_completeness(profile)
    
    # If profile is incomplete (missing required fields), block generation
    if not is_complete:
        logger.warning(f"User {current_user.id} has incomplete profile: missing {missing_fields}, completeness: {completeness}%")
        return _error_response(
            "profile_incomplete",
            f"Your profile is missing: {format_missing_fields_message(missing_fields)}. Please complete your profile for better content.",
            400,
            missing_fields=missing_fields,
            completeness=completeness,
            redirect="/profile"
        )
    
    logger.debug(f"Loaded profile for user {current_user.id} with brand: {profile.business_name}, completeness: {completeness}%")

    # STRUCTURED CONTEXT: Extract and validate dynamic input context
    context = {}
    
    # Handle image data for caption task
    if task_type == 'caption':
        image_data = data.get('image_data')
        if image_data and isinstance(image_data, str):
            # Validate base64 image data format
            if image_data.startswith('data:image/'):
                context['image_data'] = image_data
                context['image_filename'] = data.get('image_filename', 'uploaded_image')
                logger.info(f"Image data received for caption generation (user {current_user.id})")
            else:
                logger.warning(f"Invalid image_data format for caption (user {current_user.id})")
    
    # Map of dynamic fields with their validation/cleaning
    dynamic_field_processors = {
        'ad_objective': lambda v: v if v in ['traffic', 'awareness', 'leads', 'conversions', 'engagement'] else None,
        'target_audience': lambda v: v[:200] if v else None,  # Limit length
        'tone_modifier': lambda v: v if v in ['thought-leadership', 'personal-story', 'company-update', 'hiring'] else None,
        'cta': lambda v: v[:100] if v else None,  # Limit length
        'mood': lambda v: v if v in ['inspiring', 'casual', 'educational', 'behind-the-scenes'] else None,
        'video_length': lambda v: v if v in ['15', '30', '60', '90'] else None,
        # Email-specific fields
        'email_subtype': lambda v: v if v in ['newsletter', 'standard'] else 'standard',
        'email_context': lambda v: v[:2000] if v else None,  # Limit length for existing email
        # Proposal-specific fields
        'proposal_type': lambda v: v if v in ['partnership', 'sponsorship', 'funding', 'rfp_response', 'collaboration'] else None,
        'recipient': lambda v: v[:200] if v else None,
        'key_benefits': lambda v: v if isinstance(v, list) else None,
        'budget_range': lambda v: v[:100] if v else None,
        'proposal_company': lambda v: v[:200] if v else None,
        'proposal_contact_name': lambda v: v[:150] if v else None,
        'proposal_contact_email': lambda v: v[:200] if v and '@' in v else None,
        'proposal_industry': lambda v: v[:120] if v else None,
        'proposal_goals': lambda v: v[:1200] if v else None,
        'proposal_scope': lambda v: v[:1200] if v else None,
        'proposal_timeline': lambda v: v[:200] if v else None,
        'proposal_budget': lambda v: v[:120] if v else None,
        'proposal_audience': lambda v: v[:400] if v else None,
        'proposal_value_prop': lambda v: v[:400] if v else None,
        'proposal_keywords': lambda v: v if isinstance(v, list) else None,
        'proposal_primary_cta': lambda v: v[:150] if v else None,
        # Review reply-specific fields
        'review_source': lambda v: v[:100] if v else None,
        'star_rating': lambda v: v if v in ['1', '2', '3', '4', '5'] else None,
        'sentiment': lambda v: v if v in ['positive', 'neutral', 'negative'] else None,
        'issue_type': lambda v: v if v in ['shipping', 'product', 'experience', 'service'] else None,
        'desired_tone': lambda v: v if v in ['apologetic', 'grateful', 'professional', 'empathetic'] else None,
        'follow_up_action': lambda v: v[:200] if v else None,
        # Blog post-specific fields
        'post_type': lambda v: v if v in ['listicle', 'how-to', 'announcement', 'thought-leadership', 'case-study'] else None,
        'desired_length': lambda v: v if v in ['short', 'medium', 'long'] else None,
        'audience': lambda v: v[:100] if v else None,
        'seo_keywords': lambda v: v if isinstance(v, list) else None,
    }
    
    for field, processor in dynamic_field_processors.items():
        value = data.get(field)
        if value:
            processed_value = processor(value)
            if processed_value:
                context[field] = processed_value

    try:
        # STRUCTURED API CALL: Pass all context to the voice engine
        # The voice engine now builds a comprehensive, structured prompt
        # using profile data (writing samples, brand keywords, voice rules, etc.)
        content = voice_engine.generate_expert_content(
            profile, 
            topic, 
            task_type, 
            platform, 
            **context
        )

        if isinstance(content, str) and content.startswith("Error"):
            logger.error(f"Content generation failed: {content}")
            return _error_response(
                "generation_failed",
                "Failed to generate content. Check your API key and try again.",
                500,
            )

        # CLEAN RESPONSE: Return structured, copy-paste-ready content
        response_payload = {
            "content": content,
            "status": "success",
            "task_type": task_type,
            "platform": platform,
        }
        
        # Add warning for low profile completeness
        if completeness < 80:
            response_payload['warnings'] = [{
                'code': 'low_profile_completeness',
                'message': f'Your profile is {completeness}% complete. Add {format_missing_fields_message(missing_fields)} for better results.',
                'missing_fields': missing_fields
            }]
        
        return jsonify(response_payload)
    except Exception as e:
        logger.error(f"Exception during content generation: {str(e)}", exc_info=True)
        return _error_response(
            "exception",
            f"An error occurred while generating content: {str(e)}",
            500,
        )


@generate_bp.route('/api/generate', methods=['POST'])
@login_required
def generate():
    """Handle content generation requests.
    
    Supports two modes:
    1. Multi-day content plan generation (when 'days' param is present)
    2. Single task generation (when 'task_type' param is present)
    """
    data = request.get_json(silent=True) or {}
    
    # Check if this is a multi-day plan request
    if 'days' in data:
        return _handle_multi_day_generation(data)
    
    # Otherwise, handle as single task generation
    task_type = data.get('task_type', 'post')
    return _handle_generate(task_type, data)


@generate_bp.route('/api/generate/<task_type>', methods=['POST'])
@login_required
def generate_task(task_type):
    data = request.get_json(silent=True) or {}
    return _handle_generate(task_type, data)


@generate_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Handle conversational chat requests from PromptBox component.
    
    Accepts:
    - message: User's message
    - history: Conversation history array
    - pending_task: Any pending task state
    - context: 'dashboard' or 'onboarding'
    
    Returns mock responses for now (as per spec - actual AI integration in parallel task)
    """
    try:
        data = request.get_json(silent=True) or {}
        message = data.get('message', '').strip()
        pending_task = data.get('pending_task')
        context = data.get('context', 'dashboard')
        
        if not message:
            return jsonify({
                'status': 'error',
                'error': 'Message is required'
            }), 400
        
        # Mock responses based on context and message patterns
        response_message = _generate_mock_chat_response(message, context, pending_task)
        
        # Build response
        response = {
            'status': 'success',
            'message': response_message,
            'pending_task': pending_task  # Return updated task if modified
        }
        
        # Add redirect for onboarding completion
        if context == 'onboarding' and 'profile created' in response_message.lower():
            response['redirect'] = '/dashboard'
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'An error occurred processing your request'
        }), 500


def _generate_mock_chat_response(message, context, pending_task):
    """Generate mock AI responses for chat.
    
    This is a placeholder - actual AI integration will be built in parallel task.
    """
    message_lower = message.lower()
    
    if context == 'onboarding':
        # Onboarding flow mock responses
        if 'http' in message_lower or 'www.' in message_lower:
            return "Great! I found your website. Let me analyze your brand...\n\n**What I discovered:**\n- Industry: Technology\n- Tone: Professional and approachable\n- Key themes: Innovation, reliability, customer success\n\nDoes this look right?"
        elif any(word in message_lower for word in ['yes', 'correct', 'looks good']):
            return "Perfect! Your brand profile has been created. Redirecting to your dashboard..."
        else:
            return f"I understand you want to tell me about: *{message}*\n\nThat's helpful! Can you also share your website URL so I can learn more about your brand?"
    
    else:
        # Dashboard flow mock responses
        if message.startswith('/'):
            # Slash command handling
            command = message.split()[0][1:].lower()
            
            commands = {
                'post': "I'll help you create a social media post. What topic or message do you want to share?",
                'caption': "Let's create a caption for your image. Describe the image or paste a URL.",
                'reel': "Great! I'll script a short video for you. What's the video about?",
                'email': "I'll draft an email for you. Who is it for and what's the main message?",
                'review': "I can help respond to customer reviews. Paste the review you want to respond to.",
                'blog': "Let's write a blog post! What's your topic or title?",
                'ad': "I'll create ad copy for you. What product/service are you advertising?",
                'proposal': "I'll help draft a business proposal. What's the project or opportunity?"
            }
            
            response = commands.get(command, f"I don't recognize the command `/{command}`. Try `/post`, `/email`, or `/reel`.")
            return response
        
        else:
            # General conversation
            if any(word in message_lower for word in ['help', 'what can', 'how do']):
                return "I can help you create:\n- **/post** - Social media posts\n- **/caption** - Image captions\n- **/reel** - Video scripts\n- **/email** - Emails and newsletters\n- **/review** - Review responses\n- **/blog** - Blog posts\n\nJust type a slash command or describe what you need!"
            else:
                return f"I understand you want to work on: **{message}**\n\nTo get started quickly, try one of these commands:\n- `/post` for social posts\n- `/email` for emails\n- `/reel` for video scripts\n\nOr keep chatting and I'll help you refine your idea!"
