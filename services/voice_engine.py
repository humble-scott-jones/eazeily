import os
import json
from typing import Dict, List, Any

try:
    # Prefer the maintained `google.genai` package when available.
    import google.genai as _genai_new  # type: ignore
except Exception:  # pragma: no cover - package may not be installed in test env
    _genai_new = None

try:
    # Fallback to the legacy package if present. It is deprecated but harmless
    # to keep as a fallback so older deployments don't hard-fail.
    import google.generativeai as _genai_old  # type: ignore
except Exception:  # pragma: no cover - package may not be installed in test env
    _genai_old = None

# Prefer new API surface when available, otherwise fall back to legacy.
genai = _genai_new or _genai_old


class VoiceEngine:
    """Simple wrapper around Gemini (gemini-1.5-flash) for style analysis
    and few-shot generation. This class intentionally keeps calls compact and
    returns plain Python structures (dicts / lists) so callers can store results
    in the DB.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv('GENAI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.genai = genai
        # Track which library we actually have so we can adapt call shapes.
        self._using_new_genai = (_genai_new is not None)
        self._using_old_genai = (_genai_old is not None)
        if self.genai and self.api_key:
            try:
                # library provides simple configure function in many versions
                # Try the common configure pattern used by the old pkg
                try:
                    if hasattr(self.genai, 'configure'):
                        self.genai.configure(api_key=self.api_key)
                except Exception:
                    # Older/newer shims may differ; ignore if configure missing
                    pass
                # For the newer `google.genai` package there may be a client
                # object; try to construct a minimal client if exposed.
                try:
                    if self._using_new_genai and hasattr(self.genai, 'Client'):
                        # Some versions expose a Client or Generative models API.
                        try:
                            self.genai_client = self.genai.Client(api_key=self.api_key)
                        except Exception:
                            # not all versions have same constructor signature
                            self.genai_client = None
                    else:
                        self.genai_client = None
                except Exception:
                    self.genai_client = None
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
            # Attempt several compatible call shapes depending on the SDK
            response = None
            # 1) Newer `google.genai` may offer a client or a top-level generate function
            if getattr(self, 'genai_client', None) is not None:
                try:
                    # Try a common client call if available
                    response = self.genai_client.generate_text(model='gemini-1.5-flash', prompt=prompt)
                except Exception:
                    response = None

            if response is None:
                try:
                    # Some versions expose generate_text on the module
                    response = self.genai.generate_text(model='gemini-1.5-flash', prompt=prompt)
                except Exception:
                    response = None

            # If still None, try legacy names/shapes
            if response is None and hasattr(self.genai, 'TextGeneration'):
                try:
                    # defensive: try a class-based API
                    gen = self.genai.TextGeneration()
                    response = gen.generate(model='gemini-1.5-flash', prompt=prompt)
                except Exception:
                    response = None

            if response is None:
                # As a last resort, try calling the module directly (older SDK)
                response = getattr(self.genai, 'generate_text', lambda **kw: None)(model='gemini-1.5-flash', prompt=prompt)
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
            # Try same adaptive invocation strategy as above
            response = None
            if getattr(self, 'genai_client', None) is not None:
                try:
                    response = self.genai_client.generate_text(model='gemini-1.5-flash', prompt=prompt)
                except Exception:
                    response = None

            if response is None:
                try:
                    response = self.genai.generate_text(model='gemini-1.5-flash', prompt=prompt)
                except Exception:
                    response = None

            if response is None and hasattr(self.genai, 'TextGeneration'):
                try:
                    gen = self.genai.TextGeneration()
                    response = gen.generate(model='gemini-1.5-flash', prompt=prompt)
                except Exception:
                    response = None

            if response is None:
                response = getattr(self.genai, 'generate_text', lambda **kw: None)(model='gemini-1.5-flash', prompt=prompt)
            if hasattr(response, 'candidates') and response.candidates:
                return response.candidates[0].content.strip()
            if isinstance(response, dict) and 'output' in response:
                return str(response['output']).strip()
            return str(response).strip()
        except Exception:
                return f"{topic} — (generated fallback)"
