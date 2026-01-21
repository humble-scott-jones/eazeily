# Multi-Profile Support Implementation

## Overview
This implementation adds multi-profile support for Pro and Team tier users, allowing them to manage multiple brand profiles for different clients or businesses.

## Features Implemented

### 1. Database Schema
- Added `is_default` (Boolean) field to VoiceProfile
- Added `profile_name` (String 100) field to VoiceProfile
- Created Alembic migration: `20260121_add_multiprofile_support.py`
- Updated User-VoiceProfile relationship to support multiple profiles
- Maintained backward compatibility with `user.voice_profile` property

### 2. Tier-Based Limits
- Free tier: 1 profile maximum
- Pro tier: 3 profiles maximum
- Team tier: Unlimited profiles
- Implemented `User.can_create_profile()` method

### 3. API Endpoints
All endpoints in `/routes/profile_routes.py`:
- `GET /api/profiles` - List all user profiles
- `POST /api/profiles` - Create new profile (enforces tier limits)
- `PUT /api/profiles/<id>/default` - Set profile as default
- `DELETE /api/profiles/<id>` - Delete profile (prevents last deletion)
- `GET /api/profiles/current` - Get currently active profile

### 4. Chat Commands
- `/profiles` - List all profiles with indicators for active/default
- `/switch [name]` - Switch to a different profile (supports partial matching)
- Profile context tracked in session for content generation
- Updated chat generation to use active profile_id

### 5. Profile Switching Logic
- Active profile stored in Flask session
- Falls back to default profile if session not set
- Content generation uses active profile from session
- Profile ID stored in ContentHistory for audit trail

## Testing
- 21 comprehensive tests added
- 12 tests for model methods and API endpoints
- 9 tests for chat commands and profile switching
- All tests passing successfully

## Usage Examples

### API Usage
```python
# List profiles
GET /api/profiles

# Create new profile (Pro/Team tiers)
POST /api/profiles
{
  "profile_name": "Client: Acme Co",
  "business_name": "Acme Corporation",
  "industry": "Technology"
}

# Switch default
PUT /api/profiles/123/default

# Delete profile
DELETE /api/profiles/123
```

### Chat Commands
```
User: /profiles
Bot: Lists all profiles with current marker

User: /switch Client: Acme Co
Bot: Switches to specified profile

User: /post about our new product
Bot: Generates content using active profile
```

## Migration Path
1. Run migration: `alembic upgrade head`
2. Existing profiles automatically set as default
3. Existing code continues to work via `user.voice_profile` property
4. Users can create additional profiles based on tier

## Files Modified
- `models.py`
- `routes/profile_routes.py`
- `routes/chat_routes.py`
- `services/conversation_router.py`
- `alembic/versions/20260121_add_multiprofile_support.py`
- `tests/test_multiprofile_support.py` (new)
- `tests/test_multiprofile_chat_commands.py` (new)

## Backward Compatibility
- Existing `user.voice_profile` property maintained
- Returns default profile or first profile if no default
- All existing code continues to work without changes
- Migration preserves existing profiles as default

## Security Considerations
- Profile ownership verified in all endpoints
- Users can only access/modify their own profiles
- Tier limits enforced on profile creation
- Cannot delete last profile (prevents orphaned users)

## Next Steps
1. Deploy migration to staging
2. Test with real users
3. Monitor profile creation/switching metrics
4. Consider UI for profile management (optional)
