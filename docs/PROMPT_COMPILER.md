# Prompt Compiler - The "Secret Sauce" for Voice-Accurate Generation

## Overview

The Prompt Compiler is the core system for generating voice-accurate, toggle-aware content. It merges profile defaults, voice fingerprints, templates, and request toggles with deterministic precedence to produce compact, structured prompts that drive best-in-class outputs.

## Architecture

### Core Components

1. **prompt_compiler.py** - Main compiler with canonical input/output types
2. **prompt_trace.py** - Redacted logging for debugging (no PII)
3. **voice_style_builder.py** - Enhanced with micro-examples extraction
4. **output_validator.py** - Schema validation with repair pass

### Input Types (Deterministic Precedence)

```
RunToggles > TemplatePreset > VoiceFingerprint > ProfileDefaults
```

#### 1. ProfileDefaults (from DB)
Workspace/account defaults:
- company, industry, signature_tone
- platforms, timezone
- offerings, audience, taboo_topics

#### 2. VoiceFingerprint (from voice coach training)
Style constraints that persist across templates:
- sentence_length_band, emoji_rate
- punctuation_style, typical_cta_patterns
- top_phrases[], avoid_phrases[]
- signature_moves[]
- micro_examples (caption, CTA, avoid/rewrite)

#### 3. TemplatePreset (optional)
Saved template settings:
- structure_preference, cadence
- preferred_tone, preferred_platforms
- keywords_format

#### 4. RunToggles (request - highest priority)
Request-specific overrides:
- session_length, platform_focus
- tone_override, keywords, goals
- promo_note, reel_toggles, variants

### Output Types

#### 1. ModelReadyContext (JSON)
Compact context with only essentials:
```python
{
    'company_name': str,
    'industry': str,
    'tone': str,
    'platforms': List[str],
    'voice_applied': bool,
    'voice_style': {...},  # if voice applied
    'template_applied': bool
}
```

#### 2. JSON Schema
Strict schema for model output validation:
```python
{
    "type": "object",
    "required": ["posts"],  # or "script", "responses"
    "properties": {...}
}
```

#### 3. PromptSet
Three-part prompt for the model:
```python
{
    'system': str,   # role + format + safety
    'context': str,  # brand + voice (compact)
    'request': str   # toggles + platform rules
}
```

## Usage

### Basic Usage (via GenerationService)

```python
from services.generation import GenerationService

# Initialize with prompt compiler enabled
service = GenerationService(
    openai_api_key="your-key",
    use_prompt_compiler=True  # Enable new compiler
)

# Define inputs
workspace = {
    'company_name': 'My Company',
    'industry': 'tech',
    'default_tone': 'professional',
    'platforms': ['instagram', 'linkedin']
}

voice_samples = [
    "Quick wins matter! Let's celebrate small victories.",
    "Your feedback helps us grow. Drop a comment!",
    "We make complex simple, one step at a time."
]

request = {
    'session_length': 7,
    'tone': 'friendly',  # Overrides workspace default
    'platforms': ['instagram', 'facebook'],  # Overrides workspace
    'keywords': ['innovation', 'growth'],
    'goals': ['engagement', 'awareness']
}

# Generate content
result = service.generate_with_compiler(
    content_type='social',
    workspace=workspace,
    voice_samples=voice_samples,
    include_phrases=['celebrate', 'grow'],
    avoid_phrases=['synergy', 'leverage'],
    request=request
)

if result['ok']:
    posts = result['data']['posts']
    voice_applied = result['summary']['voice_applied']
    print(f"Generated {len(posts)} posts with voice: {voice_applied}")
```

### Direct Compiler Usage

```python
from services.generation.prompt_compiler import (
    PromptCompiler,
    ProfileDefaults,
    VoiceFingerprint,
    RunToggles
)

# Define inputs with canonical types
profile = ProfileDefaults(
    company='Tech Co',
    industry='software',
    signature_tone='professional',
    platforms=['linkedin'],
    offerings='SaaS platform',
    audience='Developers'
)

voice_fp = VoiceFingerprint(
    sentence_length_band='short',
    top_phrases=['game changer', 'level up'],
    avoid_phrases=['disrupt', 'synergy'],
    signature_moves=['direct', 'punchy'],
    micro_examples={
        'example_caption': 'Quick wins build momentum. Start small.',
        'example_cta': 'Drop a comment and share your story',
        'avoid_rewrite': {
            'bad': 'Leverage synergistic solutions',
            'good': 'Work together for better results'
        }
    }
)

run_toggles = RunToggles(
    session_length=7,
    tone_override='inspiring',  # Overrides all
    platform_focus=['instagram'],  # Overrides all
    keywords=['innovation'],
    goals=['engagement']
)

# Compile
compiler = PromptCompiler(
    profile_defaults=profile,
    voice_fingerprint=voice_fp
)

output = compiler.compile_for_social(run_toggles, request_id='abc123')

# Access outputs
model_context = output['model_context']
json_schema = output['json_schema']
prompt_set = output['prompt_set']
trace_summary = output['trace_summary']

print(f"Tone: {model_context['tone']}")  # 'inspiring' (from run_toggles)
print(f"Voice applied: {model_context['voice_applied']}")  # True
print(f"Token estimate: {trace_summary['token_budget_estimate']}")
```

