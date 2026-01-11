# User Journey: End-to-End Content Generation Flow

## Overview
This document describes the complete user journey from profile setup through content generation in Eazeily. It includes the technical flow, current pain points, and a QA checklist for validation.

**✅ MAJOR UPDATE (2026-01-11)**: Added standalone editable profile page at `/profile` to address missing profile editing functionality. Users can now view and edit their brand profile after initial onboarding.

**📖 Related Documentation**: See [PROFILE_TO_GENERATION_FLOW.md](PROFILE_TO_GENERATION_FLOW.md) for detailed technical data flow from profile → AI generation.

## Primary User Flow

### 1. Profile Completion
**Entry Point**: New user signs up or existing user accesses `/onboarding`

**Steps**:
1. User lands on onboarding wizard (`/onboarding` or `/onboarding_wizard`)
2. **Step 1**: Add Website URL (optional but recommended)
   - User pastes website URL
   - System scrapes website using `voice_profile.py` scraper
   - AI analyzes content and suggests brand voice, messaging, key offers
   - Pre-fills profile fields
   - Falls back to manual entry if scraping fails
3. **Step 2**: Review & Edit Profile
   - Business name (required)
   - Industry (required, from config.json)
   - Target audience (required)
   - Brand voice (required)
   - Key offer/hook (required)
   - Voice rules (optional)
   - Writing samples (required)
4. User submits form via POST to `/onboarding`
5. **Database Save**: Profile data saved to `voice_profile` table
   - Fields: user_id, business_name, industry, target_audience, brand_voice, key_offer, voice_rules, writing_samples, platforms, brand_keywords, goals, timezone, etc.
   - Backend: `routes/onboarding_routes.py` route handler processes form data
   - Validation ensures required fields are present
6. **Success**: User redirected to `/dashboard` with success message

**Current Status**:
- ✅ **Profile Save Fixed**: API endpoint works correctly (verified with tests)
- ✅ **Clear Feedback**: Success toast and redirect after save
- ⚠️ Website scraper timeout can leave user hanging without feedback (existing issue)

### 2. Profile Editing (NEW ✅)
**Entry Point**: Authenticated user navigates to `/profile` from sidebar or dashboard

**Steps**:
1. User clicks "Edit Profile" in sidebar navigation
2. Profile page loads at `/profile`
3. System fetches existing profile via GET `/api/profile`
4. Form fields pre-populated with current values:
   - Basic info: company, industry, timezone
   - Brand voice: tone, target_audience, key_offer, voice_rules
   - Platforms: checkboxes for social platforms
   - Keywords & goals: brand_keywords, goals (comma-separated)
   - Writing samples: text area with examples
5. User edits any fields
6. User clicks "Save Profile" button
7. System validates required fields (company, industry, tone)
8. POST `/api/profile` with updated data
9. **Success**: Green success message, profile persisted to DB
10. User can return to dashboard or continue editing

**Features**:
- ✅ Loading state while fetching profile
- ✅ Error handling with clear messaging
- ✅ Validation for required fields
- ✅ Success feedback with toast notification
- ✅ Back button to dashboard
- ✅ All profile fields editable

**Navigation**:
- From sidebar: Click "Edit Profile" under "Brand Setup"
- From dashboard: (Can add profile link in dashboard header if needed)

### 3. Dashboard Access
**Entry Point**: User navigates to `/dashboard` after profile save

**Steps**:
1. Dashboard loads with content generator interface
2. System fetches user profile from database via `/api/current_user` or session
3. Profile data populates generator defaults:
   - Industry/tone/keywords from profile
   - Company name from business_name
   - Brand voice informs generation tone

**Current Pain Points**:
- ⚠️ Dashboard loads but may show "missing profile" warnings even after successful save
- ⚠️ No visual indicator that profile data was successfully loaded

### 3. Generator Dashboard Interaction
**Entry Point**: User on `/dashboard` ready to generate content

**UI Components**:
- **Task Selector**: 9 content type tiles (Social Post, Image Caption, Video Script, Email, Proposal, Social Ads, Review Reply, Blog Post, Newsletter)
- **Topic Input**: Text area for content description
- **Platform Dropdown**: Appears for "Social Post" task only
  - Options: LinkedIn, Instagram, Facebook, Twitter
