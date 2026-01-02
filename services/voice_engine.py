import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from services.industry_packs import IndustryPackLoader

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("No API key found for Gemini. Please set GENAI_API_KEY or GOOGLE_API_KEY.")
else:
    genai.configure(api_key=api_key)

class VoiceEngine:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.pack_loader = IndustryPackLoader()
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None

    def analyze_style(self, raw_text):
        """
        Analyzes raw text to extract a style guide and examples.
        Returns a JSON object with 'style_guide' and 'examples'.
        """
        if not self.model:
            logger.error("VoiceEngine model is not initialized.")
            return {"style_guide": "Error: AI model not available.", "examples": []}

        prompt = """
        You are an expert content strategist. Analyze the following text to create a Voice Profile.
        
        Output strictly valid JSON with two keys:
        1. "style_guide": A concise paragraph describing the tone, sentence structure, and vocabulary.
        2. "examples": A list of 3-5 direct quotes from the text that best exemplify this style.
        
        Text to analyze:
        {text}
        """
        
        try:
            response = self.model.generate_content(prompt.format(text=raw_text[:10000])) # Limit context if needed
            # Clean up potential markdown code blocks
            text_response = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text_response)
        except Exception as e:
            logger.error(f"Error in analyze_style: {e}")
            return {"style_guide": "Default professional tone (Error during analysis).", "examples": []}

    def generate_post(self, user_profile, topic, platform="LinkedIn"):
        """
        Generates a post based on the profile and topic using Few-Shot Prompting.
        """
        if not self.model:
            logger.error("VoiceEngine model is not initialized.")
            return "Error: AI model not available."

        # 1. Load Context: Industry Defaults + User Profile Overrides
        industry = getattr(user_profile, 'industry', 'general') or 'general'
        pack = self.pack_loader.get_defaults(industry)
        
        # Fallback to pack defaults if user profile is empty
        style_guide = getattr(user_profile, 'style_guide', None) or pack.get('defaults', {}).get('style_guide', '')
        examples = user_profile.get_examples() if hasattr(user_profile, 'get_examples') else []
        if not examples:
            examples = pack.get('defaults', {}).get('examples', [])

        # 2. Construct Prompt
        prompt = f"""
        Role: You are an expert Social Media Manager for a {pack.get('industry', 'General Business')}.
        Platform: {platform}
        Topic: {topic}
        
        Style Guide:
        {style_guide}
        
        Constraint: Output final copy only. No preamble. No "Sure!", "Here is", or "Title:".
        """
        
        if examples:
            prompt += "\nFew-Shot Examples (Mimic this writing style):\n"
            for ex in examples:
                prompt += f"- {ex}\n"
            
        prompt += f"""
        
        Task: Write a new social media post about: "{topic}".
        Keep it appropriate for {platform}.
        """
        
        # 3. Call Model & 4. Guardrail
        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt)
                content = response.text.strip()
                
                # Guardrail check
                lower_content = content.lower()
                if lower_content.startswith("sure") or lower_content.startswith("here is") or lower_content.startswith("title:"):
                    logger.warning(f"Guardrail triggered on attempt {attempt+1}. Retrying...")
                    prompt += "\n\nCRITICAL: Do NOT include any conversational filler like 'Sure' or 'Here is'. Just the post text."
                    continue
                
                return content
            except Exception as e:
                logger.error(f"Error in generate_post (attempt {attempt+1}): {e}")
                if attempt == 1:
                    return "Error generating content. Please try again."
        
        return "Error generating content after retries."
