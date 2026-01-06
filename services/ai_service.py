import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Preferred models in order of priority
PREFERRED_MODELS = [
    'gemini-1.5-flash',
    'gemini-1.5-flash-001',
    'gemini-1.5-pro',
    'gemini-pro',
]

def get_best_available_model():
    """
    Attempts to find the best available Gemini model from the user's API key.
    Falls back to 'gemini-1.5-flash' if listing fails or no match found.
    """
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("No API key configured for AI service.")
        return 'gemini-1.5-flash' # Default expectation

    try:
        genai.configure(api_key=api_key)
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        logger.info(f"Available Gemini Models: {available_models}")

        # Check for preferred models
        for preference in PREFERRED_MODELS:
            # Check exact match or 'models/' prefix match
            if preference in available_models or f"models/{preference}" in available_models:
                logger.info(f"Selected AI Model: {preference}")
                return preference
        
        # If no preferred model matches, take the first one that looks like 'gemini'
        for m in available_models:
            if 'gemini' in m:
                logger.warning(f"Preferred models not found. Falling back to: {m}")
                return m
                
    except Exception as e:
        logger.error(f"Failed to list models: {e}. Defaulting to gemini-1.5-flash")
    
    return 'gemini-1.5-flash'

def get_generative_model(model_name=None, system_instruction=None):
    """
    Factory for getting a configured GenerativeModel.
    Resolves the model name dynamically if not provided.
    """
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    
    if not model_name:
        model_name = get_best_available_model()

    return genai.GenerativeModel(model_name, system_instruction=system_instruction)