- **Dynamic Context Fields**: Appear based on task/platform selection
  - Ad options (audience, objective)
  - LinkedIn style options
  - Instagram mood options
  - Video length options
  - Email CTA options
- **Generate Button**: Triggers content generation

**Steps**:
1. User selects task type (e.g., "Social Post")
2. Platform dropdown appears if task type is "post"
3. User enters topic description
4. User optionally fills dynamic context fields
5. User clicks "Generate Post" button
6. Frontend sends POST to `/api/generate` with payload:
   ```json
   {
     "topic": "user topic",
     "platform": "Instagram",
     "task_type": "post",
     "ad_objective": "traffic",
     "target_audience": "busy moms"
   }
   ```

**Current Pain Points**:
- ❌ **Generator Dashboard Dead-ends**: Some generation requests fail without clear error messaging
  - Possible cause: Missing Gemini API key (returns 503)
  - Possible cause: Timeout from Gemini API (>45s)
  - Possible cause: Rate limiting on Gemini API
- ❌ **Confusing Social Dropdown Labels**: Current platform dropdown lacks clarity
  - Inconsistent naming: "Twitter" vs "X (Twitter)"
  - Missing platforms: TikTok, Reels/Shorts
  - Ads mixed with organic platforms
  - No grouping/categorization

### 4. Gemini API Integration
**Entry Point**: Backend receives `/api/generate` request

**Steps**:
1. `app.py` route handler receives request
2. System validates request:
   - `topic` required for all tasks
   - `platform` required for task_type="post"
3. System checks for Gemini API key (`GENAI_API_KEY`)
   - If missing: returns 503 with error code "missing_api_key"
4. System loads user profile from database
   - If missing: returns 400 with redirect to "/onboarding"
5. Backend merges request payload with profile data:
   ```python
   payload = {
       "topic": request_topic,
       "platform": request_platform,
       "task_type": request_task_type,
       "industry": profile.industry,
       "tone": profile.brand_voice,
       "company": profile.business_name,
       "keywords": extracted_from_profile,
       "goals": extracted_from_profile,
       **dynamic_inputs
   }
   ```
6. System constructs Gemini prompt via `generation_service.py`:
   - Loads task definition from `services/task_registry.py`
   - Applies platform-specific hints from `PLATFORM_HINTS` in `generator.py`
   - Includes brand voice, tone, industry context
   - Adds platform-specific formatting rules from `platform_rules.py`
7. System calls Gemini API with prompt
8. Gemini returns generated content (text)
9. System applies platform-specific post-processing:
   - Hashtag formatting from `platform_rules.py`
   - Character limits
   - CTA insertion
10. Backend returns JSON response:
    ```json
    {
      "status": "success",
      "content": "Generated post text with hashtags...",
      "metadata": {
        "platform": "instagram",
        "warnings": []
      }
    }
    ```

**Current Pain Points**:
- ⚠️ No retry logic if Gemini API times out
- ⚠️ 45-second timeout may be too short for complex requests
- ⚠️ Error messages from Gemini API not user-friendly
- ⚠️ Rate limit errors not surfaced clearly to user

### 5. Content Output Display
**Entry Point**: Frontend receives `/api/generate` response

**Steps**:
1. JavaScript receives response in dashboard.html form handler
2. Success case:
   - Parse `data.content` from response
   - Display in `#resultBox` element
   - Show in `#postContent` pre element
   - Enable "Copy to Clipboard" button
   - Show success toast notification
3. Error case:
   - Parse error message and code
   - Map error codes to user-friendly messages:
     - `missing_api_key`: "AI service not configured. Please contact support."
     - `timeout`: "Generation timed out. Please try again with a simpler request."
     - `rate_limit`: "API rate limit reached. Please wait a moment and try again."
   - Display error toast notification
   - If `redirect` in response, prompt user to complete profile

**User Actions**:
- **View**: Read generated content in result box
- **Copy**: Click "Copy" button to copy to clipboard (shows "✓ Copied!" confirmation)
- **Edit**: Can manually edit copied content outside app
- **Regenerate**: Modify inputs and click Generate again

