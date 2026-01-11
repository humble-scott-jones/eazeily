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

def _missing(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _build_dummy_profile():
    class DummyProfile:
        industry = 'general'
        business_name = 'Your Business'
        target_audience = 'General audience'
        brand_voice = 'Professional and friendly'
        key_offer = ''
        voice_rules = ''

        def get_writing_samples(self):
            return []

        def get_defaults(self):
            return {}

        def get_examples(self):
            return []

    return DummyProfile()


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
    profile_missing = profile is None
    
    if profile_missing:
        logger.info(f"User {current_user.id} generating content without a brand profile, using defaults")
        profile = _build_dummy_profile()
    else:
        # Profile exists - all data is already loaded from the single query above
        # The VoiceProfile model has all fields as columns, so no additional queries needed
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
        # Proposal-specific fields
        'proposal_type': lambda v: v if v in ['partnership', 'sponsorship', 'funding', 'rfp_response', 'collaboration'] else None,
        'recipient': lambda v: v[:200] if v else None,
        'key_benefits': lambda v: v if isinstance(v, list) else None,
        'budget_range': lambda v: v[:100] if v else None,
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
        
        if profile_missing:
            response_payload["profile_missing"] = True
            response_payload["redirect"] = "/onboarding"
            
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
    data = request.get_json(silent=True) or {}
    task_type = data.get('task_type', 'post')
    return _handle_generate(task_type, data)


@generate_bp.route('/api/generate/<task_type>', methods=['POST'])
@login_required
def generate_task(task_type):
    data = request.get_json(silent=True) or {}
    return _handle_generate(task_type, data)
