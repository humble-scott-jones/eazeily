"""Prompt Compiler - the "secret sauce" for voice-accurate, toggle-aware generation.

This module compiles profile + wizard + voice coach + template + toggles into:
1. Model-ready context (JSON) - compact, only what matters
2. Strict JSON schema for model output
3. Prompt set (system + context + request) with voice anchoring

Deterministic precedence: RunToggles > TemplatePreset > VoiceFingerprint > ProfileDefaults
"""

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


# ============================================================================
# Canonical Input Types
# ============================================================================

class ProfileDefaults(TypedDict, total=False):
    """Profile defaults from database (workspace/account settings)."""
    company: str
    industry: str
    signature_tone: str
    platforms: List[str]
    timezone: Optional[str]
    offerings: Optional[str]
    audience: Optional[str]
    taboo_topics: Optional[List[str]]


class VoiceFingerprint(TypedDict, total=False):
    """Voice fingerprint from voice coach training."""
    sentence_length_band: str  # "short" | "medium" | "long"
    emoji_rate: str  # "high" | "medium" | "low" | "none"
    punctuation_style: Dict[str, int]  # exclamations, questions, ellipses counts
    typical_cta_patterns: List[str]  # extracted CTA examples
    top_phrases: List[str]  # phrases to naturally incorporate
    avoid_phrases: List[str]  # phrases/words to avoid
    signature_moves: List[str]  # e.g., "rhetorical questions", "storytelling"
    micro_examples: Optional['VoiceMicroExamples']  # voice anchoring examples


class VoiceMicroExamples(TypedDict, total=False):
    """Micro-examples for voice anchoring (2-3 short examples)."""
    example_caption: str  # One short caption in their voice
    example_cta: str  # One CTA in their voice
    avoid_rewrite: Dict[str, str]  # {"bad": "...", "good": "..."}


class TemplatePreset(TypedDict, total=False):
    """Template preset (optional, saved by user)."""
    name: str
    structure_preference: Optional[str]  # "short", "list", "story", etc.
    cadence: Optional[str]  # "daily", "weekly", etc.
    goal: Optional[str]
    keywords_format: Optional[str]  # how to integrate keywords
    preferred_tone: Optional[str]
    preferred_platforms: Optional[List[str]]


class RunToggles(TypedDict, total=False):
    """Request toggles - highest priority."""
    session_length: int  # 1, 7, 30
    platform_focus: Optional[List[str]]  # platforms for this generation
    tone_override: Optional[str]  # override tone for this request
    keywords: Optional[List[str]]
    goals: Optional[List[str]]
    promo_note: Optional[str]
    reel_toggles: Optional[Dict[str, Any]]  # reel-specific options
    variants: Optional[int]  # number of variants to generate


# ============================================================================
# Output Types
# ============================================================================

class ModelReadyContext(TypedDict, total=False):
    """Compiled context for model (compact, only essentials)."""
    company_name: str
    industry: str
    tone: str
    platforms: List[str]
    goals: Optional[List[str]]
    keywords: Optional[List[str]]
    session_length: int
    offerings: Optional[str]
    audience: Optional[str]
    voice_applied: bool
    voice_style: Optional[Dict[str, Any]]  # compact voice constraints
    template_applied: bool


class PromptSet(TypedDict):
    """Complete prompt set for model."""
    system: str  # role + format + safety constraints
    context: str  # brand + voice (compact bullet/JSON)
    request: str  # toggles + platform rules


class CompilerOutput(TypedDict):
    """Complete output from prompt compiler."""
    model_context: ModelReadyContext
    json_schema: Dict[str, Any]
    prompt_set: PromptSet
    trace_summary: Dict[str, Any]  # for debugging (redacted)


# ============================================================================
# Prompt Compiler
# ============================================================================