## Precedence Rules (Critical)

1. **Tone**: RunToggles.tone_override > TemplatePreset.preferred_tone > ProfileDefaults.signature_tone
2. **Platforms**: RunToggles.platform_focus > TemplatePreset.preferred_platforms > ProfileDefaults.platforms
3. **Voice**: Always applied as constraints (never overridden by template)
4. **Keywords/Goals**: Only from RunToggles (request-specific)

## Voice Anchoring

The compiler includes micro-examples in prompts to anchor the model's voice:

```
VOICE EXAMPLES:
  Caption example: "Quick wins build momentum. Start small, go big!"
  CTA example: "Drop a comment and share your story"
  ❌ Avoid: "Leverage synergistic solutions" → ✓ Use: "Work together for better results"
```

This ensures:
- Top phrases appear naturally
- Avoid phrases are absent
- CTA style matches user's voice
- Templates change structure, NOT voice identity

## Prompt Trace (Debugging)

Every compilation creates a redacted trace:

```python
{
    'request_id': 'abc123',
    'content_type': 'social',
    'timestamp': '2024-01-01T12:00:00Z',
    'selections': {
        'tone': 'inspiring',
        'platforms': ['instagram'],
        'session_length': 7,
        'goals_count': 1,
        'keywords_count': 1
    },
    'voice_fingerprint_applied': True,
    'template_used': None,
    'token_budget_estimate': 450,
    'flags': {
        'voice_applied': True,
        'template_applied': False
    }
}
```

**No PII**: Emails, phones, addresses are never logged.

## Output Validation & Repair

The validator enforces schema compliance:

1. **Initial validation**: Check against JSON schema
2. **Repair pass** (if invalid): Call OpenAI with stricter instructions
3. **Fallback**: Return deterministic content or error

```python
from services.generation.output_validator import validate_with_schema_enforcement

result = validate_with_schema_enforcement(
    data=openai_output,
    content_type='social',
    openai_client=client,
    prompt_set=prompt_set,
    json_schema=json_schema
)

if result['ok']:
    validated_data = result['data']
    was_repaired = result['repaired']
else:
    error = result['error']
```

## Testing

Comprehensive test suite (79 tests):

```bash
# Run all prompt compiler tests
pytest tests/test_prompt_compiler_precedence.py -v
pytest tests/test_voice_fingerprint_application.py -v
pytest tests/test_prompt_golden_*.py -v
pytest tests/test_output_schema_validation.py -v
pytest tests/test_no_pii_in_prompt_trace.py -v
pytest tests/test_generation_service_compiler.py -v
```

### Golden Tests

Golden/snapshot tests verify prompt structure consistency:
- `test_prompt_golden_social.py` - Social post prompts
- `test_prompt_golden_reels.py` - Reel/video prompts
- `test_prompt_golden_reviews.py` - Review response prompts

### Critical Tests

- **Precedence**: Every key follows correct merge order
- **Voice Persistence**: Voice fingerprint never "washed out" by templates
- **No PII**: Trace logging contains zero PII
- **Schema Validation**: Invalid output triggers repair deterministically

## Migration Path

The `use_prompt_compiler` flag allows gradual migration:

```python
# Old approach (default)
service = GenerationService(enable_openai=True)
result = service.generate_social_posts(...)

# New approach (opt-in)
service = GenerationService(enable_openai=True, use_prompt_compiler=True)
result = service.generate_with_compiler(content_type='social', ...)
```

Both approaches coexist during transition.

## UX Impact (Acceptance Criteria)

✅ **Toggle Predictability**:
- Changing platform → formatting/hashtag changes
- Changing tone → diction/CTA style changes
- Enabling voice → top phrases appear, avoid phrases absent

✅ **Voice Identity**:
- Voice fingerprint persists when templates applied
- Templates change structure, not voice
- Micro-examples guide model output

✅ **Debugging**:
- Prompt traces show what was selected
- Token estimates help optimize
- No PII exposure in logs

## Performance Notes

- Token estimate: ~200-800 tokens per social prompt
- Compilation time: < 10ms (excluding voice style building)
- Validation time: < 5ms (excluding OpenAI repair call)

## Future Enhancements

- [ ] Template library with pre-configured TemplatePresets
- [ ] Voice fingerprint versioning for A/B testing
- [ ] Prompt optimization based on trace analytics
- [ ] Multi-model support (Claude, Gemini, etc.)
