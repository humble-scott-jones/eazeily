import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables
load_dotenv()

def check_models():
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: No API key found in environment variables (GENAI_API_KEY or GOOGLE_API_KEY)")
        return

    try:
        genai.configure(api_key=api_key)
        print("✅ API Key configured. Listing available models that support 'generateContent':")
        print("-" * 50)
        
        found_flash = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"• {m.name}")
                if "gemini-1.5-flash" in m.name:
                    found_flash = True
        
        print("-" * 50)
        if found_flash:
            print("✅ 'gemini-1.5-flash' model family found.")
        else:
            print("⚠️ 'gemini-1.5-flash' NOT found in the list. This usually means:")
            print("  1. The API key is restricted or from a region/project without access.")
            print("  2. You need to enable the API in Google AI Studio.")
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    check_models()