**Current Pain Points**:
- ⚠️ No save/history feature - content lost if page refreshed
- ⚠️ No inline editing of generated content
- ⚠️ No export to other formats (PDF, DOCX)
- ⚠️ Copy button doesn't handle mobile keyboards well

## Content Type Taxonomy

Eazeily supports 9 distinct content types, each optimized for specific channels, use cases, and best practices. This comprehensive taxonomy ensures consistent, high-quality content generation across the entire user journey.

### 1. Social Post (`post`)
**What it is**: Organic social media posts for platforms like Instagram, Facebook, LinkedIn, X (Twitter), and TikTok.

**Platforms/Channels**:
- Instagram (feed posts, stories)
- Facebook (page posts, personal posts)
- LinkedIn (professional updates, thought leadership)
- X / Twitter (short-form posts, threads)
- TikTok (short-form video captions)
- Reels/Shorts (Instagram Reels, YouTube Shorts)

**Use Cases**:
- Brand awareness and visibility
- Audience engagement and community building
- Thought leadership and expertise sharing
- Product/service announcements
- Behind-the-scenes content
- Customer stories and testimonials

**Best Practices**:
- **Hook**: Start with attention-grabbing first line (especially important for Instagram/TikTok)
- **Length**: Platform-appropriate (280 chars for Twitter, 1-2 paragraphs for LinkedIn, 2000 chars max for Instagram)
- **Hashtags**: Include 3-12 relevant, niche hashtags (platform-dependent)
- **CTA**: Clear call-to-action (comment, share, visit link)
- **Tone**: Match brand voice and platform culture
- **Visuals**: Reference visual content being paired with post

**Generator Flow**:
1. User selects "Social Post" tile
2. Platform dropdown appears (Instagram, Facebook, LinkedIn, X, TikTok, Reels/Shorts)
3. User enters topic description
4. Dynamic options appear based on platform (e.g., Instagram mood, LinkedIn tone)
5. System generates platform-optimized content using `PLATFORM_HINTS` and `platform_rules.py`

---

### 2. Image Caption (`caption`)
**What it is**: Captions for photos and images to be shared on social media platforms.

**Platforms/Channels**:
- Instagram (photo posts)
- Facebook (photo albums, image posts)
- LinkedIn (image posts)
- X / Twitter (image posts)

**Use Cases**:
- Product showcase and launches
- Behind-the-scenes glimpses
- Customer stories and user-generated content
- Event highlights and coverage
- Team introductions
- Lifestyle and brand aesthetic content

**Best Practices**:
- **Context**: Describe what's happening in the image
- **Emotion**: Add emotional connection or storytelling
- **Brevity**: Keep it concise (especially for Twitter)
- **Hashtags**: Include relevant tags for discoverability
- **Accessibility**: Describe visual elements for accessibility
- **CTA**: Invite engagement (tag someone, share, comment)

**Generator Flow**:
1. User selects "Image Caption" tile
2. User describes the image or pastes image description
3. System generates caption that complements the visual
4. No platform dropdown (works across social platforms)

---

### 3. Video Script (`script`)
**What it is**: Scripts for short-form video content optimized for Reels, TikToks, and YouTube Shorts.

**Platforms/Channels**:
- TikTok (short-form vertical video)
- Instagram Reels (short-form vertical video)
- YouTube Shorts (short-form vertical video)
- Facebook Reels (short-form vertical video)

**Use Cases**:
- Tutorials and how-tos
- Product demonstrations
- Educational content
- Storytelling and narratives
- Entertainment and trending content
- Day-in-the-life content

**Best Practices**:
- **Hook**: Capture attention in first 3 seconds (critical for retention)
- **Structure**: Include timestamps for editing (e.g., 0:00-0:03 Hook)
- **Visual Cues**: Add shot descriptions and visual directions
- **Pacing**: Keep it fast-paced, punchy dialogue
- **Audio**: Consider voiceover, music, and sound effects
- **CTA**: Strong call-to-action at end (follow, comment, share)
- **Text Overlays**: Note where on-screen text should appear

**Generator Flow**:
1. User selects "Video Script" tile
2. User enters video topic and concept
3. Dynamic options: video length (15s, 30s, 60s), style (tutorial, entertainment, story)
4. System generates script with timestamps, dialogue, and shot descriptions

