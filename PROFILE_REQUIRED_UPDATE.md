# Progressive Profile Enhancement for Content Generation

## What Changed

Content generation now uses a **progressive enhancement approach**:
- ✅ Works with minimal profile data (business name + industry)
- ✅ Gets better as you add more profile details
- ✅ Provides specific guidance on what's missing

## User Experience Flow

### Minimal Required Data
- **Business Name** (required)
- **Industry** (required)

### Optional Data That Improves Quality
- Brand voice/tone
- Target audience
- Brand keywords
- Niche keywords
- Key offering
- Voice rules
- Writing samples

### Progressive Enhancement
1. **No profile** → Error: "Please create your brand profile" → Directed to `/onboarding`
2. **Missing required fields** → Error: "Your profile is missing: business name, industry" → Specific guidance
3. **Minimal profile** → ✅ Generation works! → Logged suggestion: "Profile could be enhanced with: brand voice, target audience..."
4. **Complete profile** → ✅ Best quality generation with full brand context

## Error Messages

### "Please create your brand profile to start generating content"
**Cause**: No profile exists for your account
**Fix**: Click 'Settings' or visit `/onboarding` to create profile

### "Your profile is missing: business name, industry"
**Cause**: Profile exists but missing critical required fields
**Fix**: Add the specific fields mentioned in Settings or `/onboarding`
**Note**: Error message shows exactly which fields are missing

### "AI service not configured"
**Cause**: `GENAI_API_KEY` environment variable not set
**Fix**: Add API key to `.env` file (see below)

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

### 1. Configure API Key (Required for AI Features)
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

### 2. Create Minimal Profile (Required)
Navigate to `/onboarding` and provide at minimum:
- **Business name** (required)
- **Industry** (required)

### 3. Enhance Your Profile (Recommended)
Add these fields for better content quality:
- Brand voice/tone
- Target audience
- Key offering
- Brand keywords
- Niche keywords
- Voice rules
- Writing samples

## Why Progressive Enhancement?

The profile acts as a "master prompt" providing context to AI. With progressive enhancement:
- ✅ **Start quickly** - Just business name and industry gets you started
- ✅ **Improve over time** - Add more details as you learn what works
- ✅ **Clear guidance** - Error messages tell you exactly what's missing
- ✅ **Better results** - More profile data = more on-brand content

### Minimal Profile Content
With just business name and industry:
- Generic but functional content
- Basic industry context
- Standard tone

### Complete Profile Content  
With full profile data:
- On-brand voice and tone
- Target audience-specific messaging
- Brand-specific terminology
- Customer segment awareness
- Voice matching from writing samples

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
