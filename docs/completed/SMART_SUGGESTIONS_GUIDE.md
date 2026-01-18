# Smart Suggestions for Profile Updates - Feature Documentation

## Overview

The profile update feature now provides **intelligent, context-aware suggestions** based on the user's:
- **Industry** (e.g., Fitness, Restaurant, Software)
- **Scraped website data** (if URL was provided during onboarding)
- **Industry pack templates** (keyword banks and best practices)

## How It Works

### Data Sources

1. **Industry Packs** (`industry_packs/v1/{industry}.json`)
   - Contains keyword banks with industry-specific terms
   - Example: Fitness industry includes keywords like "professional", "expert", "trusted", "results-driven"

2. **Scraped Metadata** (stored in `VoiceProfile.scraped_meta`)
   - Extracted from user's website during onboarding
   - Includes: `key_customers`, `key_offer`, `business_name`, `voice_tone_and_style`

3. **Fallback Suggestions**
   - Generic suggestions when no industry/scraped data available
   - Ensures all users get helpful options

### Suggestion Logic by Field

#### Brand Voice
- **With Industry**: Uses seed keywords from industry pack
  - Fitness → "professional and customer focused", "expert and trusted"
  - Restaurant → "welcoming and authentic", "passionate about food"
- **Fallback**: "professional and authoritative", "warm and friendly", "bold and confident"

#### Target Audience
- **With Industry**: Tailored audience segments
  - Fitness → "health-conscious individuals", "busy professionals seeking fitness"
  - Restaurant → "food lovers and foodies", "families looking for dining experiences"
  - Software → "tech-savvy businesses", "enterprise clients", "startups and SMBs"
- **With Scraped Data**: Uses `key_customers` from scraped_meta
- **Fallback**: "busy professionals", "young families", "local community members"

#### Key Offer
- **With Industry**: Industry-specific value propositions
  - Fitness → "personalized training programs", "results-driven coaching"
  - Restaurant → "fresh, locally-sourced cuisine", "authentic dining experience"
- **With Scraped Data**: Uses `key_offer` from scraped_meta
- **Fallback**: "exceptional customer service", "quality products and services"

#### Industry
- **Shows available industries** from `static/content/config.json`
- Top 5 industries displayed as suggestions

## User Experience

### Example 1: Brand Voice Update (Fitness Business)

```
User: "/voice"

System Response:
─────────────────────────────────────────────
What would you like to change your Brand Voice to?

Here are some suggestions based on your profile:
• professional and customer focused
• expert and trusted
• bold and confident
• casual and conversational
─────────────────────────────────────────────

Suggestions (clickable buttons):
[professional and customer focused] [expert and trusted]
[bold and confident] [casual and conversational]
```

**User can either:**
- Click a suggestion button
- Type their own value: "energetic and motivating"

### Example 2: Target Audience with Scraped Data

```
Profile has scraped_meta: {
  "key_customers": "busy professionals seeking work-life balance"
}

User: "/audience"

System Response:
─────────────────────────────────────────────
What would you like to change your Target Audience to?

Here are some suggestions based on your profile:
• busy professionals seeking work-life balance
• health-conscious individuals
• busy professionals seeking fitness
─────────────────────────────────────────────
```

The scraped customer data appears as the **first suggestion**.

### Example 3: Multi-Turn with Suggestions

```
User: "/update"
System: "Which field would you like to update?"

User: "brand voice"
System: 
"What would you like to change your Brand Voice to?

Here are some suggestions based on your profile:
• professional and authoritative
• warm and friendly
• bold and confident
• casual and conversational"

User: [clicks "warm and friendly"]
System: "✅ Updated your Brand Voice!
         ~~professional and friendly~~ → **warm and friendly**"
```

## API Response Format

Suggestions are included in two places:

1. **In the response text** (for display in chat):
```json
{
  "response": "What would you like to change your Brand Voice to?\n\nHere are some suggestions based on your profile:\n• professional and customer focused\n• expert and trusted",
  "action": "continue",
  "pending_task": {...},
  "suggestions": [
    "professional and customer focused",
    "expert and trusted",
    "bold and confident",
    "casual and conversational"
  ]
}
```

2. **In the suggestions array** (for rendering as buttons/pills in UI):
- Frontend can render these as clickable options
- Clicking sends the suggestion text as the user's response

## Industry Pack Structure

Example from `industry_packs/v1/fitness.json`:

```json
{
  "id": "fitness",
  "display_name": "Fitness / Wellness",
  "keyword_banks": {
    "seed_keywords": [
      "business",
      "service",
      "quality",
      "professional",     // Index 3
      "customer focused", // Index 4
      "expert",          // Index 5
      "trusted",         // Index 6
      "reliable",
      "solutions",
      "results"
    ]
  }
}
```

The system uses these keywords to generate voice suggestions like:
- "professional and customer focused" (keywords[3] + keywords[4])
- "expert and trusted" (keywords[5] + keywords[6])

## Benefits

### For Users
1. **Faster updates**: Click instead of type
2. **Better quality**: Industry-appropriate suggestions
3. **Consistency**: Aligned with best practices
4. **Personalization**: Uses their own website data

### For Business
1. **Higher completion rates**: Easier to update profiles
2. **Better content quality**: Industry-optimized voices/audiences
3. **Reduced friction**: No writer's block when updating
4. **Data-driven**: Leverages scraped insights

## Future Enhancements

Potential improvements:
- AI-generated suggestions using Gemini based on full profile context
- Learning from user's past content to suggest brand voice
- A/B testing different suggestion orders
- More industries in industry packs
- Competitor analysis for audience suggestions
- Seasonal/trending suggestions (e.g., "holiday-focused" audiences)

## Testing Coverage

All suggestion scenarios tested:
- ✅ Industry-based suggestions (fitness, restaurant, software)
- ✅ Scraped metadata integration (key_customers, key_offer)
- ✅ Clickable suggestion usage in multi-turn flows
- ✅ Fallback suggestions when no context available
- ✅ All fields: voice, audience, key offer, industry
- ✅ Integration with existing profile update flows

## Implementation Files

- **Backend**: `routes/chat_routes.py` - `_get_smart_suggestions_for_field()`
- **Data**: `industry_packs/v1/*.json` - Industry-specific templates
- **Model**: `models.py` - `VoiceProfile.scraped_meta` field
- **Tests**: `tests/test_profile_suggestions.py` - 6 comprehensive tests
