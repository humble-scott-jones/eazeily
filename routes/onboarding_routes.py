from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, VoiceProfile
import logging
import json

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
                from flask import flash
                flash("All required fields must be filled", "error")
                return render_template('onboarding.html'), 400
            
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
            logger.error(f"Error saving brand profile: {e}", exc_info=True)
            db.session.rollback()
            from flask import flash
            flash(f"Failed to save brand profile: {str(e)}", "error")
            return render_template('onboarding.html'), 500


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


@onboarding_bp.route('/onboarding/voice-chat', methods=['POST'])
@login_required
def voice_chat():
    """Conversational AI chat interface for building brand voice profile.
    
    This endpoint manages a multi-turn conversation where:
    1. User provides links to existing brand content (website, social media)
    2. AI analyzes those links and extracts voice characteristics
    3. AI asks follow-up questions for missing information
    4. AI generates final brand voice profile
    """
    try:
        import google.generativeai as genai
        import os
        import re
        
        # Configure Gemini
        api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return jsonify({"error": "AI service not configured"}), 503
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = request.get_json()
        business_name = data.get('business_name', '')
        industry = data.get('industry', '')
        user_message = data.get('user_message', '')
        conversation_history = data.get('conversation_history', [])
        current_stage = data.get('stage', 'initial')
        
        if not business_name or not industry or not user_message:
            return jsonify({"error": "Required fields missing"}), 400
        
        # Detect if user provided URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, user_message)
        
        # Build conversation context for AI
        conversation_context = f"""You are a brand voice strategist helping to build a brand profile for:
Business: {business_name}
Industry: {industry}

Current Stage: {current_stage}

Conversation so far:
"""
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = "User" if msg['role'] == 'user' else "AI"
            conversation_context += f"{role}: {msg['message']}\n"
        
        conversation_context += f"\nUser's latest message: {user_message}\n"
        
        # Determine next step based on stage and user input
        if current_stage == 'initial' and urls:
            # User provided links - analyze them
            prompt = f"""{conversation_context}

The user has provided these URLs: {', '.join(urls)}

Since you cannot actually fetch these URLs, acknowledge them and explain that you'll help build their brand voice profile through conversation instead. Ask 2-3 specific questions to understand their brand voice, such as:
- How do they want their customers to feel when reading their content?
- What makes their brand different from competitors?
- Do they have any examples of content they've written that represents their voice well?

Keep your response conversational, friendly, and under 150 words. Move to stage 'gathering_info'."""
            
            response = model.generate_content(prompt)
            ai_message = response.text.strip()
            
            return jsonify({
                "ai_message": ai_message,
                "stage": "gathering_info",
                "brand_voice": None,
                "target_audience": None
            })
            
        elif current_stage == 'initial' and not urls:
            # User didn't provide links - guide them or start gathering info
            prompt = f"""{conversation_context}

The user responded but didn't provide any URLs. Based on their response, either:
1. If they seem confused, gently remind them they can share links OR just answer questions about their brand
2. If they're describing their brand, acknowledge it and ask 1-2 follow-up questions about their brand voice

Keep it friendly and conversational (under 100 words). Move to stage 'gathering_info'."""
            
            response = model.generate_content(prompt)
            ai_message = response.text.strip()
            
            return jsonify({
                "ai_message": ai_message,
                "stage": "gathering_info",
                "brand_voice": None,
                "target_audience": None
            })
            
        elif current_stage == 'gathering_info':
            # Analyze user's responses and decide if we have enough info
            prompt = f"""{conversation_context}

Analyze the conversation. You need to extract:
1. Brand Voice/Tone (how they sound: friendly, professional, casual, authoritative, etc.)
2. Target Audience (who they're speaking to)

If you have enough information from the conversation to confidently describe both:
- Generate a concise 2-3 sentence Brand Voice description
- Generate a 1-2 sentence Target Audience description
- Respond with: "Based on our conversation, here's what I've gathered: [summary]. Does this sound right?"
- Set stage to 'confirming'

If you need more information:
- Ask 1-2 specific follow-up questions about what's missing
- Keep stage as 'gathering_info'
- Keep response under 100 words

Format your response as JSON with these fields:
{{
    "message": "your conversational response",
    "brand_voice": "brand voice description or null",
    "target_audience": "target audience description or null",
    "next_stage": "gathering_info or confirming",
    "has_enough_info": true or false
}}

Only output valid JSON, nothing else."""
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                result = json.loads(response_text)
                
                return jsonify({
                    "ai_message": result.get('message', 'Let me help you with that...'),
                    "stage": result.get('next_stage', 'gathering_info'),
                    "brand_voice": result.get('brand_voice'),
                    "target_audience": result.get('target_audience')
                })
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response from AI: {e}. Response: {response_text[:200]}")
                # Fallback if JSON parsing fails
                return jsonify({
                    "ai_message": response_text,
                    "stage": "gathering_info",
                    "brand_voice": None,
                    "target_audience": None
                })
                
        elif current_stage == 'confirming':
            # User is confirming or refining the generated profile
            user_message_lower = user_message.lower()
            
            if any(word in user_message_lower for word in ['yes', 'correct', 'right', 'good', 'perfect', 'great', 'sounds good']):
                # User confirmed - we're done!
                return jsonify({
                    "ai_message": "Perfect! I've filled in your brand voice and target audience. Feel free to adjust them in the form if needed. ✨",
                    "stage": "complete",
                    "brand_voice": None,  # Already set
                    "target_audience": None  # Already set
                })
            else:
                # User wants to refine - go back to gathering info
                prompt = f"""{conversation_context}

The user wants to refine the brand voice profile. Based on their feedback, ask 1-2 specific questions to better understand what they want to change. Keep it conversational and under 100 words."""
                
                response = model.generate_content(prompt)
                ai_message = response.text.strip()
                
                return jsonify({
                    "ai_message": ai_message,
                    "stage": "gathering_info",
                    "brand_voice": None,
                    "target_audience": None
                })
        
        # Default fallback
        return jsonify({
            "ai_message": "I'm here to help! Can you tell me more about your brand?",
            "stage": "gathering_info",
            "brand_voice": None,
            "target_audience": None
        })
        
    except ImportError as e:
        logger.error(f"ImportError in voice chat: {e}")
        return jsonify({"error": "AI service not available. Please ensure google-generativeai is installed."}), 503
    except Exception as e:
        logger.error(f"Error in voice chat: {e}", exc_info=True)
        return jsonify({"error": f"Failed to process your message: {str(e)}"}), 500


