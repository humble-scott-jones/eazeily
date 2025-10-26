import re
from datetime import timedelta
from typing import Optional
import os
import random

# Optional OpenAI integration for enhanced post generation
USE_OPENAI_FOR_POSTS = bool(os.getenv("OPENAI_API_KEY")) and os.getenv("USE_OPENAI_FOR_POSTS", "0") == "1"
if USE_OPENAI_FOR_POSTS:
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        USE_OPENAI_FOR_POSTS = False
        _openai_client = None
else:
    _openai_client = None

PILLARS_BY_DEFAULT = [
    ("Educational", "Share a quick tip that solves a common problem for your audience."),
    ("Behind-the-Scenes", "Show a candid look at your process, team, or workspace."),
    ("Testimonial/Social Proof", "Share a short customer quote and the outcome they achieved."),
    ("Product/Offer", "Highlight one offering with benefits, price (optional), and CTA."),
    ("Engagement", "Ask a question or run a simple poll to spark comments."),
    ("Story", "Tell a brief story of a challenge → action → result."),
]

PLATFORM_HINTS = {
    "instagram": "Keep it scroll-friendly with punchy line breaks and a touch of emoji.",
    "facebook": "Invite conversation with two short, friendly paragraphs.",
    "linkedin": "Lead with insight, keep it tight, and state the value upfront.",
    "tiktok": "High energy lines that read like captions for a quick reel.",
    "twitter": "Punchy and direct. No fluff.",
}

# Natural language templates for different content pillars
# Natural language templates for different content pillars
NATURAL_TEMPLATES = {
    "Educational": {
        "friendly": [
            "Hey friends! 👋 Quick tip for you: {hint}",
            "Here's something we've learned: {hint}",
            "Pro tip alert! 🎯 {hint}",
        ],
        "professional": [
            "{hint}",
            "Industry insight: {hint}",
            "Best practice: {hint}",
        ],
        "playful": [
            "Psst... want to know a secret? 🤫 {hint}",
            "Plot twist! {hint}",
            "Hot take: {hint}",
        ],
        "inspirational": [
            "Here's something powerful: {hint}",
            "Let's talk growth: {hint}",
            "Wisdom worth sharing: {hint}",
        ],
    },
    "Behind-the-Scenes": {
        "friendly": [
            "Pulling back the curtain today! 🎬 {hint}",
            "Ever wondered how we do it? {hint}",
            "Sneak peek time! {hint}",
        ],
        "professional": [
            "Transparency is key to trust. {hint}",
            "Our process matters. {hint}",
            "Inside look at our operations: {hint}",
        ],
        "playful": [
            "Ready for a backstage pass? 🎭 {hint}",
            "Shhh, we're letting you in on our secrets! {hint}",
            "BTS magic happening here! ✨ {hint}",
        ],
        "inspirational": [
            "The journey matters as much as the destination. {hint}",
            "Real work, real passion. {hint}",
            "Behind every result is a story. {hint}",
        ],
    },
    "Testimonial/Social Proof": {
        "friendly": [
            "Love hearing success stories! 💙 {hint}",
            "This made our day! {hint}",
            "When our customers shine, we all shine! ⭐ {hint}",
        ],
        "professional": [
            "Client success spotlight: {hint}",
            "Proven outcomes: {hint}",
            "Case study highlight: {hint}",
        ],
        "playful": [
            "Bragging rights incoming! 🏆 {hint}",
            "Plot twist: We have the coolest customers! {hint}",
            "Mic drop moment! 🎤 {hint}",
        ],
        "inspirational": [
            "Nothing inspires us more than your success. {hint}",
            "Your story, our pride. {hint}",
            "Success leaves clues. {hint}",
        ],
    },
    "Product/Offer": {
        "friendly": [
            "Excited to share this with you! {hint}",
            "Something special for you! ✨ {hint}",
            "We've been working on something great! {hint}",
        ],
        "professional": [
            "Introducing a solution designed with you in mind. {hint}",
            "New offering available: {hint}",
            "Enhance your results with: {hint}",
        ],
        "playful": [
            "Ta-da! 🎉 {hint}",
            "We made a thing! {hint}",
            "New drop alert! 🚨 {hint}",
        ],
        "inspirational": [
            "Created to empower you. {hint}",
            "Every solution starts with understanding your needs. {hint}",
            "Innovation meets purpose. {hint}",
        ],
    },
    "Engagement": {
        "friendly": [
            "We want to hear from YOU! {hint}",
            "Let's chat! {hint}",
            "Quick question for you! {hint}",
        ],
        "professional": [
            "Your input shapes our direction. {hint}",
            "Industry discussion: {hint}",
            "We value your expertise. {hint}",
        ],
        "playful": [
            "Okay, settle a debate! {hint}",
            "Pop quiz! 📝 {hint}",
            "Spill the tea! ☕ {hint}",
        ],
        "inspirational": [
            "Your voice creates change. {hint}",
            "Together we learn, together we grow. {hint}",
            "Every perspective adds value. {hint}",
        ],
    },
    "Story": {
        "friendly": [
            "Story time! 📖 {hint}",
            "Let us tell you about something that happened... {hint}",
            "Here's a little story from us: {hint}",
        ],
        "professional": [
            "Case in point: {hint}",
            "Learning from experience: {hint}",
            "Real-world application: {hint}",
        ],
        "playful": [
            "Buckle up for this one! 🎢 {hint}",
            "No joke, this actually happened! {hint}",
            "Storytime with a twist! {hint}",
        ],
        "inspirational": [
            "Every setback is a setup for a comeback. {hint}",
            "From challenge to triumph: {hint}",
            "The journey taught us everything. {hint}",
        ],
    },
}

