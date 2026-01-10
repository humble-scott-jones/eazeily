from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


@dataclass
class VoiceMicroExamples:
    example_caption: Optional[str] = None
    example_cta: Optional[str] = None
    avoid_rewrite: Optional[Dict[str, str]] = None


@dataclass
class VoiceFingerprint:
    sentence_length_band: Optional[str] = None
    top_phrases: List[str] = field(default_factory=list)
    avoid_phrases: List[str] = field(default_factory=list)
    typical_cta_patterns: List[str] = field(default_factory=list)
    signature_moves: List[str] = field(default_factory=list)
    micro_examples: Optional[VoiceMicroExamples] = None


@dataclass
class TemplatePreset:
    name: str
    preferred_tone: Optional[str] = None
    preferred_platforms: Optional[List[str]] = None


@dataclass
class ProfileDefaults:
    company: str = ""
    industry: str = "business"
    signature_tone: str = "professional"
    platforms: List[str] = field(default_factory=lambda: ["instagram"])
    offerings: Optional[str] = None
    audience: Optional[str] = None


@dataclass
class RunToggles:
    tone_override: Optional[str] = None
    session_length: int = 7
    platform_focus: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    include_phrases: List[str] = field(default_factory=list)
    avoid_phrases: List[str] = field(default_factory=list)


class PromptCompiler:
    def __init__(
        self,
        *,
        profile_defaults: Optional[ProfileDefaults] = None,
        voice_fingerprint: Optional[VoiceFingerprint] = None,
        template_preset: Optional[TemplatePreset] = None,
    ) -> None:
        self.profile_defaults = profile_defaults or ProfileDefaults()
        self.voice_fingerprint = voice_fingerprint
        self.template_preset = template_preset

    def _tone(self, run: RunToggles):
        if run.tone_override:
            return run.tone_override
        if self.template_preset and self.template_preset.preferred_tone:
            return self.template_preset.preferred_tone
        return self.profile_defaults.signature_tone

    def _platforms(self, run: RunToggles):
        if run.platform_focus:
            return _ensure_list(run.platform_focus)
        if self.template_preset and self.template_preset.preferred_platforms:
            return _ensure_list(self.template_preset.preferred_platforms)
        return _ensure_list(self.profile_defaults.platforms)

    def _base_context(self, run: RunToggles) -> Dict[str, Any]:
        ctx = {
            "company_name": self.profile_defaults.company or "",
            "industry": self.profile_defaults.industry or "business",
            "tone": self._tone(run),
            "platforms": self._platforms(run),
            "session_length": run.session_length or 7,
            "keywords": _ensure_list(run.keywords),
            "goals": _ensure_list(run.goals),
            "voice_applied": bool(self.voice_fingerprint),
        }
        if self.voice_fingerprint:
            ctx["voice_style"] = build_voice_style_guide(self.voice_fingerprint)
        return ctx

    def compile_for_social(self, run: RunToggles) -> Dict[str, Any]:
        model_context = self._base_context(run)
        prompt_set = self._build_prompt_set(model_context, content_type="social")
        used_signals = {
            "services_used": [],
            "pains_used": [],
            "outcomes_used": [],
            "proof_used": [],
            "differentiators_used": [],
            "custom_chips_used": [],
        }
        return {
            "model_context": model_context,
            "prompt_set": prompt_set,
            "used_signals": used_signals,
            "voice_applied": model_context.get("voice_applied", False),
        }

    def compile_for_reels(self, run: RunToggles) -> Dict[str, Any]:
        model_context = self._base_context(run)
        prompt_set = self._build_prompt_set(model_context, content_type="reels")
        return {"model_context": model_context, "prompt_set": prompt_set}

    def compile_for_reviews(self, run: RunToggles) -> Dict[str, Any]:
        model_context = self._base_context(run)
        prompt_set = self._build_prompt_set(model_context, content_type="reviews")
        return {"model_context": model_context, "prompt_set": prompt_set}

    def _build_prompt_set(self, model_context: Dict[str, Any], *, content_type: str) -> Dict[str, str]:
        system = "Eazeily: Produce valid JSON and avoid PII."
        context_lines = [
            f"Company: {model_context.get('company_name', '')}",
            f"Industry: {model_context.get('industry', '')}",
        ]
        if model_context.get("voice_style"):
            context_lines.append("VOICE STYLE: applied")
            context_lines.append(str(model_context["voice_style"]))
        request_lines = [
            f"Tone: {model_context.get('tone')}",
            f"Platforms: {', '.join(model_context.get('platforms', []))}",
            f"Session length: {model_context.get('session_length')}",
        ]
        if model_context.get("keywords"):
            request_lines.append(f"Keywords: {', '.join(model_context['keywords'])}")
        if model_context.get("goals"):
            request_lines.append(f"Goals: {', '.join(model_context['goals'])}")
        return {
            "system": system,
            "context": "\n".join(context_lines),
            "request": "\n".join(request_lines),
            "content_type": content_type,
        }


def build_voice_style_guide(fingerprint: VoiceFingerprint) -> Dict[str, Any]:
    return {
        "sentence_length": fingerprint.sentence_length_band,
        "include_naturally": list(fingerprint.top_phrases),
        "avoid": list(fingerprint.avoid_phrases),
        "cta_style": list(fingerprint.typical_cta_patterns),
        "signature_moves": list(fingerprint.signature_moves),
        "micro_examples": fingerprint.micro_examples.__dict__ if fingerprint.micro_examples else None,
    }
