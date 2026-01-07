import os
import requests

try:
    import google.genai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore

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
        if not genai:
            print("Warning: google.genai not available; skipping upload")
            return None

        api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if hasattr(genai, "Client"):
            client = genai.Client(api_key=api_key) if api_key else genai.Client()
            if hasattr(client, "files") and hasattr(client.files, "upload"):
                return client.files.upload(path=path, display_name="User Upload")

        # Legacy compatibility: if upload_file still exists
        if hasattr(genai, "upload_file"):
            return genai.upload_file(path=path, display_name="User Upload")

        print("Warning: No compatible upload method found on google.genai")
        return None
    except Exception as e:
        print(f"Error ingesting file {path}: {e}")
        return None
