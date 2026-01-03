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
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # Get user profile (handle anonymous users)
    profile = None
    if current_user.is_authenticated:
        profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    else:
        # Anonymous user - will use default profile
        profile = None
    
    # If no profile exists, create a temporary/default one wrapper or handle in engine
    # The engine handles empty profiles by falling back to industry defaults.
    # We pass the profile object (or None/mock if strictly needed, but engine expects object with attributes)
    
    if not profile:
        # Create a dummy object or handle gracefully. 
        # For anonymous users or users without profiles, use a generic default.
        # The engine expects an object with get_defaults() and get_examples() methods.
        class DummyProfile:
            industry = 'general'
            style_guide = None
            def get_defaults(self): 
                return {'style_guide': None}
            def get_examples(self): 
                return []
        profile = DummyProfile()

    try:
        content = voice_engine.generate_post(profile, topic, platform)
        return jsonify({"content": content, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500
