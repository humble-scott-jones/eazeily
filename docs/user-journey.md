# User Journey: Chat-First Content Creation

## Overview
This document describes the complete user journey in Eazeily's chat-first, conversational interface. Users interact with AI through natural language and slash commands to create on-brand content instantly.

**🎯 INTERACTION MODEL**: Chat-first conversational interface with slash commands and AI-powered profile suggestions using Gemini.

**📖 Related Documentation**: 
- [PROFILE_TO_GENERATION_FLOW.md](PROFILE_TO_GENERATION_FLOW.md) - Technical data flow from profile → AI generation
- [CONTENT_GENERATION_API.md](CONTENT_GENERATION_API.md) - API documentation
- [NORTH_STAR_USER_JOURNEY.md](NORTH_STAR_USER_JOURNEY.md) - Product vision and philosophy

## User Journey Phases

### Phase 1: Discovery & Signup
**Entry Point**: Marketing page or direct signup

**Steps**:
1. User lands on marketing page
2. Sees value proposition: "Create content as easy as texting"
3. Clicks "Start Chatting" or "Sign Up"
4. Creates account (email/password or OAuth)
5. Redirected to onboarding or dashboard

**Goal**: Get user excited about conversational content creation

### Phase 2: First-Run Experience & Profile Setup
**Entry Point**: New user lands in chat interface after signup

**The Conversational Onboarding**:
1. User lands in full-screen chat interface at `/dashboard`
2. Eazeily greets them: "Welcome! I'm your AI content assistant. Let's set up your brand so I can create content that sounds like you."
3. **Option 1 - Quick Import** (Recommended):
   - User can use `/import [URL]` to scrape website
   - AI analyzes content and suggests brand voice, messaging, key offers
   - Pre-fills profile fields automatically
   - Falls back to manual entry if scraping fails
4. **Option 2 - Conversational Collection**:
   - AI asks questions conversationally
   - Business name: "What's your business name?"
   - Industry: "What industry are you in?"
   - Brand voice: "How would you describe your brand's voice?" (AI can suggest options)
   - Target audience: "Who is your target audience?"
   - Key offer: "What's your main value proposition?"
5. Profile completeness badge shows progress (e.g., "75% complete 🎯")
6. Data saved to `voice_profile` table via `/api/profile` endpoint

**Alternative Entry**: Traditional wizard still available at `/onboarding_wizard` for users who prefer forms

**Database Storage**:
- Fields: user_id, business_name, industry, target_audience, brand_voice, key_offer, voice_rules, writing_samples, platforms, brand_keywords, goals, timezone, etc.
- Backend: `routes/onboarding_routes.py` and `services/onboarding_service.py`

**Goal**: Get minimum viable profile (business_name, industry, brand_voice) to enable content generation

### Phase 3: Profile Refinement (AI-Powered Suggestions)
**Entry Point**: User wants to improve their profile at any time

Users can refine their profile using slash commands that trigger AI-powered suggestions:

#### Slash Commands for Profile Management

| Command | What It Does | Implementation |
|---------|--------------|----------------|
| `/profile` | View/edit full profile | Opens profile management interface |
| `/voice` | AI suggests 3 brand voice options | `services/profile_expert.py` analyzes profile and writing samples |
| `/audience` | AI suggests 3 target audience descriptions | Generates demographic-specific personas |
| `/offer` | AI suggests 3 value propositions | Creates compelling key offers based on industry |
| `/samples` | Add writing samples | Updates profile with example content |
| `/import [URL]` | Import profile from website | Scrapes URL via `voice_profile.py` scraper |
| `/update [field]` | Update specific profile field | Quick update for any profile field |

#### AI Suggestion Flow Example: `/voice`
1. User types `/voice` in chat
2. System shows "Analyzing your profile..." loading state
3. AI (Gemini) analyzes:
   - Current business name
   - Industry context
   - Target audience
   - Writing samples
   - Key offer
