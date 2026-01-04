from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, VoiceProfile
import logging

onboarding_bp = Blueprint('onboarding', __name__)
logger = logging.getLogger(__name__)

@onboarding_bp.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    """Handle the Brand Brain onboarding process."""
    if request.method == 'GET':
        return render_template('onboarding.html')
    
    if request.method == 'POST':
        try:
            # Get form data
            business_name = request.form.get('business_name')
            industry = request.form.get('industry')
            target_audience = request.form.get('target_audience')
            brand_voice = request.form.get('brand_voice')
            key_offer = request.form.get('key_offer')
            voice_rules = request.form.get('voice_rules', '')
            writing_samples_raw = request.form.get('writing_samples', '')
            
            # Validate required fields
            if not all([business_name, industry, target_audience, brand_voice, key_offer, writing_samples_raw]):
                return jsonify({"error": "All required fields must be filled"}), 400
            
            # Split writing samples by double newline (blank line separator)
            # Filter out empty strings
            writing_samples = [
                sample.strip() 
                for sample in writing_samples_raw.split('\n\n') 
                if sample.strip()
            ]
            
            # Get or create voice profile
            profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
            if not profile:
                profile = VoiceProfile(user_id=current_user.id)
                db.session.add(profile)
            
            # Update profile fields
            profile.business_name = business_name
            profile.industry = industry
            profile.target_audience = target_audience
            profile.brand_voice = brand_voice
            profile.key_offer = key_offer
            profile.voice_rules = voice_rules
            profile.set_writing_samples(writing_samples)
            
            db.session.commit()
            
            logger.info(f"Brand profile saved for user {current_user.id}")
            
            # Redirect to dashboard
            return redirect(url_for('generate.dashboard'))
            
        except Exception as e:
            logger.error(f"Error saving brand profile: {e}")
            db.session.rollback()
            return jsonify({"error": "Failed to save brand profile"}), 500


@onboarding_bp.route('/onboarding/assist-voice', methods=['POST'])
@login_required
def assist_voice():
    """AI assistant to help describe brand voice based on business name and industry."""
    try:
        import google.generativeai as genai
        import os
        
        # Configure Gemini
        api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return jsonify({"error": "AI service not configured"}), 503
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = request.get_json()
        business_name = data.get('business_name', '')
        industry = data.get('industry', '')
        
        if not business_name or not industry:
            return jsonify({"error": "Business name and industry are required"}), 400
        
        # Generate brand voice description
        prompt = f"""
        You are a brand strategist. Based on the following business information, write a 3-sentence Brand Voice profile that captures the tone and personality this business should use in marketing.
        
        Business Name: {business_name}
        Industry: {industry}
        
        Output only the brand voice description (2-3 sentences). No preamble, no "Here is", just the description.
        Focus on adjectives that describe the tone (e.g., professional, friendly, authoritative, playful).
        """
        
        response = model.generate_content(prompt)
        brand_voice = response.text.strip()
        
        return jsonify({"brand_voice": brand_voice})
        
    except ImportError:
        return jsonify({"error": "AI service not available"}), 503
    except Exception as e:
        logger.error(f"Error generating brand voice: {e}")
        return jsonify({"error": "Failed to generate brand voice description"}), 500
