import os
import logging
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import google.generativeai as genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class VoiceAnalyzer:
    """Wraps Google Gemini calls to analyze a user's writing style and
    generate content in that voice.

    This class isolates external API calls so they can be easily mocked in
    tests.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set; API calls will fail in production")
        if genai is not None:
            try:
                # configure client if supported
                if hasattr(genai, "configure"):
                    try:
                        genai.configure(api_key=self.api_key)
                    except Exception:
                        # older/newer libs might differ; ignore configure errors
                        pass
                self.client = genai
            except Exception:
                self.client = None
        else:
            self.client = None

    def _call_model(self, model: str, prompt: str, system_instruction: Optional[str] = None,
                    temperature: float = 0.7, max_output_tokens: int = 512) -> str:
        """Single place to call Gemini. Returns the generated text.

        The implementation attempts to use the common entry points of the
        `google.generativeai` package but keeps errors obvious so tests can
        mock this method instead of the underlying client.
        """
        if self.client is None:
            raise RuntimeError("google.generativeai is not available")

        # Prefer a simple generate_text API where available
        try:
            if hasattr(self.client, "generate_text"):
                # Some versions expose generate_text(model=..., input=...)
                resp = self.client.generate_text(model=model, input=prompt, temperature=temperature)
                # resp may be a dict-like or an object with candidates/content
                if isinstance(resp, dict):
                    # new style: {'candidates':[{'content': '...'}], ...}
                    c = resp.get("candidates")
                    if c and isinstance(c, list) and len(c) > 0:
                        return c[0].get("content", "")
                    return resp.get("content") or str(resp)
                # try to extract text attr
                text = getattr(resp, "text", None) or getattr(resp, "content", None)
                if text:
                    return text
                return str(resp)

            # Fallback older API: TextGenerationModel
            if hasattr(self.client, "TextGenerationModel"):
                Model = self.client.TextGenerationModel.from_pretrained(model)
                out = Model.generate(prompt=prompt, temperature=temperature)
                text = getattr(out, "text", None) or getattr(out, "content", None)
                if text:
                    return text
                return str(out)

        except Exception as e:
            logger.exception("Error calling Gemini model %s", model)
            raise

        raise RuntimeError("No supported client interface found on google.generativeai")

    def analyze_style(self, text_content: str) -> str:
        """Analyze provided text and return a concise 'System Instruction'
        paragraph that instructs an AI how to write like the author.
        """
        system_prompt = (
            "You are a linguistic expert. Analyze the provided text. Extract the "
            "specific tone, sentence structure patterns, vocabulary level, emoji usage frequency, "
            "and controversial/contrarian scale. Return a concise 'System Instruction' paragraph "
            "that would tell an AI how to write exactly like this person."
        )

        prompt = f"TEXT_TO_ANALYZE:\n\n{text_content}\n\nPlease return ONLY the System Instruction paragraph."
        try:
            model = "gemini-1.5-flash"
            out = self._call_model(model=model, prompt=prompt, system_instruction=system_prompt,
                                   temperature=0.2, max_output_tokens=300)
            # Basic post-processing: strip and return
            return (out or "").strip()
        except Exception:
            logger.exception("analyze_style failed; falling back to generic instruction")
            return (
                "Write in a clear, professional, and helpful tone. Mirror the author's sentence "
                "lengths, punctuation, and vocabulary level. Keep messages concise and use emojis "
                "sparingly, matching frequency observed in the sample."
            )

    def generate_with_voice(self, user_tier: str, style_instruction: str, topic: str, platform: str) -> Dict[str, Any]:
        """Generate content for a topic using the provided style instruction.

        Returns a dict with keys: ok (bool), model (str), output (str) or error.
        """
        model = "gemini-1.5-pro" if user_tier == "pro" else "gemini-1.5-flash"
        temperature = 0.8 if user_tier == "pro" else 0.3
        prompt = (
            f"SYSTEM_INSTRUCTION:\n{style_instruction}\n\n" 
            f"TASK: Write a short {platform} post about: {topic}\n" 
            f"Constraints: Keep it concise, on-brand, and follow the system instruction."
        )
        try:
            out = self._call_model(model=model, prompt=prompt, system_instruction=style_instruction,
                                   temperature=temperature, max_output_tokens=256)
            return {"ok": True, "model": model, "output": (out or "").strip()}
        except Exception as e:
            logger.exception("generate_with_voice failed")
            return {"ok": False, "error": str(e)}
