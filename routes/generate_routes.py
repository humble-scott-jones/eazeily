from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.voice_engine import VoiceEngine
from services.task_registry import get_task_config, list_task_types
from models import VoiceProfile
import os
import logging

logger = logging.getLogger(__name__)
generate_bp = Blueprint('generate', __name__)
voice_engine = VoiceEngine()

@generate_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@generate_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """Settings page - redirects to brand setup for now."""
    from flask import redirect, url_for
    return redirect(url_for('onboarding.onboarding'))


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
    from datetime import date, timedelta
    from generator import generate_posts
    
    # Get user profile for defaults
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    
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
    
    # Helper to check if a field is empty
    def is_field_empty(field):
        return not field or not field.strip()
    
    # Check if profile exists and identify what's missing for better error messages
    if not profile:
        logger.warning(f"User {current_user.id} attempted generation without a brand profile")
        return _error_response(
            "profile_required",
            "Please create your brand profile to start generating content. Click 'Settings' or visit /onboarding to set up your business name, industry, and brand voice.",
            400,
            redirect="/onboarding"
        )
    
    # Profile exists - check for key required fields and provide specific guidance
    missing_fields = []
    if is_field_empty(profile.business_name):
        missing_fields.append("business name")
    if is_field_empty(profile.industry):
        missing_fields.append("industry")
    
    # If critical fields are missing, provide specific error
    if missing_fields:
        logger.warning(f"User {current_user.id} has incomplete profile: missing {missing_fields}")
        return _error_response(
            "incomplete_profile",
            f"Your profile is missing: {', '.join(missing_fields)}. Please complete these required fields in Settings or /onboarding for better content generation.",
            400,
            redirect="/onboarding",
            missing_fields=missing_fields
        )
    
    # Profile has minimum required data - log optional missing fields as warnings
    optional_missing = []
    if is_field_empty(profile.brand_voice):
        optional_missing.append("brand voice")
    if is_field_empty(profile.target_audience):
        optional_missing.append("target audience")
    
    # Check brand keywords (avoid redundant method call)
    brand_keywords = profile.get_brand_keywords()
    if not brand_keywords or len(brand_keywords) == 0:
        optional_missing.append("brand keywords")
    
    if optional_missing:
        logger.info(f"User {current_user.id} profile could be enhanced with: {optional_missing}")
    
    logger.debug(f"Loaded profile for user {current_user.id} with brand: {profile.business_name}")

    # STRUCTURED CONTEXT: Extract and validate dynamic input context
    context = {}
    
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
