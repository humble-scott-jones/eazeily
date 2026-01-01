import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

class VoiceEngine:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_style(self, raw_text):
        """
        Analyzes raw text to extract a style guide and examples.
        Returns a JSON object with 'style_guide' and 'examples'.
        """
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
            print(f"Error in analyze_style: {e}")
            return {"style_guide": "Default professional tone.", "examples": []}

    def generate_post(self, profile, topic):
        """
        Generates a post based on the profile and topic using Few-Shot Prompting.
        """
        examples = profile.get_examples()
        style_guide = profile.style_guide
        
        prompt = f"""
        You are a ghostwriter mimicking a specific voice.
        
        Style Guide:
        {style_guide}
        
        Here are examples of my previous writing:
        """
        
        for ex in examples:
            prompt += f"- {ex}\n"
            
        prompt += f"""
        
        Task: Write a new social media post about: "{topic}".
        Keep it under 280 characters unless specified otherwise.
        Match the style and tone of the examples exactly.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in generate_post: {e}")
            return "Error generating content."
