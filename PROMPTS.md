# Prompt Templates and Few-Shot Examples

This file contains recommended prompts and a few-shot set of examples for using the Gemini API to generate short social captions and review responses.

## Caption generation (single-brief -> N variants)

System instruction (recommended):
"You are a concise, creative social media copywriter. Produce captions optimized for the requested platform and tone. Return only the caption text with no additional commentary. Keep CTAs clear and help the user convert."

User prompt template:
"Generate {n} caption variants for {platform} in a {tone} tone.
Industry: {industry}.
Pillar: {pillar_name} — {pillar_hint}.
Company: {company}.
Goals: {goals}.
Brand keywords: {brand_keywords}.
Niche keywords: {niche_keywords}.
Constraints: Max 2200 characters for Instagram, under 280 for Twitter/X; include 1 short CTA; avoid URLs. Return each variant as plain text only."

Example few-shot (include at most 1-2 short examples in the user message if you want consistent style):

Example 1 input:
- industry: "bakery"
- platform: "instagram"
- tone: "friendly"
- pillar_name: "Behind-the-Scenes"
- pillar_hint: "Show a candid look at your process, team, or workspace."
- brand_keywords: "small-batch, sourdough"

Desired outputs (three variants):
1) "Fresh from our ovens: today's small-batch sourdough is crisp on the outside, pillowy inside, and made with love. Pop in today or order online for pickup. 🥖 #sourdough #smallbatch"
2) "Ever wondered how our crust gets so crunchy? It starts with slow fermentation and a lot of heart. Come by for a loaf and taste the difference. ❤️ #bakery #artisan"
3) "This morning's batch was worth waking up for—hand-shaped loaves, fermented overnight, baked to golden perfection. Grab one before they’re gone! 🕘"

Notes on temperature and `n`:
- Use temperature ≈ 0.6–0.9 for creative caption variants.
- Use `n` (or request multiple completions) to get several distinct outputs in one call.
- When high factual precision is required (e.g., legal claims), use lower temperature and post-validate.

## Review-response prompt (few-shot)

System instruction:
"You are a customer-support assistant that writes empathetic, human-sounding responses to customer reviews. Keep the reply to 1–3 sentences. For negative reviews, apologize and offer a channel to make it right. For positive reviews, thank and invite repeat business."

User prompt template:
"Generate a {tone} response to this review for {company}:

Review: {review_text}

Return a 1–3 sentence reply."

Few-shot example:

Input review: "Loved the pastries, but my coffee was cold."
Tone: apologetic
Output: "Thanks for the heads-up — we're glad you enjoyed the pastries but we're sorry your coffee wasn't hot. We'd love to make it right; please DM us and we'll offer a replacement on your next visit."

## Safety and moderation
- Always run moderation on user-provided content before sending to the model if you accept open text inputs from untrusted users.
- If moderation flags content, fall back to a safe template-based response.

## Suggestions for engineering
- Cache prompt templates and model responses for identical inputs to reduce cost.
- Rate-limit the generation endpoint for anonymous requests; encourage sign-in for unlimited generation.
- Store the temperature and model in environment variables (e.g., GEMINI_MODEL, OPENAI_TEMP).

## File usage
- `PROMPTS.md` is a living doc; keep it in the repository to sync prompt changes with code changes.
- When adjusting few-shot examples, prefer short examples (1–2) to avoid long prompts.
