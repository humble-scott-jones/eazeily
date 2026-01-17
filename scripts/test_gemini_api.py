#!/usr/bin/env python3
"""
Test script to verify Gemini API configuration and functionality.

This script checks:
1. API key is configured
2. google.genai package is installed
3. API key is valid and can generate content
4. Voice helper and content generation work

Usage:
    python3 scripts/test_gemini_api.py

Environment variables required:
    GENAI_API_KEY or GOOGLE_API_KEY
"""
import os
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def print_section(text):
    """Print a formatted section."""
    print(f"\n{text}")
    print("-" * 70)

def test_api_key():
    """Check if API key is configured."""
    print_section("1. Checking API Key Configuration")
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ FAIL: No API key found in environment")
        print("\nTo fix this:")
        print("1. Get an API key from: https://aistudio.google.com/app/apikey")
        print("2. Add to your .env file:")
        print("   GENAI_API_KEY=your_api_key_here")
        print("3. Or export it:")
        print("   export GENAI_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ PASS: API key found (length: {len(api_key)} characters)")
    return True

def test_import():
    """Test importing google.genai."""
    print_section("2. Checking google.genai Package")
    try:
        import google.genai as genai  # type: ignore
        print("✅ PASS: google.genai imported successfully")
        return True
    except ImportError as e:
        print(f"❌ FAIL: Cannot import google.genai: {e}")
        print("\nTo fix this:")
        print("  pip install google-genai")
        return False

def test_api_connection():
    """Test connecting to Gemini API and generating content."""
    print_section("3. Testing Gemini API Connection")
    
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  SKIP: No API key to test")
        return None
    
    try:
        import google.genai as genai  # type: ignore
        client = genai.Client(api_key=api_key)
        
        # Test with a simple prompt
        print("Sending test prompt to Gemini API...")
        prompt = "Say 'Hello from Gemini!' in one sentence."
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        
        text = getattr(response, "text", "") or getattr(response, "candidates", None)
        if response and text:
            output_text = response.text if hasattr(response, "text") else str(text)
            print("✅ PASS: Successfully generated content from Gemini API")
            print(f"   Response: {output_text.strip() if isinstance(output_text, str) else output_text}")
            return True
        else:
            print("❌ FAIL: No content generated")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: API call failed: {e}")
        print("\nPossible causes:")
        print("1. Invalid API key")
        print("2. Network connectivity issues")
        print("3. API quota exceeded")
        print("4. API service temporarily unavailable")
        return False

def test_voice_helper():
    """Test the AI voice helper endpoint functionality."""
    print_section("4. Testing AI Voice Helper")
    
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  SKIP: No API key to test")
        return None
    
    try:
        import google.genai as genai  # type: ignore
        client = genai.Client(api_key=api_key)
        
        # Simulate the voice helper prompt
        business_name = "TechCorp"
        industry = "Software"
        prompt = f"""
You are a brand strategist. Based on the following business information, write a 3-sentence Brand Voice profile that captures the tone and personality this business should use in marketing.

Business Name: {business_name}
Industry: {industry}

Output only the brand voice description (2-3 sentences). No preamble, no "Here is", just the description.
Focus on adjectives that describe the tone (e.g., professional, friendly, authoritative, playful).
"""
        
        print(f"Testing voice helper for: {business_name} ({industry})")
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        
        if response and getattr(response, "text", ""):
            print("✅ PASS: AI voice helper generated brand voice")
            print(f"   Generated voice: {response.text.strip()[:100]}...")
            return True
        else:
            print("❌ FAIL: No brand voice generated")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Voice helper test failed: {e}")
        return False

def test_content_generation():
    """Test content generation functionality."""
    print_section("5. Testing Content Generation")
    
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  SKIP: No API key to test")
        return None
    
    try:
        from services.voice_engine import VoiceEngine
        
        # Create a simple test profile
        class TestProfile:
            industry = 'tech'
            business_name = 'TestCo'
            target_audience = 'Developers'
            brand_voice = 'Professional and innovative'
            key_offer = 'Free trial'
            voice_rules = ''
            def get_writing_samples(self):
                return []
        
        engine = VoiceEngine()
        if not engine.model:
            print("❌ FAIL: VoiceEngine model not initialized")
            return False
        
        print("Generating test social post...")
        topic = "New product launch"
        platform = "LinkedIn"
        
        # Prefer generate_expert_content when present and callable
        expert_fn = getattr(engine, "generate_expert_content", None)
        if callable(expert_fn):
            content = expert_fn(TestProfile(), topic, 'post', platform)
        else:
            content = engine.generate_post(TestProfile(), topic, platform)
        
        content_text = content if isinstance(content, str) else str(content)
        if content and not content_text.startswith("Error"):
            print("✅ PASS: Content generation successful")
            print(f"   Generated content: {content_text[:100]}...")
            return True
        else:
            print(f"❌ FAIL: Content generation returned error: {content_text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Content generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print_header("Gemini API Configuration Test")
    print("\nThis script verifies that the Gemini API is properly configured")
    print("for AI-powered features including content generation and voice helper.")
    
    tests = [
        ("API Key Configuration", test_api_key),
        ("Package Import", test_import),
        ("API Connection", test_api_connection),
        ("AI Voice Helper", test_voice_helper),
        ("Content Generation", test_content_generation),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
        if result is False:
            # If a critical test fails, stop
            if name in ["API Key Configuration", "Package Import"]:
                print("\n⚠️  Critical test failed. Stopping here.")
                break
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    for name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"  {status}: {name}")
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("\nQuick Start:")
        print("1. Get API key: https://aistudio.google.com/app/apikey")
        print("2. Add to .env file: GENAI_API_KEY=your_key_here")
        print("3. Install package: pip install google-genai")
        print("4. Run this test again")
        return 1
    elif skipped == len(results):
        print("\n⚠️  All tests skipped. No API key configured.")
        print("\nTo enable AI features:")
        print("1. Get API key: https://aistudio.google.com/app/apikey")
        print("2. Add to .env file: GENAI_API_KEY=your_key_here")
        return 1
    elif skipped > 0:
        print("\n✅ Basic checks passed, but some tests were skipped.")
        print("   Configure GENAI_API_KEY to run all tests.")
        return 0
    else:
        print("\n✅ All tests passed! Gemini API is working correctly.")
        print("   Content generation and AI voice helper are ready to use.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
