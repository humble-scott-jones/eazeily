# AI-Assisted Profile Field Completion Flow

## Overview
This feature enhances the profile completion UX by providing AI-generated suggestions when users click buttons like "Add Brand Keywords" or use field-specific slash commands.

## User Experience Flow

### Before (Old Behavior)
```
User clicks "Add Brand Keywords" button
→ Input box shows: "/keywords " (cursor blinking)
→ User: "What do I type here?" 😕
```

### After (New Behavior)
```
User clicks "Add Brand Keywords" button
→ Command is sent automatically: /keywords
→ Bot responds with AI suggestions:

🏷️ **Add Brand Keywords**

Based on your profile for "Sunny Side Bakery" (Food & Beverage):

1️⃣ Fresh, Artisan, Local, Homemade, Community
2️⃣ Organic, Traditional, Family-owned, Handcrafted
3️⃣ Wholesome, Neighborhood, Authentic, Daily-baked

**Pick a number, or type your own!**

[1] [2] [3] [✏️ Write my own]

User clicks "1" or types their own
→ Field is updated, confirmation shown with progress
```

## Implementation

### Frontend Changes (promptbox.js)
- **Button Action**: Changed from `'prompt'` (pre-fill) to `'command'` (send immediately)
- **Command Mapping**: Added dedicated commands for all 8 profile fields

### Backend Changes

#### 1. Conversation Router (conversation_router.py)
**Added FIELD_COMMANDS mapping:**
```python
FIELD_COMMANDS = {
    '/name': 'business_name',
    '/industry': 'industry',
    '/voice': 'brand_voice',
    '/audience': 'target_audience',
    '/offer': 'key_offer',
    '/samples': 'writing_samples',
    '/keywords': 'brand_keywords',
    '/goals': 'goals',
}
```

**Command Parsing:**
- Bare commands (e.g., `/keywords`) → `field_assistance` task type
- Commands with values (e.g., `/keywords Fresh, Local`) → `update_field` task type

#### 2. Chat Routes (chat_routes.py)
**New Handler Functions:**

1. `_generate_field_suggestions(field, profile)` - Generates 3 AI suggestions
   - Uses Gemini API when available
   - Falls back to smart defaults based on industry
   - Returns contextual suggestions

2. `_handle_field_assistance(field, profile)` - Handles bare field commands
   - Generates suggestions
   - Returns message with buttons
   - Special handling for industry (picker) and writing_samples (no AI)

3. `_handle_direct_field_update(field, value, profile, db)` - Handles field updates
   - Updates the profile field
   - Commits to database
   - Returns confirmation with next steps

## All 8 Profile Fields Covered

| Field | Command | Behavior |
|-------|---------|----------|
| Business Name | `/name` | Shows AI suggestions |
| Industry | `/industry` | Shows industry picker (14 options) |
| Brand Voice | `/voice` | Shows AI suggestions |
| Target Audience | `/audience` | Shows AI suggestions |
| Key Offer | `/offer` | Shows AI suggestions |
| Writing Samples | `/samples` | Asks for paste input (no AI) |
| Brand Keywords | `/keywords` | Shows AI suggestions |
| Goals | `/goals` | Shows AI suggestions |

## AI Suggestions

### Strategy
1. **Try AI First**: Uses Gemini API with business context
2. **Smart Fallbacks**: Industry-appropriate defaults if AI unavailable
3. **Context-Aware**: Considers existing profile data

### Example Prompt to AI
```
Generate 3 different brand keywords suggestions for a business.

Business context:
- Name: Sunny Side Bakery
- Industry: Food & Beverage
- Target audience: Local community members

Return exactly 3 suggestions, one per line. Make them specific to this business.
Each suggestion should be concise (under 100 characters).
```

## User Confirmation Flow

After selecting or typing a value:
```
✅ **Brand Keywords updated!**

**Brand Keywords:** Fresh, Artisan, Local, Homemade, Community

📊 Profile: **75% complete**

Next up: **Goals** - type `/goals` or click below!

[Add Goals] [Start creating →]
```

## Testing

### Test Coverage
- ✅ Bare field commands trigger assistance
- ✅ Field commands with values trigger direct update
- ✅ All 8 profile fields are covered
- ✅ All field commands are in COMMAND_MAP
- ✅ 44/44 tests passing

### Test Files
- `tests/test_field_assistance_flow.py` - New comprehensive tests
- `tests/test_conversation_router.py` - Existing tests still pass

## Error Handling

### AI Service Unavailable
- Falls back to smart defaults
- Logs warning but continues gracefully

### Invalid Field Values
- Validates before saving
- Returns error message with guidance

### Database Errors
- Rolls back transaction
- Returns user-friendly error message

## Benefits

1. **Better UX**: Clear guidance instead of confusion
2. **Faster Completion**: Pre-generated suggestions save time
3. **Contextual**: Suggestions based on actual profile data
4. **Flexible**: Can pick suggestion OR write own
5. **Progress Tracking**: Shows completeness % after each update
6. **Next Steps**: Automatically suggests next missing field

## Future Enhancements

Possible improvements:
- Save user's custom suggestions for learning
- A/B test different suggestion strategies
- Add more fields to the flow
- Multi-language support for suggestions