GOAL_CTA_HINTS = {
    "Drive sales": "Ready to treat yourself? Tap the link in bio to order.",
    "Engagement": "Tell me your take in the comments 👇",
    "Build authority": "Save this for later and share it with a friend who needs it.",
    "Grow community": "Tag someone who would vibe with this.",
    "Promote": "Want first dibs? DM me and I’ll hook you up.",
    "Lead generation": "Slide into the DMs for the full breakdown.",
    # industry-specific goal chips
    "New listings": "Want first dibs? DM me \"LIST\" and I’ll send you the walkthrough.",
    "Local lifestyle": "Need more neighborhood picks? Save this and follow along.",
    "Market tips": "Need the full market breakdown? Message me \"MARKET\" and I’ll share the report.",
    "Testimonials": "Curious how we work? DM and I’ll share the full story.",
    "Menu items": "Reserve your table through the link — seats go fast.",
    "Seasonal specials": "Craving it? Tap the link to order or book a table.",
    "Events": "Grab your spot now via the link in bio.",
    "Team": "Come say hi — book a table or swing by tonight.",
    "Content emphasis": "Share this with someone who needs the inspo.",
    "New arrivals": "Snag yours — DM your size and we’ll hold it.",
    "How-to style": "Try it and tag us in your look.",
    "Promotions": "Use the link in bio to shop the drop.",
    "Community": "Know someone who’d love this? Share it with them.",
    "Motivation": "Share this with your workout buddy and let’s go.",
    "Education": "Save this drill for your next session.",
    "Member stories": "Want a plan like this? DM \"COACH\" and we’ll map it out.",
    "Process": "Follow for more behind-the-scenes moments.",
    "Products": "Want one? DM \"RESERVE\" and we’ll set it aside.",
    "Story": "Send this to someone who’ll feel the glow-up.",
    "Impact": "Help fuel the work — donate via the link.",
    "Volunteers": "Raise your hand in the DMs to volunteer.",
    "Donations": "Give today and tell a friend who cares.",
    "Before/after": "Want a transformation like this? Book a consult.",
    "Tips": "Save this checklist for the next time you tackle it.",
    "Seasonal reminders": "Need a reminder? DM us and we’ll send the list.",
    "Reviews": "Ready for your own 5-star fix? Message us.",
    "Patient resources": "Need the full guide? Send us a DM and we’ll share it.",
    "Mindset": "Share this with someone who needs the reminder.",
}

INDUSTRY_TOKEN_MAP = {
    "realtor": ["realtor", "real estate", "broker", "property"],
    "restaurant": ["restaurant", "cafe", "café", "bar", "eatery", "kitchen"],
    "retail": ["retail", "boutique", "shop"],
    "fitness": ["fitness", "gym", "studio", "wellness", "yoga", "pilates"],
    "artisan": ["artisan", "maker", "handmade", "studio", "craft"],
    "coach": ["coach", "coaching", "consult", "consultant", "mentor"],
    "nonprofit": ["nonprofit", "charity", "community", "foundation"],
    "home_services": ["home service", "hvac", "plumbing", "electric", "roof", "contractor"],
    "healthcare": ["health", "clinic", "medical", "dent", "therapy"],
}

INDUSTRY_HASHTAG_HINTS = {
    "realtor": ["#RealEstateTips", "#HomeTour", "#HouseHunting"],
    "restaurant": ["#EatLocal", "#ChefSpecial", "#Foodie"],
    "retail": ["#ShopLocal", "#StyleInspo", "#NewArrivals"],
    "fitness": ["#Wellness", "#WorkoutMotivation", "#MoveWithUs"],
    "artisan": ["#Handmade", "#StudioLife", "#SlowMade"],
    "coach": ["#Leadership", "#MindsetShift", "#BusinessTips"],
    "nonprofit": ["#GiveBack", "#CommunityLove", "#Impact"],
    "home_services": ["#HomeCare", "#BeforeAfter", "#FixerUpper"],
    "healthcare": ["#HealthyHabits", "#PatientCare", "#WellnessTips"],
}


