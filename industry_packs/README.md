# Industry Packs

Industry Packs are comprehensive configuration files that define industry-specific defaults, content strategies, compliance rules, and chip presets for content generation.

## Overview

Each industry pack provides:
- **GOOD Defaults**: Pre-configured chip presets, audience definitions, offers, and proof points
- **Content Templates**: Industry-native post structures, content angles, and CTA libraries
- **Compliance Rules**: Industry-specific safety constraints and regulatory guidelines
- **Keyword Banks**: Seed keywords, topic clusters, and seasonal hooks
- **Prompt Integration**: Do/don't lists and constraints for AI model generation

## Structure

```
industry_packs/
├── README.md (this file)
└── v1/
    ├── schema.json          # JSON schema defining pack structure
    ├── general.json         # Fallback pack for unknown industries
    ├── salon.json           # Example: Salon / Hair Studio
    ├── dentist.json         # Example: Dentist / Dental Practice
    └── ... (other industry packs)
```

## Supported Industries

### Service Industries
- `salon` - Salon / Hair Studio 💇
- `dentist` - Dentist / Dental Practice 🦷
- `gym` - Gym / Fitness Center 🏋️
- `fitness` - Fitness / Wellness 💪
- `cleaner` - Cleaning Service 🧹
- `healthcare` - Healthcare 🩺
- `home_services` - Home Services 🛠️

### Professional Services
- `realtor` - Realtor / Real Estate Agent 🏡
- `coach` - Coach / Consultant 🧭

### Retail & Hospitality
- `restaurant` - Restaurant / Café 🍽️
- `retail` - Retail / Boutique 🛍️
- `artisan` - Artisan / Maker 🎨
- `house_host` - House Host / Vacation Rental 🏠

### Community & Nonprofit
- `church` - Church ⛪
- `nonprofit` - Nonprofit / Community 🤝

### Fallback
- `general` - General Business ✨ (used for unknown industries or `other`)

## Usage

### Loading Industry Packs

```python
from industry_pack_loader import get_industry_pack, get_good_defaults

# Get an industry pack (with automatic fallback to 'general')
pack = get_industry_pack('salon')

# Get just the good_defaults section
defaults = get_good_defaults('realtor')
chip_presets = defaults['chip_presets']
focus_topics = chip_presets['focus_topics']  # 8-12 chips
audience_chips = chip_presets['audience_chips']  # 6-10 chips
```

### Using Chip Presets

The `good_defaults.chip_presets` section provides industry-native language for:
- **focus_topics**: Main content themes (8-12 chips)
- **audience_chips**: Target audience segments (6-10 chips)
- **offer_chips**: Service/product offerings (6-10 chips)
- **proof_chips**: Social proof and credibility (6-10 chips)

These chips are designed to be:
1. **Editable** by users
2. **Supplemented** with custom "write-in" chips
3. **Compiled** into prompts for consistent context

### GOOD / BETTER / BEST Progression

**GOOD** (Auto-selected):
- Uses `chip_presets.focus_topics` + default CTAs + 1 content angle
- Zero user input required
- Industry-native output

**BETTER** (3 additional inputs):
- Prompts for: audience pains, offer specifics, proof points
- Combines with GOOD defaults

**BEST** (5 additional inputs):
- Prompts for: differentiators, objections, examples, brand enforcement, exclusions
- Maximum customization

## Schema Overview

Each industry pack follows a strict JSON schema (`schema.json`) with these required sections:

### Top-Level Fields
- `id`: Unique identifier (e.g., "salon")
- `display_name`: Human-readable name
- `icon`: Emoji or icon
- `primary_customer_goal`: bookings | memberships | recurring_clients | sales | leads
- `version`: Semantic version (X.Y.Z)

