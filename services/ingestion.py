import requests
import google.generativeai as genai
import os

def ingest_url(url):
    """
    Fetches markdown content from a URL using Jina AI.
    """
    try:
        response = requests.get(f"https://r.jina.ai/{url}")
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error ingesting URL {url}: {e}")
        return ""

def ingest_file(path):
    """
    Uploads a file to Gemini using the File API.
    Returns the file object (or text content if we process it immediately).
    
    Note: For the Voice Engine 'analyze_style', we typically need raw text.
    If the file is a PDF/Image, we might need Gemini to describe it or extract text.
    For simplicity in this protocol, assuming text-based files or letting Gemini handle it.
    """
    try:
        # Ensure API key is set for genai
        if not os.getenv("GENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
             print("Warning: No API Key found for Gemini File Upload")
             
        # Upload the file
        sample_file = genai.upload_file(path=path, display_name="User Upload")
        
        # For the purpose of 'analyze_style' which expects text in our current implementation,
        # we might need to actually get the content. 
        # However, the prompt asked to use `genai.upload_file(path)`.
        # If we pass the file URI to the model, we need to adjust VoiceEngine.
        # But VoiceEngine.analyze_style takes `raw_text`.
        # Let's assume for now we return the file object, and the caller handles it,
        # OR we read the file if it's a text file.
        
        # Since the prompt specifically asked for `genai.upload_file(path)`, I will stick to that.
        return sample_file
    except Exception as e:
        print(f"Error ingesting file {path}: {e}")
        return None
