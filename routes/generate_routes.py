from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.voice_engine import VoiceEngine
from models import VoiceProfile

generate_bp = Blueprint('generate', __name__)
voice_engine = VoiceEngine()

@generate_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@generate_bp.route('/api/generate', methods=['POST'])
@login_required
def generate():
    data = request.get_json()
    topic = data.get('topic')
    platform = data.get('platform', 'LinkedIn')
    task_type = data.get('task_type', 'post')
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # Get user profile
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    
    # If no profile exists, create a temporary/default one
    if not profile:
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
        return jsonify({"content": content, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500
