# Brand Discovery & Multi-Task Engine Implementation Guide

## Overview
This implementation adds the "Secret Sauce" - a comprehensive brand identity system that captures business logic, target audience psychology, and few-shot writing samples to ensure AI-generated content sounds human.

## Architecture

### Database Schema (models.py)
The `VoiceProfile` model now includes "Secret Sauce" fields:

```python
class VoiceProfile(db.Model):
    # Existing fields
    id, user_id, industry, business_name, defaults, examples
    
    # NEW "Secret Sauce" fields
    target_audience    # Text - The "Who" 
    brand_voice        # String(255) - The "Vibe"
    key_offer         # Text - The "Hook"
    voice_rules       # Text - The "Constraints"
    writing_samples   # Text (JSON) - The "Rhythm"
```

**Helper Methods:**
- `set_writing_samples(list)` - Store samples as JSON
- `get_writing_samples()` - Retrieve samples as list

### Routes

#### 1. Onboarding Routes (`routes/onboarding_routes.py`)
- `GET /onboarding` - Display brand setup form
- `POST /onboarding` - Save complete brand profile
- `POST /onboarding/assist-voice` - AI-assisted voice description

#### 2. Generate Routes (`routes/generate_routes.py`)  
- `POST /api/generate` - Multi-task content generation
  - Parameters: `topic`, `platform`, `task_type`
  - Task types: `post`, `ad`, `email`, `review`

#### 3. Admin Routes (`app.py`)
- `GET /reset-brand-engine` - Reset database schema (auth required)

### Templates

#### 1. Onboarding Page (`templates/onboarding.html`)
**Features:**
- Industry dropdown with 6 options
- Lazy Mode prefilling (5 industry defaults)
- AI assistant button for brand voice
- Writing samples textarea (blank-line separator)
- All Secret Sauce fields with helpful labels

**JavaScript Functions:**
- `prefill()` - Auto-fills audience, voice, offer based on industry
- `assistVoice()` - Calls AI to generate brand voice description

#### 2. Dashboard (`templates/dashboard.html`)
**Features:**
- Task selector with 4 icon buttons
- Dynamic form labels based on task type
- Platform dropdown (shown only for posts)
- Enhanced copy button with feedback

**JavaScript Functions:**
- `selectTask(taskType)` - Updates UI for selected task
- `copyToClipboard()` - Copies generated content

### Services

#### Voice Engine (`services/voice_engine.py`)
**New Method: `generate_expert_content()`**

```python
def generate_expert_content(user_profile, topic, task_type, platform=None):
    """
    Generate content using Secret Sauce approach.
    
    Args:
        user_profile: VoiceProfile with Secret Sauce fields
        topic: Content topic/input
        task_type: 'post', 'ad', 'email', or 'review'
        platform: Target platform (for posts)
    
    Returns:
        str: Generated content
    """
```

**Prompt Structure:**
1. System instruction with business context
2. Audience, voice, constraints, and offer
3. Few-shot examples (writing samples)
4. Task-specific prompt
5. Guardrails against conversational filler

## Usage Flow

### Setup Flow
1. User logs in
2. Navigates to `/onboarding` (Brand Setup)
3. Fills in business details:
   - Business name
   - Industry (optional: use Lazy Mode prefill)
   - Target audience
   - Brand voice (optional: use AI assistant)
   - Key offer
   - Voice rules/constraints
   - 2-3 writing samples
4. Submits form
5. Redirected to dashboard

### Generation Flow
1. User navigates to `/dashboard`
2. Selects task type (post, ad, email, review)
3. UI updates with appropriate prompt
4. Enters topic/content
5. Selects platform (if post)
6. Clicks generate
7. AI uses Secret Sauce fields to create content
8. User copies result

## Lazy Mode Defaults

Industry defaults for instant setup:

```javascript
'Real Estate': {
    audience: "Local families looking to upsize or first-time buyers",
    voice: "Professional, reassuring, and expert-level",
    offer: "Free Home Valuation Report"
}

'Pottery': {
    audience: "Creative hobbyists looking for screen-free escape",
    voice: "Inspirational, earthy, and encouraging",
    offer: "10% off your first 4-week workshop"
}

// + Fitness, Restaurant, Consulting
```

## API Examples

### Onboarding Submission
```bash
POST /onboarding
Content-Type: application/x-www-form-urlencoded

business_name=Smith+Real+Estate
industry=Real+Estate
target_audience=Local+families
brand_voice=Professional+and+reassuring
key_offer=Free+Home+Valuation
voice_rules=Use+y'all
writing_samples=Sample+1

Sample+2
```

### Multi-Task Generation
```bash
POST /api/generate
Content-Type: application/json

{
  "topic": "New listing in downtown",
  "platform": "LinkedIn",
  "task_type": "post"
}
```

### AI-Assisted Voice
```bash
POST /onboarding/assist-voice
Content-Type: application/json

{
  "business_name": "Smith Real Estate",
  "industry": "Real Estate"
}

Response: {
  "brand_voice": "Professional, trustworthy, and locally-focused..."
}
```

## Testing

### Unit Tests
- `test_onboarding_routes.py` - Onboarding flow and validation
- `test_multitask_generation.py` - Generation engine with task types
- `test_voice_profile_secret_sauce.py` - Model field storage/retrieval

### Manual Testing
1. Start server: `PORT=5001 python3 app.py`
2. Create test user or login
3. Navigate to `/onboarding`
4. Fill form with test data
5. Navigate to `/dashboard`
6. Test each task type
7. Verify generated content

## Backward Compatibility

The implementation maintains compatibility with existing profiles:

1. **Nullable Fields** - All Secret Sauce fields are optional
2. **Fallback Logic** - If Secret Sauce fields are empty, falls back to:
   - Old `generate_post()` method
   - Industry pack defaults
   - Old `defaults` and `examples` fields
3. **Dual Storage** - Both old (defaults/examples) and new fields coexist

## Why This Works (The Secret Sauce)

### 1. Business Logic
- Industry context provides domain knowledge
- Key offer gives clear CTA direction
- Business name adds personalization

### 2. Audience Psychology  
- Target audience informs tone and messaging
- Speaks directly to customer needs
- Creates relevance and connection

### 3. Few-Shot Learning
- Writing samples teach rhythm and vocabulary
- AI mimics real examples, not generic templates
- Captures unique voice fingerprint

### 4. Constraint-Based Rules
- Voice rules enforce brand consistency
- Prevents off-brand language
- Ensures compliance (character limits, emoji usage, etc.)

Together, these elements create a 360-degree brand view that enables AI to generate content that sounds like a human partner, not a machine.

## Future Enhancements

Potential improvements:
1. Add more industry defaults
2. Import writing samples from social media
3. A/B test generated variants
4. Voice consistency scoring
5. Template library based on task types
6. Multi-language support
