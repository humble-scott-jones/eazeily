# Gemini API Setup Guide

This guide explains how to set up the Google Gemini API for AI-powered features in Eazeily.

## What Features Require Gemini API?

The following features require a configured Gemini API key:

1. **Content Generation** - Automatically generate social media posts, emails, ads, etc.
2. **AI Voice Helper** - Interactive chat to help build your brand voice profile
3. **Brand Voice Analysis** - AI-assisted brand voice description generation

## Getting Your API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

## Configuration

### Option 1: Using .env File (Recommended for Local Development)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```bash
   GENAI_API_KEY=your_api_key_here
   ```

3. The application will automatically load this when it starts.

### Option 2: Environment Variable

Export the API key in your terminal:
```bash
export GENAI_API_KEY=your_api_key_here
```

Or add it to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
echo 'export GENAI_API_KEY=your_api_key_here' >> ~/.bashrc
source ~/.bashrc
```

### Option 3: Production Deployment

For production deployments (Railway, Render, etc.), set the environment variable in your deployment platform:

- **Railway**: Settings → Variables → Add `GENAI_API_KEY`
- **Render**: Environment → Environment Variables → Add `GENAI_API_KEY`
- **Heroku**: Settings → Config Vars → Add `GENAI_API_KEY`

## Verifying Your Setup

Run the verification script to check if the Gemini API is properly configured:

```bash
python3 scripts/test_gemini_api.py
```

This script will check:
- ✅ API key is configured
- ✅ `google-generativeai` package is installed
- ✅ API key is valid and can generate content
- ✅ Voice helper works correctly
- ✅ Content generation works correctly

### Expected Output (Success)

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
   Content generation and AI voice helper are ready to use.
```

## Troubleshooting

### Error: "No API key found in environment"

**Solution**: Make sure you've set `GENAI_API_KEY` in your `.env` file or as an environment variable.

### Error: "Cannot import google.generativeai"

**Solution**: Install the required package:
```bash
pip install google-generativeai
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### Error: "API call failed: Invalid API key"

**Solutions**:
1. Verify your API key is correct (copy/paste carefully)
2. Check if the API key has been revoked or expired
3. Generate a new API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Error: "API quota exceeded"

**Solutions**:
1. Check your [API usage dashboard](https://aistudio.google.com/)
2. Wait for quota to reset (usually daily/monthly depending on plan)
3. Upgrade to a paid plan if needed

### Warning: "google.generativeai is deprecated"

This is a future warning. The package currently works but Google recommends migrating to `google.genai` in the future. The application will continue to work with the current package.

## API Rate Limits

Gemini API has rate limits that vary by plan:

- **Free tier**: 15 requests per minute, 1,500 requests per day
- **Paid tier**: Higher limits based on your plan

If you encounter rate limit errors, consider:
1. Adding delays between requests
2. Implementing request queuing
3. Upgrading to a paid plan

## Security Best Practices

1. **Never commit API keys** - The `.env` file is in `.gitignore` to prevent this
2. **Rotate keys regularly** - Generate new keys quarterly
3. **Use environment-specific keys** - Different keys for dev/staging/production
4. **Monitor usage** - Check the [API dashboard](https://aistudio.google.com/) regularly
5. **Restrict key access** - Use API key restrictions if available

## Alternative: Using GOOGLE_API_KEY

The application also supports `GOOGLE_API_KEY` as an alternative environment variable name:

```bash
GOOGLE_API_KEY=your_api_key_here
```

The application will check for `GENAI_API_KEY` first, then fall back to `GOOGLE_API_KEY`.

## Cost Information

Gemini API pricing:
- **Free tier**: Available with rate limits
- **Paid tier**: Pay-as-you-go pricing

Check current pricing at: https://ai.google.dev/pricing

## Getting Help

If you continue to have issues:

1. Run the diagnostic script: `python3 scripts/test_gemini_api.py`
2. Check the application logs for detailed error messages
3. Verify your API key at [Google AI Studio](https://aistudio.google.com/)
4. Check [Gemini API documentation](https://ai.google.dev/docs)
