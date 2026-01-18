# Content Generation API Enhancement

## Overview

The content generation API has been enhanced to support content-type-specific inputs that enable Gemini to generate highly tailored content. The API now intelligently structures profile data (including scraped metadata, customer segments, and niche keywords) into prompts that produce content matching the brand's voice.

**💬 INTERACTION MODEL**: Eazeily now features a chat-first interface with slash commands. See [user-journey.md](user-journey.md) for the complete conversational user experience. This document focuses on the underlying API architecture.

**🔗 Related Documentation**:
- [user-journey.md](user-journey.md) - Chat-first user journey with slash commands
- [PROFILE_TO_GENERATION_FLOW.md](PROFILE_TO_GENERATION_FLOW.md) - Technical data flow
- [NORTH_STAR_USER_JOURNEY.md](NORTH_STAR_USER_JOURNEY.md) - Product vision

## API Endpoints

### Primary Endpoint: POST /api/chat (Chat-First)

The conversational interface for all content generation tasks.

**Request:**
```json
{
  "message": "Write a LinkedIn post about our new feature",
  "history": [
    {"role": "user", "message": "previous message"},
    {"role": "assistant", "message": "AI response"}
  ],
  "pending_task": {
    "task_type": "post",
    "collected": {"platform": "instagram", "topic": "..."}
  }
}
```

**Response:**
```json
{
  "response": "Here's your LinkedIn post...",
  "action": "generated|continue|onboarding|error",
  "content": "Generated content text",
  "pending_task": null,
  "suggestions": ["Make it shorter", "Try Instagram instead"]
}
```

**Features:**
- Natural language parsing via `ConversationRouter`
- Slash command support (`/post`, `/email`, `/voice`, etc.)
- Multi-turn conversations with `pending_task` state
- Profile-driven content generation
- AI-powered profile suggestions

**Implementation**: `routes/chat_routes.py`

---

### Legacy Endpoint: POST /api/generate (Form-Based)

Direct API endpoint for content generation (used by dashboard forms).

**Request:**
```json
{
  "task_type": "post",
  "topic": "New product launch",
  "platform": "linkedin"
}
```

**Response:**
```json
{
  "status": "success",
  "content": "Generated content...",
  "task_type": "post",
  "platform": "linkedin"
}
```

**Implementation**: `routes/generate_routes.py`

---

## Content Generation Features

### 1. Enhanced Profile Data Flow

**Profile fields now included in generation:**
- `customers` - Target customer segments (from scraper or manual input)
- `niche_keywords` - Industry-specific terminology
- `brand_keywords` - Brand descriptors and values
- `scraped_meta` - Metadata from URL scraping (business name, customer profile, etc.)

**Example profile structure:**
```json
{
  "company": "TechStart Inc",
  "industry": "Software / Tech / Startup",
  "brand_voice": "Professional and innovative",
  "target_audience": "Software developers and tech teams",
  "customers": ["Enterprise", "SMB", "Startups"],
  "brand_keywords": ["fast", "reliable", "innovative"],
  "niche_keywords": ["API", "SaaS", "cloud-native"],
  "scraped_meta": {
    "business_name": "TechStart Inc",
    "key_customers": "Tech companies and startups"
  }
}
```

### 2. Content-Type-Specific Generation

The API now supports specialized content types with dedicated field sets:

#### Proposals (`task_type: "proposal"`)

Generate professional business proposals with structured components.

**Additional fields:**
- `proposal_type` (string): Type of proposal
  - Options: `partnership`, `sponsorship`, `funding`, `rfp_response`, `collaboration`
- `recipient` (string): Company/person name
- `key_benefits` (array): List of key benefits to highlight
- `budget_range` (string): Budget range (e.g., "$10k-$50k")
- `cta` (string): Call to action

**Example request:**
```json
{
  "task_type": "proposal",
  "topic": "Strategic Partnership Proposal",
  "proposal_type": "partnership",
  "recipient": "Acme Corp",
  "key_benefits": [
    "Access to 100k+ developer audience",
    "Co-marketing opportunities",
    "Joint product development"
  ],
  "budget_range": "$25k-$75k",
  "cta": "Schedule a discovery call"
}
```

**Generated output includes:**
- Three title options
- Executive summary
- Key benefits (formatted)
- Clear call-to-action
- Compelling subject line

---

#### Review Replies (`task_type: "review_reply"`)

Generate professional, empathetic responses to customer reviews.

**Additional fields:**
- `review_source` (string): Platform name (e.g., "Google", "Yelp", "Amazon")
- `star_rating` (string): Rating given
  - Options: `"1"`, `"2"`, `"3"`, `"4"`, `"5"`
- `sentiment` (string): Overall sentiment
  - Options: `positive`, `neutral`, `negative`
- `issue_type` (string): Type of issue mentioned
  - Options: `shipping`, `product`, `experience`, `service`
- `desired_tone` (string): Tone for the response
  - Options: `apologetic`, `grateful`, `professional`, `empathetic`
- `follow_up_action` (string): Proposed remedy or action

**Example request:**
```json
{
  "task_type": "review_reply",
  "topic": "Great product but shipping was slow. Still happy with the purchase!",
  "review_source": "Google",
  "star_rating": "4",
  "sentiment": "positive",
  "issue_type": "shipping",
  "desired_tone": "grateful",
  "follow_up_action": "Offer expedited shipping on next order"
}
```

**Generated output includes:**
- Full reply (professional and brand-aligned)
- Short reply (<140 characters for social sharing)

---

#### Blog Posts (`task_type: "blog_post"`)

Generate comprehensive, SEO-optimized blog content.

**Additional fields:**
- `post_type` (string): Type of blog post
  - Options: `listicle`, `how-to`, `announcement`, `thought-leadership`, `case-study`
