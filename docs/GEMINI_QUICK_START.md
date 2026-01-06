# Gemini API Setup - Quick Reference

## Overview

The Gemini API powers three critical features in Eazeily:
1. **Content Generation** - AI-generated social posts, emails, ads
2. **AI Voice Helper** - Interactive chat to build brand voice
3. **Brand Voice Analysis** - Automated brand voice descriptions

## Setup in 3 Steps

### 1. Get API Key
Visit: https://aistudio.google.com/app/apikey
- Sign in with Google account
- Click "Create API Key"
- Copy the key

### 2. Configure the Key
Add to `.env` file:
```bash
GENAI_API_KEY=your_api_key_here
```

### 3. Verify Setup
Run the test script:
```bash
python3 scripts/test_gemini_api.py
```

## Expected Output (Working Setup)

```
======================================================================
Gemini API Configuration Test
======================================================================

1. Checking API Key Configuration
----------------------------------------------------------------------
✅ PASS: API key found (length: 39 characters)

2. Checking google.generativeai Package
----------------------------------------------------------------------
✅ PASS: google.generativeai imported successfully

3. Testing Gemini API Connection
----------------------------------------------------------------------
Sending test prompt to Gemini API...
✅ PASS: Successfully generated content from Gemini API
   Response: Hello from Gemini!

4. Testing AI Voice Helper
----------------------------------------------------------------------
Testing voice helper for: TechCorp (Software)
✅ PASS: AI voice helper generated brand voice
   Generated voice: TechCorp should adopt a professional yet approachable...

5. Testing Content Generation
----------------------------------------------------------------------
Generating test social post...
✅ PASS: Content generation successful
   Generated content: Exciting news! We're launching...

======================================================================
Test Summary
======================================================================
  ✅ PASS: API Key Configuration
  ✅ PASS: Package Import
  ✅ PASS: API Connection
  ✅ PASS: AI Voice Helper
  ✅ PASS: Content Generation

Results: 5 passed, 0 failed, 0 skipped

✅ All tests passed! Gemini API is working correctly.
```

## Common Issues

### Issue: "No API key found"
**Fix**: Add `GENAI_API_KEY` to `.env` file

### Issue: "Cannot import google.generativeai"
**Fix**: `pip install google-generativeai`

### Issue: "Invalid API key"
**Fix**: Verify key from https://aistudio.google.com/app/apikey

### Issue: "Quota exceeded"
**Fix**: Wait for quota reset or upgrade plan

## Cost & Limits

**Free Tier:**
- 15 requests per minute
- 1,500 requests per day
- No credit card required

**Pricing**: https://ai.google.dev/pricing

## Full Documentation

For detailed setup instructions, troubleshooting, and best practices:
📖 **See [docs/GEMINI_SETUP.md](../docs/GEMINI_SETUP.md)**

## Security Checklist

- ✅ Never commit `.env` file (already in `.gitignore`)
- ✅ Use different keys for dev/staging/production
- ✅ Rotate keys quarterly
- ✅ Monitor usage at https://aistudio.google.com/

## Getting Help

1. Run diagnostic: `python3 scripts/test_gemini_api.py`
2. Check logs for detailed error messages
3. See [docs/GEMINI_SETUP.md](../docs/GEMINI_SETUP.md) for troubleshooting
