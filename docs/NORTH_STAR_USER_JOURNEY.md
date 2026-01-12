# Eazeily North Star: User Journey & Product Vision

## Vision Statement
**Eazeily is your AI-powered brand voice assistant that learns your unique style and delivers perfect, on-brand content every time.**

## Core User Journey: From Profile to Published Content

### The North Star Flow
```
Profile Creation → Profile Refinement → Content Generation → Publishing
     (Once)           (Anytime)         (Daily/Weekly)      (One-click)
```

## Detailed User Journey

### Phase 1: Initial Profile Setup (One-Time, 5-10 minutes)
**Goal**: Capture the essence of the user's brand voice and style

**Entry Point**: New user signs up → Redirected to `/onboarding_wizard`

**Steps**:
1. **Smart Auto-Fill** (Optional but Recommended)
   - User pastes ANY public URL (website, social profile, booking page, portfolio)
   - AI scrapes and analyzes content
   - Pre-fills profile with detected brand voice, messaging, and writing style
   - **Benefit**: Saves 80% of setup time

2. **Profile Completion**
   - User reviews and edits auto-filled data:
     - ✅ **Business Name** (required)
     - ✅ **Industry** (required, dropdown)
     - ✅ **Brand Voice/Tone** (required, e.g., "Professional and friendly")
     - ✅ **Target Audience** (required, e.g., "Small business owners aged 30-50")
     - ✅ **Key Offer/Value Prop** (required, e.g., "Streamlined workflow automation")
     - ✅ **Writing Samples** (required, 2-3 examples of your best content)
     - ⚪ Voice Rules (optional, e.g., "Never use jargon, always inclusive")
     - ⚪ Keywords (optional, brand-specific terms)
     - ⚪ Goals (optional, e.g., "engagement", "leads")
     - ℹ️ **Platforms** (NOT selected during onboarding - chosen per-content on dashboard)

3. **Submit & Success**
   - Click "Save & Continue to Dashboard"
   - Profile saved to database
   - Success toast: "✓ Profile saved successfully!"
   - Auto-redirect to `/dashboard`

**North Star Outcome**: User has a complete brand profile that AI can use to generate perfectly on-brand content.

---

### Phase 2: Profile Refinement (Anytime, 2-5 minutes)
**Goal**: Keep profile up-to-date as brand evolves

**Entry Point**: User clicks "Edit Profile" in sidebar → `/profile`

**Steps**:
1. **View & Edit**
   - Profile page loads with all existing data pre-filled
   - User sees organized sections:
     - Basic Information (name, industry, timezone)
     - Brand Voice & Messaging (tone, audience, offer, rules)
     - Keywords & Goals (comma-separated lists)
     - Writing Samples (examples for AI to match)
   - **Note**: Platform selection is NOT part of profile - platforms are chosen per-content on the dashboard

2. **Update & Save**
   - User edits any fields
   - Click "Save Profile"
   - Validation: Ensures required fields are present
   - Success: "✓ Profile saved successfully!" toast
   - Option to return to dashboard or continue editing
   - **Note**: Platform selection is NOT part of profile - platforms are chosen per-content on the dashboard

**North Star Outcome**: User's brand profile stays current, ensuring generated content always reflects their latest messaging.

---

### Phase 3: Content Generation (Daily/Weekly, 30 seconds - 2 minutes)
**Goal**: Generate perfect, on-brand content in seconds

**Entry Point**: User on `/dashboard` → Ready to create content

**Steps**:
1. **Choose Content Type** (9 options)
   - 📱 **Social Post** (Instagram, Facebook, LinkedIn, X, TikTok, Reels)
   - 🖼️ **Image Caption** (for photos and visuals)
   - 🎬 **Video Script** (Reels, TikToks, Shorts)
   - ✉️ **Email Draft** (outreach, follow-ups)
   - 📄 **Proposal** (project bids, quotes)
   - 📢 **Social Ads** (paid campaigns)
   - ⭐ **Review Reply** (customer responses)
   - 📝 **Blog Post** (SEO articles)
   - 📬 **Newsletter** (email campaigns)

