# 🔄 Profile Update User Flows

> **Complete conversational user flow documentation for profile updates and onboarding**
> 
> This document serves as the source of truth for how users interact with profile commands to improve content generation.

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [User Flows](#user-flows)
   - [Flow 1: New User Onboarding (Guided)](#flow-1-new-user-onboarding-guided)
   - [Flow 2: Profile Completion Nudge](#flow-2-profile-completion-nudge)
   - [Flow 3: Quick Profile Update (Single Field)](#flow-3-quick-profile-update-single-field)
   - [Flow 4: Guided Profile Update (Multi-Turn)](#flow-4-guided-profile-update-multi-turn)
   - [Flow 5: Profile Import from URL](#flow-5-profile-import-from-url)
   - [Flow 6: Pre-Generation Profile Check](#flow-6-pre-generation-profile-check)
   - [Flow 7: Post-Generation Profile Refinement](#flow-7-post-generation-profile-refinement)
   - [Flow 8: Profile View (`/profile` command)](#flow-8-profile-view-profile-command)
4. [Field Reference Table](#field-reference-table)
5. [Profile State Transitions](#profile-state-transitions)
6. [Implementation Notes](#implementation-notes)
7. [Related Documentation](#related-documentation)

---

## Overview

Eazeily's profile update system is designed to be **conversational, progressive, and contextual**. Users can build and refine their brand profile through natural language interactions, slash commands, and AI-powered suggestions.

**Key Interaction Models:**
- 💬 **Chat-first interface** - All interactions happen in a conversational UI
- ⚡ **Slash commands** - Quick shortcuts for specific actions (e.g., `/voice`, `/audience`)
- 🤖 **AI-powered suggestions** - Context-aware recommendations based on existing profile data
- 🔄 **Multi-turn conversations** - Complex updates broken into digestible steps
- 📊 **Real-time feedback** - Profile completeness shown throughout the journey

---

## Design Principles

### 1. 💬 Conversational
Feel like chatting with a brand strategist, not filling out a form. Questions are natural, responses are acknowledged, and the flow adapts to user inputs.

**Example:**
```
AI: "How would you describe your brand's personality?"
User: "We're friendly and approachable"
AI: "Perfect! I've updated your brand voice to 'Friendly and approachable'..."
```

### 2. 🎯 Progressive
Start simple, layer in sophistication. Users can create content with minimal profile data, then refine over time for better results.

**Progression:**
- **Minimal (33%)**: Business name, industry, brand voice → Can generate basic content
- **Sufficient (66%)**: + Target audience, key offer → Content is more targeted
- **Complete (100%)**: + Writing samples, voice rules → Content matches brand perfectly

### 3. 📖 Contextual
Explain WHY each field matters for content generation. Users understand the value of providing more information.

**Example:**
```
"Adding writing samples helps me match your unique writing style. 
The more examples you provide, the more authentic your content will sound."
```

### 4. 🔀 Flexible
Support both quick updates (`/voice professional and friendly`) AND guided multi-turn flows (`/update` → select field → provide value).

### 5. ✅ Feedback-rich
Show immediate impact on profile completeness. Users see their progress and understand how changes affect content quality.

---

## User Flows

### Flow 1: New User Onboarding (Guided)

**Context**: User has just signed up and has an empty profile. They need a minimum viable profile to start generating content.

**Entry Point**: User lands in chat interface at `/dashboard` after signup

**User Intent**: Get set up quickly and create first piece of content

**Required Fields**: 
- Business name (required)
- Industry (required)
- Brand voice (required)

**Optional Fields**:
- Target audience (recommended)
- Key offer (recommended)

---

#### 📝 Complete Dialog Example

**Initial Greeting:**
```
AI: Welcome to Eazeily! 👋 I'm your AI content assistant. 

Before we create amazing content together, I need to learn about your brand. 
This will only take a minute.

Let's start with the basics:

What's your business name?

[Skip to URL import if you have a website →]
```

**User Response:**
```
User: Sunny Side Bakery
```

**AI Follow-up:**
```
AI: Love it! ☀️ Sunny Side Bakery it is.

What industry are you in? (e.g., food & beverage, retail, services, tech)
```

**User Response:**
```
User: Food and beverage
```

**AI Follow-up:**
```
AI: Perfect! Now for the fun part...

How would you describe your brand's personality? Think about how you want 
to sound when talking to your customers.

Examples:
• "Warm and welcoming, like chatting with a friend"
• "Professional but approachable"
• "Fun, energetic, and a little playful"

What feels right for Sunny Side Bakery?
```

**User Response:**
```
User: Warm and welcoming, like a neighborhood bakery that's been here for years
```

**AI Follow-up:**
```
AI: Beautiful! That warmth will shine through in your content. 

Quick question: Who are your ideal customers? (Optional but helps me create 
more targeted content)

Example: "Local families looking for fresh artisan bread and pastries"

You can tell me now, or just say 'skip' and we'll come back to this later.
```

**User Response (Path A - Provides Audience):**
```
User: Local families and young professionals who appreciate artisan quality
```

```
AI: Excellent! 🎯 

One more optional question: What makes Sunny Side Bakery special? What's 
your key value proposition?

Example: "Small-batch artisan breads made from organic local ingredients"

(Say 'skip' to move on)
```

**User Response (Path B - Skips):**
```
User: skip
```

```
AI: No problem! We can add that later.

✨ Your profile is ready! (60% complete)

You can now create content that matches your brand. Want to try?

• /post - Create a social media post
• /profile - View your full profile
• Keep chatting to refine your profile

What would you like to do?
```

---

#### 🔀 Branch Points

1. **User provides URL instead of answering questions**
   - Trigger Flow 5 (Profile Import from URL)
   - Pre-fill fields from scraped data
   - Ask user to confirm/edit imported data

2. **User wants to skip optional fields**
   - Allow skipping, note minimum requirements met
   - Show profile completeness percentage
   - Offer to complete later

3. **User provides vague or unclear answers**
   - AI asks clarifying questions
   - Offers examples to guide user
   - Never gets stuck in infinite loop

---

#### ✅ Success Criteria

- User has minimum viable profile (business_name, industry, brand_voice)
- User understands they can refine profile later
- User is ready to create first content OR continue profiling

---

#### 🎯 Next Actions

- Create first content with `/post`, `/caption`, etc.
- View full profile with `/profile`
- Add more details with `/audience`, `/voice`, `/samples`
- Import from URL with `/import [url]`

---

#### ⚠️ Error Handling

**Database Save Failure:**
```
AI: "I had trouble saving that. Let me try again..."
```
- Retry the save operation
- If still fails, show user-friendly error and suggest refresh

**User Input Too Short/Invalid:**
```
AI: "Could you tell me a bit more? For example: [helpful example]"
```

**User Exits Mid-Flow:**
- Save partial progress
- Resume where they left off on next visit
- Show completion percentage

---

### Flow 2: Profile Completion Nudge

**Context**: User has partial profile (< 66% complete) and returns to the dashboard

**Entry Point**: User visits `/dashboard` with incomplete profile

**User Intent**: Create content (may not realize profile affects quality)

**Strategy**: Gentle nudge about completing profile, but don't block content creation

---

#### 📝 Complete Dialog Example

**Welcome Back Message (33% complete):**
```
AI: Welcome back! 👋

I noticed your profile is 33% complete. Adding more details helps me create 
content that truly sounds like YOUR brand.

Missing fields that would improve your content:
• 🎯 Target Audience - Helps me speak directly to YOUR customers
• 💎 Key Offer - Highlights what makes you unique
• ✍️ Writing Samples - Makes content sound authentically like you

Want to:
[Complete my profile] or [Start creating content]
```

**User Chooses "Complete my profile":**
```
AI: Perfect! Let's fill in the details that matter most.

Who are your ideal customers? Tell me about them - their needs, challenges, 
what they're looking for.
```
→ Continue with field collection (Flow 4)

**User Chooses "Start creating content":**
```
AI: Sounds good! I'll do my best with what I have. Keep in mind that adding 
those missing fields will make your content even better.

What would you like to create?
```
→ Continue with content generation

---

**Welcome Back Message (50% complete):**
```
AI: Hey there! Your profile is looking good at 50% complete. 🎯

Quick wins to boost content quality:
• ✍️ Writing Samples (3-5 examples) - Match YOUR unique voice
• 📋 Voice Rules (optional) - Specific do's and don'ts

[Add writing samples] [Set voice rules] [Create content →]
```

**Welcome Back Message (80% complete):**
```
AI: Looking great! Your profile is 80% complete. 

Nice work on:
✅ Business basics
✅ Brand voice  
✅ Target audience
✅ Key offer

Just a couple optional fields left:
• ✍️ Writing Samples - For even more authentic content
• 📋 Voice Rules - Fine-tune exactly how you sound

[Finish profile] [Start creating →]
```

---

#### 🔀 Branch Points

1. **Low completion (< 33%)**
   - More urgent messaging about missing critical fields
   - Still allow content creation, but set expectations

2. **Medium completion (33-66%)**
   - Balanced messaging - "good, but can be better"
   - Emphasize impact on content quality

3. **High completion (66-100%)**
   - Congratulatory tone
   - Focus on fine-tuning with writing samples and rules

---

#### ✅ Success Criteria

- User understands profile completeness level
- User knows which fields are missing and WHY they matter
- User can choose to complete profile OR create content immediately

---

#### 🎯 Next Actions

- Complete specific fields with slash commands (`/audience`, `/voice`, etc.)
- Start guided profile completion with `/update`
- Skip and create content (content quality may vary)

---

### Flow 3: Quick Profile Update (Single Field)

**Context**: User wants to quickly update one specific field without multi-turn conversation

**Entry Point**: User types slash command with value (e.g., `/voice professional and friendly`)

**User Intent**: Make a quick update and get back to content creation

**Supported Commands**:
- `/voice [value]` - Update brand voice
- `/audience [value]` - Update target audience  
- `/offer [value]` - Update key offer
- `/samples [text]` - Add writing sample
- `/rules [rules]` - Set voice rules

---

#### 📝 Complete Dialog Example - `/voice` Command

**User Input (With Value):**
```
User: /voice professional, warm, and approachable
```

**AI Response:**
```
AI: Perfect! I've updated your Brand Voice to:

**Professional, warm, and approachable**

This will help me create content that matches your desired tone. Ready to 
create something?

[Create a post] [Update another field] [View my profile]
```

**Profile State:**
```
BEFORE:
- Brand Voice: "Friendly and casual"

AFTER:  
- Brand Voice: "Professional, warm, and approachable"
- Profile Completeness: 60% → 60% (field already existed)
```

---

**User Input (Without Value - AI Suggestions):**
```
User: /voice
```

**AI Response:**
```
AI: Let me analyze your profile and suggest some brand voice options... 🤔

Based on your business (Sunny Side Bakery) and industry (Food & Beverage), 
here are 3 tailored brand voice suggestions:

1. **"Warm, welcoming, and community-focused"**
   Emphasizes the neighborhood bakery feel and personal connections

2. **"Artisan, passionate, and quality-driven"**  
   Highlights craft, expertise, and commitment to excellence

3. **"Friendly, approachable, and down-to-earth"**
   Balances professionalism with casual, everyday appeal

Which one resonates with Sunny Side Bakery?

[Use Option 1] [Use Option 2] [Use Option 3] [✏️ Write my own]
```

**User Selects Option:**
```
User: 1
```

```
AI: Excellent choice! I've updated your Brand Voice to:

**Warm, welcoming, and community-focused**

This perfectly captures that neighborhood bakery vibe. Your content will 
reflect this warmth!

[Create content] [Update another field]
```

**User Writes Own:**
```
User: Write my own
```

```
AI: Great! Tell me how you'd describe your brand's voice:
```
→ User provides custom value
→ Save and confirm

---

#### 📝 Complete Dialog Example - `/audience` Command

**User Input:**
```
User: /audience
```

**AI Analyzes Profile:**
```
AI: Analyzing your profile to suggest target audiences... 🎯

Based on Sunny Side Bakery and your brand voice, here are 3 ideal customer 
profiles:

1. **"Local families with young children who value wholesome, artisan-baked 
   goods and want to support neighborhood businesses"**
   
2. **"Health-conscious young professionals (25-40) looking for organic, 
   fresh-baked options near their workplace or home"**
   
3. **"Food enthusiasts and home entertainers who appreciate artisan quality 
   and want impressive bread and pastries for gatherings"**

Which group sounds most like your ideal customer?

[Use Option 1] [Use Option 2] [Use Option 3] [✏️ Describe my own]
```

**User Response:**
```
User: 1
```

**AI Confirmation:**
```
AI: Perfect! I've updated your Target Audience to:

**Local families with young children who value wholesome, artisan-baked goods 
and want to support neighborhood businesses**

Now I can create content that speaks directly to what families care about!

Profile Completeness: 60% → 75% ⬆️

[Create a post] [Add writing samples] [View profile]
```

---

#### 🔀 Branch Points

1. **User provides value directly in command**
   - Immediately save and confirm
   - No AI suggestions needed
   - Fast path for experienced users

2. **User uses command without value**
   - Analyze profile with AI
   - Generate 3 contextual suggestions
   - Allow selection OR custom input

3. **User selects an AI suggestion**
   - Save selected suggestion
   - Show confirmation with impact
   - Suggest next actions

4. **User writes own value**
   - Collect custom input
   - Validate (basic length check)
   - Save and confirm

---

#### ✅ Success Criteria

- Field updated successfully in database
- User receives immediate confirmation
- Profile completeness updated if applicable
- User knows next available actions

---

#### 🎯 Next Actions

- Create content with updated profile
- Update another field
- View full profile with `/profile`

---

#### ⚠️ Error Handling

**Invalid Input:**
```
AI: "That seems a bit short. Could you provide more detail? For example: 
[helpful example]"
```

**AI Service Unavailable:**
```
AI: "I can't generate suggestions right now, but you can still update your 
[field] manually. What would you like to set it to?"
```

**Save Failure:**
```
AI: "I had trouble saving that update. Please try again."
```

---

### Flow 4: Guided Profile Update (Multi-Turn)

**Context**: User types `/update` without specifying field, or wants to update a complex field

**Entry Point**: User types `/update` in chat

**User Intent**: Update profile with guidance on what to change

**Flow Type**: Multi-turn conversation with field selection menu

---

#### 📝 Complete Dialog Example

**Initial Command:**
```
User: /update
```

**AI Response - Field Selection:**
```
AI: I'll help you update your profile. What would you like to change?

Current profile (75% complete):
✅ Business Name: Sunny Side Bakery
✅ Industry: Food & Beverage  
✅ Brand Voice: Warm, welcoming, and community-focused
✅ Target Audience: Local families with young children...
✅ Key Offer: Not set
⚠️ Writing Samples: 0 samples
⚠️ Voice Rules: Not set

You can update:
1. Brand Voice (currently set)
2. Target Audience (currently set)
3. Key Offer (recommended - tells customers what makes you unique)
4. Writing Samples (recommended - helps match YOUR style)
5. Voice Rules (optional - specific do's and don'ts)

Which would you like to update? (Choose 1-5 or tell me the field name)
```

---

**User Selects Field:**
```
User: 3
```

**AI Collects Value:**
```
AI: Great! Let's define what makes Sunny Side Bakery special.

What's your key value proposition? What sets you apart from other bakeries?

Examples:
• "Small-batch artisan breads made from organic local ingredients"
• "Traditional French baking techniques with modern flavors"  
• "Community bakery supporting local farmers and families"

What's yours?
```

**User Provides Value:**
```
User: We use traditional European recipes with locally sourced organic 
ingredients, and everything is baked fresh daily
```

**AI Confirmation:**
```
AI: That's a compelling offer! I've updated your Key Offer to:

**Traditional European recipes with locally sourced organic ingredients, 
baked fresh daily**

This gives me a clear hook for your content - emphasizing tradition, quality, 
and freshness.

Profile Completeness: 75% → 90% ⬆️

Want to add anything else?
[Add writing samples] [Set voice rules] [Create content →]
```

---

#### 📝 Complex Field Example - Writing Samples

**User Selects Writing Samples:**
```
User: 4
```

**AI Starts Collection:**
```
AI: Writing samples help me match your unique style and voice!

You currently have 0 samples. I recommend adding 3-5 examples of your best 
writing - social media posts, website copy, emails, anything that sounds like 
YOUR brand.

Paste your first writing sample:
```

**User Provides First Sample:**
```
User: Good morning! ☀️ The smell of fresh croissants is filling the bakery. 
Stop by before they're gone - we're open until 6pm today. Made with love, as 
always. 💛
```

**AI Acknowledges:**
```
AI: Perfect example! I can feel the warmth and community vibe. Saved! 
(1 sample total)

That's a great start. Want to add another? Paste your next sample, or type 
'done' to finish.
```

**User Provides Second Sample:**
```
User: Our Saturday special: olive & rosemary focaccia 🫒 Made with organic 
flour from Green Valley Farm and rosemary from Maria's garden down the street. 
Because great bread starts with great ingredients.
```

**AI Acknowledges:**
```
AI: Excellent! This one really highlights your local sourcing and quality 
ingredients. (2 samples total)

Want to add more? Or type 'done' if you're finished.
```

**User Finishes:**
```
User: done
```

**AI Confirmation:**
```
AI: Fantastic! I've saved 2 writing samples that capture your voice beautifully.

Key patterns I noticed:
• Warm, personal tone with emojis
• Emphasis on freshness and local ingredients  
• Community-focused messaging
• Sensory descriptions (smell, taste)

I'll use these to make your content sound authentically like Sunny Side Bakery.

Profile Completeness: 90% → 100% 🎉

Your profile is now complete! Ready to create amazing content?

[Create a post] [View my profile] [Update another field]
```

---

#### 🔀 Branch Points

1. **User selects field by number**
   - Jump to that field's collection flow
   - Show current value if exists
   - Collect new value

2. **User selects field by name**
   - Parse field name ("brand voice", "audience", etc.)
   - Same flow as selection by number

3. **Multi-step collection (writing samples)**
   - Track collection state across turns
   - Allow adding multiple values
   - User can finish with "done"

4. **User wants to cancel mid-flow**
   - Accept "cancel", "stop", "nevermind"
   - Save any partial progress
   - Return to main chat

---

#### ✅ Success Criteria

- User successfully updates chosen field(s)
- Multi-step collections handled smoothly
- Profile completeness reflects changes
- User can continue to other actions

---

#### 🎯 Next Actions

- Update another field
- Create content with updated profile
- View full profile

---

### Flow 5: Profile Import from URL

**Context**: User has existing website/social presence and wants to auto-populate profile

**Entry Point**: User types `/import [url]` OR drops URL during onboarding

**User Intent**: Save time by importing existing brand info instead of typing everything

**Process**:
1. Scrape URL for brand information
2. Extract: business name, description, tone indicators, keywords
3. Present extracted data for user confirmation
4. Allow editing before saving
5. Merge with existing profile data

---

#### 📝 Complete Dialog Example

**User Command:**
```
User: /import https://sunnysidebakery.com
```

**AI Response - Scraping:**
```
AI: Great! Let me analyze your website... 🔍

Scraping https://sunnysidebakery.com...
```

**AI Response - Extracted Data:**
```
AI: Found some great information! Here's what I extracted from your website:

📋 **Extracted Profile Data:**

**Business Name:** Sunny Side Bakery
**Industry:** Food & Beverage (detected)
**Brand Voice:** Warm, community-focused, quality-driven
**Target Audience:** Local families and food enthusiasts who value 
artisan-baked goods
**Key Offer:** Traditional European recipes using organic local ingredients, 
baked fresh daily
**Keywords:** artisan, fresh, local, organic, community, traditional

**Writing Sample Found:**
"Every morning, we bake with the same love and care that your grandmother 
put into her recipes. Our small batches mean exceptional quality, and our 
commitment to local farms means you're tasting the best of our community."

Does this look accurate? 

[✅ Save all] [✏️ Edit before saving] [❌ Cancel]
```

---

**User Chooses "Save all":**
```
AI: Excellent! I've imported all that data into your profile. ✨

Profile Completeness: 40% → 90% ⬆️

Here's your updated profile:
✅ Business Name: Sunny Side Bakery
✅ Industry: Food & Beverage
✅ Brand Voice: Warm, community-focused, quality-driven
✅ Target Audience: Local families and food enthusiasts...
✅ Key Offer: Traditional European recipes using organic local ingredients...
✅ Writing Samples: 1 sample

You're all set to create content! Want to:
[Create a post] [Add more writing samples] [View full profile]
```

---

**User Chooses "Edit before saving":**
```
AI: No problem! Let's refine the extracted data. What would you like to change?

Current fields:
1. Business Name: Sunny Side Bakery
2. Brand Voice: Warm, community-focused, quality-driven
3. Target Audience: Local families and food enthusiasts...
4. Key Offer: Traditional European recipes...

Tell me which number to edit, or type 'save' when you're happy with it.
```

**User Edits:**
```
User: 2
```

```
AI: Current Brand Voice: "Warm, community-focused, quality-driven"

How would you like to update it?
```

```
User: Warm, welcoming, and passionate about artisan quality
```

```
AI: Updated! ✅

Brand Voice is now: "Warm, welcoming, and passionate about artisan quality"

Want to edit anything else? (Choose 1, 3, or 4, or type 'save')
```

```
User: save
```

```
AI: Perfect! I've saved your profile with the updates. 

Profile Completeness: 40% → 90% ⬆️

You're ready to create authentic content!

[Create a post] [View my profile]
```

---

#### 🔀 Branch Points

1. **Scraping succeeds with rich data**
   - Show all extracted fields
   - Allow bulk save or selective editing
   - High confidence message

2. **Scraping succeeds with partial data**
   - Show what was found
   - Note what's missing
   - Offer to fill in missing fields manually

3. **Scraping fails (blocked, timeout, etc.)**
   ```
   AI: "I had trouble accessing that URL. Could you check if it's correct?
   
   Or, I can help you fill out your profile manually instead.
   
   [Try another URL] [Fill out manually]"
   ```

4. **User already has profile data**
   - Show merge preview
   - Ask which fields to overwrite
   - Preserve user's existing customizations

---

#### ✅ Success Criteria

- URL successfully scraped (or graceful failure)
- Extracted data presented clearly
- User confirms or edits before saving
- Profile updated without overwriting important data

---

#### 🎯 Next Actions

- Create content with imported profile
- Refine specific fields with slash commands
- Add more writing samples manually

---

#### ⚠️ Error Handling

**URL Not Accessible:**
```
AI: "I couldn't access that URL. Possible reasons:
• The site might be private or password-protected
• The URL might be incorrect
• The site might be blocking automated access

Want to try a different URL or fill out your profile manually?"
```

**No Useful Data Found:**
```
AI: "I was able to load the page, but didn't find much brand information. 

Would you like to:
• Try a different page (like your About page)
• Fill out your profile manually
• Paste some text from your website for me to analyze"
```

**Partial Scrape:**
```
AI: "I found some information, but couldn't extract everything:

✅ Found: Business name, industry
⚠️ Missing: Brand voice, target audience, key offer

Want to save what I found and fill in the rest? Or try another URL?"
```

---

### Flow 6: Pre-Generation Profile Check

**Context**: User tries to generate content (`/post`, `/email`, etc.) but profile is incomplete

**Entry Point**: User types content generation command with insufficient profile

**User Intent**: Create content (doesn't realize profile is incomplete)

**Strategy**: Block generation with friendly explanation, show what's missing, provide quick path to complete, then resume generation

**Minimum Requirements**:
- Business name (required)
- Industry (required)
- Brand voice (required)

---

#### 📝 Complete Dialog Example

**User Attempts Generation:**
```
User: /post Write a post about our new sourdough bread
```

**AI Response - Profile Check Failed:**
```
AI: Hold on! Before I can create great content, I need a bit more information 
about your brand. ✋

Your profile is 20% complete. To generate content that truly sounds like YOU, 
I need:

**Missing Critical Fields:**
❌ Business Name - So I know who I'm writing for
❌ Industry - Helps me use the right tone and terminology  
❌ Brand Voice - Ensures content matches your personality

**Why These Matter:**
Without these basics, I'd be guessing at your brand identity. Let's spend 
60 seconds getting this right, then I'll write that post!

Ready to set up your profile?

[Yes, let's do it] [More info about why profile matters]
```

---

**User Chooses "Yes, let's do it":**
```
AI: Perfect! This will be quick. 🚀

First, what's your business name?
```

**User Provides Info:**
```
User: Sunny Side Bakery
```

```
AI: Great! What industry? (e.g., food & beverage, retail, services)
```

```
User: food and beverage
```

```
AI: Excellent! Last question:

How would you describe your brand's voice? (e.g., professional, friendly, 
casual, expert)
```

```
User: Warm and welcoming
```

```
AI: Perfect! ✨

Your profile is now ready (60% complete). I can generate content that matches 
your brand!

Now, let me write that post about your new sourdough bread...
```

**AI Generates Content:**
```
AI: Here's your Instagram post: 📝

---
Fresh from the oven: our new artisan sourdough! 🍞✨

Made with love, time, and a 48-hour fermentation process. The crust? 
Perfectly golden. The inside? Soft and tangy. 

Stop by Sunny Side Bakery and taste the difference that patience makes.

We're open today until 6pm!

#ArtisanBread #Sourdough #SunnySideBakery #FreshBaked
---

[Copy] [Edit] [Regenerate] [Try different platform]
```

---

**User Chooses "More info about why profile matters":**
```
AI: Great question! Here's why your profile matters:

**Without Profile Data:**
"Check out our new sourdough bread! It's really good and you should try it."
→ Generic, could be from any bakery

**With Profile Data:**  
"Fresh from the oven: our new artisan sourdough! Made with love, time, and 
a 48-hour fermentation process..."
→ Warm tone, emphasizes craft and quality, sounds like YOUR brand

Your profile helps me:
• Match your brand voice (professional vs casual vs warm)
• Target your specific audience (families vs food enthusiasts)  
• Highlight what makes you unique (artisan quality, local ingredients)
• Use your industry's language (bread terminology, baking processes)

Takes 60 seconds to set up, makes content 10x better. Ready?

[Yes, set up profile] [Skip for now]
```

**User Skips:**
```
AI: I understand! I'll do my best with generic content.

Keep in mind: The content won't be personalized to your brand. You can add 
profile details anytime with /profile.

Generating generic post...
```

---

#### 🔀 Branch Points

1. **Profile completely empty (0%)**
   - More urgent messaging
   - Require minimum fields before generating
   - Make setup path very clear

2. **Profile has some data (20-40%)**
   - Show what's present, what's missing
   - Generate content but note quality will be limited
   - Strong encouragement to complete profile

3. **Profile sufficient but not complete (50-80%)**
   - Allow generation
   - Show quick tip about missing fields
   - Offer to add after generation

4. **User insists on skipping**
   - Allow generation with generic content
   - Set clear expectation about quality
   - Show profile setup path for later

---

#### ✅ Success Criteria

- User understands WHY profile matters
- User completes minimum required fields
- Content generation resumes successfully
- User knows they can refine profile later

---

#### 🎯 Next Actions

- Review generated content
- Copy/share content
- Complete remaining profile fields
- Generate more content

---

### Flow 7: Post-Generation Profile Refinement

**Context**: Content was generated, but user isn't happy with the result

**Entry Point**: User provides feedback on generated content

**User Intent**: Get content that better matches their expectations

**Strategy**: Help user identify which profile field needs adjustment, update it, then regenerate

---

#### 📝 Complete Dialog Example - Content Too Formal

**Initial Generation:**
```
AI: Here's your LinkedIn post: 📝

---
We are pleased to announce the introduction of our new artisan sourdough 
bread product. This offering represents a significant advancement in our 
product portfolio and demonstrates our commitment to quality baking standards.

For more information, please visit our establishment.
---

[Copy] [Edit] [Regenerate]
```

**User Feedback:**
```
User: This is way too formal. We're a neighborhood bakery, not a corporation
```

**AI Diagnosis:**
```
AI: You're absolutely right! The tone doesn't match a warm neighborhood 
bakery at all. 

The issue is your **Brand Voice** setting. Let me check... 

Current Brand Voice: "Professional and business-focused"

For a neighborhood bakery, you probably want something warmer. Let me suggest 
some better options:

1. **"Warm, friendly, and welcoming"** - Like chatting with neighbors
2. **"Casual, authentic, and community-focused"** - Down-to-earth and real
3. **"Cozy, inviting, and personal"** - Like a family kitchen

Which feels right for Sunny Side Bakery?

[Use Option 1] [Use Option 2] [Use Option 3] [✏️ Describe my own]
```

**User Selection:**
```
User: 1
```

**AI Update & Regenerate:**
```
AI: Perfect! I've updated your Brand Voice to "Warm, friendly, and welcoming"

Let me rewrite that post with the right tone...

---
Good morning! ☀️ 

Guess what just came out of the oven? Our NEW artisan sourdough bread! 

We've been perfecting this recipe for months, and we can't wait for you to 
try it. The crust is perfectly crispy, the inside is soft and tangy - it's 
everything good bread should be.

Stop by today! We're open until 6pm. 💛

#SourdoughLove #SunnySideBakery #FreshBaked
---

Much better, right? This matches your warm, neighborly vibe!

[Copy this version] [Refine more] [Generate something else]
```

---

#### 📝 Complete Dialog Example - Wrong Audience

**User Feedback:**
```
User: This sounds like it's for corporate clients, but we target local families
```

**AI Diagnosis:**
```
AI: Great catch! The messaging is targeting the wrong audience.

Let me check your Target Audience setting...

Current: "Business professionals and corporate clients"

No wonder! Let me suggest audience definitions for a family-focused bakery:

1. **"Local families with young children who want wholesome, quality baked 
   goods for their homes"**
   
2. **"Parents and grandparents looking for nostalgic, home-style baked goods 
   that remind them of their childhood"**
   
3. **"Health-conscious families seeking artisan bread made with organic, 
   local ingredients"**

Which group sounds most like your customers?

[Use Option 1] [Use Option 2] [Use Option 3] [✏️ Write my own]
```

**User Selection:**
```
User: 2
```

**AI Regenerates:**
```
AI: Updated! Your Target Audience is now:

"Parents and grandparents looking for nostalgic, home-style baked goods that 
remind them of their childhood"

Regenerating with family-focused messaging...

---
Remember the smell of fresh bread at grandma's house? That's what we're 
bringing back. 🏠💛

Our new artisan sourdough is made the old-fashioned way - with time, care, 
and love. No shortcuts. No preservatives. Just honest, delicious bread like 
they used to make.

Bring the kids by this weekend and let them see (and smell!) real baking. 
We're open Saturday 8am-6pm.

#FamilyBakery #HomeStyle #SunnySideBakery
---

Now THAT speaks to families and nostalgia! 

[Copy] [Perfect!] [Try another platform]
```

---

#### 📝 Complete Dialog Example - Doesn't Sound Like Me

**User Feedback:**
```
User: This is okay, but it doesn't really sound like how I write
```

**AI Diagnosis:**
```
AI: I can make it sound more authentically like YOU, but I need some examples 
of your actual writing!

You currently have 0 writing samples in your profile.

Adding 3-5 samples helps me:
• Match your unique phrasing and word choices
• Copy your rhythm and sentence structure  
• Use (or avoid) emojis like you do
• Capture your personality quirks

Want to add some writing samples now? Just paste examples of your best 
social posts, website copy, or emails.

[Add samples now] [Skip and use this version]
```

**User Adds Samples:**
```
User: Add samples now
```

```
AI: Perfect! Paste your first writing sample:
```

```
User: Y'all. The cinnamon rolls today are INSANE. Like, still-warm-from-the-oven, 
cinnamon-sugar-heaven INSANE. Come get one before Jerry eats them all. 😂 
(True story, he's already on #3)
```

```
AI: Ha! I love the personality here! Saved. (1 sample)

This gives me so much to work with - informal tone, "Y'all", humor, specific 
names, emojis. Want to add another?
```

```
User: Our sourdough starter is officially 15 years old today. FIFTEEN YEARS 
of bubbling away, making magic happen. She's basically family at this point. 
🍞💛 (Yes, we call her Patricia. Don't judge.)
```

```
AI: PERFECT! "She's basically family" and naming the starter - this is gold! 
(2 samples)

Add more or type 'done'?
```

```
User: done
```

```
AI: Excellent! Now let me rewrite that sourdough post in YOUR voice...

---
Y'all. NEW SOURDOUGH just dropped. 🍞

We've been playing around with this recipe for MONTHS (shoutout to Patricia, 
our 15-year-old starter, for doing her thing). And honestly? It's incredible.

Crispy crust that crackles when you break it. Soft, tangy inside. The real 
deal.

Come grab a loaf before they're gone - you know how fast things fly out of 
here on Saturdays. Open till 6!

#Sourdough #SunnySideBakery #FreshBaked
---

NOW we're talking! That sounds like YOU, right?

[Yes! Copy it] [Close, but tweak it] [Generate another style]
```

---

#### 🔀 Branch Points

1. **Issue: Too formal/casual**
   → Update brand_voice field
   → Show tone slider or suggestions
   → Regenerate immediately

2. **Issue: Wrong audience focus**
   → Update target_audience field
   → Show demographic-specific options
   → Regenerate with new targeting

3. **Issue: Doesn't sound authentic**
   → Add writing_samples
   → Collect 2-5 examples
   → Regenerate matching their style

4. **Issue: Missing key message**
   → Update key_offer field
   → Highlight what makes them unique
   → Regenerate with new hook

5. **User happy with update**
   → Save content
   → Offer to generate more
   → Profile now improved for future content

---

#### ✅ Success Criteria

- User identifies what feels wrong
- AI suggests correct profile field to update
- Profile updated with better data
- Regenerated content matches expectations

---

#### 🎯 Next Actions

- Copy improved content
- Generate content for other platforms
- Continue refining profile
- Share/schedule content

---

### Flow 8: Profile View (`/profile` command)

**Context**: User wants to see their complete profile and current settings

**Entry Point**: User types `/profile` command

**User Intent**: Review what information is stored, see completion status, identify what to update

**Features**:
- Show all fields with current values
- Display profile completeness percentage
- Highlight missing/empty fields
- Provide quick update commands for each field

---

#### 📝 Complete Dialog Example

**User Command:**
```
User: /profile
```

**AI Response - Complete Profile:**
```
AI: Here's your brand profile: 👤

**Profile Completeness: 100%** 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📋 Basic Information**
✅ Business Name: Sunny Side Bakery
✅ Industry: Food & Beverage

**🎤 Brand Voice & Messaging**
✅ Brand Voice: Warm, friendly, and welcoming
✅ Target Audience: Local families with young children who value wholesome, 
   artisan-baked goods and want to support neighborhood businesses
✅ Key Offer: Traditional European recipes using locally sourced organic 
   ingredients, baked fresh daily

**✍️ Writing & Style**
✅ Writing Samples: 3 samples
✅ Voice Rules: Use casual language, include emojis sparingly, always 
   mention "fresh" and "local"

**🎯 Additional Details**
✅ Brand Keywords: artisan, fresh, local, organic, community, traditional
✅ Platforms: Instagram, Facebook
✅ Timezone: America/New_York

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Want to update something? Try:
• `/voice` - Update brand voice
• `/audience` - Refine target audience
• `/samples` - Add more writing samples
• `/update` - Guided update flow

Or just tell me what you'd like to change!

[Update a field] [View writing samples] [Create content →]
```

---

**AI Response - Partial Profile (60% complete):**
```
AI: Here's your brand profile: 👤

**Profile Completeness: 60%** 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📋 Basic Information**
✅ Business Name: Sunny Side Bakery
✅ Industry: Food & Beverage

**🎤 Brand Voice & Messaging**
✅ Brand Voice: Warm, friendly, and welcoming
✅ Target Audience: Local families and food enthusiasts
⚠️ Key Offer: Not set

**✍️ Writing & Style**
⚠️ Writing Samples: 0 samples
⚠️ Voice Rules: Not set

**🎯 Additional Details**
⚠️ Brand Keywords: Not set
✅ Platforms: Instagram, Facebook
✅ Timezone: America/New_York

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Recommended Next Steps:**
1. 💎 Set your Key Offer - Tells customers what makes you unique
   → `/offer [your unique value]`

2. ✍️ Add Writing Samples - Makes content sound like YOU
   → `/samples` to add examples

3. 📋 Set Voice Rules (optional) - Fine-tune your content style
   → `/rules [your guidelines]`

[Complete profile] [Add key offer] [Add writing samples] [Create content]
```

---

**AI Response - Minimal Profile (33% complete):**
```
AI: Here's your brand profile: 👤

**Profile Completeness: 33%** ⚠️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📋 Basic Information**
✅ Business Name: Sunny Side Bakery
✅ Industry: Food & Beverage

**🎤 Brand Voice & Messaging**
✅ Brand Voice: Not set yet
⚠️ Target Audience: Not set
⚠️ Key Offer: Not set

**✍️ Writing & Style**
⚠️ Writing Samples: 0 samples
⚠️ Voice Rules: Not set

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🚨 Your profile needs more details for quality content!**

**Critical Missing Fields:**
1. 🎤 Brand Voice - How should your content sound?
2. 🎯 Target Audience - Who are you trying to reach?  
3. 💎 Key Offer - What makes you unique?

Quick setup takes 2 minutes and makes a huge difference in content quality!

[Complete profile now] [Learn why it matters] [Create content anyway]
```

---

#### 🔀 Branch Points

1. **Complete Profile (90-100%)**
   - Congratulatory tone
   - Show all data
   - Emphasize they're ready for great content
   - Offer optional refinements

2. **Mostly Complete (60-90%)**
   - Positive tone
   - Show what's present and what's missing
   - Suggest next best field to add
   - Allow content creation

3. **Incomplete Profile (< 60%)**
   - Urgent but friendly tone
   - Emphasize impact on content quality
   - Clear path to complete critical fields
   - Allow content creation with warning

4. **User wants details on a specific field**
   ```
   User: "Show me my writing samples"
   
   AI: "You have 3 writing samples:
   
   1. [Sample 1 text...]
   2. [Sample 2 text...]
   3. [Sample 3 text...]
   
   [Add more samples] [Delete a sample] [Back to profile]"
   ```

---

#### ✅ Success Criteria

- User sees complete profile summary
- Completion percentage displayed prominently
- Missing fields clearly identified
- Quick update commands provided for each field

---

#### 🎯 Next Actions

- Update specific field with slash command
- Start guided update with `/update`
- Create content with current profile
- Learn more about profile fields

---

#### ⚠️ Error Handling

**Profile Load Failure:**
```
AI: "I had trouble loading your profile. Please try again, or contact support 
if this persists."
```

**Empty Profile:**
```
AI: "You don't have a profile yet! Let's set one up so I can create content 
that matches your brand.

[Set up profile] [Learn more]"
```

---

## Field Reference Table

| Field Name | Type | Required | Slash Command | Impact on Content Quality | When to Update | Example Values |
|------------|------|----------|---------------|---------------------------|----------------|----------------|
| **business_name** | String | ✅ Yes | `/update business_name` | Critical - Used in bylines, signatures, CTAs | During onboarding, rebrand | "Sunny Side Bakery" |
| **industry** | String | ✅ Yes | `/update industry` | Critical - Determines terminology, tone, audience expectations | During onboarding, business pivot | "Food & Beverage", "SaaS", "Retail" |
| **brand_voice** | String | ✅ Yes | `/voice` | Critical - Controls overall tone, formality, personality | Onboarding, tone feels off | "Warm and welcoming", "Professional but approachable" |
| **target_audience** | Text | ⚠️ Recommended | `/audience` | High - Affects messaging, pain points, language complexity | Onboarding, targeting changes | "Local families with young children..." |
| **key_offer** | Text | ⚠️ Recommended | `/offer` | High - Provides unique hook, differentiators | Onboarding, value prop evolves | "Traditional European recipes with organic local ingredients" |
| **writing_samples** | JSON Array | ⚠️ Recommended | `/samples` | High - Ensures authentic voice matching | When content doesn't sound authentic | Array of 3-5 text samples |
| **voice_rules** | Text | Optional | `/rules` | Medium - Fine-tunes specific do's/don'ts | When specific constraints needed | "Always use lowercase, no corporate jargon" |
| **brand_keywords** | JSON Array | Optional | `/update brand_keywords` | Medium - Reinforces brand terminology | When certain words must appear | ["artisan", "fresh", "local"] |
| **platforms** | JSON Array | Optional | Automatic per task | Low - Platform-specific formatting | Set once during onboarding | ["Instagram", "LinkedIn"] |
| **timezone** | String | Optional | `/update timezone` | Low - Affects scheduling suggestions | Set once during onboarding | "America/New_York" |

---

## Profile State Transitions

### State Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Profile States                              │
└─────────────────────────────────────────────────────────────────┘

Empty (0%)
    │
    │ Add: business_name, industry, brand_voice
    ↓
Minimal (33%) ──────────────────┐
    │                            │ Can generate content
    │ Add: target_audience       │ (basic quality)
    ↓                            │
Sufficient (66%) ───────────────┤
    │                            │ Can generate content
    │ Add: key_offer             │ (good quality)
    ↓                            │
Complete (100%) ────────────────┘
                                 │ Can generate content
                                 │ (excellent quality)
```

---

### Required Fields by State

**Empty → Minimal (33%)**
- ✅ business_name
- ✅ industry  
- ✅ brand_voice

**Minimal → Sufficient (66%)**
- ✅ target_audience
- ✅ key_offer

**Sufficient → Complete (100%)**
- ✅ writing_samples (at least 1)
- ⚠️ voice_rules (optional but recommended)

---

### Content Generation Requirements

| Profile State | Can Generate? | Content Quality | Recommendation |
|---------------|---------------|-----------------|----------------|
| **Empty (0-32%)** | ❌ Blocked | N/A | Complete minimum fields first |
| **Minimal (33-65%)** | ⚠️ Warning | Generic, may not match brand | Add target audience and key offer |
| **Sufficient (66-99%)** | ✅ Yes | Good, matches basic brand profile | Add writing samples for authenticity |
| **Complete (100%)** | ✅ Yes | Excellent, fully personalized | Content ready to publish |

---

### State Transition Examples

**Example 1: Fast Onboarding**
```
User signs up → Provides business name, industry, brand voice
→ 33% complete → Tries to generate content
→ System allows but suggests adding audience
→ User generates first post → Returns to add audience later
→ 66% complete
```

**Example 2: URL Import**
```
User signs up → Uses `/import [url]`
→ System extracts: name, industry, voice, audience, offer, keywords
→ 80% complete in one step
→ User can immediately generate high-quality content
```

**Example 3: Gradual Refinement**
```
User starts at 33% → Generates content → "Too formal"
→ Updates brand voice via `/voice` → Regenerates
→ "Better, but doesn't sound like me"
→ Adds writing samples via `/samples` → 100% complete
→ Content now matches perfectly
```

---

## Implementation Notes

### Code Architecture

**Frontend (Client-side)**
- **File**: `static/js/promptbox.js`
- **Responsibilities**:
  - Render conversational UI
  - Handle slash command autocomplete
  - Manage conversation history and pending tasks
  - Display profile suggestions and selection UI
  - Handle URL import flow

**Backend (Server-side)**
- **File**: `routes/chat_routes.py`
- **Responsibilities**:
  - Parse user intents via `ConversationRouter`
  - Orchestrate multi-turn profile updates
  - Check profile completeness before generation
  - Save profile updates to database
  - Generate AI suggestions via `ProfileExpert`

**AI Services**
- **File**: `services/profile_expert.py`
- **Responsibilities**:
  - Generate 3 AI suggestions for brand_voice, target_audience, key_offer
  - Analyze existing profile for context
  - Process raw user input (URLs, vague descriptions)
  
- **File**: `services/conversation_router.py`
- **Responsibilities**:
  - Parse slash commands
  - Extract field names and values from natural language
  - Determine task types (profile_update vs content generation)

**Profile Validation**
- **File**: `services/profile_validator.py`
- **Responsibilities**:
  - Calculate profile completeness percentage
  - Identify missing required/recommended fields
  - Return list of what's needed for content generation

---

### Database Schema

**Table**: `voice_profile`

**Core Profile Fields:**
```sql
business_name VARCHAR(255)      -- Business name
industry VARCHAR(255)            -- Industry/sector
brand_voice VARCHAR(255)         -- Brand voice/tone
target_audience TEXT             -- Target audience description
key_offer TEXT                   -- Unique value proposition
voice_rules TEXT                 -- Voice guidelines and constraints
writing_samples TEXT             -- JSON array of writing examples
```

**Additional Fields:**
```sql
tone VARCHAR(255)                -- Alias for brand_voice
brand_keywords TEXT              -- JSON array of keywords
platforms TEXT                   -- JSON array of platform names
timezone VARCHAR(100)            -- User timezone
goals TEXT                       -- JSON array of goals
```

**Import/Scraper Fields:**
```sql
scraped_url TEXT                 -- URL that was scraped
scraped_meta TEXT                -- JSON metadata from scraping
customers TEXT                   -- JSON array of customer segments
scraped_at DATETIME              -- Timestamp of scraping
scrape_status VARCHAR(50)        -- Status: none, pending, finished, failed
```

---

### Key Functions Reference

**Profile Updates**
```python
# routes/chat_routes.py
_handle_profile_update(message, pending_task, profile, db)
_apply_profile_update(profile, field_name, new_value, db)
_continue_profile_update(pending_task, message, profile, db)
_show_profile_summary(profile)
```

**AI Suggestions**
```python
# services/profile_expert.py
suggest_brand_voices(profile) -> List[str]
suggest_target_audiences(profile) -> List[str]
suggest_key_offers(profile) -> List[str]
process_raw_audience_input(user_input, profile) -> dict
```

**Intent Parsing**
```python
# services/conversation_router.py
ConversationRouter.parse_intent(message, profile) -> dict
# Returns: {
#   'task_type': str,
#   'extracted_params': dict,
#   'confidence': float
# }
```

**Profile Completeness**
```python
# services/profile_validator.py
get_profile_completeness(profile) -> Tuple[bool, List[str], int]
# Returns: (is_complete, missing_fields, percentage)
```

---

### Slash Command Processing Flow

```
User types: "/voice professional and friendly"
    ↓
PromptBox (client) detects slash command
    ↓
Sends to /api/chat with message
    ↓
ConversationRouter.parse_intent()
    ↓
Identifies: task_type='update_voice', extracted_params={'new_value': '...'}
    ↓
_handle_profile_update() in chat_routes
    ↓
_apply_profile_update(profile, 'brand_voice', new_value, db)
    ↓
Validate → Save to DB → Commit
    ↓
Return confirmation response
    ↓
PromptBox displays confirmation + suggestions
```

---

### Profile Completeness Calculation

**Algorithm** (from `profile_validator.py`):
```python
REQUIRED_FIELDS = ['business_name', 'industry', 'brand_voice']
RECOMMENDED_FIELDS = ['target_audience', 'key_offer']
OPTIONAL_FIELDS = ['writing_samples', 'voice_rules']

completeness = (
    (filled_required / total_required) * 50 +      # 50% weight
    (filled_recommended / total_recommended) * 30 + # 30% weight
    (filled_optional / total_optional) * 20         # 20% weight
)
```

---

### Multi-Turn State Management

**State Storage**: `pending_task` object passed in request payload

**Example State Objects:**

**Profile Update in Progress:**
```json
{
  "flow": "profile_update",
  "task_type": "update_voice",
  "field_name": "brand_voice",
  "prefilled_value": "Professional and friendly"
}
```

**Writing Samples Collection:**
```json
{
  "flow": "profile_update",
  "task_type": "update_samples",
  "collecting": "writing_samples"
}
```

**Onboarding Flow:**
```json
{
  "task_type": "onboarding",
  "collecting_field": "target_audience"
}
```

---

## Related Documentation

### User Journey & Experience
- **[user-journey.md](user-journey.md)** - Complete user journey from signup to content creation
- **[NORTH_STAR_USER_JOURNEY.md](NORTH_STAR_USER_JOURNEY.md)** - Product vision and user experience philosophy

### Technical Implementation
- **[PROFILE_TO_GENERATION_FLOW.md](PROFILE_TO_GENERATION_FLOW.md)** - Technical data flow from profile to AI generation
- **[CONTENT_GENERATION_API.md](CONTENT_GENERATION_API.md)** - API endpoints and integration details

### Feature Documentation
- **[promptbox-profile-guided-onboarding.md](promptbox-profile-guided-onboarding.md)** - Profile guided onboarding implementation

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-18 | 1.0 | Initial comprehensive documentation of all profile update user flows |

---

**Questions or Feedback?**

This is a living document. If you find gaps, errors, or have suggestions for improvement, please update this file or contact the team.

---

*Last Updated: January 18, 2026*
