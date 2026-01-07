from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, VoiceProfile
import logging
import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

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
        from services.ai_service import get_generative_model
        
        # Configure Gemini
        model = get_generative_model()
        if not model:
            return jsonify({"error": "AI service not configured"}), 503
        
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
        from services.ai_service import get_generative_model
        import re
        
        # Configure Gemini
        model = get_generative_model()
        if not model:
            return jsonify({"error": "AI service not configured"}), 503
        
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
            from services.scraper_service import scrape_url
            
            scraped_data = []
            for url in urls[:2]: # Limit to first 2 URLs to save time/tokens
                content = scrape_url(url)
                if content:
                    scraped_data.append(f"--- Content from {url} ---\n{content[:2000]}") # Truncate per site
            
            if scraped_data:
                # We have actual content!
                combined_content = "\n\n".join(scraped_data)
                prompt = f"""{conversation_context}

The user has provided these URLs: {', '.join(urls)}

I have successfully scraped the text from their website(s). Here is the content:
{combined_content}

Your task:
1. Analyze this scraped content to identify:
   - Brand Voice & Tone
   - Value Proposition
   - Key Offer (Call to Action)
2. Acknowledge that you have "read" their website.
3. Ask 1 crucial follow-up question to confirm your analysis or get the 'feeling' (or specific constraints/rules) that text alone might miss.

Keep your response conversational, friendly, and under 150 words. Move to stage 'gathering_info'."""
            
            else:
                # Scraping failed or no text found
                prompt = f"""{conversation_context}

The user has provided these URLs: {', '.join(urls)}

I attempted to read them but couldn't retrieve the text (maybe they are behind a login or blocked). 
Acknowledge the links, but explain you couldn't access them directly. Ask them to describe their brand voice and key offer instead.

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
1. If they seem confused, gently remind them they can share links OR just answer questions about their brand.
2. If they're describing their brand, acknowledge it and ask 1-2 follow-up questions about their brand voice, key offer, or any specific writing rules.

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
1. Brand Voice/Tone (e.g. friendly, professional)
2. Target Audience (who they're speaking to)
3. Key Offer (main product/service or "hook", e.g. "Free Consultation")
4. Voice Rules (constraints, e.g. "No emojis", "Always be punchy", or "None")

If you have enough information from the conversation to confidently describe all four:
- Generate a summary for each field.
- Respond with: "Based on our conversation, here's what I've gathered: [summary]. Does this sound right?"
- Set stage to 'confirming'

If you need more information:
- Ask 1-2 specific follow-up questions about what's missing (especially offer or rules).
- Keep stage as 'gathering_info'
- Keep response under 100 words

Format your response as JSON with these fields:
{{
    "message": "your conversational response",
    "brand_voice": "brand voice description or null",
    "target_audience": "target audience description or null",
    "key_offer": "key offer description or null",
    "voice_rules": "voice rules description or null",
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
                    "target_audience": result.get('target_audience'),
                    "key_offer": result.get('key_offer'),
                    "voice_rules": result.get('voice_rules')
                })
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response from AI: {e}. Response: {response_text[:200]}")
                # Fallback if JSON parsing fails
                return jsonify({
                    "ai_message": response_text,
                    "stage": "gathering_info",
                    "brand_voice": None,
                    "target_audience": None,
                    "key_offer": None,
                    "voice_rules": None
                })
                
        elif current_stage == 'confirming':
            # User is confirming or refining the generated profile
            user_message_lower = user_message.lower()
            
            if any(word in user_message_lower for word in ['yes', 'correct', 'right', 'good', 'perfect', 'great', 'sounds good']):
                # User confirmed - we're done!
                return jsonify({
                    "ai_message": "Perfect! I've filled in your brand voice, audience, and key offer details. Feel free to adjust them in the form if needed. ✨",
                    "stage": "complete",
                    "brand_voice": None,  # Already set
                    "target_audience": None,  # Already set
                    "key_offer": None,
                    "voice_rules": None
                })
            else:
                # User wants to refine - go back to gathering info
                prompt = f"""{conversation_context}

