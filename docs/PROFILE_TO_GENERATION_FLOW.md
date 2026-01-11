# Profile to Content Generation Flow

## Overview
This document describes the complete data flow from brand profile creation/editing through to AI-powered content generation in Eazeily.

## Architecture

### Database Layer
- **Table**: `voice_profile`
- **Model**: `VoiceProfile` (models.py)
- **Key Fields**:
  - Basic: `business_name`, `industry`, `timezone`
  - Brand Voice: `brand_voice`, `tone`, `target_audience`, `key_offer`, `voice_rules`
  - Lists (JSON): `platforms`, `brand_keywords`, `goals`, `writing_samples`
  - Additional: `brand_inspirations`, `brand_anti_inspirations`, `customers`

### API Layer
- **Endpoint**: `/api/profile` (GET, POST)
- **Route**: `routes/profile_routes.py`
- **Functions**:
  - `GET`: Retrieves user profile with all fields
  - `POST`: Saves/updates profile with validation

### UI Layer
1. **Profile Creation**: `/onboarding` or `/onboarding_wizard`
   - Initial profile setup during onboarding
   - Required fields: business_name, industry, brand_voice, target_audience, key_offer, writing_samples
   - Optional: URL scraping for auto-fill

2. **Profile Editing**: `/profile`
   - Standalone page for viewing and editing profile
   - All fields editable
   - Loads existing data via `/api/profile` GET
   - Saves updates via `/api/profile` POST

3. **Dashboard**: `/dashboard`
   - Content creation interface
   - Profile data flows transparently to generator

## Data Flow: Profile → Content Generation

### Step 1: Profile Save
```
User Form (profile.html or onboarding_wizard.html)
  ↓
POST /api/profile
  ↓
profile_routes.py: api_profile()
  ↓
VoiceProfile.query.filter_by(user_id=current_user.id).first()
  - If exists: Update existing record
  - If not exists: Create new VoiceProfile
  ↓
Map form data to model fields:
  - company → business_name
  - tone → tone AND brand_voice (if brand_voice not set)
  - Arrays (platforms, keywords) → JSON columns
  ↓
db.session.commit()
  ↓
Return: {"ok": true, "id": profile.id}
```

### Step 2: Profile Retrieval
```
User visits /dashboard
  ↓
JavaScript loads: dashboard.js
  ↓
Optional: Fetch /api/profile for display
  ↓
profile_routes.py: api_profile() GET
  ↓
VoiceProfile.query.filter_by(user_id=current_user.id).first()
  ↓
Build response with all fields:
  - profile.business_name → company
  - profile.get_platforms() → platforms array
  - profile.get_brand_keywords() → keywords array
  ↓
Return: {"ok": true, "profile": {...}}
```

### Step 3: Content Generation
```
User clicks "Generate" on dashboard
  ↓
POST /api/generate
Body: {
  "task_type": "post",
  "topic": "user's topic",
  "platform": "instagram",
  "ad_objective": "awareness" (if applicable)
}
  ↓
generate_routes.py: _handle_generate()
  ↓
1. Validate task_type and required fields
2. Check GENAI_API_KEY is configured
3. Fetch user profile:
   profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
  ↓
If profile exists:
  - Load all profile data (business_name, brand_voice, etc.)
  - Extract: writing_samples, brand_keywords, voice_rules
  - Profile is "hot" - all data loaded in single query
  ↓
If profile is None:
  - Use dummy profile with defaults
  - Log warning
  - Set profile_missing flag
  ↓
4. Build context from request + profile:
   context = {
     "ad_objective": request.ad_objective,
     "target_audience": profile.target_audience,
     ...
   }
  ↓
5. Call VoiceEngine:
   content = voice_engine.generate_expert_content(
     profile,
     topic,
     task_type,
     platform,
     **context
   )
  ↓
services/voice_engine.py: generate_expert_content()
  ↓
Extract profile data:
  - brand_voice = profile.brand_voice
  - brand_keywords = profile.get_brand_keywords()
  - writing_samples = profile.get_writing_samples()
  - voice_rules = profile.voice_rules
  ↓
Build AI prompt with:
  - Task definition (from task_registry.py)
  - Platform hints (from generator.py)
  - Profile context (brand voice, keywords, rules)
  - Writing samples (for style matching)
  - User topic and dynamic inputs
  ↓
Call Gemini AI API
  ↓
Post-process response:
  - Apply platform rules (character limits, hashtags)
  - Format output
  ↓
Return generated content
  ↓
generate_routes.py returns:
{
  "status": "success",
  "content": "Generated post text...",
  "task_type": "post",
  "platform": "instagram",
  "profile_missing": false (or true if no profile)
}
  ↓
Dashboard displays content in result box
  ↓
User copies content to clipboard
```

## Profile Fields → AI Prompt Mapping

| Profile Field | Used In Prompt | Purpose |
|--------------|----------------|---------|
| `business_name` | Company context | Identifies the brand in generated content |
| `industry` | Industry context | Applies industry-specific best practices |
| `brand_voice` | Tone instructions | Sets overall communication style |
| `target_audience` | Audience context | Tailors messaging to specific demographic |
| `key_offer` | Value prop | Emphasizes unique selling points |
| `voice_rules` | Writing constraints | Enforces dos and don'ts |
| `writing_samples` | Few-shot examples | Matches writing style and rhythm |
| `brand_keywords` | Keyword context | Incorporates brand-specific terminology |
| `platforms` | Not directly used | For UI defaults and filtering |
| `goals` | Context hints | Aligns content with business objectives |