class PromptCompiler:
    """Compiles contexts with deterministic precedence into compact, testable prompts."""
    
    def __init__(
        self,
        profile_defaults: Optional[ProfileDefaults] = None,
        voice_fingerprint: Optional[VoiceFingerprint] = None,
        template_preset: Optional[TemplatePreset] = None
    ):
        """Initialize compiler with static context layers.
        
        Args:
            profile_defaults: Profile/workspace defaults
            voice_fingerprint: Voice style constraints
            template_preset: Optional template preset
        """
        self.profile_defaults = profile_defaults or {}
        self.voice_fingerprint = voice_fingerprint or {}
        self.template_preset = template_preset or {}
    
    def compile_for_social(
        self,
        run_toggles: RunToggles,
        request_id: Optional[str] = None
    ) -> CompilerOutput:
        """Compile prompt for social media post generation.
        
        Args:
            run_toggles: Request-specific toggles (highest priority)
            request_id: Optional request ID for trace
            
        Returns:
            CompilerOutput with context, schema, and prompts
        """
        request_id = request_id or self._generate_request_id()
        
        # Step 1: Merge with deterministic precedence
        merged = self._merge_with_precedence(run_toggles)
        
        # Step 2: Build model-ready context (compact)
        model_context = self._build_model_context(merged)
        
        # Step 3: Build JSON schema
        json_schema = self._build_social_schema()
        
        # Step 4: Build prompt set with voice anchoring
        prompt_set = self._build_social_prompt_set(model_context)
        
        # Step 5: Build trace summary (redacted)
        trace_summary = self._build_trace_summary(
            request_id=request_id,
            content_type='social',
            merged=merged,
            model_context=model_context
        )
        
        logger.info(f"[{request_id}] Compiled social prompt (voice={model_context.get('voice_applied')})")
        
        return CompilerOutput(
            model_context=model_context,
            json_schema=json_schema,
            prompt_set=prompt_set,
            trace_summary=trace_summary
        )
    
    def compile_for_reels(
        self,
        run_toggles: RunToggles,
        request_id: Optional[str] = None
    ) -> CompilerOutput:
        """Compile prompt for reel/video generation.
        
        Args:
            run_toggles: Request-specific toggles
            request_id: Optional request ID for trace
            
        Returns:
            CompilerOutput with context, schema, and prompts
        """
        request_id = request_id or self._generate_request_id()
        
        merged = self._merge_with_precedence(run_toggles)
        model_context = self._build_model_context(merged)
        json_schema = self._build_reel_schema(run_toggles.get('reel_toggles', {}))
        prompt_set = self._build_reel_prompt_set(model_context, run_toggles.get('reel_toggles', {}))
        
        trace_summary = self._build_trace_summary(
            request_id=request_id,
            content_type='reels',
            merged=merged,
            model_context=model_context
        )
        
        logger.info(f"[{request_id}] Compiled reel prompt (voice={model_context.get('voice_applied')})")
        
        return CompilerOutput(
            model_context=model_context,
            json_schema=json_schema,
            prompt_set=prompt_set,
            trace_summary=trace_summary
        )
    
    def compile_for_reviews(
        self,
        run_toggles: RunToggles,
        review_text: str,
        rating: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> CompilerOutput:
        """Compile prompt for review response generation.
        
        Args:
            run_toggles: Request-specific toggles
            review_text: The review to respond to
            rating: Star rating (1-5)
            request_id: Optional request ID for trace
            
        Returns:
            CompilerOutput with context, schema, and prompts
        """
        request_id = request_id or self._generate_request_id()
        
        merged = self._merge_with_precedence(run_toggles)
        model_context = self._build_model_context(merged)
        json_schema = self._build_review_schema()
        prompt_set = self._build_review_prompt_set(model_context, review_text, rating)
        
        trace_summary = self._build_trace_summary(
            request_id=request_id,
            content_type='reviews',
            merged=merged,
            model_context=model_context
        )
        
        logger.info(f"[{request_id}] Compiled review prompt (voice={model_context.get('voice_applied')})")
        
        return CompilerOutput(
            model_context=model_context,
            json_schema=json_schema,
            prompt_set=prompt_set,
            trace_summary=trace_summary
        )
    
    # ========================================================================
    # Internal Methods - Merge Logic
    # ========================================================================
    
    def _merge_with_precedence(self, run_toggles: RunToggles) -> Dict[str, Any]:
        """Merge inputs with deterministic precedence.
        
        Precedence (highest to lowest):
        1. RunToggles (request)
        2. TemplatePreset
        3. VoiceFingerprint (as constraints, not overridable)
        4. ProfileDefaults
        
        Returns:
            Merged dict with final values
        """
        merged: Dict[str, Any] = {}
        
        # Layer 1: Profile defaults (lowest priority)
        if self.profile_defaults:
            merged['company'] = self.profile_defaults.get('company', '')
            merged['industry'] = self.profile_defaults.get('industry', 'business')
            merged['tone'] = self.profile_defaults.get('signature_tone', 'professional')
            merged['platforms'] = self.profile_defaults.get('platforms', [])
            merged['offerings'] = self.profile_defaults.get('offerings')
            merged['audience'] = self.profile_defaults.get('audience')
            merged['taboo_topics'] = self.profile_defaults.get('taboo_topics', [])
        
        # Layer 2: Voice fingerprint (constraints, not overridden)
        # Voice is stored separately and applied as constraints
        merged['voice_fingerprint'] = self.voice_fingerprint if self.voice_fingerprint else None
        
        # Layer 3: Template preset
        if self.template_preset:
            if self.template_preset.get('preferred_tone'):
                merged['tone'] = self.template_preset['preferred_tone']
            if self.template_preset.get('preferred_platforms'):
                merged['platforms'] = self.template_preset['preferred_platforms']
            merged['template_name'] = self.template_preset.get('name')
            merged['structure_preference'] = self.template_preset.get('structure_preference')
        
        # Layer 4: Run toggles (highest priority)
        if run_toggles.get('tone_override'):
            merged['tone'] = run_toggles['tone_override']
        if run_toggles.get('platform_focus'):
            merged['platforms'] = run_toggles['platform_focus']
        
        merged['session_length'] = run_toggles.get('session_length', 7)
        merged['keywords'] = run_toggles.get('keywords', [])
        merged['goals'] = run_toggles.get('goals', [])
        merged['promo_note'] = run_toggles.get('promo_note')
        merged['reel_toggles'] = run_toggles.get('reel_toggles', {})
        merged['variants'] = run_toggles.get('variants', 1)
        
        return merged
    
    def _build_model_context(self, merged: Dict[str, Any]) -> ModelReadyContext:
        """Build compact model-ready context (only essentials).
        
        Args:
            merged: Merged parameters from precedence logic
            
        Returns:
            ModelReadyContext with compact data
        """
        voice_fingerprint = merged.get('voice_fingerprint')
        voice_applied = bool(voice_fingerprint and voice_fingerprint.get('top_phrases'))
        
        # Build compact voice style summary
        voice_style = None
        if voice_applied:
            voice_style = {
                'sentence_length': voice_fingerprint.get('sentence_length_band', 'medium'),
                'tone_markers': voice_fingerprint.get('signature_moves', [])[:3],
                'include_naturally': voice_fingerprint.get('top_phrases', [])[:5],
                'avoid': voice_fingerprint.get('avoid_phrases', [])[:5],
                'cta_style': voice_fingerprint.get('typical_cta_patterns', [])[:2]
            }
            
            # Add micro-examples if available
            if micro_examples := voice_fingerprint.get('micro_examples'):
                voice_style['micro_examples'] = micro_examples
        
        return ModelReadyContext(
            company_name=merged.get('company', ''),
            industry=merged.get('industry', 'business'),
            tone=merged.get('tone', 'professional'),
            platforms=merged.get('platforms', []),
            goals=merged.get('goals'),
            keywords=merged.get('keywords'),
            session_length=merged.get('session_length', 7),
            offerings=merged.get('offerings'),
            audience=merged.get('audience'),
            voice_applied=voice_applied,
            voice_style=voice_style,
            template_applied=bool(merged.get('template_name'))
        )
    
    # ========================================================================
    # Schema Builders
    # ========================================================================
    
    def _build_social_schema(self) -> Dict[str, Any]:
        """Build strict JSON schema for social posts output."""
        return {
            "type": "object",
            "required": ["posts"],
            "properties": {
                "posts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["date", "pillar", "cards"],
                        "properties": {
                            "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "pillar": {
                                "type": "string",
                                "enum": ["Educational", "Behind-the-Scenes", "Testimonial", 
                                        "Product", "Engagement", "Story"]
                            },
                            "cards": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                    "type": "object",
                                    "required": ["platform", "caption"],
                                    "properties": {
                                        "platform": {"type": "string"},
                                        "caption": {"type": "string", "minLength": 1},
                                        "hashtags": {"type": "array", "items": {"type": "string"}},
                                        "hook": {"type": "string"},
                                        "cta": {"type": "string"},
                                        "media_idea": {"type": "string"}
                                    }
                                }
                            },
                            "voice_note": {"type": "string"}
                        }
                    }
                }
            }
        }
    
    def _build_reel_schema(self, reel_toggles: Dict[str, Any]) -> Dict[str, Any]:
        """Build strict JSON schema for reel script output."""
        schema = {
            "type": "object",
            "required": ["script"],
            "properties": {
                "script": {
                    "type": "object",
                    "required": ["hook", "beats", "cta", "caption", "hashtags"],
                    "properties": {
                        "hook": {"type": "string", "minLength": 1},
                        "beats": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["text"],
                                "properties": {
                                    "text": {"type": "string"},
                                    "shot": {"type": "string"},
                                    "on_screen_text": {"type": "string"}
                                }
                            }
                        },
                        "cta": {"type": "string", "minLength": 1},
                        "caption": {"type": "string"},
                        "hashtags": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        }
        
        # Add optional fields based on toggles
        if reel_toggles.get('include_shot_list'):
            schema['properties']['script']['properties']['shot_list'] = {
                "type": "array",
                "items": {"type": "string"}
            }
        
        return schema
    
    def _build_review_schema(self) -> Dict[str, Any]:
        """Build strict JSON schema for review responses output."""
        return {
            "type": "object",
            "required": ["responses"],
            "properties": {
                "responses": {
                    "type": "object",
                    "properties": {
                        "short": {"type": "string", "minLength": 1},
                        "medium": {"type": "string", "minLength": 1},
                        "long": {"type": "string", "minLength": 1}
                    },
                    "minProperties": 1
                },
                "tone": {"type": "string"},
                "voice_applied": {"type": "boolean"}
            }
        }
    
    # ========================================================================
    # Prompt Set Builders
    # ========================================================================
    
    def _build_social_prompt_set(self, context: ModelReadyContext) -> PromptSet:
        """Build complete prompt set for social generation with voice anchoring."""
        
        # System message
        system = (
            "You are Eazeily, an expert social media content generator. "
            "Generate engaging, on-brand content that sounds natural and human. "
            "CRITICAL: Return ONLY valid JSON matching the exact schema provided. "
            "Never include private contact information (phone, email, address) in public posts."
        )
        
        # Context section (compact)
        context_parts = []
        if context.get('company_name'):
            context_parts.append(f"Company: {context['company_name']}")
        if context.get('industry'):
            context_parts.append(f"Industry: {context['industry']}")
        if context.get('offerings'):
            context_parts.append(f"Offerings: {context['offerings']}")
        if context.get('audience'):
            context_parts.append(f"Audience: {context['audience']}")
        
        # Voice style (if applied)
        if context.get('voice_applied') and (voice_style := context.get('voice_style')):
            voice_parts = []
            voice_parts.append(f"VOICE STYLE:")
            voice_parts.append(f"  Sentence length: {voice_style.get('sentence_length', 'medium')}")
            
            if include := voice_style.get('include_naturally'):
                voice_parts.append(f"  Include naturally: {', '.join(include)}")
            if avoid := voice_style.get('avoid'):
                voice_parts.append(f"  AVOID: {', '.join(avoid)}")
            if cta_style := voice_style.get('cta_style'):
                voice_parts.append(f"  CTA style: {', '.join(cta_style)}")
            
            # Voice anchoring: micro-examples
            if micro_examples := voice_style.get('micro_examples'):
                voice_parts.append(f"\nVOICE EXAMPLES:")
                if example_caption := micro_examples.get('example_caption'):
                    voice_parts.append(f'  Caption example: "{example_caption}"')
                if example_cta := micro_examples.get('example_cta'):
                    voice_parts.append(f'  CTA example: "{example_cta}"')
                if avoid_rewrite := micro_examples.get('avoid_rewrite'):
                    voice_parts.append(
                        f'  ❌ Avoid: "{avoid_rewrite.get("bad")}" '
                        f'→ ✓ Use: "{avoid_rewrite.get("good")}"'
                    )
            
            context_parts.append('\n'.join(voice_parts))
        
        context_section = '\n'.join(context_parts)
        
        # Request section
        request_parts = []
        request_parts.append(f"GENERATE: {context.get('session_length', 7)} social media posts")
        request_parts.append(f"TONE: {context.get('tone', 'professional')}")
        
        if platforms := context.get('platforms'):
            request_parts.append(f"PLATFORMS: {', '.join(platforms)}")
            # Add platform-specific rules
            request_parts.append(self._build_platform_rules(platforms))
        
        if goals := context.get('goals'):
            request_parts.append(f"GOALS: {', '.join(goals)}")
        if keywords := context.get('keywords'):
            request_parts.append(f"KEYWORDS: {', '.join(keywords)}")
        
        request_section = '\n'.join(request_parts)
        
        return PromptSet(
            system=system,
            context=context_section,
            request=request_section
        )
    
    def _build_reel_prompt_set(
        self,
        context: ModelReadyContext,
        reel_toggles: Dict[str, Any]
    ) -> PromptSet:
        """Build complete prompt set for reel generation."""
        
        system = (
            "You are Eazeily, an expert video content creator. "
            "Generate engaging video scripts (Reels/TikTok/Shorts) with hooks, beats, and CTAs. "
            "CRITICAL: Return ONLY valid JSON matching the exact schema provided. "
            "Hook viewers in first 3 seconds. Use short, punchy lines."
        )
        
        # Build context (reuse social logic, it's compact)
        context_parts = []
        if context.get('company_name'):
            context_parts.append(f"Company: {context['company_name']}")
        if context.get('industry'):
            context_parts.append(f"Industry: {context['industry']}")
        
        if context.get('voice_applied') and (voice_style := context.get('voice_style')):
            context_parts.append(f"Voice style: {voice_style.get('sentence_length', 'medium')} sentences")
            if include := voice_style.get('include_naturally'):
                context_parts.append(f"Include: {', '.join(include[:3])}")
        
        context_section = '\n'.join(context_parts)
        
        # Request
        request_parts = ["GENERATE: Video script (Reel/TikTok/Short)"]
        request_parts.append(f"TONE: {context.get('tone', 'professional')}")
        
        if hook_style := reel_toggles.get('hook_style'):
            request_parts.append(f"HOOK STYLE: {hook_style}")
        if duration := reel_toggles.get('duration'):
            request_parts.append(f"DURATION: ~{duration} seconds")
        
        request_parts.append(
            "KEY REQUIREMENTS:\n"
            "- Hook in first 3 seconds\n"
            "- Short lines (5-8 words)\n"
            "- Clear visual progression\n"
            "- Strong CTA"
        )
        
        request_section = '\n'.join(request_parts)
        
        return PromptSet(
            system=system,
            context=context_section,
            request=request_section
        )
    
    def _build_review_prompt_set(
        self,
        context: ModelReadyContext,
        review_text: str,
        rating: Optional[int]
    ) -> PromptSet:
        """Build complete prompt set for review response generation."""
        
        system = (
            "You are Eazeily, an expert at crafting professional review responses. "
            "Generate authentic, gracious responses that acknowledge specific feedback. "
            "CRITICAL: Return ONLY valid JSON matching the exact schema provided. "
            "Stay professional regardless of review tone. Never include contact info."
        )
        
        # Context
        context_parts = []
        if context.get('company_name'):
            context_parts.append(f"Company: {context['company_name']}")
        
        if context.get('voice_applied') and (voice_style := context.get('voice_style')):
            context_parts.append(f"Brand voice: {context.get('tone', 'professional')}")
            if cta_style := voice_style.get('cta_style'):
                context_parts.append(f"CTA approach: {', '.join(cta_style[:1])}")
        
        context_section = '\n'.join(context_parts)
        
        # Request
        request_parts = ["GENERATE: Response to customer review"]
        request_parts.append(f"TONE: {context.get('tone', 'professional')}")
        if rating:
            request_parts.append(f"RATING: {rating}/5 stars")
        
        request_parts.append(f"\nREVIEW TEXT:\n{review_text}")
        request_parts.append(
            "\nGUIDELINES:\n"
            "- Acknowledge specific feedback\n"
            "- Stay professional and gracious\n"
            "- Be genuine, not generic\n"
            "- Provide short (~50w), medium (~100w), long (~150w) variants"
        )
        
        request_section = '\n'.join(request_parts)
        
        return PromptSet(
            system=system,
            context=context_section,
            request=request_section
        )
    
    def _build_platform_rules(self, platforms: List[str]) -> str:
        """Build platform-specific constraints."""
        platform_rules = {
            'instagram': 'Visual-first. 2200 chars max. 12 hashtags. Line breaks.',
            'facebook': 'Conversational. 1200 chars max. 4 hashtags. Community focus.',
            'linkedin': 'Professional. 1300 chars max. 5 hashtags. Value-forward.',
            'twitter': 'Punchy. 280 chars max. 3 hashtags. Thread if needed.',
            'tiktok': 'Hook first. 1500 chars max. 5 hashtags. Short lines.',
            'youtube': 'Hook + value. 5000 chars max. 6 hashtags. Structure.'
        }
        
        rules = []
        for platform in platforms:
            if rule := platform_rules.get(platform.lower()):
                rules.append(f"  {platform.upper()}: {rule}")
        
        return '\n'.join(['PLATFORM RULES:'] + rules) if rules else ''
    
    # ========================================================================
    # Trace & Debugging
    # ========================================================================
    
    def _build_trace_summary(
        self,
        request_id: str,
        content_type: str,
        merged: Dict[str, Any],
        model_context: ModelReadyContext
    ) -> Dict[str, Any]:
        """Build redacted trace summary for debugging (no PII).
        
        Args:
            request_id: Request identifier
            content_type: Type of content (social, reels, reviews)
            merged: Merged parameters
            model_context: Final model context
            
        Returns:
            Trace summary dict (safe for logging)
        """
        voice_fingerprint = merged.get('voice_fingerprint')
        
        # Estimate token budget (rough)
        token_estimate = self._estimate_tokens(model_context)
        
        return {
            'request_id': request_id,
            'content_type': content_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'selections': {
                'tone': merged.get('tone'),
                'platforms': merged.get('platforms', []),
                'session_length': merged.get('session_length'),
                'goals_count': len(merged.get('goals', [])),
                'keywords_count': len(merged.get('keywords', []))
            },
            'voice_fingerprint_applied': bool(voice_fingerprint and voice_fingerprint.get('top_phrases')),
            'template_used': merged.get('template_name'),
            'token_budget_estimate': token_estimate,
            'flags': {
                'voice_applied': model_context.get('voice_applied', False),
                'template_applied': model_context.get('template_applied', False)
            }
        }
    
    def _estimate_tokens(self, context: ModelReadyContext) -> int:
        """Rough token estimate for prompt size.
        
        Args:
            context: Model-ready context
            
        Returns:
            Estimated token count (very rough, ~4 chars per token)
        """
        # Rough estimation: sum character counts and divide by 4
        char_count = 0
        
        # System message ~150 tokens
        char_count += 600
        
        # Context fields
        char_count += len(str(context.get('company_name', '')))
        char_count += len(str(context.get('industry', '')))
        char_count += len(str(context.get('offerings', '')))
        char_count += len(str(context.get('audience', '')))
        
        # Voice style (if present)
        if voice_style := context.get('voice_style'):
            char_count += len(json.dumps(voice_style))
        
        # Request params
        char_count += len(str(context.get('platforms', []))) * 20
        char_count += len(str(context.get('keywords', []))) * 10
        char_count += len(str(context.get('goals', []))) * 10
        
        # Rough conversion (4 chars per token)
        return char_count // 4
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return uuid.uuid4().hex[:12]
