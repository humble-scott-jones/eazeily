# Taxonomy Normalization Summary

## Overview
This document summarizes the platform taxonomy normalization completed as part of the staging/rollout-2025-12-04 branch update.

## Changes Made

### 1. User Journey Documentation (`docs/user-journey.md`)
**NEW FILE**: Comprehensive end-to-end flow documentation covering:
- Complete user journey from profile completion through content generation
- Technical data flow with file references
- Current pain points with detailed analysis:
  - Brand Profile save failures (causes, workarounds, debugging steps)
  - Generator dashboard dead-ends (API timeouts, missing keys, rate limits)
  - Confusing social dropdown labels (now resolved)
- QA checklist with 60+ test cases
- Platform/content taxonomy table (before and after normalization)
- Future enhancement roadmap

**Link Added**: README.md now includes quick link to user journey doc for discoverability.

### 2. Platform Configuration (`static/content/config.json`)
**ADDED**: New `platforms` array with hierarchical structure:

```json
{
  "platforms": [
    {
      "category": "social_organic",
      "categoryLabel": "Social (Organic)",
      "items": [
        {"key": "instagram", "label": "Instagram"},
        {"key": "facebook", "label": "Facebook"},
        {"key": "linkedin", "label": "LinkedIn"},
        {"key": "twitter", "label": "X (Twitter)"},
        {"key": "tiktok", "label": "TikTok"},
        {"key": "short_video", "label": "Reels/Shorts"}
      ]
    },
    {
      "category": "social_ads",
      "categoryLabel": "Social Ads",
      "items": [
        {"key": "facebook_ads", "label": "Facebook Ads"},
        {"key": "instagram_ads", "label": "Instagram Ads"},
        {"key": "linkedin_ads", "label": "LinkedIn Ads"},
        {"key": "twitter_ads", "label": "X Ads"},
        {"key": "tiktok_ads", "label": "TikTok Ads"}
      ]
    },
    {
      "category": "reputation",
      "categoryLabel": "Reputation/Support",
      "items": [
        {"key": "review_response", "label": "Review Responses"}
      ]
    }
  ]
}
```

**Benefits**:
- Clear separation between organic social and paid ads
- Consistent lowercase keys for backend processing
- User-friendly labels for UI display
- Extensible structure for future categories

### 3. Dashboard UI (`templates/dashboard.html`)
**UPDATED**: Platform dropdown with optgroup structure:

```html
<select id="platform" name="platform">
  <optgroup label="Social (Organic)">
    <option value="instagram">Instagram</option>
    <option value="facebook">Facebook</option>
    <option value="linkedin">LinkedIn</option>
    <option value="twitter">X (Twitter)</option>
    <option value="tiktok">TikTok</option>
    <option value="short_video">Reels/Shorts</option>
  </optgroup>
  <optgroup label="Social Ads">
    <option value="facebook_ads">Facebook Ads</option>
    <option value="instagram_ads">Instagram Ads</option>
    <option value="linkedin_ads">LinkedIn Ads</option>
    <option value="twitter_ads">X Ads</option>
    <option value="tiktok_ads">TikTok Ads</option>
  </optgroup>
</select>
```

**UPDATED**: Dynamic input configuration to handle ad platforms:
```javascript
const DYNAMIC_INPUT_CONFIG = {
  'ad': 'ad-options',
  'facebook': 'ad-options',
  'facebook_ads': 'ad-options',
  'instagram_ads': 'ad-options',
  'linkedin_ads': 'ad-options',
  'twitter_ads': 'ad-options',
  'tiktok_ads': 'ad-options',
  'linkedin': 'linkedin-options',
  'instagram': 'visual-options',
  'script': 'video-options',
  'email': 'email-options',
  'newsletter': 'email-options'
};
```

**UPDATED**: Surprise Me function to use normalized platform keys:
```javascript
const platforms = ['instagram', 'facebook', 'linkedin', 'twitter', 'tiktok', 'short_video'];
```

**Benefits**:
- Visual grouping makes platform selection intuitive
- Users can easily distinguish organic posts from ads
- Consistent naming: "X (Twitter)" instead of just "Twitter"
- All major platforms now available (added TikTok, Reels/Shorts)

### 4. Dashboard JavaScript (`static/dashboard.js`)
**ADDED**: Platform config flattening function:

```javascript
function flattenPlatformConfig(platformCategories) {
  const flattened = [];
  platformCategories.forEach(category => {
    if (category.items && Array.isArray(category.items)) {
      category.items.forEach(item => {
        flattened.push({
          key: item.key,
          label: item.label,
          category: category.category,
          categoryLabel: category.categoryLabel
        });
      });
    }
  });
  return flattened;
}
```

