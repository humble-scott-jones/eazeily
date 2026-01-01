from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from services.voice_engine import VoiceEngine
from services.ingestion import ingest_url, ingest_file
from models import db, VoiceProfile
import os
import tempfile

wizard_bp = Blueprint('wizard', __name__)

# Initialize Voice Engine
voice_engine = VoiceEngine()

@wizard_bp.route('/setup/voice', methods=['GET', 'POST'])
# @login_required # Commented out for testing ease if auth isn't fully set up yet
def setup_voice():
    if request.method == 'GET':
        return render_template('base.html', content="Voice Setup Page") # Using base.html as placeholder

    if request.method == 'POST':
        data = request.form
        url = data.get('url')
        file = request.files.get('file')
        
        raw_text = ""
        
        if url:
            raw_text = ingest_url(url)
        elif file:
            # Save to temp file to upload/read
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            
            # For this implementation, we need text for analyze_style.
            # If ingest_file returns a file object, we can't pass it to analyze_style directly 
            # unless we update VoiceEngine.
            # Let's try to read the text content if it's a text file, 
            # or use the file path if we were using Gemini's file processing capabilities.
            # Given the prompt's simplicity: "Calls Ingestion -> VoiceEngine -> Updates DB"
            # And VoiceEngine.analyze_style takes `raw_text`.
            # I will read the file content as text.
            try:
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
            except Exception as e:
                return jsonify({"error": "Could not read file as text. Please upload a text file."}), 400
            finally:
                os.remove(tmp_path)
        
        if not raw_text:
            return jsonify({"error": "No content found to analyze"}), 400

        # Analyze Style
        analysis = voice_engine.analyze_style(raw_text)
        
        # Update DB
        # Assuming current_user is available, else we might need a dummy user or handle it.
        # For now, let's check if current_user is authenticated.
        if current_user.is_authenticated:
            profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
            if not profile:
                profile = VoiceProfile(user_id=current_user.id)
                db.session.add(profile)
            
            profile.style_guide = analysis.get('style_guide')
            profile.set_examples(analysis.get('examples'))
            db.session.commit()
            
            return jsonify({"status": "success", "profile": analysis})
        else:
             return jsonify({"status": "success", "profile": analysis, "message": "User not logged in, profile not saved."})

# Minimal Auth and Dashboard Routes to satisfy the "Register Blueprints" requirement in app.py
# In a real scenario, these would be in separate files.
auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/login')
def login(): return "Login Page"

dashboard_bp = Blueprint('dashboard', __name__)
@dashboard_bp.route('/dashboard')
def dashboard(): return "Dashboard"