### Core Sections
1. **business_profile_fields**: Required/optional fields for setup wizard
2. **default_channel_strategy**: Platforms, cadence, best-performing content types
3. **keyword_banks**: Seed keywords, topic clusters, seasonal hooks
4. **cta_library**: Categorized CTAs (booking, inquiry, review/referral, offer)
5. **compliance_safety_rules**: Forbidden claims, privacy constraints, regulatory notes
6. **content_templates**: Post structures, reel structures, email templates
7. **example_outputs**: Reference examples for each content type
8. **prompt_integration_hooks**: Model constraints and do/don't lists
9. **good_defaults**: ⭐ NEW - Chip presets and industry defaults

### Good Defaults Structure

```json
{
  "good_defaults": {
    "audience": {
      "who": "Plain English description",
      "pain_points": ["3-5 pain points"],
      "desired_outcomes": ["3-5 desired outcomes"]
    },
    "offers": {
      "common_services": ["5-8 services"],
      "ctas": ["4-6 CTAs"]
    },
    "proof": {
      "common_proof_points": ["4-6 safe proof points"]
    },
    "content_angles": [
      {
        "key": "transformation",
        "label": "Before/After Transformation",
        "when_to_use": "Showcase dramatic results"
      }
      // 6-8 total angles
    ],
    "do_say": ["positive examples"],
    "dont_say": ["risky language to block"],
    "chip_presets": {
      "focus_topics": ["8-12 chips"],
      "audience_chips": ["6-10 chips"],
      "offer_chips": ["6-10 chips"],
      "proof_chips": ["6-10 chips"]
    }
  }
}
```

## Fallback Behavior

If an industry pack doesn't exist, the system automatically falls back to the `general` pack:

```python
# Unknown industry automatically uses 'general' pack
pack = get_industry_pack('unknown_industry')  # Returns general.json
pack['id']  # 'general'
```

The `general` pack provides safe, industry-agnostic defaults suitable for any business type.

## Creating New Industry Packs

To add a new industry:

1. Copy `general.json` as a starting template
2. Update all required fields according to `schema.json`
3. Customize `good_defaults` with industry-specific language
4. Add industry-specific keywords, CTAs, and compliance rules
5. Validate with: `pytest tests/test_industry_pack_schema.py -k "new_industry_id"`

### Key Principles

- **Natural Language**: Chips should sound native to the industry
- **Paste-Ready**: Content should require minimal editing
- **Compliance-Safe**: Block risky claims and respect regulations
- **User-Extendable**: Allow custom chips and write-ins
- **Consistent**: Follow existing pack patterns

## Testing

Run all industry pack tests:

```bash
pytest tests/test_industry_pack*.py -v
```

Test specific areas:
- Schema validation: `test_industry_pack_schema.py`
- Existence checks: `test_industry_packs_exist_for_supported.py`
- Fallback behavior: `test_industry_pack_fallback_general.py`

## Integration Points

Industry packs integrate with:

1. **Prompt Compiler** (`services/generation/prompt_compiler.py`)
   - Loads constraints and do/don't lists
   - Includes industry context in prompts

2. **Setup Wizard** (future)
   - Auto-populates fields based on industry selection
   - Suggests chip presets

3. **Generate Page** (future)
   - Shows industry-specific chip suggestions
   - Allows custom write-in chips
   - Compiles into generation context

4. **Future Generators** (Email, Quotes)
   - Use same industry pack data
   - Consistent voice across channels

## Version History

- **v1.0.0** (2025-01): Initial implementation
  - 16 industry packs created
  - good_defaults schema added
  - Fallback to 'general' pack
  - Comprehensive test coverage

## Contributing

When adding or updating industry packs:

1. Follow the JSON schema strictly
2. Test with `validate_industry_pack()`
3. Ensure all required minimums (e.g., 8+ focus_topics)
4. Use industry-native language, not generic
5. Include compliance constraints where applicable
6. Add tests for new packs

## Questions?

See:
- `industry_pack_loader.py` - Loading and validation logic
- `schema.json` - Complete schema definition
- `tests/test_industry_pack_schema.py` - Validation examples
