"""Lightweight voice engine shims for tests.

These implementations avoid network calls and match the contracts expected by
unit tests. All generation is Gemini-first; OpenAI is unused except where tests
patch a client directly.
"""
from __future__ import annotations
import json
import os
from typing import Any, List, Protocol


class UserProfile(Protocol):
    """Protocol defining the expected interface for user profiles."""
    industry: str
    business_name: str
    brand_voice: str


try:  # Prefer new google.genai; keep optional
    import google.genai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore


class VoiceEngine:
    def __init__(self):
        # Tests patch genai.GenerativeModel; otherwise keep None
        self.model = None
        self.model = self._make_model()

    def _make_model(self):
        if not genai:
            return None

        api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        # Legacy/test path first so mocks of GenerativeModel are honored
        if hasattr(genai, "GenerativeModel"):
            try:
                return genai.GenerativeModel("gemini-pro")
            except Exception:
                return None

        # New google.genai client path
        if hasattr(genai, "Client"):
            try:
                client = genai.Client(api_key=api_key) if api_key else genai.Client()
                if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                    class _ModelAdapter:
                        def __init__(self, client_ref):
                            self._client = client_ref
                        def generate_content(self, contents):
                            return self._client.models.generate_content(
                                model="gemini-1.5-flash", contents=contents
                            )
                    return _ModelAdapter(client)
            except Exception:  # pragma: no cover
                return None

        return None

    def analyze_style(self, raw_text: str) -> dict[str, Any]:
        """Return style_summary + examples, handling errors gracefully."""
        try:
            response = self.model.generate_content(raw_text) if self.model else None
            text_response = response.text if response else ""
            parsed = json.loads(text_response) if text_response else {}
            style_summary = parsed.get("style_summary") or parsed.get("style_guide") or "Default professional tone (Error during analysis)."
            examples = parsed.get("examples") or []
            return {
                "style_summary": style_summary,
                "style_guide": parsed.get("style_guide") or style_summary,
                "examples": examples,
            }
        except Exception:
            return {"style_summary": "Error during analysis", "style_guide": "Error during analysis", "examples": []}

    def generate_post(self, user_profile: Any, topic: str, platform: str = "LinkedIn") -> str:
        """Generate copy using optional few-shot examples."""
        style_guide = getattr(user_profile, "style_guide", "Professional tone")
        examples: List[str] = []
        if hasattr(user_profile, "get_examples"):
            try:
                examples = list(user_profile.get_examples() or [])
            except Exception:
                examples = []

        prompt_parts = [
            f"Role: You are an expert Social Media Manager for {platform}.",
            f"Topic: {topic}",
            f"Style guide: {style_guide}",
        ]
        if examples:
            prompt_parts.append("Few-shot examples (mimic this writing style):")
            for ex in examples[:3]:
                prompt_parts.append(f"- {ex}")
        prompt_parts.append("Return final post copy only.")
        prompt = "\n".join(prompt_parts)

        if not self.model:
            return "Generated content"
        try:
            response = self.model.generate_content(prompt)
            return response.text if response else "Generated content"
        except Exception:
            return "Generated content"

    def generate_expert_content(
        self,
        user_profile: UserProfile | Any,
        topic: str,
        task_type: str = "post",
        platform: str = "LinkedIn",
        **context
    ) -> str:
        """Generate content based on task type with comprehensive brand profile context.
        
        This method builds a highly structured prompt that incorporates all available
        brand profile data to ensure generated content matches the user's voice and is
        immediately copy-paste ready for the target platform.
        
        Args:
            user_profile: User profile with comprehensive brand data
            topic: Content topic
            task_type: Type of content to generate (post, email, ad, etc.)
            platform: Target platform for the content
            **context: Additional context from dynamic inputs (ad_objective, target_audience, etc.)
            
        Returns:
            Generated content string formatted for the specific platform/task type
        """
        # Extract comprehensive profile data using safe getters
        industry = getattr(user_profile, "industry", "general")
        business_name = getattr(user_profile, "business_name", "Your Business")
        brand_voice = getattr(user_profile, "brand_voice", "Professional and friendly")
        target_audience = getattr(user_profile, "target_audience", "")
        key_offer = getattr(user_profile, "key_offer", "")
        voice_rules = getattr(user_profile, "voice_rules", "")
        
        # Get structured data from JSON fields
        writing_samples = []
        brand_keywords = []
        niche_keywords = []
        customers = []
        scraped_meta = {}
        
        if hasattr(user_profile, 'get_writing_samples'):
            writing_samples = user_profile.get_writing_samples()
        if hasattr(user_profile, 'get_brand_keywords'):
            brand_keywords = user_profile.get_brand_keywords()
        if hasattr(user_profile, 'get_niche_keywords'):
            niche_keywords = user_profile.get_niche_keywords()
        if hasattr(user_profile, 'get_customers'):
            customers = user_profile.get_customers()
        if hasattr(user_profile, 'get_scraped_meta'):
            scraped_meta = user_profile.get_scraped_meta()
        
        # Build comprehensive, structured prompt
        prompt_parts = [
            "# CONTENT GENERATION REQUEST",
            "",
            "## Brand Context",
            f"Business: {business_name}",
            f"Industry: {industry}",
            f"Brand Voice: {brand_voice}",
        ]
        
        if target_audience:
            prompt_parts.append(f"Target Audience: {target_audience}")
        if key_offer:
            prompt_parts.append(f"Key Offering: {key_offer}")
        
        # Add customer segments (from scraper or manual input)
        if customers:
            prompt_parts.extend([
                "",
                "## Customer Segments",
                "Key audiences: " + ", ".join(customers[:5])
            ])
        
        # Add brand keywords for consistent terminology
        if brand_keywords:
            prompt_parts.extend([
                "",
                "## Brand Keywords",
                "Use these terms naturally: " + ", ".join(brand_keywords[:10])
            ])
        
        # Add niche keywords for specificity
        if niche_keywords:
            prompt_parts.extend([
                "",
                "## Niche Keywords",
                "Industry-specific terms: " + ", ".join(niche_keywords[:10])
            ])
        
        # Add scraped metadata insights if available
        if scraped_meta:
            if scraped_meta.get('key_customers'):
                prompt_parts.append(f"Customer Profile: {scraped_meta['key_customers']}")
            if scraped_meta.get('business_name'):
                prompt_parts.append(f"Official Name: {scraped_meta['business_name']}")
        
        # Add voice rules/constraints
        if voice_rules:
            prompt_parts.extend([
                "",
                "## Writing Constraints",
                voice_rules
            ])
        
        # Add writing samples for style matching
        if writing_samples:
            prompt_parts.extend([
                "",
                "## Voice Examples",
                "Match the style, tone, and structure of these examples:"
            ])
            for i, sample in enumerate(writing_samples[:3], 1):  # Limit to 3 samples
                prompt_parts.append(f"\nExample {i}:")
                prompt_parts.append(sample)
        
        # Add task-specific requirements
        prompt_parts.extend([
            "",
            "## Task Requirements",
            f"Content Type: {task_type}",
            f"Platform: {platform}",
            f"Topic: {topic}",
        ])
        
        # Add context from dynamic inputs
        if context.get('ad_objective'):
            prompt_parts.append(f"Campaign Goal: {context['ad_objective']}")
        if context.get('target_audience'):
            prompt_parts.append(f"Specific Audience: {context['target_audience']}")
        if context.get('tone_modifier'):
            prompt_parts.append(f"Tone Adjustment: {context['tone_modifier']}")
        if context.get('cta'):
            prompt_parts.append(f"Call-to-Action: {context['cta']}")
        if context.get('mood'):
            prompt_parts.append(f"Mood/Vibe: {context['mood']}")
        if context.get('video_length'):
            prompt_parts.append(f"Video Length: {context['video_length']} seconds")
        
        # Proposal-specific context
        if context.get('proposal_type'):
            prompt_parts.append(f"Proposal Type: {context['proposal_type']}")
        if context.get('recipient'):
            prompt_parts.append(f"Recipient: {context['recipient']}")
        if context.get('proposal_company'):
            prompt_parts.append(f"Prospect: {context['proposal_company']}")
        if context.get('proposal_contact_name'):
            prompt_parts.append(f"Contact: {context['proposal_contact_name']}")
        if context.get('proposal_contact_email'):
            prompt_parts.append(f"Contact Email: {context['proposal_contact_email']}")
        if context.get('proposal_industry'):
            prompt_parts.append(f"Prospect Industry: {context['proposal_industry']}")
        if context.get('proposal_goals'):
            prompt_parts.append(f"Objectives: {context['proposal_goals']}")
        if context.get('proposal_scope'):
            prompt_parts.append(f"Scope Summary: {context['proposal_scope']}")
        if context.get('proposal_timeline'):
            prompt_parts.append(f"Timeline: {context['proposal_timeline']}")
        if context.get('proposal_budget'):
            prompt_parts.append(f"Budget Range: {context['proposal_budget']}")
        if context.get('proposal_audience'):
            prompt_parts.append(f"Primary Audience: {context['proposal_audience']}")
        if context.get('proposal_value_prop'):
            prompt_parts.append(f"Value Proposition: {context['proposal_value_prop']}")
        if context.get('proposal_keywords'):
            prompt_parts.append(f"Positioning Keywords: {', '.join(context['proposal_keywords'])}")
        if context.get('key_benefits'):
            prompt_parts.append(f"Key Benefits: {', '.join(context['key_benefits'])}")
        if context.get('budget_range'):
            prompt_parts.append(f"Budget Range: {context['budget_range']}")
        if context.get('proposal_primary_cta'):
            prompt_parts.append(f"Primary CTA: {context['proposal_primary_cta']}")
        
        # Review reply-specific context
        if context.get('review_source'):
            prompt_parts.append(f"Review Platform: {context['review_source']}")
        if context.get('star_rating'):
            prompt_parts.append(f"Star Rating: {context['star_rating']}/5")
        if context.get('sentiment'):
            prompt_parts.append(f"Sentiment: {context['sentiment']}")
        if context.get('issue_type'):
            prompt_parts.append(f"Issue Type: {context['issue_type']}")
        if context.get('desired_tone'):
            prompt_parts.append(f"Desired Tone: {context['desired_tone']}")
        if context.get('follow_up_action'):
            prompt_parts.append(f"Follow-up Action: {context['follow_up_action']}")
        
        # Blog post-specific context
        if context.get('post_type'):
            prompt_parts.append(f"Blog Post Type: {context['post_type']}")
        if context.get('desired_length'):
            length_map = {'short': '400-600 words', 'medium': '750-1000 words', 'long': '1200-1500 words'}
            prompt_parts.append(f"Target Length: {length_map.get(context['desired_length'], 'medium')}")
        if context.get('audience'):
            prompt_parts.append(f"Target Audience: {context['audience']}")
        if context.get('seo_keywords'):
            prompt_parts.append(f"SEO Keywords: {', '.join(context['seo_keywords'])}")
        
        # Email-specific context
        if context.get('email_subtype'):
            subtype_label = 'Newsletter' if context['email_subtype'] == 'newsletter' else 'Standard Email'
            prompt_parts.append(f"Email Type: {subtype_label}")
        if context.get('email_context'):
            prompt_parts.extend([
                "",
                "## Existing Email to Respond To",
                "Generate a suggested response to this email:",
                context['email_context'],
                ""
            ])
        
        # Add format-specific output instructions
        prompt_parts.extend([
            "",
            "## Output Format",
            self._get_output_format_instructions(task_type, platform),
            "",
            "Generate content that:",
            "1. Perfectly matches the brand voice and examples provided",
            "2. Is immediately copy-paste ready for the target platform",
            "3. Incorporates all constraints and requirements",
            "4. Sounds authentically like the brand",
            "5. Is optimized for engagement on the specified platform"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Return fallback if no model available
        if not self.model:
            return f"Generated {task_type} content for {platform}"
        
        try:
            # Generate content with structured prompt
            response = self.model.generate_content(prompt)
            generated_content = response.text if response else f"Generated {task_type} content"
            
            # Post-process to ensure clean, copy-paste-ready output
            return self._clean_generated_content(generated_content, task_type, platform)
        except Exception as e:
            # Log error and return user-friendly message
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                return "Error: Request timed out. Please try again."
            elif "rate limit" in error_msg or "quota" in error_msg:
                return "Error: API rate limit reached. Please try again in a moment."
            elif "api key" in error_msg or "auth" in error_msg:
                return "Error: API authentication failed. Please check configuration."
            else:
                return f"Error: Failed to generate content. Please try again."
    
    def _get_output_format_instructions(self, task_type: str, platform: str) -> str:
        """Get platform and task-specific formatting instructions."""
        format_map = {
            'post': {
                'LinkedIn': "Write a professional LinkedIn post with a strong hook, clear paragraphs, and appropriate line breaks. Include 3-5 relevant hashtags at the end.",
                'Instagram': "Write an engaging Instagram caption with emojis where appropriate. Include line breaks for readability and 10-15 relevant hashtags at the end.",
                'Facebook': "Write a conversational Facebook post that encourages engagement. Use a friendly tone with clear paragraphs.",
                'Twitter': "Write a concise, engaging tweet under 280 characters. Make every word count."
            },
            'ad': {
                'default': "Write compelling ad copy with: 1) Attention-grabbing headline, 2) Clear benefit statement, 3) Strong call-to-action. Keep it concise and action-oriented."
            },
            'email': {
                'default': "Write a professional email with: 1) Compelling subject line (on first line), 2) Personalized greeting, 3) Clear body with value proposition, 4) Strong call-to-action, 5) Professional signature."
            },
            'script': {
                'default': "Write a video script with: 1) Hook (first 3 seconds), 2) Main content with clear sections, 3) Call-to-action. Include [Visual cues] in brackets where helpful."
            },
            'blog': {
                'default': "Write a blog post with: 1) SEO-optimized title, 2) Engaging introduction, 3) Well-structured sections with subheadings, 4) Conclusion with call-to-action."
            },
            'blog_post': {
                'default': "Write a comprehensive blog post with: 1) Three SEO-optimized title options, 2) Meta description (150-160 chars), 3) Outline with H2 headings, 4) Full article (750-1200 words), 5) Strong call-to-action."
            },
            'caption': {
                'default': "Write an engaging image caption that describes what's shown, adds context, and includes relevant hashtags."
            },
            'review': {
                'default': "Write a warm, professional response that: 1) Thanks the reviewer, 2) Acknowledges specific feedback, 3) Reinforces brand values."
            },
            'review_reply': {
                'default': "Write a professional review response that: 1) Acknowledges and thanks the reviewer, 2) Addresses specific points mentioned, 3) Offers remedy or next steps if needed, 4) Maintains brand voice. Keep it concise and genuine."
            },
            'proposal': {
                'default': "Write a professional business proposal with: 1) Three compelling title options, 2) Executive summary (3-4 bullet points), 3) Key benefits (bullet list), 4) Clear call-to-action, 5) Compelling subject line for outreach."
            },
            'newsletter': {
                'default': "Write a newsletter with: 1) Catchy subject line, 2) Personal greeting, 3) Main content sections with headings, 4) Clear call-to-action."
            }
        }
        
        if task_type in format_map:
            if isinstance(format_map[task_type], dict):
                return format_map[task_type].get(platform, format_map[task_type].get('default', ''))
            return format_map[task_type]
        
        return "Provide well-formatted, engaging content ready to use immediately."
    
    def _clean_generated_content(self, content: str, task_type: str, platform: str) -> str:
        """Clean and format generated content for immediate copy-paste use."""
        if not content or content.startswith("Error"):
            return content
        
        # Remove markdown formatting artifacts that shouldn't be in final output
        content = content.strip()
        
        # Remove common AI preambles
        preambles_to_remove = [
            "Here's a ", "Here is a ", "Here's the ", "Here is the ",
            "I've created ", "I've written ", "I have created ", "I have written "
        ]
        for preamble in preambles_to_remove:
            if content.lower().startswith(preamble.lower()):
                # Find the colon or newline after preamble
                idx = content.find(':')
                if idx > 0 and idx < 100:  # Reasonable preamble length
                    content = content[idx+1:].strip()
                    break
        
        # Remove markdown code blocks if present
        if content.startswith('```') and content.endswith('```'):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]).strip()
        
        return content


class VoiceAnalyzer:
    """Minimal analyzer shim used by tests."""

    def __init__(self, *args, **kwargs):
        pass

    def analyze(self, text: str):
        tokens = (text or "").split()
        return {
            "style_guide": "Tone: professional. Sentence length: medium. Avoid coaching language.",
            "examples": tokens[:3],
        }