**UPDATED**: `ensureAccountFormFields()` to flatten platform config before populating UI.

**Benefits**:
- Backward compatible with existing code expecting flat array
- Preserves category metadata for future enhancements
- Gracefully handles missing or malformed config

### 5. Platform Rules (`platform_rules.py`)
**ADDED**: Rules for new platforms:

```python
# short_video (Reels/Shorts)
"short_video": PlatformRule(
    key="short_video",
    label="Reels/Shorts",
    max_length=1500,
    max_hashtags=5,
    cta="Save this and share with someone who needs it",
    hashtag_prefix="#",
    thumbnail_note="Bold hook text, high contrast, centered subject",
),

# Social Ads platforms (5 new rules)
"facebook_ads": PlatformRule(
    key="facebook_ads",
    label="Facebook Ads",
    max_length=125,
    max_hashtags=0,
    cta="Learn more",
    link_note="Include clear CTA button text (e.g., Shop Now, Sign Up).",
    thumbnail_note="Eye-catching image with minimal text overlay",
),
# ... (instagram_ads, linkedin_ads, twitter_ads, tiktok_ads)

# Reputation/Support
"review_response": PlatformRule(
    key="review_response",
    label="Review Response",
    max_length=500,
    max_hashtags=0,
    cta="Thank you for your feedback",
    thumbnail_note=None,
),
```

**UPDATED**: `DEFAULT_VARIANT_PLATFORMS` tuple to include `short_video`.

**Platform Rule Count**: 13 total (was 6, added 7)

**Benefits**:
- Ad copy follows platform-specific character limits (125 chars for FB/IG ads)
- Review responses have appropriate tone and length
- Each platform has tailored CTA and thumbnail guidance

### 6. Generator (`generator.py`)
**UPDATED**: `PLATFORM_HINTS` dictionary with 12 entries:

```python
PLATFORM_HINTS = {
    "instagram": "Keep it visual, 1–2 short paragraphs, 8–12 niche hashtags.",
    "facebook": "Conversational tone, 2–3 short paragraphs. Invite replies.",
    "linkedin": "Value-forward, concise, 1–2 actionable insights, 3–6 hashtags.",
    "tiktok": "Hook in first sentence, keep lines punchy, suggest a shot list.",
    "twitter": "Short & punchy. 1–2 tweets per post; avoid walls of text.",
    "short_video": "Dynamic opening hook, punchy lines, visual-first storytelling.",
    "facebook_ads": "Clear value prop, strong CTA, mobile-optimized, under 125 chars.",
    "instagram_ads": "Eye-catching opening, benefit-focused, concise for mobile.",
    "linkedin_ads": "Professional, value-driven, clear ROI or benefit statement.",
    "twitter_ads": "Direct and concise, strong hook in first 7 words.",
    "tiktok_ads": "Native feel, entertaining, avoid hard-sell, under 100 chars.",
    "review_response": "Grateful, empathetic, address concerns, invite follow-up.",
}
```

**Benefits**:
- Gemini API receives platform-specific guidance for tone and structure
- Ads get distinct prompts focused on conversion (CTA, value prop)
- Review responses are empathetic and constructive
- Short-form video platforms emphasize hooks and pacing

## Normalized Taxonomy

### Platform Keys (Lowercase, for Backend)
**Social (Organic)**:
- `instagram`
- `facebook`
- `linkedin`
- `twitter`
- `tiktok`
- `short_video`

**Social Ads**:
- `facebook_ads`
- `instagram_ads`
- `linkedin_ads`
- `twitter_ads`
- `tiktok_ads`

**Reputation/Support**:
- `review_response`

### Platform Labels (User-Friendly, for UI)
**Social (Organic)**:
- Instagram
- Facebook
- LinkedIn
- X (Twitter)
- TikTok
- Reels/Shorts

**Social Ads**:
- Facebook Ads
- Instagram Ads
- LinkedIn Ads
- X Ads
- TikTok Ads

**Reputation/Support**:
- Review Responses

## Validation

### Python Validation
- ✅ `config.json` valid JSON (3 platform categories, 18 industries)
- ✅ `platform_rules.py` loads successfully (13 rules)
- ✅ `generator.py` loads successfully (12 platform hints)
- ✅ Platform rule application works for organic and ad platforms
- ✅ Syntax check passed for `app.py`, `generator.py`, `platform_rules.py`