---

### 4. Email Draft (`email`)
**What it is**: Personalized outreach emails for customer communication, follow-ups, and relationship building.

**Platforms/Channels**:
- Email (direct inbox delivery)
- Gmail, Outlook, Apple Mail, etc.

**Use Cases**:
- Customer outreach and prospecting
- Follow-up emails after meetings/calls
- Partnership and collaboration proposals
- Personal connection and networking
- Customer check-ins
- Sales outreach

**Best Practices**:
- **Subject Line**: Compelling, curiosity-driven (30-50 characters)
- **Personalization**: Use recipient's name and reference specific details
- **Value Proposition**: Lead with what's in it for them
- **Brevity**: Keep it short and scannable (3-5 short paragraphs max)
- **Single CTA**: One clear call-to-action (schedule call, reply, visit link)
- **Tone**: Warm, conversational, relationship-first
- **Signature**: Professional email signature

**Generator Flow**:
1. User selects "Email Draft" tile
2. User enters email purpose and recipient context
3. Dynamic options: email objective (outreach, follow-up, introduction)
4. System generates subject line + email body
5. CTA options available (schedule call, request reply, visit link)

---

### 5. Proposal (`proposal`)
**What it is**: Professional business proposals for projects, services, and partnerships.

**Platforms/Channels**:
- PDF document
- Google Docs / Microsoft Word
- Email attachment
- Proposal software (PandaDoc, Proposify)

**Use Cases**:
- Project bids and RFP responses
- Service quotes and estimates
- Partnership proposals
- Contract proposals
- Consulting engagement proposals
- Freelance project proposals

**Best Practices**:
- **Executive Summary**: Clear overview of project and value
- **Scope**: Detailed project scope and deliverables
- **Timeline**: Milestones and estimated completion dates
- **Pricing**: Transparent pricing structure (fixed, hourly, milestone-based)
- **Value Proposition**: Why you're the best fit
- **Terms**: Payment terms, contract duration, revisions
- **Call-to-Action**: Clear next steps (sign, schedule call, ask questions)

**Generator Flow**:
1. User selects "Proposal" tile
2. User enters project details and client context
3. System generates structured proposal with sections:
   - Project Overview
   - Deliverables
   - Timeline
   - Pricing
   - Value Proposition
   - Next Steps

---

### 6. Social Ads (`ad`)
**What it is**: Paid advertising copy for social media platforms optimized for conversions.

**Platforms/Channels**:
- Facebook Ads (newsfeed, stories, reels)
- Instagram Ads (feed, stories, reels, explore)
- LinkedIn Ads (sponsored content, message ads)
- X Ads / Twitter Ads (promoted posts)
- TikTok Ads (in-feed ads, branded hashtag challenges)

**Use Cases**:
- Lead generation (email capture, form fills)
- Product sales and e-commerce
- Event promotion and ticket sales
- App installs
- Brand awareness campaigns
- Retargeting and remarketing

**Best Practices**:
- **Hook**: Scroll-stopping first line (3-5 words max)
- **Value Prop**: Clear benefit and unique selling point
- **Brevity**: Under 125 characters for primary text (mobile-optimized)
- **CTA**: Strong, action-oriented CTA (Shop Now, Learn More, Sign Up)
- **Urgency**: Create sense of urgency when appropriate (limited time, exclusive)
- **Mobile-First**: Optimize for mobile viewing
- **Testing**: A/B test different hooks and CTAs

**Generator Flow**:
1. User selects "Social Ads" tile
2. User enters ad topic and offer details
3. Dynamic ad options:
   - Ad objective (traffic, conversions, awareness)
   - Target audience description
   - Special offer or promotion
4. System generates ad copy optimized for paid social (125 chars, strong CTA)

---

### 7. Review Reply (`review`)
**What it is**: Professional, empathetic responses to customer reviews across platforms.

**Platforms/Channels**:
- Google My Business / Google Reviews
- Yelp reviews
- Facebook reviews
- TripAdvisor reviews
- Amazon reviews
- App Store / Google Play reviews

**Use Cases**:
- Customer service and support
- Reputation management
- Conflict resolution and complaint handling
- Thanking satisfied customers
- Addressing negative feedback
- Encouraging future business

