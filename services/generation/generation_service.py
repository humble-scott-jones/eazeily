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
from .openai_client import create_client as create_openai_client
from .output_validator import (
    validate_and_repair_social_posts,
    validate_and_repair_reel_script,
    validate_and_repair_review_responses,
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


logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating content with context awareness and voice personalization."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
        enable_openai: bool = True
    ):
        """Initialize generation service.
        
        Args:
            openai_api_key: Optional OpenAI API key
            openai_model: Optional OpenAI model name
            enable_openai: Whether to use OpenAI (default True)
        """
        self.openai_client = None
        if enable_openai:
            self.openai_client = create_openai_client(
                api_key=openai_api_key,
                model=openai_model
            )
        
        logger.info(
            f"GenerationService initialized (OpenAI: {'enabled' if self.openai_client else 'disabled'})"
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
        return {
            'ok': True,
            'request_id': request_id,
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
                    keywords=params.get('keywords')
                )
                data = validate_and_repair_social_posts(fallback_result)
            
            # Check for sensitive content in posts
            warnings = []
            for post in data.get('posts', []):
                for card in post.get('cards', []):
                    caption = card.get('caption', '')
                    if warning := detect_sensitive_content(caption):
                        warnings.append(warning)
                        card['caption'] = sanitize_public_content(caption)
            
            # Build response
            return self._build_success_response(
                request_id=request_id,
                data=data,
                openai_used=openai_used,
                summary={
                    'posts_generated': data.get('count', 0),
                    'voice_applied': voice_guide is not None
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
