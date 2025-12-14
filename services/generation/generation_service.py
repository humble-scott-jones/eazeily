"""Generation Service - orchestrates content generation with context and voice.

This is the "secret sauce" - intelligently merges context, applies voice style,
and generates content via OpenAI with fallback to deterministic generation.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from .context_builder import merge_contexts, extract_merged_params
from .voice_style_builder import build_voice_style_guide
from .prompt_builder import build_social_prompt, build_reel_prompt, build_review_response_prompt
from .prompt_compiler import PromptCompiler, ProfileDefaults, VoiceFingerprint, RunToggles
from .openai_client import create_client as create_openai_client
from .output_validator import (
    validate_and_repair_social_posts,
    validate_and_repair_reel_script,
    validate_and_repair_review_responses,
    validate_with_schema_enforcement,
    detect_sensitive_content,
    sanitize_public_content,
    ValidationError
)
from .fallback_generator import (
    generate_social_posts_fallback,
    generate_reel_script_fallback,
    generate_review_response_fallback
)
from .output_schemas import SuccessResponse, ErrorResponse
from .prompt_trace import create_trace_from_compiler_output
from .social_post_ready_pipeline import normalize_and_guardrail
from .social_quality_gate import evaluate_all_posts, attempt_repair


logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating content with context awareness and voice personalization."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
        enable_openai: bool = True,
        use_prompt_compiler: bool = False
    ):
        """Initialize generation service.
        
        Args:
            openai_api_key: Optional OpenAI API key
            openai_model: Optional OpenAI model name
            enable_openai: Whether to use OpenAI (default True)
            use_prompt_compiler: Whether to use new PromptCompiler (default False for gradual migration)
        """
        self.openai_client = None
        if enable_openai:
            self.openai_client = create_openai_client(
                api_key=openai_api_key,
                model=openai_model
            )
        
        self.use_prompt_compiler = use_prompt_compiler
        
        logger.info(
            f"GenerationService initialized (OpenAI: {'enabled' if self.openai_client else 'disabled'}, "
            f"PromptCompiler: {'enabled' if use_prompt_compiler else 'disabled'})"
        )
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        return uuid.uuid4().hex[:12]
    
    def _build_error_response(
        self,
        request_id: str,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> ErrorResponse:
        """Build standardized error response."""
        return {
            'ok': False,
            'request_id': request_id,
            'source': 'fallback',
            'mode': 'error',
            'error': {
                'code': code,
                'message': message,
                'details': details
            }
        }
    
    def _build_success_response(
        self,
        request_id: str,
        data: Dict[str, Any],
        openai_used: bool,
        summary: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None
    ) -> SuccessResponse:
        """Build standardized success response."""
        source = "openai" if openai_used else "fallback"
        mode = "generated" if openai_used else "fallback_suggestions"
        
        # Add fallback warning if not using OpenAI
        if not openai_used:
            if warnings is None:
                warnings = []
            if "AI generation temporarily unavailable - showing template suggestions" not in warnings:
                warnings.insert(0, "AI generation temporarily unavailable - showing template suggestions")
        
        return {
            'ok': True,
            'request_id': request_id,
            'source': source,
            'mode': mode,
            'openai_used': openai_used,
            'fallback_used': not openai_used,
            'data': data,
            'summary': summary,
            'warnings': warnings
        }
    
    def generate_social_posts(
        self,
        request_id: Optional[str] = None,
        workspace: Optional[Dict[str, Any]] = None,
        profile: Optional[Dict[str, Any]] = None,
        template: Optional[Dict[str, Any]] = None,
        request: Optional[Dict[str, Any]] = None,
        voice_samples: Optional[List[str]] = None,
        include_phrases: Optional[List[str]] = None,
        avoid_phrases: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate social media posts with full context and voice personalization.
        
        Args:
            request_id: Optional request ID (generated if not provided)
            workspace: Workspace settings (company, industry, defaults)
            profile: User profile/wizard tuning
            template: Saved template settings
            request: Request-specific parameters (session_length, platforms, tone, etc.)
            voice_samples: List of voice sample texts for style guide
            include_phrases: Phrases to emphasize in output
            avoid_phrases: Phrases to avoid in output
            
        Returns:
            Success or error response dict
        """
        request_id = request_id or self._generate_request_id()
        logger.info(f"[{request_id}] Generating social posts")
        
        try:
            # Build voice style guide if samples provided
            voice_guide = None
            if voice_samples:
                voice_guide = build_voice_style_guide(
                    samples=voice_samples,
                    include_phrases=include_phrases,
                    avoid_phrases=avoid_phrases
                )
                logger.info(f"[{request_id}] Built voice style guide from {len(voice_samples)} samples")
            
            # Merge contexts
            context = merge_contexts(
                workspace=workspace,
                profile=profile,
                template=template,
                request=request,
                voice_guide=voice_guide
            )
            
            # Extract merged params
            params = extract_merged_params(context)
            session_length = params.get('session_length', 7)
            
            logger.info(
                f"[{request_id}] Context merged: session_length={session_length}, "
                f"platforms={params.get('platforms')}, tone={params.get('tone')}"
            )
            
            # Try OpenAI first
            openai_used = False
            data = None
            
            if self.openai_client:
                try:
                    logger.info(f"[{request_id}] Attempting OpenAI generation")
                    
                    # Build prompt
                    messages = build_social_prompt(context, session_length=session_length)
                    
                    # Generate
                    result = self.openai_client.generate_structured(messages)
                    
                    # Validate
                    validated = validate_and_repair_social_posts(result)
                    data = validated
                    openai_used = True
                    
                    logger.info(f"[{request_id}] OpenAI generation successful")
                    
                except Exception as e:
                    logger.warning(f"[{request_id}] OpenAI generation failed: {e}, falling back")
            
            # Fallback if OpenAI not available or failed
            if data is None:
                logger.info(f"[{request_id}] Using fallback generation")
                fallback_result = generate_social_posts_fallback(
                    session_length=session_length,
                    platforms=params.get('platforms'),
                    tone=params.get('tone', 'professional'),
                    industry=params.get('industry', 'business'),
                    company_name=params.get('company_name', ''),
                    goals=params.get('goals'),
                    keywords=params.get('keywords'),
                    variant_types=params.get('variant_types', [])
                )
                data = validate_and_repair_social_posts(fallback_result)
            
            # Apply post-ready pipeline normalization
            pipeline_result = normalize_and_guardrail(
                raw_output={'data': data},
                context=context,
                request_id=request_id
            )
            
            if not pipeline_result.get('ok'):
                # Pipeline failed, return error
                return self._build_error_response(
                    request_id=request_id,
                    code=pipeline_result['error']['code'],
                    message=pipeline_result['error']['message']
                )
            
            normalized_posts = pipeline_result['posts']
            warnings = list(pipeline_result.get('warnings', []))
            
            # Quality gate evaluation
            quality_result = evaluate_all_posts(normalized_posts)
            
            if not quality_result['passed']:
                # Some posts failed quality gate - attempt repair if OpenAI available
                if self.openai_client:
                    logger.info(f"[{request_id}] Quality gate failed, attempting repair")
                    repaired_posts = []
                    
                    for result in quality_result['results']:
                        if result['passed']:
                            # Post already passed, keep it
                            repaired_posts.append(normalized_posts[result['post_index']])
                        else:
                            # Attempt repair
                            post_card = normalized_posts[result['post_index']]
                            repair_result = attempt_repair(
                                post_card=post_card,
                                evaluation=result,
                                openai_client=self.openai_client,
                                context=context,
                                request_id=request_id
                            )
                            
                            if repair_result['ok']:
                                repaired_posts.append(repair_result['repaired_card'])
                            else:
                                # Repair failed, include original with warning
                                repaired_posts.append(post_card)
                                warnings.append(
                                    f"{post_card.get('platform')}: {repair_result['error']}"
                                )
                    
                    # Re-evaluate repaired posts
                    final_quality = evaluate_all_posts(repaired_posts)
                    if final_quality['passed']:
                        logger.info(f"[{request_id}] Repair successful, all posts now pass")
                        normalized_posts = repaired_posts
                    else:
                        # Still failing after repair - return error
                        logger.error(f"[{request_id}] Posts still fail after repair")
                        return self._build_error_response(
                            request_id=request_id,
                            code='output_not_post_ready',
                            message='Generated content does not meet quality standards after repair',
                            details={'quality_result': final_quality}
                        )
                else:
                    # No OpenAI for repair - if using fallback, add warning but continue
                    # The fallback generator returns template/guidance format by design
                    logger.warning(f"[{request_id}] Quality gate failed, no OpenAI available for repair")
                    if not openai_used:
                        warnings.append(
                            "AI generation unavailable - showing template suggestions that may contain guidance"
                        )
                        # Continue with fallback output despite quality gate failures
                    else:
                        # OpenAI should have been available but isn't, this is an error
                        return self._build_error_response(
                            request_id=request_id,
                            code='output_not_post_ready',
                            message='Generated content does not meet quality standards',
                            details={'quality_result': quality_result}
                        )
            
            # Check for sensitive content in posts
            for post in normalized_posts:
                caption = post.get('caption', '')
                if warning := detect_sensitive_content(caption):
                    warnings.append(warning)
                    post['caption'] = sanitize_public_content(caption)
            
            # Build response with post-ready format
            return self._build_success_response(
                request_id=request_id,
                data={'posts': normalized_posts, 'count': len(normalized_posts)},
                openai_used=openai_used,
                summary={
                    'posts_generated': len(normalized_posts),
                    'voice_applied': voice_guide is not None,
                    'quality_gate_passed': quality_result['passed']
                },
                warnings=warnings if warnings else None
            )
            
        except ValidationError as e:
            logger.error(f"[{request_id}] Validation failed: {e}")
            return self._build_error_response(
                request_id=request_id,
                code='validation_error',
                message=str(e)
            )
        except Exception as e:
            logger.exception(f"[{request_id}] Generation failed: {e}")
            return self._build_error_response(
                request_id=request_id,
                code='generation_failed',
                message='Failed to generate social posts'
            )
    
    def generate_reel_script(
        self,
        request_id: Optional[str] = None,
        workspace: Optional[Dict[str, Any]] = None,
        profile: Optional[Dict[str, Any]] = None,
        request: Optional[Dict[str, Any]] = None,
        voice_samples: Optional[List[str]] = None,
        include_phrases: Optional[List[str]] = None,
        avoid_phrases: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate reel/video script with context and voice.
        
        Args:
            request_id: Optional request ID
            workspace: Workspace settings
            profile: User profile
            request: Request parameters (hook_style, format, duration, etc.)
            voice_samples: Voice sample texts
            include_phrases: Phrases to emphasize
            avoid_phrases: Phrases to avoid
            
        Returns:
            Success or error response dict
        """
        request_id = request_id or self._generate_request_id()
        logger.info(f"[{request_id}] Generating reel script")
        
        try:
            # Build voice guide
            voice_guide = None
            if voice_samples:
                voice_guide = build_voice_style_guide(
                    samples=voice_samples,
                    include_phrases=include_phrases,
                    avoid_phrases=avoid_phrases
                )
            
            # Merge contexts
            context = merge_contexts(
                workspace=workspace,
                profile=profile,
                request=request,
                voice_guide=voice_guide
            )
            
            # Extract params
            params = extract_merged_params(context)
            request_data = request or {}
            
            hook_style = request_data.get('hook_style')
            format_type = request_data.get('format')
            duration = request_data.get('duration', 30)
            include_shot_list = request_data.get('include_shot_list', False)
            include_on_screen_text = request_data.get('include_on_screen_text', False)
            
            # Try OpenAI
            openai_used = False
            data = None
            
            if self.openai_client:
                try:
                    logger.info(f"[{request_id}] Attempting OpenAI generation")
                    
                    messages = build_reel_prompt(
                        context,
                        hook_style=hook_style,
                        format_type=format_type,
                        duration=duration,
                        include_shot_list=include_shot_list,
                        include_on_screen_text=include_on_screen_text
                    )
                    
                    result = self.openai_client.generate_structured(messages)
                    validated = validate_and_repair_reel_script(result)
                    data = validated
                    openai_used = True
                    
                    logger.info(f"[{request_id}] OpenAI generation successful")
                    
                except Exception as e:
                    logger.warning(f"[{request_id}] OpenAI failed: {e}, falling back")
            
            # Fallback
            if data is None:
                logger.info(f"[{request_id}] Using fallback generation")
                fallback_result = generate_reel_script_fallback(
                    hook_style=hook_style,
                    format_type=format_type,
                    duration=duration,
                    industry=params.get('industry', 'business'),
                    tone=params.get('tone', 'engaging')
                )
                data = validate_and_repair_reel_script(fallback_result)
            
            # Check for sensitive content
            warnings = []
            script = data.get('script', {})
            if warning := detect_sensitive_content(script.get('caption', '')):
                warnings.append(warning)
                script['caption'] = sanitize_public_content(script['caption'])
            
            return self._build_success_response(
                request_id=request_id,
                data=data,
                openai_used=openai_used,
                summary={'voice_applied': voice_guide is not None},
                warnings=warnings if warnings else None
            )
            
        except ValidationError as e:
            logger.error(f"[{request_id}] Validation failed: {e}")
            return self._build_error_response(
                request_id=request_id,
                code='validation_error',
                message=str(e)
            )
        except Exception as e:
            logger.exception(f"[{request_id}] Generation failed: {e}")
            return self._build_error_response(
                request_id=request_id,
                code='generation_failed',
                message='Failed to generate reel script'
            )
    
    def generate_review_response(
        self,
        request_id: Optional[str] = None,
        workspace: Optional[Dict[str, Any]] = None,
        request: Optional[Dict[str, Any]] = None,
        voice_samples: Optional[List[str]] = None,
        include_phrases: Optional[List[str]] = None,
        avoid_phrases: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate review response with optional voice personalization.
        
        Args:
            request_id: Optional request ID
            workspace: Workspace settings
            request: Request parameters (review_text, rating, channel, tone, etc.)
            voice_samples: Voice samples (used if use_brand_voice=True)
            include_phrases: Phrases to emphasize
            avoid_phrases: Phrases to avoid
            
        Returns:
            Success or error response dict
        """
        request_id = request_id or self._generate_request_id()
        logger.info(f"[{request_id}] Generating review response")
        
        try:
            request_data = request or {}
            review_text = request_data.get('review_text', '')
            rating = request_data.get('rating')
            channel = request_data.get('channel')
            tone = request_data.get('tone', 'professional')
            use_brand_voice = request_data.get('use_brand_voice', False)
            
            if not review_text:
                return self._build_error_response(
                    request_id=request_id,
                    code='validation_error',
                    message='Review text is required'
                )
            
            # Build voice guide only if use_brand_voice is True
            voice_guide = None
            if use_brand_voice and voice_samples:
                voice_guide = build_voice_style_guide(
                    samples=voice_samples,
                    include_phrases=include_phrases,
                    avoid_phrases=avoid_phrases
                )
            
            # Merge contexts
            context = merge_contexts(
                workspace=workspace,
                request=request,
                voice_guide=voice_guide
            )
            
            # Try OpenAI
            openai_used = False
            data = None
            
            if self.openai_client:
                try:
                    logger.info(f"[{request_id}] Attempting OpenAI generation")
                    
                    messages = build_review_response_prompt(
                        context,
                        review_text=review_text,
                        rating=rating,
                        channel=channel,
                        use_brand_voice=use_brand_voice
                    )
                    
                    result = self.openai_client.generate_structured(messages)
                    validated = validate_and_repair_review_responses(result)
                    data = validated
                    openai_used = True
                    
                    logger.info(f"[{request_id}] OpenAI generation successful")
                    
                except Exception as e:
                    logger.warning(f"[{request_id}] OpenAI failed: {e}, falling back")
            
            # Fallback
            if data is None:
                logger.info(f"[{request_id}] Using fallback generation")
                company_name = workspace.get('company_name', '') if workspace else ''
                fallback_result = generate_review_response_fallback(
                    review_text=review_text,
                    rating=rating,
                    tone=tone,
                    company_name=company_name
                )
                data = validate_and_repair_review_responses(fallback_result)
            
            # Check for sensitive content
            warnings = []
            responses = data.get('responses', {})
            for key in ['short', 'medium', 'long']:
                if key in responses:
                    if warning := detect_sensitive_content(responses[key]):
                        warnings.append(f"{key}: {warning}")
                        responses[key] = sanitize_public_content(responses[key])
            
            return self._build_success_response(
                request_id=request_id,
                data=data,
                openai_used=openai_used,
                summary={'voice_applied': use_brand_voice and voice_guide is not None},
                warnings=warnings if warnings else None
            )
            
        except ValidationError as e:
            logger.error(f"[{request_id}] Validation failed: {e}")
            return self._build_error_response(
                request_id=request_id,
                code='validation_error',
                message=str(e)
            )
        except Exception as e:
            logger.exception(f"[{request_id}] Generation failed: {e}")
            return self._build_error_response(
                request_id=request_id,
                code='generation_failed',
                message='Failed to generate review response'
            )
    
    # ========================================================================
    # PromptCompiler-based generation methods (new approach)
    # ========================================================================
    
    def _convert_to_profile_defaults(self, workspace: Optional[Dict[str, Any]]) -> ProfileDefaults:
        """Convert workspace dict to ProfileDefaults type."""
        if not workspace:
            return ProfileDefaults()
        
        return ProfileDefaults(
            company=workspace.get('company_name', ''),
            industry=workspace.get('industry', 'business'),
            signature_tone=workspace.get('default_tone', 'professional'),
            platforms=workspace.get('platforms', []),
            timezone=workspace.get('timezone'),
            offerings=workspace.get('offerings'),
            audience=workspace.get('audience'),
            taboo_topics=workspace.get('taboo_topics')
        )
    
    def _convert_to_voice_fingerprint(
        self,
        voice_samples: Optional[List[str]],
        include_phrases: Optional[List[str]] = None,
        avoid_phrases: Optional[List[str]] = None
    ) -> Optional[VoiceFingerprint]:
        """Build VoiceFingerprint from voice samples."""
        if not voice_samples:
            return None
        
        # Build voice style guide
        voice_guide = build_voice_style_guide(
            samples=voice_samples,
            include_phrases=include_phrases,
            avoid_phrases=avoid_phrases
        )
        
        # Convert to VoiceFingerprint type
        return VoiceFingerprint(
            sentence_length_band=voice_guide.get('sentence_length', 'medium'),
            emoji_rate=voice_guide.get('formatting', {}).get('emoji_frequency', 'low'),
            punctuation_style=voice_guide.get('formatting', {}).get('punctuation', {}),
            typical_cta_patterns=voice_guide.get('cta_patterns', []),
            top_phrases=voice_guide.get('vocabulary', {}).get('top_phrases', []),
            avoid_phrases=voice_guide.get('vocabulary', {}).get('taboo_phrases', []),
            signature_moves=voice_guide.get('signature_moves', []),
            micro_examples=voice_guide.get('micro_examples')
        )
    
    def _convert_to_run_toggles(self, request: Optional[Dict[str, Any]]) -> RunToggles:
        """Convert request dict to RunToggles type."""
        if not request:
            return RunToggles(session_length=7)
        
        return RunToggles(
            session_length=request.get('session_length', 7),
            platform_focus=request.get('platforms'),
            tone_override=request.get('tone'),
            keywords=request.get('keywords'),
            goals=request.get('goals'),
            promo_note=request.get('promo_note'),
            reel_toggles=request.get('reel_options'),
            variants=request.get('variants', 1)
        )
    
    def generate_with_compiler(
        self,
        content_type: str,
        request_id: Optional[str] = None,
        workspace: Optional[Dict[str, Any]] = None,
        voice_samples: Optional[List[str]] = None,
        include_phrases: Optional[List[str]] = None,
        avoid_phrases: Optional[List[str]] = None,
        request: Optional[Dict[str, Any]] = None,
        review_text: Optional[str] = None,
        rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate content using the new PromptCompiler approach.
        
        This is the new unified generation method that uses PromptCompiler.
        
        Args:
            content_type: Type of content ('social', 'reels', 'reviews')
            request_id: Optional request ID
            workspace: Workspace settings
            voice_samples: Voice samples for fingerprint
            include_phrases: Phrases to include
            avoid_phrases: Phrases to avoid
            request: Request parameters
            review_text: Review text (for reviews only)
            rating: Rating (for reviews only)
            
        Returns:
            Success or error response dict
        """
        request_id = request_id or self._generate_request_id()
        logger.info(f"[{request_id}] Generating {content_type} with PromptCompiler")
        
        try:
            # Convert inputs to PromptCompiler types
            profile_defaults = self._convert_to_profile_defaults(workspace)
            voice_fingerprint = self._convert_to_voice_fingerprint(
                voice_samples, include_phrases, avoid_phrases
            )
            run_toggles = self._convert_to_run_toggles(request)
            
            # Create compiler
            compiler = PromptCompiler(
                profile_defaults=profile_defaults,
                voice_fingerprint=voice_fingerprint
            )
            
            # Compile prompt based on content type
            if content_type == 'social':
                compiler_output = compiler.compile_for_social(run_toggles, request_id)
            elif content_type == 'reels':
                compiler_output = compiler.compile_for_reels(run_toggles, request_id)
            elif content_type == 'reviews':
                if not review_text:
                    return self._build_error_response(
                        request_id=request_id,
                        code='missing_parameter',
                        message='Review text is required'
                    )
                compiler_output = compiler.compile_for_reviews(
                    run_toggles, review_text, rating, request_id
                )
            else:
                return self._build_error_response(
                    request_id=request_id,
                    code='invalid_content_type',
                    message=f'Unknown content type: {content_type}'
                )
            
            # Log prompt trace
            trace = create_trace_from_compiler_output(compiler_output)
            trace.log_trace('info')
            
            # Get prompt set for generation
            prompt_set = compiler_output['prompt_set']
            json_schema = compiler_output['json_schema']
            
            # Try OpenAI generation
            openai_used = False
            data = None
            
            if self.openai_client:
                try:
                    logger.info(f"[{request_id}] Attempting OpenAI generation with compiled prompt")
                    
                    # Build messages from prompt set
                    messages = [
                        {"role": "system", "content": prompt_set['system']},
                        {"role": "user", "content": f"{prompt_set['context']}\n\n{prompt_set['request']}"}
                    ]
                    
                    # Generate
                    result = self.openai_client.generate_structured(messages)
                    
                    # Validate with schema enforcement (includes repair pass)
                    validation_result = validate_with_schema_enforcement(
                        result,
                        content_type,
                        openai_client=self.openai_client,
                        prompt_set=prompt_set,
                        json_schema=json_schema
                    )
                    
                    if validation_result['ok']:
                        data = validation_result['data']
                        openai_used = True
                        logger.info(
                            f"[{request_id}] OpenAI generation successful "
                            f"(repaired: {validation_result.get('repaired', False)})"
                        )
                    else:
                        logger.warning(f"[{request_id}] Validation failed: {validation_result['error']}")
                    
                except Exception as e:
                    logger.warning(f"[{request_id}] OpenAI generation failed: {e}, falling back")
            
            # Fallback if needed
            if data is None:
                logger.info(f"[{request_id}] Using fallback generation")
                data = self._generate_fallback(
                    content_type,
                    compiler_output['model_context'],
                    review_text,
                    rating
                )
            
            # Check for sensitive content and build response
            warnings = self._check_sensitive_content(data, content_type)
            
            return self._build_success_response(
                request_id=request_id,
                data=data,
                openai_used=openai_used,
                summary={
                    'voice_applied': compiler_output['model_context'].get('voice_applied', False),
                    'template_applied': compiler_output['model_context'].get('template_applied', False),
                    'prompt_compiler_used': True
                },
                warnings=warnings if warnings else None
            )
            
        except Exception as e:
            logger.exception(f"[{request_id}] Generation with compiler failed: {e}")
            return self._build_error_response(
                request_id=request_id,
                code='generation_failed',
                message=f'Failed to generate {content_type}'
            )
    
    def _generate_fallback(
        self,
        content_type: str,
        model_context: Dict[str, Any],
        review_text: Optional[str] = None,
        rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate fallback content based on content type."""
        if content_type == 'social':
            result = generate_social_posts_fallback(
                session_length=model_context.get('session_length', 7),
                platforms=model_context.get('platforms', []),
                tone=model_context.get('tone', 'professional'),
                industry=model_context.get('industry', 'business'),
                company_name=model_context.get('company_name', ''),
                goals=model_context.get('goals'),
                keywords=model_context.get('keywords')
            )
            return validate_and_repair_social_posts(result)
        
        elif content_type == 'reels':
            result = generate_reel_script_fallback(
                tone=model_context.get('tone', 'professional'),
                industry=model_context.get('industry', 'business')
            )
            return validate_and_repair_reel_script(result)
        
        elif content_type == 'reviews':
            result = generate_review_response_fallback(
                review_text=review_text or '',
                rating=rating,
                tone=model_context.get('tone', 'professional'),
                company_name=model_context.get('company_name', '')
            )
            return validate_and_repair_review_responses(result)
        
        else:
            raise ValueError(f'Unknown content type: {content_type}')
    
    def _check_sensitive_content(self, data: Dict[str, Any], content_type: str) -> Optional[List[str]]:
        """Check for and sanitize sensitive content."""
        warnings = []
        
        if content_type == 'social':
            for post in data.get('posts', []):
                for card in post.get('cards', []):
                    caption = card.get('caption', '')
                    if warning := detect_sensitive_content(caption):
                        warnings.append(warning)
                        card['caption'] = sanitize_public_content(caption)
        
        elif content_type == 'reels':
            script = data.get('script', {})
            for field in ['hook', 'caption']:
                if text := script.get(field):
                    if warning := detect_sensitive_content(text):
                        warnings.append(f"{field}: {warning}")
                        script[field] = sanitize_public_content(text)
        
        elif content_type == 'reviews':
            responses = data.get('responses', {})
            for key in ['short', 'medium', 'long']:
                if text := responses.get(key):
                    if warning := detect_sensitive_content(text):
                        warnings.append(f"{key}: {warning}")
                        responses[key] = sanitize_public_content(text)
        
        return warnings if warnings else None
