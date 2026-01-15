# Profile-Required Content Generation Fix

## What Changed

Content generation now **requires a brand profile** to ensure high-quality, on-brand content. The dummy profile fallback has been removed.

## User Experience Flow

### Before (Problematic)
1. Click "Generate" → Generic content with no brand context
2. Confusing UX - users didn't know they needed a profile
3. Poor quality output

### After (Fixed)
1. Click "Generate" without profile → Clear error: "Please set up your brand profile"
2. User is directed to `/onboarding` to create profile
3. After profile setup → Generate with full brand context

## Setup Requirements

### 1. Create Brand Profile (Required)
Navigate to `/onboarding` and complete your brand profile:
- Business name
- Industry
- Brand voice
- Target audience
- Key offering
- Brand keywords
- Writing samples

### 2. Configure API Key (Required)
Set up your Gemini API key to enable AI features:

```bash
# Add to .env file
GENAI_API_KEY=your_api_key_here
```

**Get API Key**: https://aistudio.google.com/app/apikey

**Verify Setup**: 
```bash
python3 scripts/test_gemini_api.py
```

See [docs/GEMINI_QUICK_START.md](docs/GEMINI_QUICK_START.md) for detailed instructions.

## Error Messages

### "AI service not configured"
**Cause**: `GENAI_API_KEY` environment variable not set
**Fix**: Add API key to `.env` file (see above)

### "Please set up your brand profile before generating content"
**Cause**: No brand profile exists for your account
**Fix**: Navigate to `/onboarding` and complete profile setup

## Why This Change?

The profile acts as a "master prompt" providing:
- Brand voice and tone
- Target audience context
- Brand keywords
- Niche-specific terminology
- Customer segments
- Writing samples for voice matching

Without this context, AI generates generic content that doesn't match your brand. This change ensures every piece of content is:
- ✅ On-brand
- ✅ Contextual
- ✅ High-quality
- ✅ Immediately usable

## Testing

All tests pass:
- Profile requirement is enforced
- Clear error messages guide users
- Generation works correctly with profile
- Profile data flows into AI prompts

```bash
# Run tests
PYTHONPATH=. pytest tests/test_profile_required_for_generation.py -v
```
