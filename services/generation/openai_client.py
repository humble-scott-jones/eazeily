"""OpenAI client wrapper with retry logic and structured output."""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

# Optional OpenAI import
try:
    from openai import OpenAI, OpenAIError, RateLimitError, APITimeoutError
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OpenAIError = Exception
    RateLimitError = Exception
    APITimeoutError = Exception
    OPENAI_AVAILABLE = False


logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI API calls with retry logic and structured output."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = 'gpt-4o-mini',
        timeout: float = 30.0,
        max_retries: int = 2
    ):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for generation
            timeout: Request timeout in seconds
            max_retries: Max retry attempts for transient errors
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _should_retry(self, error: Exception) -> bool:
        """Determine if error is transient and should be retried."""
        # Retry on rate limits and timeouts
        if isinstance(error, (RateLimitError, APITimeoutError)):
            return True
        
        # Check error message for transient indicators
        error_msg = str(error).lower()
        transient_keywords = ['timeout', 'rate limit', 'try again', 'temporarily']
        return any(keyword in error_msg for keyword in transient_keywords)
    
    def _extract_json_from_response(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract JSON from OpenAI response."""
        try:
            # Try to get content from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content
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
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to extract JSON from response: {e}")
            return None
    
    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON output from OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Max tokens to generate
            
        Returns:
            Parsed JSON dict
            
        Raises:
            OpenAIError: On API errors
            ValueError: If response is not valid JSON
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout,
                    response_format={"type": "json_object"}  # Request JSON output
                )
                
                # Extract and parse JSON
                result = self._extract_json_from_response(response)
                if result is None:
                    raise ValueError("Response did not contain valid JSON")
                
                return result
                
            except Exception as e:
                last_error = e
                
                # Don't retry on non-transient errors
                if not self._should_retry(e):
                    logger.error(f"OpenAI API error (non-retryable): {e}")
                    raise
                
                # Retry with backoff
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0  # exponential backoff
                    logger.warning(
                        f"OpenAI API error (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"OpenAI API error after {self.max_retries + 1} attempts: {e}")
                    raise
        
        # Should not reach here, but just in case
        raise last_error or Exception("OpenAI generation failed")
    
    def generate_text(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate plain text output from OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Max tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            OpenAIError: On API errors
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout
                )
                
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        return str(choice.message.content or '')
                
                raise ValueError("No content in response")
                
            except Exception as e:
                last_error = e
                
                if not self._should_retry(e):
                    logger.error(f"OpenAI API error (non-retryable): {e}")
                    raise
                
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(
                        f"OpenAI API error (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"OpenAI API error after {self.max_retries + 1} attempts: {e}")
                    raise
        
        raise last_error or Exception("OpenAI generation failed")


def create_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[OpenAIClient]:
    """Create OpenAI client if available and configured.
    
    Args:
        api_key: Optional API key (defaults to env var)
        model: Optional model name (defaults to env var or gpt-4o-mini)
        
    Returns:
        OpenAIClient instance or None if not available
    """
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    model = model or os.getenv('OPENAI_GENERATE_MODEL', 'gpt-4o-mini')
    
    try:
        return OpenAIClient(api_key=api_key, model=model)
    except Exception as e:
        logger.warning(f"Failed to create OpenAI client: {e}")
        return None
