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

    # Get user profile
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    
    # If no profile exists, create a temporary/default one wrapper or handle in engine
    # The engine handles empty profiles by falling back to industry defaults.
    # We pass the profile object (or None/mock if strictly needed, but engine expects object with attributes)
    
    if not profile:
        # Create a dummy object or handle gracefully. 
        # Ideally, every user should have a profile created on signup or first login.
        # For now, let's pass a dummy object if needed, or just let the engine handle 'None' if we adjust it.
        # But engine does `getattr(user_profile, ...)` so we need an object.
        class DummyProfile:
            industry = 'general'
            style_guide = None
            def get_examples(self): return []
        profile = DummyProfile()

    try:
        content = voice_engine.generate_post(profile, topic, platform)
        return jsonify({"content": content, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500
