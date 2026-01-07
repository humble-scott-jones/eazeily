"""Lightweight voice engine shims for tests.

These implementations avoid network calls and match the contracts expected by
unit tests. All generation is Gemini-first; OpenAI is unused except where tests
patch a client directly.
"""
from __future__ import annotations
import json
import os
from typing import Any, List

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