## Key Integration Points

### 1. Profile API Contract
```python
# GET /api/profile Response
{
  "ok": true,
  "profile_status": "loaded",
  "profile": {
    "id": 123,
    "company": "Acme Corp",
    "industry": "software",
    "tone": "Professional and friendly",
    "platforms": ["instagram", "linkedin"],
    "brand_keywords": ["innovative", "reliable"],
    "goals": ["engagement", "leads"],
    "target_audience": "Small business owners",
    "key_offer": "Streamlined workflow automation",
    "voice_rules": "Always use inclusive language",
    "writing_samples": ["Sample 1...", "Sample 2..."],
    ...
  }
}

# POST /api/profile Request
{
  "company": "Acme Corp",
  "industry": "software",
  "tone": "Professional and friendly",
  "platforms": ["instagram", "linkedin"],
  "brand_keywords": ["innovative", "reliable"],
  "goals": ["engagement", "leads"],
  "target_audience": "Small business owners",
  "key_offer": "Streamlined workflow automation",
  "voice_rules": "Always use inclusive language",
  "writing_samples": ["Sample 1...", "Sample 2..."]
}
```

### 2. Generation API Contract
```python
# POST /api/generate Request
{
  "task_type": "post",
  "topic": "Our new product launch",
  "platform": "instagram",
  "ad_objective": "awareness" (optional, for ads)
}

# Response
{
  "status": "success",
  "content": "🚀 Exciting news! We just launched...",
  "task_type": "post",
  "platform": "instagram",
  "profile_missing": false
}
```

## Error Handling

### Missing Profile
- If user has no profile, generation still works with defaults
- Response includes `"profile_missing": true` and `"redirect": "/onboarding"`
- Dashboard should prompt user to complete profile

### Invalid Fields
- Profile API validates required fields (company, industry, tone)
- Returns 400 with error message if validation fails
- Frontend shows inline error and allows retry

### API Key Missing
- Generation returns 503 if GENAI_API_KEY not configured
- Error code: "missing_api_key"
- Message: "AI service is not configured"

## Testing Strategy

### Profile Save/Load
```python
# Test profile creation
POST /api/profile → 200 OK
GET /api/profile → Returns saved data

# Test profile update
POST /api/profile (with existing profile) → 200 OK
GET /api/profile → Returns updated data

# Test complex fields
POST /api/profile (with arrays, long text) → 200 OK
Verify all fields persist correctly
```

### Generation Flow
```python
# Test with profile
1. Create profile via POST /api/profile
2. Generate content via POST /api/generate
3. Verify content reflects profile data

# Test without profile
1. Don't create profile
2. Generate content via POST /api/generate
3. Verify defaults are used
4. Verify response includes profile_missing flag
```

## Performance Considerations

### Database Queries
- **Optimized**: Single query to fetch entire profile
- VoiceProfile has all fields as columns, no additional joins needed
- Writing samples and keywords stored as JSON in single column

### Caching
- Currently no caching (profile fetched on each generation request)
- Future: Consider caching profile in session or Redis
- Profile changes are infrequent, good candidate for caching

### API Calls
- Gemini API is rate-limited (check quota)
- Consider request queuing for high-volume users
- Timeout set to 45 seconds (may need adjustment)

## Future Enhancements

### Profile Management
- [ ] Profile versioning (track changes over time)
- [ ] Profile templates (save multiple profiles, switch between them)
- [ ] Profile export/import (JSON format)
- [ ] Profile preview (show how profile affects generated content)

### Generation
- [ ] Profile-aware suggestions (suggest topics based on industry/goals)
- [ ] A/B testing (generate multiple variants, track performance)
- [ ] Content calendar (schedule posts, bulk generation)
- [ ] Analytics (track which profile settings generate best content)

### Integration
- [ ] Direct social media posting (connect to Buffer/Hootsuite)
- [ ] Image generation (DALL-E integration for visuals)
- [ ] Team collaboration (share profiles across team members)

## Troubleshooting

### Profile Not Saving
1. Check server logs for validation errors
2. Verify required fields are present (company, industry, tone)
3. Check database connection
4. Test with minimal payload (only required fields)

### Profile Not Loading in Generator
1. Verify user is authenticated
2. Check profile exists: `SELECT * FROM voice_profile WHERE user_id = ?`
3. Verify profile has data: `business_name`, `brand_voice` not null
4. Check server logs for query errors

### Generated Content Doesn't Match Profile
1. Verify profile fields are populated correctly
2. Check writing_samples are substantial (at least 2-3 good examples)
3. Review voice_rules for contradictions
4. Test with simpler/clearer brand_voice description
5. Check Gemini API response for truncation/errors

## Related Files

### Backend
- `routes/profile_routes.py` - Profile API endpoints
- `routes/generate_routes.py` - Content generation endpoints
- `services/voice_engine.py` - AI prompt builder and API integration
- `services/task_registry.py` - Task definitions
- `models.py` - VoiceProfile model and methods

### Frontend
- `templates/profile.html` - Standalone profile editing page
- `templates/onboarding_wizard.html` - Initial profile creation
- `templates/dashboard.html` - Content generator interface
- `static/dashboard.js` - Generator logic and API calls

### Configuration
- `static/content/config.json` - Industries, platforms, content types
- `generator.py` - Platform hints and formatting rules

## Contact & Support
For issues with profile data flow:
1. Check server logs: `server.log` or `server_5001.log`
2. Test profile API directly: `curl http://localhost:5001/api/profile`
3. Verify database: `SELECT * FROM voice_profile LIMIT 5`