4. Returns 3 personalized brand voice suggestions:
   ```
   Here are 3 brand voice options based on your profile:
   
   1. "Professional, warm, and approachable" - Balances expertise with 
      accessibility for your small business audience
   
   2. "Casual, friendly, and action-oriented" - Energetic tone that drives
      engagement and feels personal
   
   3. "Expert, trustworthy, and results-focused" - Emphasizes your authority
      and proven track record
   
   [Use Option 1] [Use Option 2] [Use Option 3] [✏️ Write my own]
   ```
5. User clicks a button or types their choice
6. Profile updates via `POST /api/profile`
7. Profile completeness badge refreshes

#### Profile Completeness Badge
- Visual indicator: "75% complete 🎯" or "Complete! ✓"
- Calculated based on required fields: business_name, industry, brand_voice, target_audience, key_offer
- Updated in real-time as profile is enhanced
- Implementation: `services/profile_validator.py` - `get_profile_completeness()`

**Backend Services**:
- `services/profile_expert.py` - AI-powered suggestion generation
- `services/conversation_router.py` - Slash command parsing and routing
- `routes/profile_routes.py` - Profile update endpoints

**Goal**: Continuously improve profile quality for better content generation

### Phase 4: Content Creation (Chat-First)
**Entry Point**: User ready to create content in chat interface

Users can create content in two ways:

#### Method 1: Natural Language (Conversational)
User simply describes what they need:

**Examples**:
- "Write a LinkedIn post about our new product launch"
- "Draft an email to follow up with a prospect"
- "Create an Instagram caption for this photo of our team"
- "Write a proposal for a potential sponsor"
- "Help me respond to this 5-star review: [review text]"

**Behind the Scenes**:
1. Message sent to `POST /api/chat` endpoint
2. `services/conversation_router.py` parses intent
3. Identifies task type (post, email, caption, etc.)
4. Extracts initial parameters (platform, topic)
5. If more info needed, asks follow-up questions via `pending_task` state
6. When ready, calls generation service

#### Method 2: Slash Commands (Quick Access)

| Command | Creates | Example |
|---------|---------|---------|
| `/post` | Social media post | `/post LinkedIn post about new feature` |
| `/caption` | Image caption | `/caption Team photo from conference` |
| `/script` or `/reel` | Video script | `/script 30-second product demo` |
| `/email` | Email draft | `/email Follow-up with lead` |
| `/ad` | Ad copy | `/ad Instagram ad for sale` |
| `/review` | Review response | `/review [paste review text]` |
| `/blog` | Blog post | `/blog How to use our product` |

**Slash Command Flow Example: `/post`**
```
User: /post LinkedIn post about our Q4 results

AI: Great! I'll create a LinkedIn post about Q4 results.
    [Analyzing your profile...]
    
    Here's your post:
    
    🎯 Q4 Results Are In! 
    
    [Generated content matching brand voice]
    
    [Copy] [Regenerate] [Edit tone]

User: Make it more celebratory

AI: Here's a more celebratory version:
    
    🎉 Q4 Results Are Here and We're Thrilled!
    
    [Regenerated content with celebratory tone]
    
    [Copy] [Regenerate]
```

**Multi-Turn Conversation** (for complex requests):
```
User: Write a post about our new feature

AI: I'll help you create a post! Which platform?
    Instagram | Facebook | LinkedIn | Twitter | TikTok

User: Instagram

AI: Perfect! What should the post focus on?
    (e.g., benefits, how-to, announcement)

User: Benefits for small businesses

AI: [Generates Instagram post about feature benefits for small businesses]
```

**Content Generation Pipeline**:
1. User input (natural language or slash command)
2. Intent parsing via `ConversationRouter`
3. Field collection via chat (`pending_task` state)
4. Profile fetch from database (`VoiceProfile`)
5. Prompt construction via `services/voice_engine.py`
6. AI generation via Gemini API
7. Platform-specific post-processing (`platform_rules.py`)
8. Return formatted content to chat