**Best Practices**:
- **Gratitude**: Always thank the customer for feedback
- **Personalization**: Reference specific details from their review
- **Empathy**: Show understanding, especially for negative reviews
- **Resolution**: Offer to make things right (refund, redo, discount)
- **Professional**: Stay calm and professional, never defensive
- **Concise**: Keep response brief (100-200 words)
- **Action**: Provide contact info for follow-up if needed

**Generator Flow**:
1. User selects "Review Reply" tile
2. User pastes the customer review text
3. System analyzes sentiment (positive, neutral, negative)
4. Dynamic options: review platform, response tone
5. System generates empathetic, professional response

---

### 8. Blog Post (`blog`)
**What it is**: Long-form, SEO-optimized articles for websites and company blogs.

**Platforms/Channels**:
- Company website blog
- Medium
- WordPress / Webflow / Wix
- LinkedIn articles
- Substack

**Use Cases**:
- Thought leadership and expertise
- SEO content for organic traffic
- Educational content and guides
- Product tutorials and use cases
- Industry insights and trends
- Case studies and success stories

**Best Practices**:
- **Keyword Research**: Target 1-2 primary keywords
- **Title**: Compelling, keyword-rich title (50-60 characters)
- **Meta Description**: Clear summary for search results (150-160 characters)
- **Structure**: Use H2/H3 headings for scannability
- **Length**: 1000-2000 words for thorough coverage
- **Actionable**: Include specific takeaways and how-tos
- **Images**: Add relevant images, screenshots, diagrams
- **Internal Links**: Link to related content
- **CTA**: Clear next step at end (subscribe, download, contact)

**Generator Flow**:
1. User selects "Blog Post" tile
2. User enters blog topic and target keywords
3. System generates:
   - 3 title options
   - Meta description
   - Article outline with H2/H3 headings
   - Full article content
   - Conclusion with CTA

---

### 9. Newsletter (`newsletter`)
**What it is**: Email newsletter content for regular communication with subscribers.

**Platforms/Channels**:
- Email (Mailchimp, ConvertKit, Substack, etc.)
- Direct inbox delivery to subscriber list

**Use Cases**:
- Community updates and announcements
- Product launches and updates
- Content roundups (blog posts, videos, podcasts)
- Exclusive offers and promotions
- Behind-the-scenes insights
- Event invitations

**Best Practices**:
- **Subject Line**: Catchy, value-driven (30-50 characters)
- **Preheader**: Complementary preview text
- **Scannable**: Use short paragraphs, bullet points, subheadings
- **Sections**: Clear sections with visual separation
- **Value-First**: Lead with what subscribers will gain
- **Consistency**: Send on consistent schedule (weekly, bi-weekly, monthly)
- **Personal**: Write in first person, build relationship
- **CTA**: 1-2 clear calls-to-action (not overwhelming)
- **Footer**: Include unsubscribe and contact info

**Generator Flow**:
1. User selects "Newsletter" tile
2. User enters newsletter theme and key topics
3. System generates:
   - Subject line
   - Opening section
   - 2-3 content sections
   - Closing with CTA
4. Optional: include promotions, announcements, content links

---

## Content Type Selection Matrix

Choose the right content type based on your goal:

| Goal | Best Content Type(s) |
|------|---------------------|
| Build brand awareness | Social Post, Blog Post |
| Drive engagement | Social Post, Image Caption, Video Script |
| Generate leads | Social Ads, Newsletter, Blog Post |
| Make sales | Social Ads, Email Draft, Proposal |
| Provide customer service | Review Reply, Email Draft |
| Educate audience | Blog Post, Video Script, Newsletter |
| Network & build relationships | Email Draft, LinkedIn Post (Social Post) |
| Promote event | Social Ads, Newsletter, Social Post |

## Platform & Content Type Taxonomy

### Current Taxonomy (Before Normalization)
**Social Platforms** (mixed organic + ads):
- LinkedIn
- Instagram  
- Facebook
- Twitter

**Missing Platforms**:
- TikTok
- Reels/Shorts (short_video)
- X (Twitter) - inconsistent naming