2. **Provide Context**
   - **Topic**: "What do you want to talk about?" (required)
   - **Platform**: (if Social Post) Select where it'll be posted
   - **Optional Details**: Platform-specific refinements
     - Ad objective (traffic, awareness, leads, etc.)
     - LinkedIn tone (thought leadership, personal story, etc.)
     - Instagram mood (inspiring, casual, educational, etc.)
     - Video length (15s, 30s, 60s, 90s)
     - Email CTA (schedule call, visit link, etc.)

3. **Generate**
   - Click "Generate [Content Type]" button
   - **Behind the Scenes**:
     1. System fetches user's profile from database
     2. Merges profile data (brand voice, writing samples, rules) with topic
     3. Constructs AI-optimized prompt for Gemini API
     4. Applies platform-specific best practices and formatting rules
     5. Returns polished, ready-to-publish content
   - Loading state: "Generating your content..." (3-10 seconds)

4. **Review & Use**
   - Generated content displays in result box
   - User reviews:
     - ✅ On-brand? (matches their voice)
     - ✅ Accurate? (reflects their message)
     - ✅ Platform-optimized? (right length, hashtags, CTAs)
   - **Actions**:
     - **Copy to Clipboard**: One-click copy
     - **Regenerate**: Tweak topic and try again
     - **Edit**: Manual edits before posting (outside Eazeily for now)

**North Star Outcome**: User gets perfect, on-brand content in seconds that's ready to paste directly into their social media scheduler or platform.

---

### Phase 4: Publishing (Future Enhancement)
**Goal**: One-click publishing from Eazeily to social platforms