@onboarding_bp.route('/onboarding/interview-voice', methods=['POST'])
@login_required
def interview_voice():
    """Interview-style AI assistant to extract brand voice from user's natural description.
    
    This endpoint takes a paragraph-style response from the user describing their brand
    and uses AI to extract structured brand voice characteristics.
    """
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
        user_response = data.get('user_response', '')
        
        if not business_name or not industry or not user_response:
            return jsonify({"error": "All fields are required"}), 400
        
        # Use AI to analyze the user's response and extract brand voice
        prompt = f"""
        You are a brand strategist conducting a voice profile interview. A business owner has shared the following about their brand:
        
        Business Name: {business_name}
        Industry: {industry}
        
        Their Response: "{user_response}"
        
        Based on their natural description, write a concise 2-3 sentence Brand Voice profile that captures the tone and personality they should use in marketing. Extract the essence of their communication style and values from what they shared.
        
        Output only the brand voice description. No preamble, no "Based on your response", just the refined description.
        Focus on specific adjectives that describe tone (e.g., professional, friendly, authoritative, conversational, warm, technical).
        """
        
        response = model.generate_content(prompt)
        brand_voice = response.text.strip()
        
        return jsonify({"brand_voice": brand_voice})
        
    except ImportError:
        return jsonify({"error": "AI service not available"}), 503
    except Exception as e:
        logger.error(f"Error analyzing voice interview: {e}")
        return jsonify({"error": "Failed to analyze your response"}), 500