The user wants to refine the brand voice profile. Based on their feedback, ask 1-2 specific questions to better understand what they want to change about the voice, audience, offer, or rules. Keep it conversational and under 100 words."""
                
                response = model.generate_content(prompt)
                ai_message = response.text.strip()
                
                return jsonify({
                    "ai_message": ai_message,
                    "stage": "gathering_info",
                    "brand_voice": None,
                    "target_audience": None,
                    "key_offer": None,
                    "voice_rules": None
                })
        
        # Default fallback
        return jsonify({
            "ai_message": "I'm here to help! Can you tell me more about your brand?",
            "stage": "gathering_info",
            "brand_voice": None,
            "target_audience": None,
            "key_offer": None,
            "voice_rules": None
        })
        
    except ImportError as e:
        logger.error(f"ImportError in voice chat: {e}")
        return jsonify({"error": "AI service not available. Please ensure google-generativeai is installed."}), 503
    except Exception as e:
        logger.error(f"Error in voice chat: {e}", exc_info=True)
        return jsonify({"error": f"Failed to process your message: {str(e)}"}), 500


def _extract_samples_from_html(html: str, max_samples: int = 5) -> list:
    """Pull short text snippets from a social page to use as samples."""
    soup = BeautifulSoup(html, 'html.parser')

    # Try obvious places first
    meta_desc = soup.find('meta', attrs={'property': 'og:description'}) or soup.find('meta', attrs={'name': 'description'})
    candidates = []
    if meta_desc and meta_desc.get('content'):
        candidates.append(meta_desc.get('content'))

    # Collect paragraph-like text blocks
    for tag in soup.find_all(['p', 'span', 'div', 'li']):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        # Filter out navigation and extremely short/long blobs
        if 20 <= len(text) <= 400:
            candidates.append(text)

    # Deduplicate and trim
    samples = []
    seen = set()
    for raw in candidates:
        cleaned = " ".join(raw.split())
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        samples.append(cleaned[:280])
        if len(samples) >= max_samples:
            break

    return samples


def _infer_style(samples: list) -> dict:
    """Compute simple heuristics (emoji density, hashtags, sentence length) and map to tone cues."""
    if not samples:
        return {
            "tones": ["friendly", "approachable"],
            "notes": "Defaulted to approachable tone; no samples available.",
            "emoji_density": 0,
            "avg_sentence_length": 0,
            "hashtags": 0
        }

    full_text = " ".join(samples)
    emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    emoji_count = len(emoji_pattern.findall(full_text))
    word_count = max(len(full_text.split()), 1)
    emoji_density = emoji_count / word_count

    sentences = re.split(r"[.!?]", full_text)
    sent_lengths = [len(s.split()) for s in sentences if len(s.strip()) > 0]
    avg_sentence_length = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0

    hashtags = len(re.findall(r"#\w+", full_text))

    tones = []
    if emoji_density > 0.02:
        tones.append("playful")
    elif emoji_density > 0.005:
        tones.append("warm")
    else:
        tones.append("professional")

    if avg_sentence_length >= 18:
        tones.append("thoughtful")
    elif avg_sentence_length <= 10:
        tones.append("punchy")

    if hashtags >= 4:
        tones.append("social-first")

    return {
        "tones": tones,
        "notes": "Emoji density {:.2f}, avg sentence length {:.1f} words, {} hashtags.".format(emoji_density, avg_sentence_length, hashtags),
        "emoji_density": emoji_density,
        "avg_sentence_length": avg_sentence_length,
        "hashtags": hashtags
    }


def _build_suggestions(samples: list, style: dict, business_name: str = "") -> dict:
    tone_phrase = ", ".join(style.get("tones", []) or ["approachable"])
    top_sample = samples[0] if samples else ""

    brand_voice = f"{tone_phrase} with { 'emoji-friendly, ' if style.get('emoji_density', 0) > 0.02 else ''}clear, social-ready phrasing."

    tagline = "" if not business_name else f"{business_name}: {tone_phrase.title()} stories that convert."
    if not tagline and top_sample:
        tagline = top_sample[:90] + ("…" if len(top_sample) > 90 else "")

    voice_rules = []
    if style.get("emoji_density", 0) > 0.02:
        voice_rules.append("Include a couple emojis to keep it upbeat.")
    if style.get("avg_sentence_length", 0) > 18:
        voice_rules.append("Prefer concise sentences (<18 words).")
    else:
        voice_rules.append("Keep sentences punchy and easy to skim.")
    if style.get("hashtags", 0) >= 4:
        voice_rules.append("Use 2-3 focused hashtags at the end.")

    sample_copy = samples[:3] if samples else []

    return {
        "brand_voice": brand_voice,
        "tagline": tagline,
        "voice_rules": "; ".join(voice_rules) if voice_rules else "",
        "sample_copy": sample_copy
    }


@onboarding_bp.route('/onboarding/social-style', methods=['POST'])
@login_required
def social_style():
    """Fetch content from a provided URL. For FB/IG, only surface rhythm samples; for websites, infer broader suggestions."""
    try:
        from services.scraper_service import scrape_url

        data = request.get_json() or {}
        raw_url = (data.get('url') or '').strip()
        consent = bool(data.get('consent'))
        business_name = (data.get('business_name') or '').strip()

        if not raw_url:
            return jsonify({"error": "A URL is required"}), 400
        if not consent:
            return jsonify({"error": "Consent is required before scraping"}), 400

        parsed = urlparse(raw_url if '://' in raw_url else f"https://{raw_url}")
        host = (parsed.hostname or '').lower()
        social_hosts = {'facebook.com', 'www.facebook.com', 'm.facebook.com', 'fb.com', 'instagram.com', 'www.instagram.com'}
        normalized_url = parsed.geturl()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36'
        }

        # Social path: only provide rhythm samples
        if host in social_hosts:
            try:
                resp = requests.get(normalized_url, headers=headers, timeout=10)
                resp.raise_for_status()
            except requests.HTTPError as http_err:
                status = http_err.response.status_code if http_err.response else 500
                if status == 429:
                    return jsonify({"error": "Rate limited by the social platform. Please retry later."}), 429
                return jsonify({"error": f"Failed to fetch the page (status {status})."}), status
            except Exception as e:
                logger.error(f"Error fetching social URL {normalized_url}: {e}")
                return jsonify({"error": "Could not reach that URL. Double-check it and try again."}), 500

            samples = _extract_samples_from_html(resp.text)
            style = _infer_style(samples)
            # For socials, restrict suggestions to rhythm/writing samples only
            suggestions = {
                "brand_voice": None,
                "tagline": None,
                "voice_rules": None,
                "sample_copy": samples[:3]
            }

            return jsonify({
                "samples": samples,
                "style": style,
                "suggestions": suggestions,
                "source": "social"
            })

        # Website path: use scraper_service to get visible text, then derive samples and suggestions
        scraped_text = scrape_url(normalized_url, max_length=6000)
        if not scraped_text:
            return jsonify({"error": "Could not read that page (maybe it is blocked or empty)."}), 400

        # Derive samples from the text (split into sentences/paragraphs)
        sentences = re.split(r"(?<=[.!?])\s+", scraped_text)
        samples = []
        for s in sentences:
            cleaned = s.strip()
            if 40 <= len(cleaned) <= 280:
                samples.append(cleaned)
            if len(samples) >= 5:
                break
        if not samples:
            samples = [scraped_text[:240]]

        style = _infer_style(samples)
        suggestions = _build_suggestions(samples, style, business_name)

        return jsonify({
            "samples": samples,
            "style": style,
            "suggestions": suggestions,
            "source": "website"
        })

    except Exception as e:
        logger.error(f"Error in social_style: {e}", exc_info=True)
        return jsonify({"error": "Failed to analyze the link."}), 500


@onboarding_bp.route('/onboarding/interview-voice', methods=['POST'])
@login_required
def interview_voice():
    """Interview-style AI assistant to extract brand voice from user's natural description.
    
    This endpoint takes a paragraph-style response from the user describing their brand
    and uses AI to extract structured brand voice characteristics.
    """
    try:
        from services.ai_service import get_generative_model
        
        # Configure Gemini
        model = get_generative_model()
        if not model:
            return jsonify({"error": "AI service not configured"}), 503
        
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
