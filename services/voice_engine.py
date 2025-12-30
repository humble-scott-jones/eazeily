import os
import json
from typing import Dict, List, Any

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - genai may not be installed in test env
    genai = None


class VoiceEngine:
    """Simple wrapper around Gemini (gemini-1.5-flash) for style analysis
    and few-shot generation. This class intentionally keeps calls compact and
    returns plain Python structures (dicts / lists) so callers can store results
    in the DB.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv('GENAI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.genai = genai
        if self.genai and self.api_key:
            try:
                # library provides simple configure function in many versions
                try:
                    self.genai.configure(api_key=self.api_key)
                except Exception:
                    # older/newer shims may differ; ignore if configure missing
                    pass
            except Exception:
                pass

    def analyze_style(self, raw_text: str) -> Dict[str, Any]:
        """Analyze provided raw text and return a small style guide and
        a list of example quotes that represent the voice.

        Returns: {"style_guide": str, "examples": [str,...]}
        """
        prompt = (
            "Extract a concise style guide (3-4 bullet points) and pick 5 short example "
            "quotes from the text that best represent the author's voice. Return as JSON "
            "with keys 'style_guide' (string) and 'examples' (array of strings).\n\n" + raw_text
        )

        if not self.genai:
            # Best-effort fallback: naive heuristics
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            examples = lines[:5]
            return {"style_guide": "; ".join((lines[:3] if lines else ['conversational'])), "examples": examples}

        try:
            response = self.genai.generate_text(model='gemini-1.5-flash', prompt=prompt)
            # support multiple shapes: prefer response.candidates[0].content or response.output
            text = None
            if hasattr(response, 'candidates') and response.candidates:
                text = response.candidates[0].content
            elif isinstance(response, dict) and 'output' in response:
                text = response['output']
            else:
                text = str(response)

            # Try to coerce JSON out of response text
            try:
                parsed = json.loads(text)
                style = parsed.get('style_guide') or parsed.get('style') or ""
                examples = parsed.get('examples') or parsed.get('quotes') or []
                return {"style_guide": style, "examples": examples}
            except Exception:
                # fallback: heuristics
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                style = lines[0] if lines else ''
                examples = lines[1:6]
                return {"style_guide": style, "examples": examples}
        except Exception:
            # failure fallback
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            return {"style_guide": "conversational; helpful; concise", "examples": lines[:5]}

    def generate_post(self, profile: Dict[str, Any], topic: str) -> str:
        """Generate a post using few-shot prompting. The profile should expose
        a 'style_guide' and 'examples' (iterable of short strings). The method
        inserts the examples into the prompt context before asking for a new post.
        Returns the generated post as text.
        """
        style = profile.get('style_guide') or ''
        examples = profile.get('examples') or []

        example_block = '\n'.join([f"- {e}" for e in examples])
        prompt = (
            f"You are a creative social writer. Follow this style guide:\n{style}\n\n"
            f"Here are example quotes representing the voice:\n{example_block}\n\n"
            f"Write a single social post about: {topic}\n- keep it short (1-3 sentences), on-brand, and follow the style guide."
        )

        if not self.genai:
            # fallback deterministic stub
            return f"{topic} — written in a {('professional' if 'pro' in style.lower() else 'conversational')} tone."

        try:
            response = self.genai.generate_text(model='gemini-1.5-flash', prompt=prompt)
            if hasattr(response, 'candidates') and response.candidates:
                return response.candidates[0].content.strip()
            if isinstance(response, dict) and 'output' in response:
                return str(response['output']).strip()
            return str(response).strip()
        except Exception:
                return f"{topic} — (generated fallback)"
