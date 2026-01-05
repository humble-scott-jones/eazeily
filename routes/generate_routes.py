from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.voice_engine import VoiceEngine
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

@generate_bp.route('/api/generate', methods=['POST'])
@login_required
def generate():
    data = request.get_json()
    topic = data.get('topic')
    platform = data.get('platform', 'LinkedIn')
    task_type = data.get('task_type', 'post')
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # Check if API key is configured
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return jsonify({
            "error": "AI service is not configured. Please set up your API key in the environment variables (GENAI_API_KEY or GOOGLE_API_KEY).",
            "status": "error"
        }), 503

    # Get user profile
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    
    # If no profile exists, create a temporary/default one
    if not profile:
        logger.info(f"User {current_user.id} generating content without a brand profile, using defaults")
        # Create a dummy object with default values
        class DummyProfile:
            industry = 'general'
            business_name = 'Your Business'
            target_audience = 'General audience'
            brand_voice = 'Professional and friendly'
            key_offer = ''
            voice_rules = ''
            def get_writing_samples(self):
                return []
        profile = DummyProfile()

    try:
        # Use the expert content generation with role-based prompting
        content = voice_engine.generate_expert_content(profile, topic, task_type, platform)
        
        # Check if content generation returned an error message
        if content.startswith("Error"):
            logger.error(f"Content generation failed: {content}")
            return jsonify({
                "error": "Failed to generate content. Please check your API key and try again.",
                "status": "error"
            }), 500
            
        return jsonify({"content": content, "status": "success"})
    except Exception as e:
        logger.error(f"Exception during content generation: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"An error occurred while generating content: {str(e)}",
            "status": "error"
        }), 500
