# User Journey & Platform Taxonomy

## Overview

This document describes the platform taxonomy used throughout the Eazeily application for content generation and organization.

## Platform Taxonomy

Platforms are organized into three main categories to provide clear separation between organic social, paid advertising, and reputation management.

### Social (Organic)

Organic social media content for engagement and brand building.

| Key | Label | Description | Character Limit |
|-----|-------|-------------|-----------------|
| `instagram` | Instagram | Visual-focused posts with hashtags | 2,200 |
| `facebook` | Facebook | Conversational tone, community engagement | 63,206 |
| `linkedin` | LinkedIn | Professional, value-forward content | 3,000 |
| `twitter` | X (Twitter) | Short, punchy updates and threads | 280 |
| `tiktok` | TikTok | Short-form video with entertainment focus | 2,200 |
| `short_video` | Reels / Shorts | Instagram Reels & YouTube Shorts | 2,200 |

### Social Ads

Paid social media advertising campaigns with conversion-focused messaging.

| Key | Label | Description | Character Limit |
|-----|-------|-------------|-----------------|
| `facebook_ads` | Facebook Ads | Performance marketing on Facebook | 125 |
| `instagram_ads` | Instagram Ads | Visual ads with strong CTAs | 2,200 |
| `linkedin_ads` | LinkedIn Ads | B2B focused sponsored content | 150 |
| `twitter_ads` | X Ads | Promoted tweets and campaigns | 280 |
| `tiktok_ads` | TikTok Ads | Native-feeling promotional content | 100 |

### Reputation

Review responses and reputation management.

| Key | Label | Description | Character Limit |
|-----|-------|-------------|-----------------|
| `reviews` | Review responses | Customer review replies and feedback | 1,000 |

## Platform Hints for Content Generation

Each platform has specific content generation hints to guide tone, structure, and best practices:

- **Instagram**: Keep it visual, 1–2 short paragraphs, 8–12 niche hashtags
- **Facebook**: Conversational tone, 2–3 short paragraphs. Invite replies
- **LinkedIn**: Value-forward, concise, 1–2 actionable insights, 3–6 hashtags
- **X (Twitter)**: Short & punchy. 1–2 tweets per post; avoid walls of text
- **TikTok**: Hook in first sentence, keep lines punchy, suggest a shot list
- **Reels / Shorts**: Hook in first second, keep visual focus, include shot suggestions
- **Facebook Ads**: Clear CTA, benefit-focused, compelling headline under 125 chars
- **Instagram Ads**: Visual-first, strong hook, clear value prop, CTA button friendly
- **LinkedIn Ads**: Professional tone, value proposition first, B2B focused messaging
- **X Ads**: Concise benefit statement, clear CTA, attention-grabbing first line
- **TikTok Ads**: Native feel, authentic voice, entertainment-first with soft sell
- **Review responses**: Acknowledge sentiment, provide value, maintain brand voice

## Key Design Principles

1. **Consistent Keys**: All platform keys use lowercase with underscores (e.g., `facebook_ads`, `short_video`)
2. **Parent/Child Clarity**: Categories clearly separate organic social from paid ads
3. **User-Friendly Labels**: Display labels are human-readable (e.g., "X (Twitter)" not "twitter")
4. **Normalized Payload**: API payloads use the key values, not labels
5. **Extensible**: New platforms can be added to existing categories or new categories can be created

## Usage in Application

### Configuration (config.json)

Platforms are defined in `static/content/config.json` with:
- `key`: Internal identifier used in code and payloads
- `label`: User-facing display name
- `category`: Parent category (social, ads, reputation)

### Dashboard UI (dashboard.html)

Platforms are organized into separate sections by category:
- Social (organic) group
- Social Ads group
- Reputation group

### JavaScript (dashboard.js)

Platform buttons are retrieved from all category groups using `getGeneratorPlatformButtons()`.
Labels are formatted using `formatPlatformLabel()` with overrides defined in `PLATFORM_LABEL_OVERRIDES`.

### Content Generation (generator.py)

Platform-specific hints are provided in `PLATFORM_HINTS` dictionary for Gemini prompt generation.

### Backend (app.py)

Platform values in payloads are validated and normalized throughout the API endpoints.

## Migration Notes

The platform taxonomy was normalized to:
1. Remove confusion between organic social and paid ads
2. Provide clear parent/child categorization
3. Ensure consistency between UI labels and backend keys
4. Support future expansion of advertising platforms

Legacy platform references (e.g., "X / Twitter" vs "X (Twitter)") have been unified to use the normalized labels.