**Content Types**:
- Social Post (requires platform)
- Image Caption
- Video Script
- Email Draft
- Proposal
- Social Ads
- Review Reply
- Blog Post
- Newsletter

**Issues**:
- Ads mixed with organic posts (Social Ads in task list, but no other ads)
- Platform dropdown doesn't match available content types
- No "Review responses" platform shown in dropdown
- Inconsistent key naming: "twitter" vs "Twitter" vs "X (Twitter)"

### Normalized Taxonomy (Target State)

#### Social (Organic)
- **Instagram** (`instagram`) - Feed posts, stories
- **Facebook** (`facebook`) - Page posts, groups
- **LinkedIn** (`linkedin`) - Professional posts
- **X (Twitter)** (`twitter`) - Short-form posts
- **TikTok** (`tiktok`) - Short-form video
- **Reels/Shorts** (`short_video`) - Instagram Reels, YouTube Shorts

#### Social Ads
- **Social Adss** (`facebook_ads`)
- **Instagram Ads** (`instagram_ads`)
- **LinkedIn Ads** (`linkedin_ads`)
- **X Ads** (`twitter_ads`)
- **TikTok Ads** (`tiktok_ads`)

#### Reputation/Support
- **Review Responses** (`review_response`) - Google, Yelp, Facebook reviews
- **Customer Support** (`customer_support`) - Email responses, chat

#### Content Marketing
- **Blog Posts** (`blog`)
- **Email Newsletters** (`newsletter`)
- **Email Campaigns** (`email`)

#### Business Documents
- **Proposals** (`proposal`)
- **Case Studies** (`case_study`)

## Technical Data Flow

```
User Input (Frontend)
  ↓
POST /api/generate
  ↓
app.py route handler
  ↓
Validate request (topic, platform)
  ↓
Load user profile (DB query)
  ↓
Merge payload (profile + request)
  ↓
generation_service.py
  ↓
task_registry.py (load task definition)
  ↓
generator.py (build prompt with PLATFORM_HINTS)
  ↓
Gemini API call (genai.GenerativeModel)
  ↓
Response text
  ↓
platform_rules.py (apply formatting rules)
  ↓
JSON response
  ↓
Frontend (display in #resultBox)
  ↓
User copies content
```

## Key Files & Components

### Backend
- **`app.py`**: Main Flask app, routes, database operations
  - `/onboarding`: Profile save endpoint
  - `/api/generate`: Content generation endpoint
  - `/api/current_user`: User profile fetch
- **`generator.py`**: Core generation logic, platform hints, variant building
  - `PLATFORM_HINTS`: Platform-specific guidance for prompts
  - `build_platform_variants()`: Generate multi-platform content
- **`platform_rules.py`**: Platform-specific formatting rules
  - `PLATFORM_RULES`: Dict mapping platform keys to PlatformRule objects
  - `DEFAULT_VARIANT_PLATFORMS`: Tuple of supported platforms
  - `apply_platform_rules()`: Apply character limits, hashtag rules, CTAs
- **`generation_service.py`**: Gemini API integration
- **`services/task_registry.py`**: Task type definitions (post, email, ad, etc.)
- **`voice_profile.py`**: Website scraper for profile auto-fill

### Frontend
- **`templates/dashboard.html`**: Main generator UI
  - Task selector tiles
  - Platform dropdown (lines 130-140)
  - Form submission handler (lines 577-716)
- **`templates/onboarding_wizard.html`**: Profile setup wizard
- **`static/dashboard.js`**: Dashboard JavaScript logic
  - Platform handling (lines 116-121, 806-838)
  - Generator state management
- **`static/content/config.json`**: Industry definitions (currently no platforms)

### Database
- **`profiles` table**: User profile data
  - Columns: id, user_id, business_name, industry, target_audience, brand_voice, key_offer, voice_rules, writing_samples, website_url, created_at, updated_at

## QA Checklist

### Profile Completion
- [ ] User can access onboarding wizard at `/onboarding`
- [ ] Website URL scraper successfully fetches content
- [ ] Website URL scraper handles timeouts gracefully (shows error, allows manual entry)
- [ ] Profile form validates all required fields before submission
- [ ] Profile form shows clear validation errors if fields missing
- [ ] Profile save persists data to `profiles` table in database
- [ ] Profile save shows success confirmation to user
- [ ] Profile save redirects user to dashboard after successful save
- [ ] Profile can be edited after initial save (PUT/PATCH endpoint)
- [ ] Large writing samples (>5000 chars) are handled without database errors