**Task Types Supported** (from `services/task_registry.py`):
- `post` - Social media posts
- `caption` - Image captions
- `script` - Video scripts (Reels, TikToks, Shorts)
- `email` - Email drafts
- `review` - Review responses
- `ad` - Social ads
- `blog` - Blog posts
- `custom` - Custom content types

**Goal**: Generate perfect, on-brand content through natural conversation or quick commands

### Phase 5: Iteration & Refinement
**Entry Point**: After content is generated in chat

After AI generates content, user can refine it through conversation:

**User Actions**:
- **Copy** - One-tap copy to clipboard (✓ Copied! confirmation)
- **Regenerate** - "Try again" or "Generate another"
- **Adjust tone** - "Make it more casual" or "More professional"
- **Request changes** - "Add more urgency" or "Shorten it" or "Remove emojis"
- **Change platform** - "Rewrite this for Twitter instead"
- **Combine commands** - "Make it shorter and more fun"

**Iterative Conversation Example**:
```
User: Write a post about our sale

AI: [Generates LinkedIn post about sale]
    [Copy] [Regenerate]

User: Make it more casual

AI: [Regenerates with casual tone]
    [Copy] [Regenerate]

User: Perfect! Now rewrite it for Instagram

AI: [Adapts content for Instagram with hashtags]
    [Copy] [Regenerate]
```

**Behind the Scenes**:
- Chat history maintained in session
- Previous messages provide context
- AI understands references ("it", "that post", "shorter")
- Profile data remains consistent across iterations

**Goal**: Iterate to perfection through natural conversation

### Phase 6: Ongoing Usage & Learning
**Entry Point**: Regular user returns to create more content

**Features**:
- Chat history persists within session
- Profile learns from user preferences over time
- AI suggestions improve with more writing samples
- Quick access via slash commands
- Keyboard shortcuts for common actions

**Power User Workflow**:
```
User: /post Instagram story about workshop
AI: [Generates story]

User: /post LinkedIn announcement about same workshop  
AI: [Generates formal LinkedIn version]

User: /email Send to waitlist
AI: [Generates email to workshop waitlist]
```

**Multi-Content Generation**:
Users can create multiple pieces of content in one session, with AI maintaining context across the conversation.

**Goal**: Build muscle memory for conversational content creation

---

## Chat Interface Components

