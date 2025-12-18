"""Gemini client wrapper with retry logic and structured output."""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

# Optional Gemini import
try:
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    google_exceptions = None
    GEMINI_AVAILABLE = False


logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for Gemini API calls with retry logic and structured output."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = 'gemini-1.5-pro-latest',
        timeout: float = 30.0,
        max_retries: int = 2
    ):
        """Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model to use for generation
            timeout: Request timeout in seconds (Note: Gemini client doesn't directly support a timeout on generate_content)
            max_retries: Max retry attempts for transient errors
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key required")
        
        genai.configure(api_key=self.api_key)
        
        self.model = genai.GenerativeModel(model)
        self.timeout = timeout
        self.max_retries = max_retries

    def _should_retry(self, error: Exception) -> bool:
        """Determine if error is transient and should be retried."""
        if isinstance(error, (
            google_exceptions.ResourceExhausted,  # Rate limiting
            google_exceptions.ServiceUnavailable,
            google_exceptions.DeadlineExceeded,
            google_exceptions.InternalServerError,
            google_exceptions.BadGateway
        )):
            return True
        
        error_msg = str(error).lower()
        transient_keywords = ['timeout', 'rate limit', 'try again', 'temporarily', 'service unavailable']
        return any(keyword in error_msg for keyword in transient_keywords)

    def _extract_json_from_response(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract JSON from Gemini response."""
        try:
            # Gemini response text should be the content
            content = response.text
            if isinstance(content, str):
                # Try to parse as JSON
                content = content.strip()
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    lines = content.split('\n')
                    # Remove first line (```json or ```)
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    # Remove last line (```)
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    content = '\n'.join(lines).strip()
                
                return json.loads(content)
            
            # If response is already a dict, return it
            if isinstance(response, dict):
                return response
            
            return None
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            logger.warning(f"Failed to extract JSON from response: {e}")
            return None

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON output from Gemini.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_instruction: Optional system instruction to override model's default
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            
        Returns:
            Parsed JSON dict
            
        Raises:
            Exception: On API errors or if response is not valid JSON
        """
        last_error = None
        
        # Prioritize the explicit system_instruction if provided
        final_system_instruction = system_instruction
        if not final_system_instruction:
            final_system_instruction = next((m['content'] for m in messages if m['role'] == 'system'), None)
        
        history = [m for m in messages if m['role'] in ('user', 'assistant', 'model')]
        current_prompt = history.pop(-1)['content'] if history else ''

        # Re-initialize model with system prompt if provided
        model = self.model
        if final_system_instruction:
             model = genai.GenerativeModel(self.model.model_name, system_instruction=final_system_instruction)
        
        generation_config = {
            "temperature": temperature,
            "response_mime_type": "application/json",
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        for attempt in range(self.max_retries + 1):
            try:
                # Make API call
                response = model.generate_content(
                    current_prompt,
                    generation_config=generation_config,
                    history=history,
                )
                
                # Extract and parse JSON
                result = self._extract_json_from_response(response)
                if result is None:
                    raise ValueError("Response did not contain valid JSON")
                
                return result
                
            except Exception as e:
                last_error = e
                
                if not self._should_retry(e):
                    logger.error(f"Gemini API error (non-retryable): {e}")
                    raise
                
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0  # exponential backoff
                    logger.warning(
                        f"Gemini API error (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Gemini API error after {self.max_retries + 1} attempts: {e}")
                    raise
        
        raise last_error or Exception("Gemini generation failed")

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate plain text output from Gemini.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_instruction: Optional system instruction to override model's default
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            Exception: On API errors
        """
        last_error = None
        
        final_system_instruction = system_instruction
        if not final_system_instruction:
            final_system_instruction = next((m['content'] for m in messages if m['role'] == 'system'), None)

        history = [m for m in messages if m['role'] in ('user', 'assistant', 'model')]
        current_prompt = history.pop(-1)['content'] if history else ''

        model = self.model
        if final_system_instruction:
             model = genai.GenerativeModel(self.model.model_name, system_instruction=final_system_instruction)

        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        for attempt in range(self.max_retries + 1):
            try:
                response = model.generate_content(
                    current_prompt,
                    generation_config=generation_config,
                    history=history,
                )
                
                return response.text
                
            except Exception as e:
                last_error = e
                
                if not self._should_retry(e):
                    logger.error(f"Gemini API error (non-retryable): {e}")
                    raise
                
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(
                        f"Gemini API error (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Gemini API error after {self.max_retries + 1} attempts: {e}")
                    raise
        
        raise last_error or Exception("Gemini generation failed")


def create_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[GeminiClient]:
    """Create Gemini client if available and configured.
    
    Args:
        api_key: Optional API key (defaults to env var)
        model: Optional model name (defaults to env var or gemini-1.5-pro-latest)
        
    Returns:
        GeminiClient instance or None if not available
    """
    if not GEMINI_AVAILABLE:
        return None
    
    api_key = api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    
    model = model or os.getenv('GEMINI_GENERATE_MODEL', 'gemini-1.5-pro-latest')
    
    try:
        return GeminiClient(api_key=api_key, model=model)
    except Exception as e:
        logger.warning(f"Failed to create Gemini client: {e}")
        return None