### Dashboard Access & Profile Load
- [ ] Dashboard loads successfully after profile save
- [ ] Dashboard fetches user profile from database
- [ ] Dashboard shows user's business name in UI
- [ ] Dashboard populates generator with profile defaults (industry, tone, keywords)
- [ ] Dashboard shows "incomplete profile" warning if profile missing required fields
- [ ] Dashboard redirects to `/onboarding` if no profile exists

### Generator UI
- [ ] All 9 task type tiles are visible and clickable
- [ ] Clicking task tile updates form (label, placeholder, button text)
- [ ] Platform dropdown appears only for "Social Post" task
- [ ] Platform dropdown contains all normalized platforms (Instagram, Facebook, LinkedIn, X, TikTok, Reels/Shorts)
- [ ] Dynamic context fields appear based on task/platform selection:
  - [ ] Ad options for "Social Ads" or Facebook platform
  - [ ] LinkedIn options for LinkedIn platform
  - [ ] Instagram options for Instagram platform
  - [ ] Video options for "Video Script" task
  - [ ] Email options for "Email" or "Newsletter" tasks
- [ ] Topic input accepts multi-line text
- [ ] Topic input shows placeholder appropriate to task type
- [ ] "Surprise Me" button populates random topic suggestion
- [ ] "Generate" button is enabled when required fields filled
- [ ] "Generate" button shows loading state (spinner, "Generating..." text)

### Content Generation Flow
- [ ] POST to `/api/generate` includes all required fields (topic, platform for posts, task_type)
- [ ] Backend validates request payload
- [ ] Backend returns 400 if `topic` missing
- [ ] Backend returns 400 if `platform` missing for task_type="post"
- [ ] Backend returns 503 if Gemini API key missing (with error code "missing_api_key")
- [ ] Backend returns 400 if user profile missing (with redirect to "/onboarding")
- [ ] Backend merges request payload with user profile data
- [ ] Backend constructs Gemini prompt with:
  - [ ] Task definition from task_registry
  - [ ] Platform hints from PLATFORM_HINTS
  - [ ] Brand voice from profile
  - [ ] Industry context from profile
- [ ] Backend calls Gemini API with constructed prompt
- [ ] Backend handles Gemini API timeout (>45s) gracefully
- [ ] Backend handles Gemini API rate limit errors gracefully
- [ ] Backend applies platform-specific formatting rules from platform_rules.py
- [ ] Backend returns JSON response with status, content, metadata

