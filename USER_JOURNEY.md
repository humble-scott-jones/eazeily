# Swelly User Journey Documentation

## Overview

This document outlines the end-to-end user journey for Swelly, the AI-powered social media content generator. Use this as a reference for feature development, QA testing, and stakeholder alignment on the intended user flow.

**Last Updated:** January 2026  
**App Name:** Swelly (formerly Togetherly)  
**Purpose:** Generate authentic, brand-perfect social media content for small businesses

---

## Table of Contents

1. [Complete User Journey Flow](#complete-user-journey-flow)
2. [Detailed Step-by-Step Flow](#detailed-step-by-step-flow)
3. [Current Pain Points](#current-pain-points)
4. [QA Acceptance Checklist](#qa-acceptance-checklist)
5. [Technical Implementation Notes](#technical-implementation-notes)

---

## Complete User Journey Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY MAP                            │
└─────────────────────────────────────────────────────────────────────┘

1. LANDING → 2. AUTH → 3. PROFILE WIZARD → 4. DB SAVE → 5. GENERATOR → 6. AI PROMPT → 7. CONTENT OUTPUT

┌──────────┐    ┌──────────┐    ┌───────────────┐    ┌─────────┐
│  Landing │───▶│  Sign Up │───▶│ Profile Setup │───▶│   DB    │
│   Page   │    │/Sign In  │    │    Wizard     │    │  Save   │
└──────────┘    └──────────┘    └───────────────┘    └─────────┘
                                                            │
                                                            ▼
┌──────────┐    ┌──────────┐    ┌───────────────┐    ┌─────────┐
│  Export/ │◀───│  Content │◀───│  AI Response  │◀───│Generator│
│   Copy   │    │  Display │    │   (OpenAI)    │    │Dashboard│
└──────────┘    └──────────┘    └───────────────┘    └─────────┘
```

---

## Detailed Step-by-Step Flow

### Step 1: Landing Page (`/` or `/app`)

**Purpose:** Introduce the user to Swelly and initiate account creation or sign-in.

**User Actions:**
- Views landing page with hero section and setup wizard preview
- Sees "Quick Start" button (requires auth) or "Scroll to wizard" button
- Clicks "Create your free account" or "Already have an account? Sign in"

**Key UI Elements:**
- Hero section with gradient background
- Step indicators (Steps 1-4 preview)
- Quick Start auto-fill option
- Account creation/sign-in CTAs

**Success Criteria:**
- User can clearly understand the value proposition
- Auth buttons are prominently displayed
- Quick Start option is visible but gated for authenticated users

---

### Step 2: Authentication

**Purpose:** Create a new account or sign into existing account.

**User Actions:**
- Enters email and password
- Submits sign-up or sign-in form
- System creates session and user record in database

**Technical Flow:**
```
POST /api/auth/signup or /api/auth/signin
→ Password hashing (pbkdf2:sha256)
→ User record created/verified in SQLite (users table)
→ Session established (Flask session with SECRET_KEY)
→ Redirect to profile setup wizard
```

**Success Criteria:**
- User account created in database
- Session cookie established
- User redirected to appropriate page (wizard or dashboard)

---

### Step 3: Profile Setup Wizard (`/app` - Steps 1-4)

**Purpose:** Capture brand voice, industry, tone, platforms, and keywords to personalize content generation.

#### Step 3.1: Industry Selection (Step 1)

**User Actions:**
- Selects industry from 12 options:
  - Realtor / Real Estate 🏡
  - Restaurant / Café 🍽️
  - Retail / Boutique 🛍️
  - Fitness / Wellness 💪
  - Artisan / Maker 🎨
  - Coach / Consultant 🧭
  - Nonprofit / Community 🤝
  - Home Services 🛠️
  - Healthcare 🩺
  - Church ⛪
  - House Host / Vacation Rental 🏠
  - Other / Custom ✨

**Technical Details:**
- Industry options loaded from `/static/content/config.json`
- Each industry has pre-configured suggested keywords and industry-specific questions

#### Step 3.2: Industry-Specific Questions (Step 2)

**User Actions:**
- Answers industry-specific questions (e.g., "Primary area" for realtors, "Cuisine" for restaurants)
- Selects goals using chip-style multi-select (e.g., "New listings", "Market tips")
- Selects reel style preferences (e.g., "Face-camera tips", "Property b-roll + captions")

**Note:** This step is hidden if the selected industry has no specific questions.

#### Step 3.3: Tone & Platforms (Step 3)

**User Actions:**
- Selects tone: Friendly, Professional, Playful, or Inspirational
- Selects one or more platforms:
  - Instagram
  - Facebook
  - LinkedIn
  - X / Twitter
  - TikTok
  - Reels / Shorts
  - Review responses

**Success Criteria:**
- At least one platform must be selected
- Tone selection is required
- Multi-select for platforms works correctly

#### Step 3.4: Keywords & Company (Step 4)

**User Actions:**
- Enters company/brand name (required)
- Adds brand keywords (descriptors that define the brand voice)
- Adds niche keywords (industry-specific terms)
- Optional: Toggles "Include image suggestions"

**Validation:**
- Company name is required and must be 2-100 characters
- Keywords are trimmed, deduplicated (case-insensitive)
- Both keyword fields accept comma-separated values or multi-select chips

---

### Step 4: Database Save (`POST /api/profile`)

**Purpose:** Persist the user's profile configuration to enable content generation.

**Technical Flow:**
```python
POST /api/profile
{
  "industry": "realtor",
  "tone": "friendly",
  "platforms": ["instagram", "facebook"],
  "brand_keywords": ["luxury", "coastal living"],
  "niche_keywords": ["Johns Island", "Charleston"],
  "goals": ["New listings", "Local lifestyle"],
  "company": "Coastal Realty Co.",
  "include_images": true,
  "details": {
    "area": "Johns Island",
    "reel_style": "Property b-roll + captions"
  }
}
```

**Database Schema:**
```sql
CREATE TABLE profiles (
  id TEXT PRIMARY KEY,           -- Session-based profile_id
  industry TEXT,
  tone TEXT,
  platforms TEXT,                -- JSON array
  brand_keywords TEXT,           -- JSON array
  niche_keywords TEXT,           -- JSON array
  goals TEXT,                    -- JSON array
  company TEXT,
  include_images INTEGER,        -- Boolean (0 or 1)
  details TEXT                   -- JSON object with industry-specific answers
);
```

**Success Criteria:**
- Profile data successfully written to SQLite database
- API returns `{"ok": true, "id": "...", "profile": {...}}`
- User is redirected to generator dashboard (`/generate`)

**⚠️ Known Pain Point:** Profile save can fail silently if database connection is lost or if required fields are missing. See [Current Pain Points](#current-pain-points) section.

---

### Step 5: Generator Dashboard (`/generate`)

**Purpose:** Configure content generation parameters and initiate AI-powered content creation.

**User Actions:**
- Reviews "Voice locked in" status badge (confirms profile was saved)
- Selects session length: 1 day (sample), 7 days (weekly), or 30 days (monthly)
- Confirms or adjusts platform focus (pre-filled from profile)
- Reviews tone setting (pre-filled from profile)
- Optionally enters additional goals or keywords
- Clicks "Generate" button

**Quick Recipes (One-Click Options):**
- ✨ Fresh 1-day sample
- 📅 7-day cadence
- 📊 30-day calendar

**Technical Details:**
- Dashboard auto-loads profile data via `GET /api/profile`
- Platform chips pre-populate based on saved profile
- Tone dropdown pre-selects from profile
- Template library allows saving/loading common configurations

**Success Criteria:**
- Profile data correctly populates all form fields
- User can modify any settings before generating
- "Generate" button is enabled when valid selections are made
- Loading state is shown during generation

**⚠️ Known Pain Point:** Dashboard can appear as a "dead-end" if profile failed to save in Step 4, as no profile data will populate. See [Current Pain Points](#current-pain-points) section.

---

### Step 6: AI Prompt & Generation (`POST /api/generate`)

**Purpose:** Send user configuration to OpenAI API (or fallback generator) to create content.

**Technical Flow:**

1. **Frontend Request:**
```javascript
POST /api/generate
{
  "days": 7,
  "start_day": "2026-01-11",
  "platforms": ["instagram", "facebook"],
  "tone": "friendly",
  // Additional profile data merged from database
}
```

2. **Backend Processing:**
```python
# app.py - api_generate() function
1. Validate user authentication and quota
2. Load profile from database
3. Merge request payload with profile data
4. Check reels quota if short_video platform is included
5. Choose generation method:
   - If OpenAI API key is set: Use _generate_posts_via_openai()
   - Otherwise: Use local generator (generator.py)
```

3. **OpenAI API Call (if enabled):**
```python
# app.py - _generate_posts_via_openai()
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",  # or configured OPENAI_MODEL
    messages=[
        {"role": "system", "content": "You are an expert social media content creator..."},
        {"role": "user", "content": json.dumps({
            "industry": "realtor",
            "tone": "friendly",
            "platforms": ["instagram", "facebook"],
            "brand_keywords": ["luxury", "coastal living"],
            "niche_keywords": ["Johns Island"],
            "goals": ["New listings"],
            "company": "Coastal Realty Co.",
            "days": 7
        })}
    ],
    response_format={"type": "json_object"}
)
```

4. **Fallback Local Generator:**
```python
# generator.py - generate_posts()
- Uses templated content pillars (Educational, Behind-the-Scenes, Testimonial, etc.)
- Applies platform-specific hints (e.g., Instagram uses more emojis)
- Incorporates tone adjustments (friendly, professional, playful, inspirational)
- Generates hashtags based on keywords and industry
```

**Success Criteria:**
- API request completes within 30 seconds
- Content is returned in standardized JSON format
- Fallback generator activates if OpenAI fails
- Rate limiting prevents abuse (30 requests per minute per IP)

---

### Step 7: Content Output Display

**Purpose:** Present generated content in a viewable, copyable, and actionable format.

**User Actions:**
- Reviews generated posts in card format
- Sees platform-specific formatting (emojis, hashtags, hooks)
- Copies individual posts or all content
- Optionally downloads as text or saves to drafts

**Content Card Structure:**
```
┌────────────────────────────────────────┐
│ 📅 Day 1 - Monday, Jan 13              │
│ 📱 Instagram                           │
├────────────────────────────────────────┤
│                                        │
│ [Generated Caption Text]               │
│                                        │
│ #hashtag1 #hashtag2 #hashtag3          │
│                                        │
├────────────────────────────────────────┤
│ [Copy Button] [Save to Drafts]        │
└────────────────────────────────────────┘
```

**Post Format:**
```json
{
  "day": 1,
  "date": "2026-01-13",
  "platform": "instagram",
  "pillar": "Educational",
  "caption": "🏡 New listing alert! 3BR/2BA coastal beauty on Johns Island...",
  "hashtags": "#CharlestonRealEstate #JohnsIsland #CoastalLiving",
  "image_suggestion": "Exterior shot during golden hour",
  "reel_hook": "POV: Your dream home just hit the market",
  "reel_cta": "Link in bio to schedule a showing!"
}
```

**Success Criteria:**
- All generated posts are visible without scrolling issues
- Copy button successfully copies to clipboard
- Platform icons and labels are correct
- Content matches selected tone and keywords
- Image suggestions and reel instructions appear when applicable

---

## Current Pain Points

### 🔴 Critical Issues

#### 1. Profile Save Failing Silently

**Issue:** `/api/profile` endpoint may fail without clear user feedback, causing downstream issues.

**Symptoms:**
- User completes wizard but profile doesn't persist
- Generator dashboard shows empty/default values
- User assumes they need to re-enter data

**Root Causes:**
- Database connection timeouts not caught
- Validation errors return 400 but UI doesn't show specific field errors
- Race condition if user clicks "Save" multiple times rapidly

**Recommended Fixes:**
- [ ] Add retry logic with exponential backoff for DB operations
- [ ] Display field-level error messages in wizard
- [ ] Show loading spinner and disable submit button during save
- [ ] Add success toast notification after successful save
- [ ] Log detailed error messages for debugging

---

#### 2. Generator Dashboard Dead-Ends

**Issue:** Generator dashboard (`/generate`) appears broken if profile was not successfully saved.

**Symptoms:**
- All form fields are empty or show defaults
- "Voice locked in" badge may still appear (false positive)
- User can't generate content without re-entering everything
- No clear path back to wizard

**Root Causes:**
- Dashboard assumes profile exists without checking
- No error handling for missing profile data
- UI doesn't detect or communicate empty profile state

**Recommended Fixes:**
- [ ] Check if profile exists on dashboard load
- [ ] Redirect to wizard with warning if profile is missing
- [ ] Add "Complete Setup" CTA if profile is incomplete
- [ ] Show profile summary card so users can verify their saved data
- [ ] Add "Edit Profile" link to return to wizard

---

#### 3. Confusing Dropdown Labels

**Issue:** Platform and content type labels are unclear, particularly around "Reels / Shorts" vs other video options.

**Specific Examples:**
- ❌ "Facebook ads" label should be clarified (this app doesn't generate ads)
- ❌ "Reels / Shorts" vs "TikTok" vs "short_video" terminology is inconsistent
- ❌ "Review responses" might be confused with responding to reviews vs generating review content

**Current Labels (from config.json):**
```json
"platforms": [
  {"key": "instagram", "label": "Instagram"},
  {"key": "facebook", "label": "Facebook"},
  {"key": "linkedin", "label": "LinkedIn"},
  {"key": "twitter", "label": "X / Twitter"},
  {"key": "tiktok", "label": "TikTok"},
  {"key": "short_video", "label": "Reels / Shorts"},  // Confusing
  {"key": "reviews", "label": "Review responses"}      // Confusing
]
```

**Recommended Fixes:**
- [ ] Clarify "short_video" label: Change to "Instagram Reels / YouTube Shorts"
- [ ] Clarify "reviews" label: Change to "Review Response Templates" or "Reply to Reviews"
- [ ] Remove any references to "ads" unless ad copy generation is actually supported
- [ ] Add tooltips or helper text explaining each platform option
- [ ] Use consistent terminology across UI, config, and documentation
- [ ] Consider renaming internal `short_video` key to `reels_shorts` for clarity

---

### 🟡 Medium Priority Issues

#### 4. Quota Display Confusion

**Issue:** Users on free tier don't clearly understand their generation limits.

**Recommended Fixes:**
- [ ] Add quota counter badge to dashboard header
- [ ] Show "X of Y reels remaining this month" before generation
- [ ] Explain upgrade benefits before hitting quota limit

---

#### 5. No Saved Draft Management

**Issue:** Users can't easily review or manage previously generated content.

**Recommended Fixes:**
- [ ] Add "My Drafts" page to store generated posts
- [ ] Allow users to regenerate or create variants
- [ ] Export to CSV or calendar format

---

## QA Acceptance Checklist

Use this checklist for manual or automated testing of the complete user journey.

### ✅ Pre-Test Setup

- [ ] Test environment has valid `SECRET_KEY` configured
- [ ] Database is empty or in known state (fresh `swelly.db` or in-memory)
- [ ] OpenAI API key is set (or fallback generator is working)
- [ ] Stripe keys configured if testing paid features
- [ ] Dev mode enabled for testing: `FLASK_ENV=development`

---

### ✅ Step 1: Landing Page & Auth

**Landing Page:**
- [ ] Page loads without errors (check browser console)
- [ ] Hero section with gradient background renders correctly
- [ ] "Create your free account" button is visible
- [ ] "Already have an account? Sign in" button is visible
- [ ] Step indicators (1-4) are shown
- [ ] Quick Start button is present but indicates auth required

**Sign Up Flow:**
- [ ] Click "Create your free account"
- [ ] Enter email (e.g., `qa-test-user@example.com`) and password
- [ ] Submit form
- [ ] Verify success: User is redirected to wizard (`/app`)
- [ ] Verify: Session cookie is set (check browser dev tools)

**Sign In Flow:**
- [ ] Sign out (if signed in)
- [ ] Click "Already have an account? Sign in"
- [ ] Enter existing email and password
- [ ] Submit form
- [ ] Verify: User is redirected to dashboard or wizard
- [ ] Verify: Session is established

---

### ✅ Step 2: Profile Wizard - Step 1 (Industry)

- [ ] Wizard page loads with Step 1 visible
- [ ] Step indicator shows Step 1 as active
- [ ] All 12 industry options are displayed with icons
- [ ] Clicking an industry highlights it (visual feedback)
- [ ] "Next" button is enabled after selection
- [ ] Click "Next" to advance to Step 2

---

### ✅ Step 3: Profile Wizard - Step 2 (Industry Questions)

- [ ] Step 2 is shown (or skipped if industry has no questions)
- [ ] Industry-specific questions appear for selected industry
- [ ] Multi-select chips work correctly (goals, reel_style)
- [ ] Text inputs accept values (e.g., "area" for realtors)
- [ ] "Back" button returns to Step 1 without losing data
- [ ] "Next" button advances to Step 3

**Test with multiple industries:**
- [ ] Realtor: Shows "Primary area" and "Reel style" questions
- [ ] Other/Custom: Shows "Describe your work" text field
- [ ] Verify industry with no questions auto-skips to Step 3

---

### ✅ Step 4: Profile Wizard - Step 3 (Tone & Platforms)

- [ ] Step 3 is shown with tone dropdown
- [ ] Tone dropdown shows all 4 options: Friendly, Professional, Playful, Inspirational
- [ ] Default tone is "Friendly" (or as configured)
- [ ] Platform chips are displayed (7 platforms)
- [ ] At least one platform is pre-selected (Instagram by default)
- [ ] Clicking platform chips toggles selection (visual active state)
- [ ] Multi-select works (multiple platforms can be selected)
- [ ] "Next" button is enabled
- [ ] "Back" button works

---

### ✅ Step 5: Profile Wizard - Step 4 (Keywords & Company)

- [ ] Step 4 is shown with company name field
- [ ] Brand keywords input is present
- [ ] Niche keywords input is present
- [ ] "Include image suggestions" toggle is present and checked by default
- [ ] Suggested keywords appear as chips (from config.json)
- [ ] Clicking suggested keyword adds it to the field

**Validation Tests:**
- [ ] Submit without company name → Shows error "Company name is required"
- [ ] Enter company name < 2 chars → Shows validation error
- [ ] Enter company name > 100 chars → Shows validation error
- [ ] Valid company name (e.g., "QA Test Co.") → No error

**Keyword Entry:**
- [ ] Enter comma-separated keywords: "test1, test2, test3"
- [ ] Verify keywords are parsed correctly
- [ ] Duplicate keywords are deduplicated (case-insensitive)
- [ ] Extra whitespace is trimmed

**Final Submission:**
- [ ] Click "Save Profile" or "Complete Setup" button
- [ ] Loading spinner appears
- [ ] Button is disabled during save

---

### ✅ Step 6: Database Save Verification

**Success Case:**
- [ ] API request `POST /api/profile` returns 200 status
- [ ] Response JSON includes `{"ok": true, "id": "...", "profile": {...}}`
- [ ] Success toast/notification appears
- [ ] User is redirected to generator dashboard (`/generate`)

**Database Verification (backend check):**
```bash
sqlite3 swelly.db "SELECT * FROM profiles WHERE company='QA Test Co.';"
```
- [ ] Profile record exists in database
- [ ] `industry` field matches selection
- [ ] `tone` field matches selection
- [ ] `platforms` field is valid JSON array
- [ ] `brand_keywords` field is valid JSON array
- [ ] `niche_keywords` field is valid JSON array
- [ ] `goals` field is valid JSON array
- [ ] `company` field matches input
- [ ] `details` field contains industry-specific answers as JSON

**Failure Case Testing:**
- [ ] Simulate DB connection failure (stop server mid-save)
- [ ] Verify error message is shown to user
- [ ] User is not redirected on failure
- [ ] Form data is preserved (user doesn't lose work)

---

### ✅ Step 7: Generator Dashboard Load

**Page Load:**
- [ ] Dashboard page (`/generate`) loads without errors
- [ ] "Voice locked in" status badge is visible
- [ ] Profile summary is displayed (industry, tone, platforms)
- [ ] Session length chips show (1 day, 7 days, 30 days)
- [ ] Platform chips pre-populate from saved profile
- [ ] Tone dropdown pre-selects saved tone
- [ ] Quick recipe buttons are visible

**Profile Data Verification:**
- [ ] Saved platforms are highlighted in platform picker
- [ ] Saved tone is selected in tone dropdown
- [ ] Brand keywords and niche keywords appear (if configured to display)
- [ ] Industry-specific details are available (not necessarily visible in UI)

**Dead-End Check (Pain Point Test):**
- [ ] Clear browser cookies/session
- [ ] Navigate directly to `/generate` without completing wizard
- [ ] Verify: User is redirected to wizard OR shown clear error
- [ ] Verify: Dashboard doesn't appear broken with empty fields

---

### ✅ Step 8: Content Generation Request

**1-Day Sample Generation:**
- [ ] Select "1 day" session length
- [ ] Ensure at least one platform is selected
- [ ] Click "Generate" button
- [ ] Loading state appears (spinner, disabled button, progress indicator)
- [ ] Wait for response (typically 5-30 seconds)

**API Request Verification:**
```bash
# Check server logs or network tab
POST /api/generate
{
  "days": 1,
  "start_day": "2026-01-11",
  "platforms": ["instagram"],
  "tone": "friendly"
  // ... other merged profile data
}
```

**Response Verification:**
- [ ] API returns 200 status
- [ ] Response includes `{"ok": true, "count": N, "posts": [...]}`
- [ ] `count` matches number of posts in `posts` array
- [ ] `posts` array contains at least 1 post object

**7-Day & 30-Day Generation:**
- [ ] Select 7-day session
- [ ] Verify auth requirement (must be signed in)
- [ ] Verify quota check (paid users only if gated)
- [ ] Generate successfully
- [ ] Repeat for 30-day session

**Reels/Shorts Generation:**
- [ ] Select "Reels / Shorts" platform
- [ ] Verify auth requirement
- [ ] Verify paid subscription requirement
- [ ] Verify quota display ("X of Y reels remaining")
- [ ] Generate successfully
- [ ] Verify `reel_hook` and `reel_cta` fields are populated

---

### ✅ Step 9: Content Output Display

**Post Card Rendering:**
- [ ] Generated posts appear in scrollable list
- [ ] Each post card shows:
  - [ ] Day number and date
  - [ ] Platform icon and label
  - [ ] Caption text with proper formatting
  - [ ] Hashtags (if applicable)
  - [ ] Image suggestion (if enabled)
  - [ ] Reel instructions (if short_video platform)
- [ ] Cards are visually distinct and easy to read
- [ ] No layout overflow or truncation issues

**Content Verification:**
- [ ] Captions reflect selected tone (friendly, professional, etc.)
- [ ] Brand keywords are naturally incorporated
- [ ] Niche keywords appear where appropriate
- [ ] Industry-specific content is relevant (e.g., realtor posts mention listings)
- [ ] Platform-specific formatting is correct:
  - [ ] Instagram: More emojis, engaging hooks
  - [ ] LinkedIn: Professional tone, industry insights
  - [ ] TikTok: Casual, trend-aware language

**Copy to Clipboard:**
- [ ] Click "Copy" button on a post card
- [ ] Paste into text editor
- [ ] Verify entire caption + hashtags are copied
- [ ] Verify formatting is preserved (line breaks, emojis)

**Copy All:**
- [ ] Click "Copy All" button (if available)
- [ ] Paste into text editor
- [ ] Verify all posts are copied in order
- [ ] Verify post separators are included

**Save to Drafts (if implemented):**
- [ ] Click "Save to Drafts" button
- [ ] Verify post is saved to user's draft list
- [ ] Navigate to drafts page
- [ ] Verify saved post appears

---

### ✅ Negative Test Cases

**Authentication:**
- [ ] Access `/generate` without signing in → Redirects to login or shows auth required
- [ ] Attempt to generate content without auth → 401 Unauthorized

**Validation:**
- [ ] Submit profile with empty company name → Error message shown
- [ ] Select zero platforms in wizard → Error prevents advancement
- [ ] Generate content with zero platforms selected → Error message

**Rate Limiting:**
- [ ] Send 30+ generation requests rapidly → 429 Too Many Requests
- [ ] Wait 60 seconds → Rate limit resets

**Quota Enforcement:**
- [ ] Free user attempts 7-day plan → Upgrade required (if gated)
- [ ] Free user attempts reels generation → Upgrade required
- [ ] Paid user exceeds monthly reels quota → Quota reached error

**OpenAI Fallback:**
- [ ] Set invalid `OPENAI_API_KEY`
- [ ] Attempt generation
- [ ] Verify fallback to local generator works
- [ ] Content is still generated (from `generator.py`)

---

### ✅ Cross-Browser & Device Testing

**Desktop Browsers:**
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (macOS)

**Mobile Browsers:**
- [ ] iOS Safari (iPhone)
- [ ] Android Chrome

**Responsive Design:**
- [ ] Wizard works on mobile viewport (< 768px)
- [ ] Dashboard works on tablet viewport (768px - 1024px)
- [ ] Content cards stack properly on mobile
- [ ] All CTAs are tappable on touch devices

---

### ✅ Accessibility Testing

- [ ] Keyboard navigation works through wizard
- [ ] Tab order is logical
- [ ] Focus indicators are visible
- [ ] Screen reader announces step changes
- [ ] Form labels are properly associated
- [ ] Error messages are accessible
- [ ] ARIA attributes are correct

---

## Technical Implementation Notes

### Database Schema

```sql
-- Users table
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  is_paid INTEGER DEFAULT 0,
  free_sample_used INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Profiles table
CREATE TABLE profiles (
  id TEXT PRIMARY KEY,              -- Tied to session profile_id
  industry TEXT,
  tone TEXT,
  platforms TEXT,                   -- JSON array: ["instagram", "facebook"]
  brand_keywords TEXT,              -- JSON array: ["luxury", "coastal"]
  niche_keywords TEXT,              -- JSON array: ["Charleston", "Johns Island"]
  goals TEXT,                       -- JSON array: ["New listings", "Market tips"]
  company TEXT NOT NULL,
  include_images INTEGER DEFAULT 1, -- Boolean
  details TEXT,                     -- JSON object with industry-specific data
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reels usage tracking (for quota enforcement)
CREATE TABLE reels_usage (
  user_id TEXT,
  year INTEGER,
  month INTEGER,
  reels_generated INTEGER DEFAULT 0,
  PRIMARY KEY (user_id, year, month)
);
```

### API Endpoints Reference

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/auth/signup` | POST | Create new user account | No |
| `/api/auth/signin` | POST | Authenticate existing user | No |
| `/api/profile` | GET | Retrieve saved profile | Yes (session) |
| `/api/profile` | POST | Save/update profile | Yes (session) |
| `/api/generate` | POST | Generate content posts | Yes (session) |
| `/api/generate-variants` | POST | Create alternate versions | Yes (session) |
| `/api/current_user` | GET | Get current session user | Yes (session) |

### Configuration Files

**`/static/content/config.json`** - Industry and platform definitions
```json
{
  "version": "2025.01",
  "industries": [...],
  "tones": [...],
  "platforms": [...],
  "questions": {...}
}
```

**`/static/content/flags.json`** - Feature flags
```json
{
  "openai_chat": true,
  "subscriptions": true,
  "gate7DayToPaid": false
}
```

### Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `SECRET_KEY` | Flask session encryption | Yes |
| `OPENAI_API_KEY` | Enable OpenAI content generation | No (fallback available) |
| `STRIPE_SECRET_KEY` | Enable payment processing | No (gated features) |
| `FLASK_ENV` | Set to `development` for dev mode | No |
| `DB_PATH` | Custom SQLite database path | No (defaults to `swelly.db`) |
| `REELS_QUOTA_MONTHLY` | Monthly reels limit per user | No (default: 5) |

### Content Generation Logic

**Platform-Specific Hints:**
- **Instagram:** Emphasize visual storytelling, use 3-5 emojis, hashtag groups
- **Facebook:** Conversational tone, encourage comments/shares
- **LinkedIn:** Professional insights, industry expertise, thought leadership
- **Twitter/X:** Concise (280 chars), trending topics, thread starters
- **TikTok:** Casual, trending sounds, viral format awareness
- **Reels/Shorts:** Strong hook in first 3 seconds, clear CTA

**Content Pillars:**
1. **Educational:** Tips, how-tos, industry insights
2. **Behind-the-Scenes:** Process, team, company culture
3. **Testimonial:** Client stories, reviews, social proof
4. **Promotional:** Offers, new products, events
5. **Engagement:** Questions, polls, community building

---

## Stakeholder Alignment

### Product Team
- Use this document to ensure feature consistency
- Reference pain points when prioritizing fixes
- Validate that new features fit into the documented flow

### Engineering Team
- Use as technical specification for implementation
- Reference API endpoints and data schemas
- Follow database conventions outlined here

### QA Team
- Use acceptance checklist for test case creation
- Reference pain points for regression testing
- Validate each step in the flow for releases

### Support Team
- Use to troubleshoot user-reported issues
- Reference known pain points to provide workarounds
- Escalate issues not covered in this document

---

## Document Maintenance

**Update Frequency:** Monthly or when major features are added

**Change Log:**
- 2026-01-11: Initial user journey documentation created
- [Future updates will be logged here]

**Contact:** For questions or updates to this document, contact the product team or open a GitHub issue.

---

## Quick Reference: Critical User Paths

### Happy Path (Complete Success)
1. Land on homepage → 2. Sign up → 3. Complete wizard (all 4 steps) → 4. Profile saves ✅ → 5. Dashboard loads with data → 6. Generate content → 7. View/copy output ✅

### Common Failure Path (Profile Save Issue)
1. Land on homepage → 2. Sign up → 3. Complete wizard → 4. Profile save fails ❌ → 5. Dashboard loads empty → 6. User confused, abandons ❌

### Quick Start Path (Experienced User)
1. Sign in → 2. Click Quick Start → 3. Auto-filled wizard → 4. One-click save → 5. Dashboard with pre-generated sample ✅

---

**End of User Journey Documentation**