### Main Chat Interface
```
┌─────────────────────────────────────────┐
│ ☰  ✨ Eazeily          [75% complete 🎯] │  ← Header with menu + profile badge
├─────────────────────────────────────────┤
│                                         │
│  [AI Message]                           │
│  Welcome! What would you like to        │
│  create today?                          │
│                                         │
│  💡 Try: /post, /email, /voice          │
│                                         │
│                      [User Message]     │
│                      Write a LinkedIn   │
│                      post about our     │
│                      new feature        │
│                                         │
│  [AI Message]                           │
│  I'll create a LinkedIn post about      │
│  your new feature...                    │
│                                         │
│  🎯 Your New Feature is Here!           │
│                                         │
│  [Full generated content...]            │
│                                         │
│  [Copy] [Regenerate]                    │
│                                         │
├─────────────────────────────────────────┤
│ 💡 Type / to see commands               │  ← Dismissible hint
├─────────────────────────────────────────┤
│ ┌───────────────────────────────────┐   │
│ │ What do you want to create?       │[→]│  ← Sticky input
│ └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Slash Command Autocomplete
When user types `/`:
```
┌─────────────────────────────────────────┐
│ 📝 /post     Create a social post       │
│ 📧 /email    Draft an email             │
│ 📷 /caption  Write an image caption     │
│ 🎬 /script   Create video script        │
│ 📢 /ad       Create ad copy             │
│ ⭐ /review   Respond to a review        │
│ 📝 /blog     Write a blog post          │
│ ─────────────────────────────────────   │
│ 🎤 /voice    Update brand voice         │
│ 🎯 /audience Define target audience     │
│ 💎 /offer    Set key offer              │
│ 📋 /samples  Add writing samples        │
│ 🔗 /import   Import from URL            │
│ 👤 /profile  View/edit full profile     │
│ ❓ /help     Show all commands          │
└─────────────────────────────────────────┘
```

### AI Profile Suggestion UI
When user types `/audience`:
```
┌─────────────────────────────────────────┐
│ ## Update Target Audience 🎯            │
│                                         │
│ Based on your profile (TechCorp,        │
│ Software industry):                     │
│                                         │
│ **Option 1:**                           │
│ Small business owners aged 30-50 who    │
│ struggle with manual workflows and      │
│ are actively looking for automation...  │
│                                         │
│ **Option 2:**                           │
│ Solopreneurs and freelancers who        │
│ wear multiple hats and need tools that  │
│ save time without complexity...         │
│                                         │
│ **Option 3:**                           │
│ Marketing managers at 10-50 person      │
│ agencies seeking scalable solutions...  │
│                                         │
│ [Use Option 1] [Use Option 2]           │
│ [Use Option 3] [✏️ Write my own]        │
└─────────────────────────────────────────┘
```

### Multi-Turn Field Collection
When AI needs more information:
```
┌─────────────────────────────────────────┐
│  [User Message]                         │
│  Write a post about our sale            │
│                                         │
│  [AI Message]                           │
│  Great! Which platform would you like   │
│  this post for?                         │
│                                         │
│  [Instagram] [Facebook] [LinkedIn]      │
│  [Twitter] [TikTok]                     │
│                                         │
│  [User Message]                         │
│  Instagram                              │
│                                         │
│  [AI Message]                           │
│  Perfect! Creating an Instagram post    │
│  about your sale...                     │
│                                         │
│  [Generated content appears]            │
└─────────────────────────────────────────┘
```

### Profile Completeness Badge
```
┌─────────────────────────┐
│  [25% complete 🎯]      │  ← Just started
│  [50% complete 🎯]      │  ← Basic info added
│  [75% complete 🎯]      │  ← Most fields filled
│  [Complete! ✓]         │  ← All required fields done
└─────────────────────────┘
```

---

## Content Types Supported

Eazeily supports comprehensive content creation through natural language or slash commands:

### Social Media
- **Posts** (`/post`) - Instagram, LinkedIn, Facebook, Twitter/X, TikTok
- **Captions** (`/caption`) - For images and photos
- **Scripts** (`/script` or `/reel`) - Video content with hooks and B-roll suggestions for Reels, TikToks, Shorts

### Email & Outreach
- **Emails** (`/email`) - Professional correspondence, follow-ups, outreach
- **Newsletters** - Regular updates to subscribers

### Business Documents
- **Proposals** - Partnership, sponsorship, collaboration proposals
- **Review Replies** (`/review`) - Respond to customer reviews
- **Case Studies** - Success stories

### Marketing
- **Ad Copy** (`/ad`) - For paid campaigns
- **Blog Posts** (`/blog`) - Long-form SEO content
- **Landing Page Copy** - Conversion-focused copy

### Platform-Specific Features

| Platform | Content Types | Key Features |
|----------|--------------|--------------|
| **Instagram** | Posts, Captions, Reels | 2000 char max, 10-15 hashtags, visual storytelling |
| **LinkedIn** | Posts, Articles | 1300 char optimal, professional tone, thought leadership |
| **Facebook** | Posts, Ads | Conversational, community-focused, CTA |
| **Twitter/X** | Posts | 280 chars, punchy hooks, 1-2 hashtags |
| **TikTok** | Scripts, Captions | Hook in 3 seconds, trending audio suggestions |

---

## Technical Architecture & Implementation

### Chat API Endpoint: `/api/chat`

**Request Format**:
```json
{
  "message": "user's input text",
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

**Response Format**:
```json
{
  "response": "AI response text to display",
  "action": "continue|generated|onboarding|error",
  "pending_task": {...} | null,
  "content": "generated content" | null,
  "suggestions": ["..."] | null
}
```

### Conversational Flow Pipeline

```
User Input → ConversationRouter → Intent Detection → Field Collection
                                                            ↓
Generated Content ← Platform Rules ← Gemini API ← Profile + Prompt
```

**Key Components**:
1. **`routes/chat_routes.py`** - Chat API endpoint handler
2. **`services/conversation_router.py`** - Slash command parsing and intent detection
3. **`services/voice_engine.py`** - Prompt construction with profile context
4. **`services/profile_expert.py`** - AI-powered profile suggestions
5. **`services/task_registry.py`** - Content type definitions
6. **`platform_rules.py`** - Platform-specific formatting rules
7. **`models.py`** - VoiceProfile database model

### Slash Command Implementation

**Command Map** (from `ConversationRouter.COMMAND_MAP`):
```python
{
    '/post': 'post',
    '/caption': 'caption',
    '/script': 'script',
    '/email': 'email',
    '/review': 'review',
    '/ad': 'ad',
    '/blog': 'blog',
    '/reel': 'script',  # alias
    '/profile': 'profile',
    '/voice': 'update_voice',
    '/audience': 'update_audience',
    '/samples': 'update_samples',
    '/import': 'import_profile',
}
```

### Multi-Turn Conversation State

**Pending Task Structure**:
```python
pending_task = {
    'task_type': 'post',
    'collected': {
        'platform': 'instagram',
        'topic': 'new product launch'
    },
    'next_field': 'mood'  # What to collect next
}
```

AI uses `pending_task` to track progress through field collection and resume conversations after interruption.

### Profile-Driven Generation

**Profile → Prompt Flow**:
1. Load `VoiceProfile` from database
2. Extract key fields: business_name, industry, brand_voice, target_audience, writing_samples
3. Construct prompt template with profile context
4. Add task-specific requirements from `task_registry.py`
5. Apply platform hints from `PLATFORM_HINTS`
6. Call Gemini API with enriched prompt
7. Post-process with `platform_rules.py`
8. Return formatted content

**Example Prompt Construction**:
```python
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

Now create a {task_type} for {platform} about: {user_topic}
"""
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to first content | < 2 minutes |
| Profile completion rate | > 80% |
| Content generation success | > 95% |
| Slash commands used per session | > 3 |
| Return user rate (7-day) | > 40% |

---

## Detailed Content Type Reference

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

## Updated Technical Data Flow (Chat-First)

### Conversational Content Generation Flow
```
User Input (Chat Message)
  ↓
POST /api/chat
  ↓
routes/chat_routes.py
  ↓
Check profile completeness
  ↓
services/conversation_router.py (parse intent & slash commands)
  ↓
Intent Detection → Task Type + Parameters
  ↓
Field Collection (if needed) → pending_task state
  ↓
Profile loaded from database (VoiceProfile model)
  ↓
services/voice_engine.py (build prompt with profile context)
  ↓
services/task_registry.py (load task definition)
  ↓
PLATFORM_HINTS (platform-specific guidance)
  ↓
Gemini AI API call
  ↓
Response text
  ↓
platform_rules.py (apply formatting rules)
  ↓
JSON response to chat
  ↓
Frontend displays in chat UI
  ↓
User copies/iterates
```

### Legacy Dashboard Flow (Still Available)
The traditional dashboard with form-based generation is still available as an alternative interface:
```
User Input (Dashboard Form)
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

### Backend (Chat-First Architecture)
- **`routes/chat_routes.py`**: Chat API endpoint (`/api/chat`)
  - Handles conversational interactions
  - Multi-turn conversation state management
  - Profile readiness checking
- **`services/conversation_router.py`**: Intent parsing and routing
  - Slash command detection (`COMMAND_MAP`)
  - Task field collection (`TASK_FIELDS`)
  - Platform recognition
- **`services/profile_expert.py`**: AI-powered profile suggestions
  - Gemini-based suggestions for voice, audience, offer
  - Context-aware recommendations
- **`services/voice_engine.py`**: Prompt construction with profile context
  - Profile data integration
  - Brand voice application
- **`services/task_registry.py`**: Task type definitions
  - Content type templates
  - Required fields per task
- **`platform_rules.py`**: Platform-specific formatting
  - Character limits, hashtag rules, CTAs
- **`models.py`**: VoiceProfile database model
- **`voice_profile.py`**: Website scraper for profile import

### Frontend (Chat Interface)
- **`templates/dashboard.html`**: Chat interface UI (if implemented)
- **`static/js/promptbox.js`**: Chat interaction logic
- **`static/css/chat.css`**: Chat styling
- **`templates/onboarding_wizard.html`**: Alternative form-based onboarding

### Database
- **`voice_profile` table**: User profile data
  - Columns: user_id, business_name, industry, target_audience, brand_voice, key_offer, voice_rules, writing_samples, platforms, brand_keywords, goals, timezone, etc.

---

## QA Checklist (Chat-First Model)

### Profile Setup
- [ ] User can start chat conversation after signup
- [ ] Chat prompts for essential profile fields conversationally
- [ ] `/import [URL]` command successfully scrapes websites
- [ ] Website scraper handles timeouts gracefully
- [ ] Profile completeness badge displays and updates correctly
- [ ] Profile data persists to `voice_profile` table
- [ ] Minimum required fields enforced (business_name, industry, brand_voice)

### Slash Commands
- [ ] `/post` command triggers post creation flow
- [ ] `/email` command triggers email creation flow
- [ ] `/voice` generates 3 AI-powered brand voice suggestions
- [ ] `/audience` generates 3 target audience suggestions
- [ ] `/offer` generates 3 value proposition suggestions
- [ ] `/samples` allows adding writing samples
- [ ] `/profile` opens profile view/edit interface
- [ ] `/import [URL]` imports profile from website
- [ ] Slash command autocomplete appears when typing `/`
- [ ] All commands properly routed via `ConversationRouter`

### Conversational Generation
- [ ] Natural language requests parsed correctly ("Write a LinkedIn post about...")
- [ ] Intent detection identifies task type from message
- [ ] Multi-turn conversations maintain context via `pending_task`
- [ ] AI asks for missing required fields (platform, topic, etc.)
- [ ] Profile data automatically included in prompts
- [ ] Generated content matches brand voice from profile
- [ ] Platform-specific formatting applied correctly
- [ ] Content displays in chat with Copy and Regenerate buttons

### Iteration & Refinement
- [ ] "Make it more casual" adjusts tone appropriately
- [ ] "Shorten it" reduces content length
- [ ] "Rewrite for [platform]" adapts to new platform
- [ ] Chat history provides context for iterations
- [ ] Copy button successfully copies to clipboard
- [ ] Regenerate button produces new variant

### AI Profile Expert
- [ ] AI suggestions based on actual profile data
- [ ] Suggestions are specific and actionable (not generic)
- [ ] User can select suggestion or write their own
- [ ] Profile updates immediately after selection
- [ ] Profile completeness badge refreshes after update

### Error Handling
- [ ] Missing API key shows user-friendly error
- [ ] Gemini API timeout handled gracefully
- [ ] Rate limit errors surfaced clearly
- [ ] Incomplete profile prompts field collection
- [ ] Network errors don't break chat state
- [ ] Invalid slash commands show helpful message

### Error Handling
- [ ] Missing API key shows user-friendly error
- [ ] Gemini API timeout handled gracefully
- [ ] Rate limit errors surfaced clearly
- [ ] Incomplete profile prompts field collection
- [ ] Network errors don't break chat state
- [ ] Invalid slash commands show helpful message
- [ ] Empty messages handled gracefully
- [ ] Special characters in input don't break parsing
- [ ] Long messages (>1000 chars) handled correctly

### Platform Support
- [ ] All supported platforms available in chat
- [ ] Platform-specific formatting applied correctly
- [ ] Character limits enforced per platform
- [ ] Hashtag rules followed per platform
- [ ] Platform labels user-friendly (X (Twitter), not just Twitter)

---

## Future Enhancements

### Near-Term
- [ ] **Persistent Chat History** - Save conversation history across sessions
- [ ] **Content Library** - Save and organize generated content
- [ ] **Keyboard Shortcuts** - Quick access to common commands
- [ ] **Voice Input** - Speak commands instead of typing
- [ ] **Mobile App** - Native iOS/Android apps
- [ ] **Browser Extension** - Generate content from any webpage

### Mid-Term
- [ ] **Multi-Variant Generation** - Generate 2-3 options, user picks best
- [ ] **Bulk Content Creation** - Create 7-30 days of content at once
- [ ] **Content Calendar** - Schedule and visualize content plan
- [ ] **Platform Preview** - See how content looks on each platform
- [ ] **A/B Testing** - Track performance of different variants
- [ ] **Team Collaboration** - Share profiles, approve content

### Long-Term
- [ ] **Direct Publishing** - Post directly to social platforms
- [ ] **Image Generation** - DALL-E/Midjourney integration
- [ ] **Video Editing** - Auto-create videos from scripts
- [ ] **Analytics Dashboard** - Track content performance
- [ ] **Multi-Language** - Generate content in any language
- [ ] **White-Label** - Agencies can brand for clients

---

## Support & Troubleshooting

### Documentation
- **Setup Guide**: `README.md`
- **Gemini Configuration**: `docs/GEMINI_SETUP.md`
- **API Reference**: `docs/CONTENT_GENERATION_API.md`
- **North Star Vision**: `docs/NORTH_STAR_USER_JOURNEY.md`

### Testing & Debugging
- **Test Gemini API**: `python3 scripts/test_gemini_api.py`
- **Test Chat Endpoint**: `curl -X POST http://127.0.0.1:5001/api/chat -H "Content-Type: application/json" -d '{"message":"test"}'` (requires auth)
- **Check Profile**: `SELECT * FROM voice_profile WHERE user_id = 'USER_ID';`

### Server Logs
- `server.log` - Main application logs
- `server_5001.log` - Port-specific logs

### Common Issues

**Chat Not Responding**:
1. Check Gemini API key (`GENAI_API_KEY` in environment)
2. Verify profile completeness (minimum: business_name, industry, brand_voice)
3. Check server logs for errors
4. Test Gemini API connectivity

**Slash Commands Not Working**:
1. Ensure commands start with `/` (no space)
2. Check `ConversationRouter.COMMAND_MAP` for valid commands
3. Verify chat route is properly initialized

**Profile Suggestions Generic**:
1. Add more writing samples to profile
2. Make brand voice description more specific
3. Provide detailed target audience info
4. Use `/samples` to add examples of your best content

---

## Conclusion

Eazeily's chat-first interface makes content creation as easy as texting. Through natural conversation and powerful slash commands, users can:

1. **Set up their brand profile** conversationally or via URL import
2. **Refine their profile** with AI-powered suggestions
3. **Generate perfect content** through simple commands or natural language
4. **Iterate quickly** with conversational refinement
5. **Build muscle memory** for efficient content creation

The system learns from user profiles and writing samples to generate consistently on-brand content across all platforms and formats.

**Key Success Factors**:
- ✅ Profile-driven generation ensures brand consistency
- ✅ Slash commands provide power user efficiency
- ✅ Natural language makes it accessible to everyone
- ✅ AI suggestions continuously improve profile quality
- ✅ Multi-turn conversations enable complex requests

**Next Steps**:
- Review [CONTENT_GENERATION_API.md](CONTENT_GENERATION_API.md) for API details
- Check [NORTH_STAR_USER_JOURNEY.md](NORTH_STAR_USER_JOURNEY.md) for product vision
- Explore slash commands in `services/conversation_router.py`
- Test chat interface at `/dashboard` or `/chat`