def _clean_tag(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", str(text))
    return cleaned[:18]


def _format_list(items: list[str]) -> str:
    filtered = [str(i).strip() for i in items if isinstance(i, str) and i.strip()]
    if not filtered:
        return ""
    if len(filtered) == 1:
        return filtered[0]
    if len(filtered) == 2:
        return f"{filtered[0]} and {filtered[1]}"
    return ", ".join(filtered[:-1]) + f", and {filtered[-1]}"


def _first_value(items: Optional[list[str]]) -> str:
    if not items:
        return ""
    for item in items:
        if isinstance(item, str) and item.strip():
            return item.strip()
    return ""


def resolve_industry_key(industry: str, details: Optional[dict] = None) -> str:
    if isinstance(details, dict):
        from_details = details.get("_industry_key") or details.get("industry_key")
        if isinstance(from_details, str) and from_details.strip():
            return from_details.strip().lower()
    # normalize and match on word boundaries to avoid accidental substring matches
    slug = (industry or "").lower()
    tokens_in_slug = re.findall(r"[a-z0-9]+", slug)
    for key, tokens in INDUSTRY_TOKEN_MAP.items():
        for token in tokens:
            t = token.lower()
            # match whole token or exact token presence in slug tokens
            if t in tokens_in_slug or re.search(rf"\b{re.escape(t)}\b", slug):
                return key
    return "other"



def default_hashtags(industry: str, niche_keywords: list[str]):
    industry_key = resolve_industry_key(industry)
    base_tag = _clean_tag(industry or "Business")
    base = [f"#{base_tag}" if base_tag else "#Brand"]
    base.extend(["#SmallBusiness", "#LocalBiz", "#BehindTheScenes", "#Tips"])
    industry_specific = INDUSTRY_HASHTAG_HINTS.get(industry_key, [])
    extra = [f"#{_clean_tag(k)}" for k in niche_keywords if isinstance(k, str) and k.strip()]
    tags = []
    seen = set()
    for t in base + industry_specific + extra:
        if not t:
            continue
        lowered = t.lower()
        if lowered not in seen:
            tags.append(t)
            seen.add(lowered)
    return tags[:12]

def to_sentence_case(s: str):
    if not s:
        return s
    return s[0].upper() + s[1:]
def naturalize_hint(hint: str, industry: str, brand_keywords: list[str]) -> str:
    """Convert a generic hint into a more natural, industry-specific suggestion."""
    hint = (hint or "").strip()
    # Create more natural conversational phrases
    if "Share a quick tip" in hint or "solves a common problem" in hint:
        options = [
            f"did you know this trick can really transform your {industry.lower()} game?",
            f"here's something that's been a total game-changer for our {industry.lower()} work!",
            f"this simple hack makes such a difference!",
            f"we discovered this recently and had to share!",
        ]
        return random.choice(options)

    if "candid look" in hint or "process, team" in hint:
        options = [
            "we're pulling back the curtain and showing you exactly how we do what we do!",
            "ever wondered what goes on behind the scenes? Here's a peek!",
            "this is what a typical day looks like for us!",
            "the real magic happens when you're not looking – check this out!",
        ]
        return random.choice(options)

    if "customer quote" in hint or "outcome they achieved" in hint:
        options = [
            "one of our amazing customers shared this and we just had to tell you!",
            "seeing results like this never gets old – here's what happened!",
            "this testimonial made our whole week!",
            "when our customers win, we ALL win!",
        ]
        return random.choice(options)

    if "Highlight one offering" in hint or "benefits, price" in hint:
        options = [
            "we're excited to share something special with you!",
            "this is one of our favorites and we think you're going to love it too!",
            "ready for something amazing?",
            "let us introduce you to something we've been working on!",
        ]
        return random.choice(options)

    if "question" in hint or "poll" in hint or "spark comments" in hint:
        options = [
            "we have a question for you and we're really curious to hear what you think!",
            "let's settle this once and for all – we need your opinion!",
            "we're polling our community – what's YOUR take?",
            "your input would be super valuable here!",
        ]
        return random.choice(options)

    if "story" in hint or "challenge" in hint or "action → result" in hint:
        options = [
            "let us tell you about something that happened recently!",
            "so this happened and we learned something important!",
            "here's a quick story we think you'll relate to!",
            "we faced a challenge recently – here's what we learned!",
        ]
        return random.choice(options)

    # Fallback: make it more conversational
    return f"we wanted to share something about {industry.lower()} with you!"


def generate_cta(pillar_name: str, tone: str, platform: str) -> str:
    """Generate a natural call-to-action based on pillar and tone."""
    ctas = {
        "Educational": {
            "friendly": ["Try this and let us know how it works!", "Have you tried something similar?",
                         "Share your tips below!", "What's worked for you?"],
            "professional": ["What strategies have you implemented?", "Share your insights below.",
                             "Connect with us to discuss further.", "What are your thoughts?"],
            "playful": ["Give it a shot! 🚀", "Your turn – what do you think?",
                        "Tag someone who needs this!", "Try it and report back! 😄"],
            "inspirational": ["What will you try today?", "Share your journey below.",
                               "Let's grow together.", "What's your next step?"],
        },
        "Behind-the-Scenes": {
            "friendly": ["What would you like to see next?", "Want more behind-the-scenes content?",
                         "Drop a 👋 if you enjoyed this peek!", "Questions? We're here!"],
            "professional": ["Want to learn more about our process?", "Connect with our team for details.",
                             "Follow us for more insights.", "Reach out with questions."],
            "playful": ["Cool, right?! 😎", "Mind. Blown. 🤯", "More of this? Say yes!",
                        "Bet you didn't know that! 🎉"],
            "inspirational": ["This is the work that matters.", "Behind every success is dedication.",
                               "What's your behind-the-scenes story?", "The process is beautiful."],
        },
        "Testimonial/Social Proof": {
            "friendly": ["What's your success story?", "Share your experience below!",
                         "We'd love to celebrate your wins too!", "Tell us how it went!"],
            "professional": ["Ready for similar results?", "Connect with us to get started.",
                             "Schedule your consultation.", "Learn how we can help you."],
            "playful": ["Your turn to shine! ⭐", "Drop your success story!", "Brag a little – we won't judge! 😉",
                        "You could be next! 🎯"],
            "inspirational": ["Your success inspires others.", "Share your story, inspire someone.",
                               "What did you overcome?", "Every journey matters."],
        },
        "Product/Offer": {
            "friendly": ["Interested? DM us!", "Check it out at the link in bio!",
                         "Want to learn more? Just ask!", "Questions? Drop them below!"],
            "professional": ["Contact us for details.", "Schedule a consultation today.",
                             "Learn more at [link].", "Reach out to discuss pricing."],
            "playful": ["Grab yours now! 🔥", "Don't sleep on this! ⚡", "You know you want it! 😄",
                        "Link in bio – go go go! 🏃"],
            "inspirational": ["Ready to transform your results?", "Take the next step today.",
                               "Your success starts here.", "Invest in yourself."],
        },
        "Engagement": {
            "friendly": ["Tell us in the comments!", "We're curious – what do YOU think?",
                         "Comment below! 👇", "Let's discuss!"],
            "professional": ["Share your perspective.", "Join the discussion.",
                             "We value your input.", "What's your take?"],
            "playful": ["Spill! We're waiting! ☕", "Comment or forever hold your peace! 😄",
                        "Don't be shy – speak up! 💬", "All answers welcome! 🎉"],
            "inspirational": ["Your voice matters.", "Contribute to the conversation.",
                               "Share your wisdom.", "Let's learn together."],
        },
        "Story": {
            "friendly": ["Have a similar story?", "Can you relate?",
                         "What happened in your situation?", "Share your story!"],
            "professional": ["What lessons have you learned?", "Share your experience.",
                             "How have you handled similar situations?", "Your insights welcome."],
            "playful": ["Top that! 😄", "Your turn – story time! 📖",
                        "What's YOUR wild story?", "Beat this! 🎭"],
            "inspirational": ["What challenge did you overcome?", "Share your transformation.",
                               "Your journey inspires.", "What did you learn?"],
        },
    }

    pillar_ctas = ctas.get(pillar_name, {})
    tone_ctas = pillar_ctas.get(tone, pillar_ctas.get("friendly", ["Let us know what you think!"]))
    return random.choice(tone_ctas)


def enhance_caption_with_ai(caption_draft: str, industry: str, tone: str, platform: str, company: str = "") -> str:
    """
    Optionally enhance a caption using OpenAI for more sophisticated, natural language.
    Falls back to the original caption if OpenAI is not available or fails.
    """
    if not USE_OPENAI_FOR_POSTS or not _openai_client:
        return caption_draft

    try:
        system_prompt = f"""You are an expert social media copywriter specializing in {platform} content.
Your task is to enhance social media captions to be more engaging, natural, and effective while maintaining the core message.
Keep the tone {tone} and preserve any hashtags provided."""

        company_context = f" for {company}" if company else ""
        user_prompt = f"""Enhance this {industry} social media caption{company_context}:

{caption_draft}

Requirements:
- Keep it natural and engaging
- Maintain the {tone} tone
- Keep it appropriate for {platform}
- Preserve all hashtags at the end
- Keep the length similar (don't make it much longer)
- Make it feel more human and less template-like

Enhanced caption:"""

        response = _openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        enhanced = response.choices[0].message.content.strip()
        has_hashtags = '#' in enhanced
        reasonable_length = 20 < len(enhanced) < 1000
        has_content = enhanced and not enhanced.isspace()

        original_hashtags = [tag for tag in caption_draft.split() if tag.startswith('#')]
        if has_hashtags and reasonable_length and has_content:
            enhanced_has_tags = any(tag in enhanced for tag in original_hashtags[:3])
            if enhanced_has_tags or len(original_hashtags) == 0:
                return enhanced

        return caption_draft

    except Exception as e:
        if os.getenv('FLASK_ENV') == 'development' or os.getenv('ALLOW_DEV_DEBUG') == '1':
            print(f"[AI Enhancement] Failed to enhance caption: {type(e).__name__}: {str(e)}")
        return caption_draft


def choose_goal_cta(goals: list[str], details: Optional[dict] = None):
    combined = list(goals or [])
    if isinstance(details, dict):
        extra_goals = details.get("goals")
        if isinstance(extra_goals, list):
            combined.extend([g for g in extra_goals if isinstance(g, str)])
    for goal in combined:
        hint = GOAL_CTA_HINTS.get(goal)
        if hint:
            return hint
    if combined:
        return "Let me know if you want details — my DMs are open."
    return "Drop a comment if this hit home 👇"


def describe_tone(tone: str):
    return {
        "friendly": ("😊", "Warm and encouraging"),
        "professional": ("💼", "Clear and confident"),
        "playful": ("✨", "Upbeat with a wink"),
        "inspirational": ("🌱", "Uplifting and mission-minded"),
    }.get((tone or "").lower(), ("💡", "Helpful and human"))


def build_opening(pillar_name: str, industry: str, keywords: list[str]):
    key_phrase = ", ".join(keywords[:2]) if keywords else industry
    hook_templates = {
        "Educational": f"Quick {industry} tip incoming ➡️",
        "Behind-the-Scenes": f"Step inside {key_phrase} with me ✨",
        "Testimonial/Social Proof": f"Proof it works: {key_phrase} wins",
        "Product/Offer": f"New drop for {industry} lovers",
        "Engagement": f"Real talk: {industry} edition",
        "Story": f"A {industry} moment you’ll feel",
    }
    return hook_templates.get(pillar_name, f"Let’s talk {industry}")


def platform_flair(platform: str):
    return PLATFORM_HINTS.get((platform or "").lower(), "Keep it short and memorable.")



def _realtor_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                        niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    area = ""
    if isinstance(details, dict):
        area = details.get("area", "") or details.get("note", "")
    if not area:
        area = _first_value(niche_keywords)
    area_phrase = area or "our market"
    audience = _first_value(niche_keywords) or "buyers"
    signature = _format_list(brand_keywords[:3]) or "smart staging and local insight"
    goal = _first_value(goals) or (isinstance(details, dict) and _first_value(details.get("goals")) or "")
    focus_phrase = f"Focus: {goal.lower()}" if goal else pillar_hint
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")

    lines = [
        f"📍 {to_sentence_case(audience)} are watching {area_phrase} inventory — here’s how we get them ready before tour day.",
        f"🗝️ {focus_phrase}. We lead with {signature} so every showing feels curated, not rushed.",
    ]
    if note:
        lines.append(f"🏡 Next up: {note.rstrip('.')} — message me for the walkthrough.")
    else:
        lines.append("🏡 Want the private tour? DM me and I’ll send the details.")
    return lines


def _restaurant_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                           niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    cuisine = ""
    if isinstance(details, dict):
        cuisine = details.get("cuisine", "")
    cuisine = cuisine or _first_value(niche_keywords) or "seasonal plates"
    spotlight = _format_list(brand_keywords[:3]) or "the chef’s latest drop"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    source = _format_list(niche_keywords[:2] or []) or "local producers"
    lines = [
        f"🍽️ Tonight’s {cuisine.lower()} spotlight: {spotlight} fresh out of the kitchen.",
        f"🌿 We source from {source} so every bite tastes like the neighborhood.",
    ]
    if note:
        lines.append(f"📅 {note.rstrip('.')} — reserve your table while there’s room.")
    else:
        lines.append("📅 Seats go fast — tap the link to book or order pickup.")
    return lines


def _retail_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                       niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    drop = _format_list(brand_keywords[:3]) or "fresh finds"
    styling = _format_list(niche_keywords[:2]) or "your everyday favorites"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    lines = [
        f"🛍️ Drop alert: {drop} just landed in-store and online.",
        f"✨ Style it with {styling} for an effortless look.",
    ]
    if note:
        lines.append(f"📦 {note.rstrip('.')} — DM your size and we’ll hold it.")
    else:
        lines.append("📦 Want first access? DM ‘LIST’ and we’ll set one aside.")
    return lines


def _fitness_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                        niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    focus = _format_list(brand_keywords[:3]) or "our go-to circuit"
    audience = _first_value(niche_keywords) or "members"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    lines = [
        f"💥 {to_sentence_case(audience)} keep asking for something that actually fits the schedule — here’s our fix.",
        f"🔥 Breakdown: {focus} with smart pacing so you can feel wins fast.",
    ]
    if note:
        lines.append(f"📆 {note.rstrip('.')} — join us and tag your workout buddy.")
    else:
        lines.append("📆 Ready to move? DM ‘GO’ and we’ll send the schedule.")
    return lines


def _coach_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                      niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    challenge = _first_value(niche_keywords) or "founders"
    framework = _format_list(brand_keywords[:3]) or "our 3-part framework"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    lines = [
        f"🧠 {to_sentence_case(challenge)} keep running into the same wall — here’s the small shift that opens it up.",
        f"🛠️ Framework: {framework}. Screenshot it for the next planning sprint.",
    ]
    if note:
        lines.append(f"📩 {note.rstrip('.')} — DM ‘WIN’ and I’ll send the worksheet.")
    else:
        lines.append("📩 Want the worksheet? DM ‘WIN’ and I’ll send it.")
    return lines


def _nonprofit_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                          niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    initiative = _format_list((details.get("goals") if isinstance(details, dict) else []) or goals or [])
    if not initiative:
        initiative = pillar_hint
    audience = _format_list(niche_keywords[:2]) or "neighbors"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    lines = [
        f"🤝 Impact focus: {initiative}.",
        f"📊 Because {audience} deserve support without the wait.",
    ]
    if note:
        lines.append(f"📆 {note.rstrip('.')} — raise your hand if you can join us.")
    else:
        lines.append("📆 Volunteer link in bio — bring a friend with you.")
    return lines


def _home_services_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                              niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    area = ""
    if isinstance(details, dict):
        area = details.get("area", "") or details.get("note", "")
    feature = _format_list(brand_keywords[:3]) or "a fresh transformation"
    tip = _format_list(niche_keywords[:2]) or "seasonal maintenance"
    lines = [
        f"🛠️ Before/after spotlight: {feature} in {area or 'the neighborhood'}.",
        f"🔍 Pro tip: keep up with {tip} so the fixes stay small.",
    ]
    lines.append("📞 Need a quote? DM your project and we’ll send options.")
    return lines


def _healthcare_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                           niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    question = _first_value(niche_keywords) or "patients"
    resource = _format_list(brand_keywords[:3]) or "our care checklist"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    lines = [
        f"🩺 Question of the week from {question}: here’s the short version.",
        f"✅ We walk you through {resource} so it’s easy to act.",
    ]
    if note:
        lines.append(f"📅 {note.rstrip('.')} — book through the link when you’re ready.")
    else:
        lines.append("📅 Need support? Book through the link and we’ll take it from there.")
    return lines


def _artisan_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                        niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    process = _format_list(brand_keywords[:3]) or "slow-made pieces"
    audience = _format_list(niche_keywords[:2]) or "people who love intentional pieces"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    lines = [
        f"🎨 Studio moment: {process} coming to life on the bench.",
        f"👐 Crafted for {audience} who want something that lasts.",
    ]
    if note:
        lines.append(f"📦 {note.rstrip('.')} — DM to claim yours before the batch is gone.")
    else:
        lines.append("📦 Limited batch — DM ‘RESERVE’ and I’ll hold one for you.")
    return lines


def _generic_body_lines(pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                        niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    differentiator = _format_list(brand_keywords[:3]) or "what makes us different"
    audience = _format_list(niche_keywords[:2]) or "your people"
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    lines = [
        f"📌 Focus: {pillar_hint}",
        f"✨ We lean on {differentiator} so {audience} get the win fast.",
    ]
    if note:
        lines.append(f"📬 {note.rstrip('.')} — reply if you want more.")
    else:
        lines.append("📬 Curious? Drop a comment and I’ll share more.")
    return lines


BODY_BUILDERS = {
    "realtor": _realtor_body_lines,
    "restaurant": _restaurant_body_lines,
    "retail": _retail_body_lines,
    "fitness": _fitness_body_lines,
    "coach": _coach_body_lines,
    "nonprofit": _nonprofit_body_lines,
    "home_services": _home_services_body_lines,
    "healthcare": _healthcare_body_lines,
    "artisan": _artisan_body_lines,
}


def build_body_lines(industry_key: str, pillar_name: str, pillar_hint: str, brand_keywords: list[str],
                     niche_keywords: list[str], details: Optional[dict], goals: list[str], company: str) -> list[str]:
    builder = BODY_BUILDERS.get(industry_key, _generic_body_lines)
    lines = builder(pillar_name, pillar_hint, brand_keywords, niche_keywords, details, goals, company)
    return [line.strip() for line in lines if line and line.strip()]


def build_signature_line(company: str, brand_keywords: list[str], industry: str) -> str:
    keywords_line = _format_list(brand_keywords[:3])
    # Prefer a short "From Company." signature to match tests that expect that phrasing.
    if company and keywords_line:
        return f"From {company}. • {keywords_line}"
    if company:
        return f"From {company}."
    if keywords_line:
        return keywords_line
    return industry


def build_industry_context(industry: str, brand_keywords: list[str], niche_keywords: list[str],
                           details: Optional[dict], goals: list[str], company: str = "") -> dict:
    industry_key = resolve_industry_key(industry, details)
    primary_goal = _first_value(goals) or (isinstance(details, dict) and _first_value(details.get("goals")) or "")
    focus = _format_list(brand_keywords[:3])
    audience = _format_list(niche_keywords[:2])
    note = ""
    if isinstance(details, dict):
        note = details.get("note", "")
    context = {
        "industry_key": industry_key,
        "focus": focus,
        "audience": audience,
        "primary_goal": primary_goal,
        "company": company,
    }
    if isinstance(details, dict):
        context.update({k: v for k, v in details.items() if k not in {"industry_key", "_industry_key"}})
    if note:
        context["highlight"] = note
    return {k: v for k, v in context.items() if v}


def make_caption(industry: str, tone: str, pillar_name: str, pillar_hint: str,
                 platform: str, brand_keywords: list[str], hashtags: list[str], goals: list[str], company: str = "",
                 niche_keywords: Optional[list[str]] = None, details: Optional[dict] = None):
    niche_keywords = niche_keywords or []
    details = details or {}
    tone_icon, tone_desc = describe_tone(tone)
    # prefer niche keywords for the hook if available
    opening = build_opening(pillar_name, industry, niche_keywords or brand_keywords)
    industry_key = resolve_industry_key(industry, details)
    # Naturalize the pillar hint so builders get conversational language
    natural_hint = naturalize_hint(pillar_hint or "", industry, brand_keywords)
    # Capitalize first letter of natural hint if needed
    if natural_hint and natural_hint[0].islower():
        natural_hint = natural_hint[0].upper() + natural_hint[1:]
    body_lines = build_body_lines(industry_key, pillar_name, natural_hint, brand_keywords, niche_keywords, details, goals, company)
    signature_line = build_signature_line(company, brand_keywords, industry)
    flair = platform_flair(platform)
    cta_line = choose_goal_cta(goals, details)

    lines = [f"{tone_icon} {opening}"]
    lines.extend(body_lines)
    if signature_line:
        lines.append(signature_line)
    lines.append(f"{tone_desc} • {flair}")
    lines.append(cta_line)

    caption = "\n\n".join(line for line in lines if line and line.strip())
    # platform-specific hashtag limits
    p = (platform or "").lower()
    if p == "twitter":
        tags = " ".join(hashtags[:3])
    elif p == "linkedin":
        tags = " ".join(hashtags[:5])
    elif p == "instagram":
        tags = " ".join(hashtags[:12])
    elif p == "facebook":
        tags = " ".join(hashtags[:8])
    else:
        tags = " ".join(hashtags[:8])

    return f"{caption}\n\n{tags}"

def image_prompt(industry: str, pillar_name: str, brand_keywords: list[str], company: str = ""):
    kw = ", ".join(brand_keywords) if brand_keywords else "on-brand colors"
    company_part = f"Company: {company}. " if company else ""
    return (f"High-quality photo for social post. {company_part}Industry: {industry}. "
            f"Content pillar: {pillar_name}. Style: natural light, minimal background, {kw}.")

def make_reel_plan(industry: str, pillar_name: str, brand_keywords: list[str], tone: str, company: str = "", reel_style: Optional[str] = None, goals: Optional[list[str]] = None, niche_keywords: Optional[list[str]] = None, length_seconds: int = 30, production_tier: str = "solo", details: Optional[dict] = None):
    # structured reel plan; tailor suggestions by industry and an optional `reel_style` preference
    style = (reel_style or "Face-camera tips")
    goals = goals or []
    niche_keywords = niche_keywords or []
    length_seconds = int(length_seconds or 30)

    # industry-specific modifiers to make outputs more relevant to the professional
    industry_key = resolve_industry_key(industry, details)
    industry_mods = {
        "realtor": {
            "cta": "Schedule a showing or DM for details.",
            "thumb_extra": "Show a room or exterior with bold feature text",
            "hook_pfx": "House tip:"
        },
        "restaurant": {
            "cta": "Reserve a table or check the menu link.",
            "thumb_extra": "Close-up of dish with appetizing colors",
            "hook_pfx": "Chef's secret:"
        },
        "retail": {
            "cta": "Shop now or visit us in-store.",
            "thumb_extra": "Product shot with clear price/text",
            "hook_pfx": "New in:"
        },
        "fitness": {
            "cta": "Try this move & tag us in your video.",
            "thumb_extra": "Action shot with energetic typography",
            "hook_pfx": "Quick workout:"
        },
        "artisan": {
            "cta": "Shop the collection or visit the studio.",
            "thumb_extra": "Close-up of hands at work",
            "hook_pfx": "Behind the craft:"
        },
        "coach": {
            "cta": "Book a consult or grab the free worksheet.",
            "thumb_extra": "Headshot with clear value statement",
            "hook_pfx": "Quick tip:"
        },
        "nonprofit": {
            "cta": "Learn how to help or donate today.",
            "thumb_extra": "Impact photo with short stat overlay",
            "hook_pfx": "Impact story:"
        },
        "home_services": {
            "cta": "Book an estimate or ask for a quote.",
            "thumb_extra": "Before/after split with clear label",
            "hook_pfx": "Before & after:"
        },
        "healthcare": {
            "cta": "Book a consult or learn more on our site.",
            "thumb_extra": "Friendly staff or clinic photo with clear text",
            "hook_pfx": "Health tip:"
        }
    }

    mods = industry_mods.get(industry_key, {"cta": "Comment / DM / Link in bio", "thumb_extra": "Clean bold text, subject centered", "hook_pfx": "Quick tip:"})

    # pick some hooks based on style
    hooks_map = {
        "Face-camera tips": [
            "3 mistakes costing you customers 👇",
            "Try this before your next post…",
            "The 30-second fix for engagement"
        ],
        "Property b-roll + captions": [
            f"Inside this {industry} feature in 30s 🏡",
            "3 features you’ll miss if you scroll fast…",
            "Before/After: tiny changes, big feel"
        ],
        "Product b-roll + captions": [
            f"Check out this {pillar_name} in 30s ✨",
            "3 reasons customers love this…",
            "Quick tour: what makes it special"
        ],
        "Local hotspot montage": [
            f"Spend a perfect morning in {pillar_name} ☀️",
            "Hidden gem you’ve gotta try…",
            "Locals know this trick 🤫"
        ],
        "Story + before/after": [
            "From idea → launch in 30s",
            "We almost gave up—then this happened",
            "Tiny change → big result"
        ],
        "Workout montage": [
            "Quick 3-move sequence to level up your routine",
            "Try this superset for max results",
            "Short challenge: do 3 rounds"
        ]
    }

    # allow fallback to a style-agnostic set if exact match not found
    chosen_hooks = hooks_map.get(style) or hooks_map.get("Face-camera tips")
    if not chosen_hooks:
        chosen_hooks = hooks_map["Face-camera tips"]
    # produce ranked hooks (industry-prefixed variants) and alternates
    ranked_hooks = [f"{mods.get('hook_pfx','Quick tip:')} {h}" for h in chosen_hooks]
    # add short alternates
    for h in chosen_hooks[:2]:
        short = h.replace('…', '').split(' - ')[0].strip()
        if short and short not in ranked_hooks:
            ranked_hooks.append(short)
    hook = ranked_hooks[0]

    # script beats: timestamps for the requested length_seconds
    # use a deterministic allocation that guarantees strictly increasing boundaries
    total = max(10, int(length_seconds))
    # percentage allocation for Hook, Problem, Tip, Example, CTA
    slots = [0.12, 0.25, 0.35, 0.18, 0.10]
    # compute float cut points then convert to integer seconds while ensuring monotonicity
    cut_points = []
    acc = 0.0
    for pct in slots:
        acc += pct
        cut_points.append(acc * total)
    bounds = []
    prev = 0
    for i, cp in enumerate(cut_points):
        # round cut point but ensure it's at least prev+1 except for the last which is total
        if i == len(cut_points) - 1:
            end = total
        else:
            end = max(prev + 1, int(round(cp)))
            # safety: don't let end exceed total - remaining beats
            remaining = len(cut_points) - 1 - i
            if end > total - remaining:
                end = total - remaining
        start = prev
        # ensure strictly increasing
        if end <= start:
            end = start + 1
        bounds.append((start, end))
        prev = end

    problem_line = "A common pain point your audience has and why it matters."
    if goals:
        problem_line = f"Pain point related to: {', '.join(goals[:2])}."
    tip_line = "One actionable tip the viewer can try right away."
    example_line = f"Quick example or result — mention {company} if relevant." if company else "Quick example or result to make it real."
    cta_line = mods.get('cta')

    beats = [
        {"start_s": bounds[0][0], "end_s": bounds[0][1], "osd": "Hook", "line": hook},
        {"start_s": bounds[1][0], "end_s": bounds[1][1], "osd": "Problem", "line": problem_line},
        {"start_s": bounds[2][0], "end_s": bounds[2][1], "osd": "Tip", "line": tip_line},
        {"start_s": bounds[3][0], "end_s": bounds[3][1], "osd": "Example", "line": example_line},
        {"start_s": bounds[4][0], "end_s": bounds[4][1], "osd": "CTA", "line": cta_line}
    ]

    # combine style-based shot guidance with industry-specific suggestions
    shot_map = {
        "Face-camera tips": [
            "Front-facing A-roll, eye-level, natural light",
            "Cutaways: screen recording, product close-up",
            "End with CTA text overlay"
        ],
        "Property b-roll + captions": [
            "Exterior wide → entry → kitchen → feature highlight",
            "Quick pans, 0.8x speed ramp between rooms",
            "On-screen captions for each highlight"
        ],
        "Product b-roll + captions": [
            "Wide shot → detail close-ups → demo",
            "Match edits to beat; short clips per feature",
            "Add caption overlays for key specs"
        ],
        "Local hotspot montage": [
            "Sign → interior → hero item → smiling staff → crowd",
            "Match cuts to beat; 0.5s–1.0s per clip",
            "End with text: name + location"
        ],
        "Story + before/after": [
            "Talking head intro",
            "B-roll: before clip/photos",
            "After reveal with text overlay"
        ],
        "Workout montage": [
            "Demonstration A-roll",
            "Close-ups on form",
            "Speed ramps and finishing CTA"
        ]
    }

    style_shots = shot_map.get(style, ["Talking head + a few cutaways, end with CTA"])
    # add industry-specific shot hints to the start of the list where helpful
    industry_shots = []
    if industry_key == 'realtor':
        industry_shots = ["Start with exterior wide, show hero room, highlight value props"]
    elif industry_key == 'restaurant':
        industry_shots = ["Close-up of dish, plating, hands prepping"]
    elif industry_key == 'fitness':
        industry_shots = ["Full-body demo shot, side view for form"]
    elif industry_key == 'artisan':
        industry_shots = ["Hands-on process close-ups, product reveal"]

    # convert simple descriptions into structured shots aligned to beats
    shot_list = []
    combined_shots = industry_shots + style_shots
    for idx, b in enumerate(beats):
        base = combined_shots[idx % max(1, len(combined_shots))]
        shot_list.append({
            "start_s": b["start_s"],
            "end_s": b["end_s"],
            "shot_type": base,
            "duration_s": b["end_s"] - b["start_s"],
            "notes": "Match cuts to spoken lines; stable framing; consider jump cuts for energy."
        })

    hashtags_all = default_hashtags(industry, brand_keywords + niche_keywords)
    hashtags = {"primary": hashtags_all[:3], "optional": hashtags_all[3:8]}
    thumb_prompt = f"Portrait thumbnail: {industry} • {style}. {mods.get('thumb_extra')}"

    # generate SRT text from beats
    def fmt_ts(s):
        ms = int(s * 1000)
        h = ms // 3600000
        ms -= h * 3600000
        m = ms // 60000
        ms -= m * 60000
        sec = ms // 1000
        ms = ms % 1000
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    srt_lines = []
    for i, b in enumerate(beats, start=1):
        start = fmt_ts(b["start_s"])
        end = fmt_ts(b["end_s"])
        text = b["line"]
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    srt_text = "\n".join(srt_lines)

    # music suggestion mapping by tone
    mood_map = {
        "friendly": "acoustic upbeat, 90-110 BPM",
        "professional": "minimal ambient, 60-80 BPM",
        "playful": "funky pop, 100-125 BPM",
        "inspirational": "uplifting cinematic, 70-100 BPM"
    }
    music = mood_map.get(tone.lower(), "neutral upbeat, 90 BPM")

    cta_variants = [{"type": "primary", "text": cta_line}, {"type": "soft", "text": "Learn more / link in bio"}, {"type": "engage", "text": "Comment your favorite"}]

    return {
        "style": style,
        "length_seconds": length_seconds,
        "ranked_hooks": ranked_hooks,
        "hook": hook,
        "beats": beats,
        "script_beats": [b.get('line') for b in beats],
        "shot_list": shot_list,
        "on_screen_text": [b.get('osd') for b in beats],
        "hashtags": hashtags,
        "cta": cta_line,
        "cta_variants": cta_variants,
        "thumbnail_prompt": thumb_prompt,
        "srt": srt_text,
        "music_suggestion": music,
        "production_tier": production_tier
    }

def unsplash_link(industry: str, pillar_name: str):
    q = f"{industry} {pillar_name}".replace(" ", "+")
    return f"https://source.unsplash.com/featured/?{q}"

def rolling_pillars():
    while True:
        for name, hint in PILLARS_BY_DEFAULT:
            yield (name, hint)

def generate_posts(days: int, start_day, industry: str, tone: str,
                   platforms: list[str], brand_keywords: list[str],
                   include_images: bool, niche_keywords: list[str], goals: list[str], company: str = "", details: Optional[dict] = None):
    posts = []
    pillar_stream = rolling_pillars()
    hashtags = default_hashtags(industry, niche_keywords)

    for i in range(days):
        day = start_day + timedelta(days=i)
        pillar_name, pillar_hint = next(pillar_stream)
        for p in platforms:
            caption = make_caption(
                industry=to_sentence_case(industry.strip() or "Business"),
                tone=tone,
                pillar_name=pillar_name,
                pillar_hint=pillar_hint,
                platform=p,
                brand_keywords=brand_keywords,
                hashtags=hashtags,
                goals=goals,
                company=company,
                niche_keywords=niche_keywords,
                details=details,
            )
            iprompt = image_prompt(industry, pillar_name, brand_keywords, company)
            img_url = unsplash_link(industry, pillar_name) if include_images else None

            reel_obj = None
            if p.lower() in ["instagram", "tiktok", "short_video"]:
                reel_style = None
                try:
                    reel_style = (details or {}).get('reel_style')
                except Exception:
                    reel_style = None
                reel_length = None
                production_tier = None
                try:
                    reel_length = int((details or {}).get('reel_length') or 30)
                except Exception:
                    reel_length = 30
                try:
                    production_tier = (details or {}).get('production_tier') or 'solo'
                except Exception:
                    production_tier = 'solo'
                reel_obj = make_reel_plan(
                    industry,
                    pillar_name,
                    brand_keywords,
                    tone,
                    company,
                    reel_style,
                    goals=goals,
                    niche_keywords=niche_keywords,
                    length_seconds=reel_length,
                    production_tier=production_tier,
                    details=details,
                )

            posts.append({
                "date": day.isoformat(),
                "day_index": i + 1,
                "platform": p,
                "pillar": pillar_name,
                "caption": caption,
                "image_prompt": iprompt,
                "image_url": img_url,
                "reel": reel_obj
            })
    return posts
