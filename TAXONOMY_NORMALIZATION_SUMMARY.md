# Taxonomy Normalization Summary

## Overview
This document summarizes the platform taxonomy normalization completed as part of the staging/rollout-2025-12-04 branch update. The approach focuses on simplicity and aligns with the existing content type structure.

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

### 2. Content Type Naming (`templates/dashboard.html`)
**UPDATED**: Task button label from "Facebook Ad" to "Social Ads":

```html
<div class="font-semibold text-gray-900">Social Ads</div>
<div class="text-xs text-gray-500 mt-1">FB, IG, LinkedIn & more</div>
```

**Benefits**:
- Clarifies that ads aren't limited to Facebook
- Aligns with multi-platform ad generation capabilities
- More accurate representation of the task type

### 3. Platform Configuration (`static/content/config.json`)
**ADDED**: Simple flat platform array:

```json
{
  "platforms": [
    {"key": "instagram", "label": "Instagram"},
    {"key": "facebook", "label": "Facebook"},
    {"key": "linkedin", "label": "LinkedIn"},
    {"key": "twitter", "label": "X (Twitter)"},
    {"key": "tiktok", "label": "TikTok"},
    {"key": "short_video", "label": "Reels/Shorts"}
  ]
}
```

**Benefits**:
- Simple, maintainable structure
- Focuses on organic social platforms used by "Social Post" task
- Consistent lowercase keys for backend processing
- User-friendly labels for UI display

### 4. Dashboard UI (`templates/dashboard.html`)
**UPDATED**: Platform dropdown with simple structure (no optgroups):

```html
<select id="platform" name="platform">
  <option value="instagram">Instagram</option>
  <option value="facebook">Facebook</option>
  <option value="linkedin">LinkedIn</option>
  <option value="twitter">X (Twitter)</option>
  <option value="tiktok">TikTok</option>
  <option value="short_video">Reels/Shorts</option>
</select>
```

**Benefits**:
- Clean, simple UI
- All major organic social platforms included
- Consistent naming: "X (Twitter)" instead of just "Twitter"
- Added TikTok and Reels/Shorts support

### 5. Dashboard JavaScript (`static/dashboard.js`)
**SIMPLIFIED**: Removed complex flattening logic, platforms now simple array.

**Benefits**:
- Less code complexity
- Direct handling of platform array from config.json
- Maintains backward compatibility

### 6. Platform Rules (`platform_rules.py`)
**RETAINED**: Comprehensive platform-specific formatting rules (13 total)

Platform rules define character limits, hashtag rules, CTAs, and formatting for each platform:
- Organic social: instagram, facebook, linkedin, twitter, tiktok, youtube, short_video
- Ad platforms: facebook_ads, instagram_ads, linkedin_ads, twitter_ads, tiktok_ads
- Support: review_response

**Benefits**:
- Backend can handle multiple platform types even with simplified UI
- Platform-specific formatting ensures content fits each channel
- Extensible for future platform additions

### 7. Generator (`generator.py`)
**UPDATED**: `PLATFORM_HINTS` dictionary with 12 entries for AI prompts:

Includes platform-specific guidance for content generation:
- Organic platforms: Instagram, Facebook, LinkedIn, TikTok, Twitter, Reels/Shorts
- Ad platforms: Facebook Ads, Instagram Ads, LinkedIn Ads, X Ads, TikTok Ads  
- Support: Review responses

**Benefits**:
- Gemini API receives platform-specific guidance for tone and structure
- Ads get distinct prompts focused on conversion (CTA, value prop)
- Review responses are empathetic and constructive

## Content Type Structure

The dashboard maintains 9 content type tiles:

1. **Social Post** (task='post') - Requires platform selection from dropdown
2. **Image Caption** (task='caption') - For photos
3. **Video Script** (task='script') - Reels & TikToks
4. **Email Draft** (task='email') - Newsletters & More
5. **Proposal** (task='proposal') - Project bids & quotes
6. **Social Ads** (task='ad') - FB, IG, LinkedIn & more (renamed from "Facebook Ad")
7. **Review Reply** (task='review') - Customer Responses
8. **Blog Post** (task='blog') - SEO Articles
9. **Newsletter** (task='newsletter') - Community Updates

