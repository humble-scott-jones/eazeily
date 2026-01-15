# Fix Summary: Brand Keywords, Goals, and Target Audience Population

## Problem Statement
When users analyzed a website on the profile page, brand keywords, content goals, and target audience were not populating in the profile text boxes.

## Root Cause Analysis

### Backend Issue
The scraper service (`services/scraper_service.py`) was correctly extracting `content_goals` from website text using keyword detection (e.g., "learn" → awareness/education, "sign up" → lead_gen/conversion, "help" → retention/support).

However, the `/onboarding/social-style` endpoint (`routes/onboarding_routes.py`) was **not** including these extracted content_goals in the suggestions object returned to the frontend. It was only returning:
- business_name
- industry
- key_customers
- key_offer
- brand_keywords
- niche_keywords

### Frontend Issue
The `mergeScrapedData()` function in `templates/profile.html` was merging most scraped data fields (brand_keywords, key_offer, target_audience, etc.) but was **missing code to merge content_goals** into the `goals` input field.

## Solution

### Backend Changes (routes/onboarding_routes.py)
Added extraction of content_goals from the scraper service's `required_sections` data structure and included them in the suggestions response:

```python
# Extract content goals from required_sections
content_goals_data = business_info.get("required_sections", {}).get("content_goals", {}).get("values", [])
# Convert goal objects to simple strings for frontend consumption
suggestions["content_goals"] = [goal.get("goal") for goal in content_goals_data if goal.get("goal")]
```

This converts the goal objects (e.g., `{"goal": "awareness/education", "rationale": "Found marker 'learn'"}`) into simple strings (`"awareness/education"`) for easier frontend consumption.

### Frontend Changes (templates/profile.html)
Added code to merge content_goals into the goals field in the `mergeScrapedData()` function:

```javascript
// Content goals - MERGE with existing in the UI
const goalsField = document.getElementById('goals');
if (suggestions.content_goals && Array.isArray(suggestions.content_goals)) {
    const existing = goalsField.value.split(',').map(g => g.trim()).filter(g => g);
    const newGoals = suggestions.content_goals.filter(g => g);
    const merged = [...new Set([...existing, ...newGoals])]; // Remove duplicates
    goalsField.value = merged.join(', ');
}
```

This follows the same pattern used for brand_keywords: merging new goals with existing ones while removing duplicates.

## Testing

### Manual Testing
Created manual test scripts to verify:
1. `test_scraper_goals_manual.py` - Verifies scraper service extracts content_goals correctly
2. `test_endpoint_goals_manual.py` - Verifies the endpoint returns content_goals in suggestions
3. `test_merge_frontend.html` - Interactive HTML test for the frontend merge function

All manual tests passed successfully.

### Automated Testing
Added comprehensive test file `tests/test_content_goals_extraction.py` with:
1. `test_onboarding_social_style_returns_content_goals()` - Integration test verifying the full flow
2. `test_content_goals_extraction_from_keywords()` - Unit test for goal keyword detection

## Impact

**Before Fix:**
- Users would analyze a website
- Brand keywords, goals, and target audience would be extracted by the backend
- But content_goals would NOT appear in the profile form
- Users had to manually enter content goals

**After Fix:**
- Users analyze a website
- All extracted data including brand_keywords AND content_goals populate automatically
- Content goals like "awareness/education", "lead_gen/conversion", "retention/support" appear in the goals field
- Target audience continues to populate as before (this was already working)

## Files Changed
- `routes/onboarding_routes.py` - Added content_goals to suggestions
- `templates/profile.html` - Added goals merging logic
- `tests/test_content_goals_extraction.py` - New test file
- `.gitignore` - Added manual test files

## Notes
- The fix maintains backward compatibility - if content_goals aren't available, the field simply remains unchanged
- The merge strategy prevents duplicates using JavaScript Sets
- The goal detection uses industry-standard keywords for awareness, lead generation, and retention