**Future Vision** (Not Yet Implemented):
- Direct integration with Buffer, Hootsuite, or native APIs
- Schedule posts for optimal times
- Bulk generation (create week's worth of content at once)
- A/B testing (generate variants, track performance)
- Content calendar (plan and schedule entire month)

---

## Key Differentiators: Why Users Love Eazeily

### 1. **AI That Learns Your Voice**
- **Not Generic**: Unlike ChatGPT, Eazeily studies YOUR writing samples
- **Always On-Brand**: Generated content matches your unique style
- **Context-Aware**: Uses your industry, audience, and goals

### 2. **Profile-Driven Generation**
```
Your Profile → AI Prompt → Generated Content
     ↓              ↓               ↓
Brand Voice    Optimized      Perfect Output
Keywords       Platform       Ready to Post
Writing Style  Best Practices Copy-Paste Ready
```

### 3. **Dead-Simple Workflow**
- **Setup Once**: 5-10 minutes to create profile
- **Generate Forever**: 30 seconds to create post
- **No Training Needed**: Intuitive UI, instant results

### 4. **Platform-Specific Optimization**
- **Instagram**: 2000 chars max, 10-15 hashtags, visual storytelling
- **LinkedIn**: 1300 chars optimal, professional tone, thought leadership
- **X/Twitter**: 280 chars, punchy hooks, 1-2 hashtags
- **Facebook**: Conversational, community-focused, call-to-action
- **TikTok/Reels**: Video script with timestamps, hook in 3 seconds

---

## Critical Success Factors

### Database as AI Preparer
**Current State**: ✅ WORKING
```
User Profile (DB)
  ↓
Flask API (/api/profile)
  ↓
VoiceProfile Model
  ↓
Voice Engine (services/voice_engine.py)
  ↓
AI Prompt Builder
  ↓
Gemini AI API
  ↓
Generated Content
```

**Key Design**: Profile data flows seamlessly from DB → AI without manual intervention

### Profile Persistence
**Current State**: ✅ FIXED

**What Was Broken**:
- ❌ No standalone profile editing page
- ❌ JavaScript referenced non-existent HTML form fields
- ❌ Users couldn't update profile after onboarding

**What's Fixed**:
- ✅ New `/profile` page with full editing capability
- ✅ All profile fields accessible and editable
- ✅ Clear save success/error feedback
- ✅ Navigation from sidebar ("Edit Profile")

### UX Flow Clarity
**Current State**: ✅ IMPROVED

**What Was Confusing**:
- ❌ Facebook posts showed "Ad Options" (organic ≠ ads)
- ❌ Platform dropdowns mixed organic and paid

**What's Fixed**:
- ✅ Ad options only show for task_type='ad' (Social Ads)
- ✅ Facebook organic posts no longer show ad fields
- ✅ Clear labels: "Ad Campaign Details" vs. "Platform"

---

## Quality Gates: How Profile Ensures Great Content

### 1. Required Profile Fields
**Minimum for Generation**:
- ✅ Business Name (identifies the brand)
- ✅ Industry (applies best practices)
- ✅ Brand Voice (sets tone)

**Enhanced with**:
- ⭐ Target Audience (tailors messaging)
- ⭐ Key Offer (emphasizes value)
- ⭐ Writing Samples (matches style)
- ⭐ Voice Rules (enforces guidelines)

### 2. AI Prompt Construction
**How Profile Data is Used**:
```python
# Simplified example
prompt = f"""
You are writing for {profile.business_name}, a {profile.industry} company.

Brand Voice: {profile.brand_voice}
Target Audience: {profile.target_audience}
Key Offer: {profile.key_offer}

Writing Style Examples:
{profile.writing_samples[0]}
{profile.writing_samples[1]}

Voice Rules (Must Follow):
{profile.voice_rules}

Brand Keywords to Include: {profile.brand_keywords}

Now write a {task_type} for {platform} about: {user_topic}
"""
```

### 3. Platform-Specific Post-Processing
**After AI Generates**:
- ✅ Apply character limits (Twitter 280, Instagram 2000)
- ✅ Add platform-appropriate hashtags (Instagram 10-15, Twitter 1-2)
- ✅ Insert CTAs (LinkedIn "Comment below", Instagram "Link in bio")
- ✅ Format for readability (line breaks, emojis if brand allows)

---

## User Success Metrics

### Onboarding Success
- ⏱️ **Time to First Generated Post**: < 15 minutes (from signup)
- 📊 **Profile Completion Rate**: > 80%
- ✅ **Successful First Generation**: > 90%

### Ongoing Usage
- 🔄 **Return Rate**: > 60% (users return within 7 days)
- 📈 **Posts per User per Week**: 3-5 average
- ⭐ **Satisfaction with Generated Content**: > 4.5/5 stars

### Content Quality
- ✅ **On-Brand**: > 90% of users say content matches their voice
- ⏱️ **Time Saved**: 80% reduction vs. writing from scratch
- 📋 **Copy-Paste Ready**: > 85% of generated content used with minimal edits

---

## Future Enhancements: The Roadmap

### Near-Term (Next 3 Months)
- [ ] **Profile Templates**: Save multiple profiles, switch between brands
- [ ] **Content History**: Save and track all generated content
- [ ] **Bulk Generation**: Create 7-30 days of content at once
- [ ] **A/B Testing**: Generate multiple variants, user picks best

### Mid-Term (3-6 Months)
- [ ] **Direct Publishing**: Post to social media from Eazeily
- [ ] **Content Calendar**: Schedule posts, visualize content plan
- [ ] **Analytics Dashboard**: Track which posts perform best
- [ ] **Team Collaboration**: Share profiles, approve content

### Long-Term (6-12 Months)
- [ ] **Image Generation**: DALL-E/Midjourney integration for visuals
- [ ] **Video Editing**: Auto-create videos from scripts
- [ ] **Multi-Language**: Generate content in any language
- [ ] **White-Label**: Agencies can brand Eazeily for clients

---

## Troubleshooting: Common User Journeys

### User Journey: "My Content Doesn't Sound Like Me"
**Diagnosis**:
1. Check writing samples: Are they substantial? (at least 100 words each)
2. Check brand voice: Is it specific? ("Professional" vs. "Professional and friendly with a touch of humor")
3. Check voice rules: Any contradictions? ("Be casual" but "Never use slang")

**Solution**:
1. Edit profile at `/profile`
2. Add more/better writing samples (your BEST content)
3. Refine brand voice description (be specific!)
4. Add voice rules (what to avoid, what to emphasize)
5. Regenerate content → Should match your style now

### User Journey: "I Need to Update My Profile"
**Steps**:
1. Click "Edit Profile" in sidebar (📱 Mobile: Open menu → Edit Profile)
2. Profile page loads with current data
3. Edit any fields (business name, tone, audience, etc.)
4. Click "Save Profile"
5. See success: "✓ Profile saved successfully!"
6. Return to dashboard
7. Generate new content → Reflects updated profile

### User Journey: "I'm Not Sure Which Content Type to Choose"
**Decision Guide**:
- **Social Post**: Daily social media updates (Instagram, LinkedIn, Facebook, X)
- **Image Caption**: Posting a photo? Need a caption
- **Video Script**: Making a Reel, TikTok, or Short? Need dialogue
- **Email Draft**: Reaching out to someone? Need personalized email
- **Proposal**: Pitching a project? Need professional proposal
- **Social Ads**: Running paid campaigns? Need ad copy
- **Review Reply**: Customer left a review? Need response
- **Blog Post**: Writing a long-form article? Need SEO content
- **Newsletter**: Sending email to subscribers? Need newsletter content

---

## Developer Notes: Maintaining the North Star

### Code Structure Reflects User Journey
```
routes/
  ├── onboarding_routes.py  # Phase 1: Profile Creation
  ├── profile_routes.py     # Phase 2: Profile Editing (NEW!)
  └── generate_routes.py    # Phase 3: Content Generation

templates/
  ├── onboarding_wizard.html  # Phase 1 UI
  ├── profile.html            # Phase 2 UI (NEW!)
  └── dashboard.html          # Phase 3 UI

services/
  ├── voice_engine.py        # Profile → AI Prompt
  └── task_registry.py       # Content Type Definitions
```

### Data Flow Integrity
**Critical Path**: Profile → Database → API → AI → Content
- **Entry Point**: User edits profile at `/profile`
- **Persistence**: POST `/api/profile` → `VoiceProfile` model → DB
- **Retrieval**: GET `/api/profile` → Load from DB
- **Usage**: POST `/api/generate` → Fetch profile → Build AI prompt
- **Output**: Generated content reflects profile data

### Testing Philosophy
**Test the North Star, Not Implementation Details**

**Good Tests**:
```python
# Does profile save work?
def test_profile_saves_and_loads():
    save_profile(data)
    loaded = get_profile()
    assert loaded == data  # ✅ Tests North Star

# Does generator use profile?
def test_generated_content_matches_profile():
    save_profile(brand_voice="Casual and fun")
    content = generate("post", "New product")
    assert "casual" in analyze_tone(content)  # ✅ Tests North Star
```

**Bad Tests**:
```python
# Tests implementation detail, not user value
def test_profile_json_serialization():
    profile = VoiceProfile(...)
    json_str = profile.to_json()
    assert "business_name" in json_str  # ❌ Tests internal detail
```

---

## Conclusion: Staying True to the North Star

**North Star = Profile-Driven, AI-Powered, On-Brand Content Generation**

Every feature, fix, and enhancement should ask:
1. **Does it improve the profile → content flow?**
2. **Does it make generated content more on-brand?**
3. **Does it reduce time/friction for users?**

If the answer is "yes" to any of these, it's aligned with our North Star.
If the answer is "no" to all three, it's a distraction.

**Next Actions**:
- ✅ Profile editing: DONE
- ✅ Platform consistency: DONE
- ✅ Documentation: DONE
- 🔄 End-to-end testing: IN PROGRESS
- 🎯 User feedback: COLLECT & ITERATE

**Remember**: The best feature is the one that gets users from "I need content" to "Here's my perfect post" in 30 seconds or less.