**Key Change**: Task #6 renamed from "Facebook Ad" to "Social Ads" to clarify multi-platform capability.

## Platform Taxonomy

### Platform Keys (Lowercase, for Backend)
**Organic Social** (used in "Social Post" platform dropdown):
- `instagram`
- `facebook`
- `linkedin`
- `twitter`
- `tiktok`
- `short_video`

**Ad Platforms** (handled via task='ad', platform-specific logic in backend):
- `facebook_ads`, `instagram_ads`, `linkedin_ads`, `twitter_ads`, `tiktok_ads`

**Support** (future use):
- `review_response`

### Platform Labels (User-Friendly, for UI)
**Social Post Dropdown**:
- Instagram
- Facebook
- LinkedIn
- X (Twitter)
- TikTok
- Reels/Shorts

**Social Ads Task**:
- UI label: "Social Ads"
- Subtitle: "FB, IG, LinkedIn & more"

## Validation

### Python Validation
- ✅ `config.json` valid JSON (6 platforms, 18 industries)
- ✅ `platform_rules.py` loads successfully (13 rules)
- ✅ `generator.py` loads successfully (12 platform hints)
- ✅ Platform rule application works for organic and ad platforms
- ✅ Syntax check passed for `app.py`, `generator.py`, `platform_rules.py`

### JavaScript Validation
- ✅ `dashboard.js` syntax validated
- ✅ Simplified platform handling (no complex flattening needed)

### HTML Validation
- ✅ `dashboard.html` simple dropdown structure (no optgroups)
- ✅ Task button renamed: "Social Ads" (was "Facebook Ad")
- ✅ All platform labels present (X (Twitter), Reels/Shorts, TikTok)

## Migration Notes

### Breaking Changes
**None**. Changes are backward compatible:
- Old platform keys still work (`twitter`, `instagram`, etc.)
- New keys added: `tiktok`, `short_video`
- UI gracefully handles missing config fields

### Simplified Approach
This implementation focuses on:
1. **Content types** are the primary UI element (9 task tiles)
2. **Platform dropdown** is simple and only for "Social Post" task
3. **Backend** retains full platform taxonomy for flexibility

### Recommended Usage
- Use "Social Post" task + platform dropdown for organic social content
- Use "Social Ads" task for paid advertising (platform-agnostic UI, platform-specific backend)
- Backend handles platform-specific rules via platform_rules.py

## Testing Checklist

### Manual Testing (High Priority)
- [ ] Load `/dashboard` and verify 9 content type tiles displayed
- [ ] Verify "Social Ads" task button (not "Facebook Ad")
- [ ] Click "Social Post", verify platform dropdown appears
- [ ] Select "Instagram" from dropdown, verify dynamic options appear
- [ ] Select "TikTok" from dropdown, verify available
- [ ] Click "Surprise Me" button, verify random platform selected
- [ ] Generate content for "Instagram" (organic), verify correct output
- [ ] Generate content using "Social Ads" task, verify ad-appropriate content
- [ ] Verify X (Twitter) label in dropdown (not just "Twitter")

### Automated Testing (If Available)
- [ ] Run `PYTHONPATH=. pytest tests/test_api_generate_payload.py -v`
- [ ] Run full test suite: `PYTHONPATH=. pytest -v`

### Edge Cases
- [ ] Select platform, switch task type, verify platform resets appropriately
- [ ] Load dashboard with no saved profile, verify defaults work
- [ ] Test on mobile viewport (dropdown readable)
- [ ] Test with slow network (config.json fetch timeout)

## Files Changed

| File | Lines Changed | Type |
|------|--------------|------|
| `docs/user-journey.md` | +497 | NEW |
| `README.md` | +6 | UPDATED |
| `static/content/config.json` | Simplified | UPDATED |
| `templates/dashboard.html` | Simplified dropdown, renamed task | UPDATED |
| `static/dashboard.js` | Removed flattening logic | UPDATED |
| `platform_rules.py` | +84, -9 (13 rules total) | UPDATED |
| `generator.py` | +7, -1 (12 hints total) | UPDATED |
| `TAXONOMY_NORMALIZATION_SUMMARY.md` | +371 | NEW |

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
