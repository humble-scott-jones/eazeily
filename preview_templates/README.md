# Preview Templates

This directory contains deterministic, offline-capable preview templates for generating sample content across multiple channels without requiring OpenAI or any external API.

## Overview

The preview template system provides instant before/after comparisons showing:
- **Baseline**: Generic template content
- **Personalized**: Content with slot substitutions based on user inputs

## Channels

### Social (`preview_templates/social/`)
Templates for social media posts (Instagram, Facebook, LinkedIn, Twitter, TikTok)
- `promotional.json` - Promotional/offer posts
- `educational.json` - Educational/value content
- `testimonial.json` - Customer success stories

### Email (`preview_templates/email/`)
Templates for email campaigns
- `welcome.json` - Welcome/onboarding emails
- `followup.json` - Follow-up emails
- `offer.json` - Special offer/promotional emails

### Quote (`preview_templates/quote/`)
Templates for quotes and proposals
- `service.json` - Service quotes
- `project.json` - Project-based quotes
- `consultation.json` - Consultation quotes

## Slot Variables

All templates support the following slot variables for personalization:

- `{service}` - The service or product being offered
- `{audience}` - Target audience
- `{pain}` - Customer pain point
- `{outcome}` - Desired outcome
- `{differentiator}` - What makes you unique
- `{proof}` - Social proof or credibility
- `{cta}` - Call to action
- `{validity_days}` - Number of days offer/quote is valid
- `{deposit_policy}` - Deposit requirements

## API Usage

### List all templates
```bash
GET /api/preview-templates
```

Returns all available templates grouped by channel.

### List templates for a channel
```bash
GET /api/preview-templates/{channel}
```

Returns templates for a specific channel (social, email, or quote).

### Generate a preview
```bash
POST /api/preview-templates/{channel}/{template_id}
Content-Type: application/json

{
  "slots": {
    "service": "Professional Cleaning",
    "audience": "busy professionals",
    "pain": "lack of time for housework",
    "outcome": "a spotless home"
  },
  "use_baseline": false
}
```

Returns a preview with slot substitutions applied.

## Python Usage

```python
from preview_builder import PreviewTemplateBuilder

builder = PreviewTemplateBuilder()

# Get all channels
channels = builder.get_available_channels()  # ['email', 'quote', 'social']

# Get templates for a channel
templates = builder.get_templates_for_channel('social')

# Build a personalized preview
preview = builder.build_preview(
    channel='social',
    template_id='social_promotional',
    slots={
        'service': 'Professional Cleaning',
        'audience': 'busy professionals',
        'pain': 'lack of time',
        'outcome': 'a spotless home'
    }
)

# Build a baseline preview
baseline = builder.build_preview(
    channel='social',
    template_id='social_promotional',
    use_baseline=True
)
```

## Demo Page

Visit `/preview-demo` to see the interactive demo with live preview updates as you type.

## Key Features

✅ **Instant**: No waiting for API calls - previews generate in milliseconds  
✅ **Offline**: Works without internet or OpenAI API  
✅ **Deterministic**: Same inputs always produce same outputs  
✅ **Live Updates**: Previews update as you type (300ms debounce)  
✅ **Before/After**: See generic vs. personalized side-by-side  

## Adding New Templates

1. Create a JSON file in the appropriate channel directory
2. Follow the template schema:

```json
{
  "id": "unique_id",
  "name": "Human-readable Name",
  "channel": "social|email|quote",
  "description": "Brief description",
  "baseline": {
    "caption": "Generic content...",
    "hashtags": ["#generic", "#example"]
  },
  "personalized": {
    "caption": "Content with {service} and {audience}...",
    "hashtags": ["#{service}", "#custom"]
  },
  "slots": {
    "service": {
      "description": "What this slot represents",
      "example": "Example value"
    }
  }
}
```

3. The template will be automatically discovered by the system

## Testing

```bash
# Unit tests
pytest tests/test_preview_builder_supports_all_channels.py

# E2E tests (requires running server)
RUN_UI_SMOKE=1 pytest tests/e2e/e2e_preview_selector_switches_channels.py
```

## Architecture

- **`preview_builder.py`**: Core builder class with template loading and slot substitution
- **`preview_templates/`**: Template library organized by channel
- **`templates/preview_demo.html`**: Interactive demo page
- **API endpoints**: Flask routes in `app.py` for serving templates

## Benefits

1. **No OpenAI Dependency**: Works offline, instant results
2. **Cost-effective**: No API costs for previews
3. **Consistent**: Deterministic output for testing and demos
4. **Fast**: Perfect for demos, onboarding, and sales presentations
5. **Extensible**: Easy to add new templates and channels