### Content Display & User Actions
- [ ] Frontend receives response from `/api/generate`
- [ ] Frontend parses success response and extracts content
- [ ] Frontend displays generated content in result box (#resultBox)
- [ ] Frontend shows success toast notification
- [ ] Frontend shows "Copy to Clipboard" button
- [ ] Copy button successfully copies content to clipboard
- [ ] Copy button shows "✓ Copied!" confirmation for 2 seconds
- [ ] Frontend handles error responses and shows user-friendly error messages:
  - [ ] Missing API key: "AI service not configured. Please contact support."
  - [ ] Timeout: "Generation timed out. Please try again with a simpler request."
  - [ ] Rate limit: "API rate limit reached. Please wait a moment and try again."
  - [ ] Missing profile: Prompt to complete profile with link to /onboarding
- [ ] Long-running requests (>5s) show "Still working..." message
- [ ] Request timeout (45s) aborts and shows error
- [ ] User can modify inputs and regenerate content
- [ ] Generated content persists in UI until page refresh

### Platform Taxonomy Consistency
- [ ] Platform keys are consistent across all files:
  - [ ] config.json uses lowercase keys (instagram, facebook, linkedin, twitter, tiktok, short_video)
  - [ ] dashboard.html dropdown uses normalized labels (Instagram, Facebook, LinkedIn, X (Twitter), TikTok, Reels/Shorts)
  - [ ] generator.py PLATFORM_HINTS uses lowercase keys
  - [ ] platform_rules.py PLATFORM_RULES uses lowercase keys
  - [ ] API payloads use lowercase keys
- [ ] Platform labels are user-friendly:
  - [ ] "X (Twitter)" not "Twitter" alone
  - [ ] "Reels/Shorts" not "short_video"
  - [ ] "Review Responses" grouped under Reputation/Support
- [ ] Social Ads are clearly separated from organic social
- [ ] No unsupported/dead platforms in dropdowns

### Error Handling & Edge Cases
- [ ] Form submission with empty topic shows error
- [ ] Form submission with empty platform (for posts) shows error
- [ ] Network error during generation shows user-friendly message
- [ ] Browser back button doesn't break generator state
- [ ] Mobile viewport displays form correctly (no horizontal scroll)
- [ ] Long topic text (>1000 chars) is handled without breaking UI
- [ ] Special characters in topic (emoji, unicode) are handled correctly
- [ ] Rapid-fire clicking Generate button doesn't trigger multiple requests
- [ ] Timeout timer is cleared on successful response (no memory leak)

## Known Issues & Workarounds

### Brand Profile Save Failing
**Symptoms**: User completes onboarding form, clicks submit, but profile data not saved to database.

**Possible Causes**:
1. Database connection timeout
2. Writing samples field exceeding database column length
3. Form validation failing silently
4. Transaction rollback due to constraint violation

**Workarounds**:
- Reduce writing samples to <2000 characters
- Check browser console for JavaScript errors
- Verify database connection in server logs
- Try clearing browser cache and cookies

**Debugging Steps**:
1. Check `app.py` logs for `/onboarding` POST requests
2. Verify database query execution in logs
3. Check for SQLAlchemy/psycopg2 errors
4. Test database connection: `SELECT 1 FROM profiles LIMIT 1`
5. Inspect form data payload in browser Network tab

### Generator Dashboard Dead-ends
**Symptoms**: User clicks Generate, sees loading spinner, then error or nothing happens.

**Possible Causes**:
1. Missing Gemini API key (GENAI_API_KEY)
2. Gemini API timeout (>45s)
3. Rate limit reached on Gemini API
4. Invalid prompt construction

**Workarounds**:
- Simplify topic description
- Wait 60s before retrying (rate limit cooldown)
- Contact admin to verify API key configuration

**Debugging Steps**:
1. Check server logs for Gemini API errors
2. Verify GENAI_API_KEY is set in environment
3. Test Gemini API directly: `python3 scripts/test_gemini_api.py`
4. Check for 503 response with error code "missing_api_key"
5. Monitor Gemini API quota in Google AI Studio

### Confusing Social Dropdown Labels
**Symptoms**: Users unsure which platform to select, don't see TikTok or Reels options.

**Root Cause**: Platform dropdown is incomplete and inconsistently labeled.

**Fix**: Implement normalized taxonomy (see "Normalized Taxonomy" section above).

## Future Enhancements
- [ ] Save generated content to database (content history)
- [ ] Export content to PDF, DOCX, or social media scheduler
- [ ] Inline editing of generated content before copying
- [ ] A/B testing variants (generate 2-3 options, user picks best)
- [ ] Bulk generation (create 7-day content calendar)
- [ ] Platform-specific preview (show how post looks on Instagram/LinkedIn)
- [ ] Character counter for platform limits
- [ ] Hashtag suggestions based on industry/topic
- [ ] Emoji suggestions
- [ ] Image generation integration (DALL-E, Midjourney)
- [ ] Schedule posts to Buffer/Hootsuite
- [ ] Analytics dashboard (track which posts perform best)

## Support & Troubleshooting
- **Documentation**: See README.md, docs/GEMINI_SETUP.md
- **Server Logs**: `server.log`, `server_5001.log`
- **Test Gemini API**: `python3 scripts/test_gemini_api.py`
- **Test Endpoints**: 
  - `curl http://127.0.0.1:5001/__dev__/ping` (dev mode only)
  - `curl http://127.0.0.1:5001/api/current_user` (requires auth)
- **Database**: PostgreSQL `togetherly_v2`
  - Inspect profiles: `SELECT * FROM profiles WHERE user_id = 'USER_ID';`
