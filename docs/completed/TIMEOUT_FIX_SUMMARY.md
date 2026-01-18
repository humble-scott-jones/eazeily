# Content Generation: Timeout Protection & UX Improvements

## Problem Statement

The content generation flow had the following issues:
1. No timeout protection - requests could hang indefinitely
2. No feedback for long-running operations (>5 seconds)
3. Generic error messages that didn't help users understand what went wrong
4. Missing `generate_expert_content` method in VoiceEngine causing runtime errors

## Solution Implemented

### 1. Backend Changes (services/voice_engine.py)

**Added `generate_expert_content()` method:**
```python
def generate_expert_content(
    self,
    user_profile: Any,
    topic: str,
    task_type: str = "post",
    platform: str = "LinkedIn"
) -> str:
    """Generate content based on task type with timeout protection."""
```

**Key Features:**
- Safe attribute access with getattr() for profile data
- Comprehensive error handling for:
  - Timeout errors
  - Rate limit errors  
  - Authentication errors
  - Generic errors
- Returns user-friendly error messages instead of stack traces
- Graceful fallback when no AI model is available

### 2. Frontend Changes (templates/dashboard.html)

**Added Timeout Protection:**
- 45-second hard timeout using AbortController
- Prevents indefinite hanging on slow AI responses
- Automatically aborts request if it takes too long

**Long-Running Process Notification:**
- Shows "Still working..." message after 5 seconds
- Displays toast notification: "Generation is taking longer than usual. Please wait..."
- Keeps user informed that the system is still working

**Enhanced Error Messages:**
```javascript
// Timeout error
"Request timed out after 45 seconds. Please try again with a simpler topic."

// Rate limit error
"API rate limit reached. Please wait a moment and try again."

// Network error
"Network error. Please check your connection and try again."

// Auth error
"AI service not configured. Please contact support."
```

### 3. Testing

Added comprehensive unit tests in `tests/test_voice_engine_generate_expert_content.py`:
- Tests return value type and structure
- Tests graceful handling of missing model
- Tests all parameter combinations
- Tests minimal profile attributes
- All 4 tests passing ✓

## User Experience Flow

### Before Fix:
1. User clicks "Generate"
2. Button shows "Generating..."
3. **If slow:** Button stays in "Generating..." state indefinitely
4. **If error:** Generic error message

### After Fix:
1. User clicks "Generate"
2. Button shows "Generating..."
3. **After 5 seconds:** Button text changes to "Still working..." + toast notification
4. **After 45 seconds:** Request auto-aborts with clear timeout message
5. **On error:** Specific, actionable error message based on error type

## Technical Details

### Timeout Implementation
```javascript
const LONG_RUNNING_THRESHOLD = 5000; // 5 seconds
const TIMEOUT_MS = 45000; // 45 seconds

let abortController = new AbortController();

setTimeout(() => {
    btnText.textContent = 'Still working...';
    showToast('Generation is taking longer than usual...', 'info');
}, LONG_RUNNING_THRESHOLD);

setTimeout(() => {
    abortController.abort();
}, TIMEOUT_MS);

fetch('/api/generate', {
    signal: abortController.signal
    // ...
});
```

### Error Classification
The backend classifies errors and returns appropriate messages:
- `TimeoutError` → User-friendly timeout message
- Rate limit errors → Suggests waiting
- Auth errors → Directs to support
- Generic errors → Suggests retry

## Files Changed

1. **services/voice_engine.py**
   - Added `generate_expert_content()` method (69 lines)
   - Added error handling logic

2. **templates/dashboard.html**
   - Enhanced generation flow with timeout (88 lines modified)
   - Added long-running notification
   - Added error classification

3. **tests/test_voice_engine_generate_expert_content.py** (NEW)
   - 4 comprehensive unit tests
   - All passing ✓

## Testing Checklist

- [x] Unit tests pass for generate_expert_content
- [x] Method accepts all required parameters
- [x] Graceful handling of missing model
- [x] Timeout protection implemented
- [x] Long-running notification implemented
- [x] Error messages are user-friendly
- [ ] Manual E2E test on running server (requires AI API key)
- [ ] Browser timeout behavior verification
- [ ] Error message display verification

## Next Steps

To fully validate:
1. Deploy to staging environment with GENAI_API_KEY configured
2. Test actual generation with various topics
3. Verify timeout behavior with intentionally slow requests
4. Verify error messages display correctly in UI
5. Test on multiple browsers for timeout behavior consistency
