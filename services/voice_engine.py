import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

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
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None

    def analyze_style(self, raw_text):
        """
        Analyzes raw text to extract a style summary and examples.
        Returns a JSON object with 'style_summary' and 'examples'.
        """
        if not self.model:
            logger.error("VoiceEngine model is not initialized.")
            return {"style_summary": "Error: AI model not available.", "style_guide": "Error: AI model not available.", "examples": []}

        prompt = """
        You are an expert content strategist. Analyze the following text to create a Voice Profile.
        
        Output strictly valid JSON with two keys:
        1. "style_summary": A concise paragraph describing the tone, sentence structure, and vocabulary.
        2. "examples": A list of 3-5 direct quotes from the text that best exemplify this style.
        
        Text to analyze:
        {text}
        """
        
        try:
            response = self.model.generate_content(prompt.format(text=raw_text[:10000])) # Limit context if needed
            # Clean up potential markdown code blocks
            text_response = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(text_response)
            # Add style_guide as an alias for backward compatibility
            if 'style_summary' in result and 'style_guide' not in result:
                result['style_guide'] = result['style_summary']
            return result
        except Exception as e:
            logger.error(f"Error in analyze_style: {e}")
            return {"style_summary": "Default professional tone (Error during analysis).", "style_guide": "Default professional tone (Error during analysis).", "examples": []}

    def generate_post(self, profile, topic):
        """
        Generates a post based on the profile and topic using Few-Shot Prompting.
        Must check if profile.examples exists before using it.
        """
        if not self.model:
            logger.error("VoiceEngine model is not initialized.")
            return "Error: AI model not available."

        # Check if profile has examples (user's uploaded past work)
        examples = profile.get_examples() if hasattr(profile, 'get_examples') else []
        
        if not examples:
            # Fallback: generate without few-shot examples
            logger.warning("No examples found in profile. Generating post without few-shot learning.")
            style_guide = getattr(profile, 'style_guide', 'Professional tone')
            prompt = f"""
            You are a content writer. Write a social media post about: "{topic}".
            Style: {style_guide}
            Keep it under 280 characters unless specified otherwise.
            """
        else:
            # Use Few-Shot prompting with examples
            examples_text = "\n\n".join([f"Example {i+1}: {ex}" for i, ex in enumerate(examples[:3])])
            prompt = f"""
Here are 3 examples of the user's past writing style. Study the sentence length, vocabulary, and tone.

{examples_text}

Now write a new post about {topic} MIMICKING this style exactly.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in generate_post: {e}")
            return "Error generating content."
