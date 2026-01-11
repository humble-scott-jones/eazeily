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
        platform: str = "LinkedIn"
    ) -> str:
        """Generate content based on task type with error handling for timeout scenarios.
        
        Note: Timeout protection is handled by the calling code (frontend/service layer).
        This method provides appropriate error messages when timeout or other errors occur.
        
        Args:
            user_profile: User profile with brand voice settings (expects industry,
                         business_name, brand_voice attributes but handles missing attrs)
            topic: Content topic
            task_type: Type of content to generate (post, email, etc.)
            platform: Target platform for the content
            
        Returns:
            Generated content string or user-friendly error message
        """
        # Get profile attributes safely
        industry = getattr(user_profile, "industry", "general")
        business_name = getattr(user_profile, "business_name", "Your Business")
        brand_voice = getattr(user_profile, "brand_voice", "Professional and friendly")
        
        # Build prompt based on task type
        prompt_parts = [
            f"You are an expert content creator for {business_name} in the {industry} industry.",
            f"Brand voice: {brand_voice}",
            f"Task: Create {task_type} content about: {topic}",
            f"Platform: {platform}",
            f"Provide engaging, on-brand content that resonates with the target audience.",
        ]
        
        prompt = "\n".join(prompt_parts)
        
        # Return fallback if no model available
        if not self.model:
            return f"Generated {task_type} content for {platform}"
        
        try:
            # Generate content with timeout handled by the model's underlying client
            response = self.model.generate_content(prompt)
            return response.text if response else f"Generated {task_type} content"
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