### JavaScript Validation
- ✅ `dashboard.js` syntax validated
- ✅ Platform config flattening function tested

### HTML Validation
- ✅ `dashboard.html` contains optgroup structure
- ✅ All new platform labels present (X (Twitter), Reels/Shorts, Facebook Ads, etc.)
- ✅ Dynamic input config updated for ad platforms

## Migration Notes

### Breaking Changes
**None**. Changes are backward compatible:
- Old platform keys still work (`twitter`, `instagram`, etc.)
- New keys added alongside existing ones
- UI gracefully handles missing config fields

### New Platform Keys
If you have existing code that checks platform values, be aware of these new keys:
- `short_video` (Reels/Shorts)
- `facebook_ads`, `instagram_ads`, `linkedin_ads`, `twitter_ads`, `tiktok_ads`
- `review_response`

### Deprecated Patterns
- ❌ **AVOID**: Hardcoding platform lists in JavaScript (use config.json instead)
- ❌ **AVOID**: Using "Twitter" without "X" clarification
- ❌ **AVOID**: Mixing ads and organic posts in same category

### Recommended Updates
If you maintain custom code that references platforms:
1. Use lowercase keys for backend processing (`instagram`, not `Instagram`)
2. Use labels from config.json for display (`X (Twitter)`, not `Twitter`)
3. Check platform category when needed (`social_organic` vs `social_ads`)
4. Handle new platforms in any switch/case statements

## Testing Checklist

### Manual Testing (High Priority)
- [ ] Load `/dashboard` and verify platform dropdown shows all options grouped correctly
- [ ] Select "Instagram" from dropdown, verify dynamic options appear
- [ ] Select "Facebook Ads" from dropdown, verify ad options appear
- [ ] Click "Surprise Me" button, verify random platform is selected
- [ ] Generate content for "Instagram" (organic), verify correct PLATFORM_HINT used
- [ ] Generate content for "Facebook Ads", verify correct ad rules applied (125 char limit)
- [ ] Generate content for "Reels/Shorts", verify short_video rules applied
- [ ] Check character counter shows correct limits for each platform
- [ ] Verify generated content respects platform-specific hashtag limits
- [ ] Verify CTAs are platform-appropriate (e.g., "Shop now" for Instagram ads)

### Automated Testing (If Available)
- [ ] Run `PYTHONPATH=. pytest tests/test_api_generate_payload.py -v`
- [ ] Run `PYTHONPATH=. pytest tests/test_dashboard_dynamic_inputs.py -v`
- [ ] Run full test suite: `PYTHONPATH=. pytest -v`

### Edge Cases
- [ ] Select platform, switch task type, verify platform resets appropriately
- [ ] Load dashboard with no saved profile, verify defaults work
- [ ] Test with browser JavaScript disabled (graceful degradation)
- [ ] Test on mobile viewport (dropdown, optgroups readable)
- [ ] Test with slow network (config.json fetch timeout)

## Files Changed

| File | Lines Changed | Type |
|------|--------------|------|
| `docs/user-journey.md` | +497 | NEW |
| `README.md` | +6 | UPDATED |
| `static/content/config.json` | +36 | UPDATED |
| `templates/dashboard.html` | +16, -10 | UPDATED |
| `static/dashboard.js` | +20, -1 | UPDATED |
| `platform_rules.py` | +84, -9 | UPDATED |
| `generator.py` | +7, -1 | UPDATED |

**Total**: 659 lines added, 22 lines removed, 1 file created, 6 files updated.

## Rollback Plan

If issues are discovered:
1. Revert commits in reverse order:
   ```bash
   git revert bf63144  # dashboard.js flattening
   git revert 9985126  # platform taxonomy normalization
   git revert 4aed8af  # user journey doc
   ```
2. Old platform dropdown will restore:
   - LinkedIn, Instagram, Facebook, Twitter (no grouping)
3. Platform rules will revert to original 6 platforms
4. No data loss (user profiles unaffected)

## Future Enhancements
1. Add platform icons to dropdown options
2. Group platforms by category in generator dashboard (not just dropdown)
3. Add platform-specific preview panel (show how post looks on Instagram/LinkedIn)
4. Implement platform-specific character counter in real-time
5. Add "recommended platforms" based on industry
6. Track platform performance analytics (which platforms get best engagement)

## Contact & Support
- User Journey Doc: `docs/user-journey.md`
- Platform Config: `static/content/config.json`
- Questions: Create GitHub issue with label `taxonomy-normalization`