- `desired_length` (string): Target word count
  - Options: `short` (400-600 words), `medium` (750-1000 words), `long` (1200-1500 words)
- `audience` (string): Specific target audience
- `seo_keywords` (array): Keywords to optimize for
- `cta` (string): Call to action

**Example request:**
```json
{
  "task_type": "blog_post",
  "topic": "How to Build a Scalable API Architecture",
  "post_type": "how-to",
  "desired_length": "medium",
  "audience": "Software architects and engineering leads",
  "seo_keywords": ["API architecture", "scalable systems", "microservices"],
  "cta": "Download our API design guide"
}
```

**Generated output includes:**
- Three SEO-optimized title options
- Meta description (150-160 characters)
- Content outline with H2 headings
- Full article (750-1000 words)
- Call-to-action

---

### 3. Backward Compatibility

All existing content types continue to work without modification:
- `post` - Social media posts
- `ad` - Advertising copy
- `email` - Email marketing
- `review` - Generic review responses
- `newsletter` - Newsletter content
- `blog` - Generic blog posts
- `script` - Video scripts
- `caption` - Image captions

---

## Profile Management API

### POST /api/profile

Update user profile with new data.

**Authentication:** Required (session-based)

**Request:**
```json
{
  "company": "TechStart Inc",
  "industry": "Software / Tech / Startup",
  "tone": "Professional",
  "platforms": ["linkedin", "twitter"],
  "brand_keywords": ["innovative", "reliable"],
  "niche_keywords": ["API", "cloud"],
  "customers": ["Enterprise", "SMB"],
  "target_audience": "Software development teams"
}
```

**Enhanced fields:**
- `customers` (array): Target customer segments
- `scraped_url` (string): URL that was scraped
- `scraped_meta` (object): Metadata from scraping
- `scrape_status` (string): Status of scraping operation

**Response:**
```json
{
  "status": "success",
  "message": "Profile updated successfully"
}
```

---

### POST /api/profile/suggest

Get AI-powered suggestions for profile fields (used by `/voice`, `/audience`, `/offer` commands).

**Authentication:** Required (session-based)

**Request:**
```json
{
  "field": "target_audience|brand_voice|key_offer"
}
```

**Response:**
```json
{
  "status": "success",
  "suggestions": [
    "Small business owners aged 30-50 who struggle with...",
    "Solopreneurs and freelancers who need...",
    "Marketing managers at agencies seeking..."
  ],
  "field": "target_audience"
}
```

**Implementation:** `services/profile_expert.py` - Uses Gemini to analyze current profile and generate contextual suggestions.

**Features:**
- Context-aware suggestions based on full profile
- Industry-specific recommendations
- Analyzes writing samples for tone matching
- Returns 3 specific, actionable options

---

## Gemini Integration

### services/generation/gemini_adapter.py

New module providing structured Gemini API interface.

**Key functions:**

```python
def call_gemini(
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    model: str = 'gemini-1.5-flash',
    temperature: float = 0.7,
    timeout: int = 30,
    max_retries: int = 2
) -> Optional[Dict[str, Any]]
```

**Features:**
- Automatic retry on failure (with exponential backoff)
- Timeout handling (30s default)
- JSON parsing with markdown code block removal
- Comprehensive error handling and logging

**Example usage:**
```python
from services.generation.gemini_adapter import call_gemini

result = call_gemini(
    prompt="Generate a blog post about...",
    context={"company": "TechStart", "industry": "Tech"},
    temperature=0.7
)
```

## Testing

### Unit Tests

**tests/test_gemini_adapter.py** - 12 tests covering:
- Content validation for all content types
- Prompt building for different content types
- JSON parsing and error handling
- Client availability checks

**tests/test_profile_data_flow.py** - 9 tests covering:
- Profile data inclusion in prompts
- Content-type-specific context handling
- Error handling (timeouts, rate limits)
- Optional field handling

**Run tests:**
```bash
PYTHONPATH=. python -m pytest tests/test_gemini_adapter.py tests/test_profile_data_flow.py -v
```

## Error Handling

The system provides clear error messages for common failure scenarios:

1. **Timeout errors:**
   - Message: "Error: Request timed out. Please try again."
   - Cause: API request exceeded timeout threshold

2. **Rate limit errors:**
   - Message: "Error: API rate limit reached. Please try again in a moment."
   - Cause: Too many requests to Gemini API

3. **Authentication errors:**
   - Message: "Error: API authentication failed. Please check configuration."
   - Cause: Invalid or missing API key

4. **Generic errors:**
   - Message: "Error: Failed to generate content. Please try again."
   - Cause: Unexpected errors during generation

## Configuration

### Environment Variables

- `GENAI_API_KEY` or `GOOGLE_API_KEY` - Required for Gemini API access
- Default model: `gemini-1.5-flash`
- Default timeout: 30 seconds
- Max retries: 2

## Migration Guide

### For Frontend Developers

1. **Add content-type-specific UI panels** (see `static/content-type-handlers.js`)
2. **Collect additional fields** based on selected task_type
3. **Include fields in POST /api/generate** request
4. **Handle enhanced responses** (may include structured data)

### For Backend Developers

Profile data automatically flows through the generation pipeline. No changes required for basic integration.

To add new content types:
1. Add to `services/task_registry.py`
2. Add validation in `routes/generate_routes.py`
3. Add format instructions in `services/voice_engine.py`
4. Add prompt template in `services/generation/gemini_adapter.py`

## Future Enhancements

- [ ] Add UI panels to dashboard for content-type fields
- [ ] Add template library for common proposals/blog posts
- [ ] Add content preview before final generation
- [ ] Add A/B testing for different prompt variations
- [ ] Add analytics for content performance
