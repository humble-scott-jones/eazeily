"""Prompt Trace - redacted logging for prompt debugging.

Stores prompt compilation metadata without exposing user PII.
Useful for debugging generation issues and analyzing prompt patterns.
"""

import re
import logging
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


# PII patterns to redact
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
ADDRESS_PATTERN = re.compile(r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|lane|ln|drive|dr|way|court|ct)\b', re.IGNORECASE)


def redact_pii(text: str) -> str:
    """Redact PII from text.
    
    Args:
        text: Input text potentially containing PII
        
    Returns:
        Text with PII redacted
    """
    if not text:
        return text
    
    # Redact emails
    text = EMAIL_PATTERN.sub('[EMAIL]', text)
    
    # Redact phone numbers
    text = PHONE_PATTERN.sub('[PHONE]', text)
    
    # Redact addresses
    text = ADDRESS_PATTERN.sub('[ADDRESS]', text)
    
    return text


def hash_text(text: str, length: int = 8) -> str:
    """Create short hash of text for tracking without exposing content.
    
    Args:
        text: Text to hash
        length: Hash length (default 8 chars)
        
    Returns:
        Short hash string
    """
    if not text:
        return ''
    
    hash_obj = hashlib.sha256(text.encode('utf-8'))
    return hash_obj.hexdigest()[:length]


class PromptTrace:
    """Stores redacted trace of prompt compilation for debugging."""
    
    def __init__(self, request_id: str):
        """Initialize trace.
        
        Args:
            request_id: Request identifier
        """
        self.request_id = request_id
        self.timestamp = datetime.utcnow().isoformat()
        self.metadata: Dict[str, Any] = {
            'request_id': request_id,
            'timestamp': self.timestamp
        }
    
    def set_content_type(self, content_type: str):
        """Set content type (social, reels, reviews).
        
        Args:
            content_type: Type of content being generated
        """
        self.metadata['content_type'] = content_type
    
    def set_selections(
        self,
        tone: Optional[str] = None,
        platforms: Optional[list] = None,
        session_length: Optional[int] = None,
        goals: Optional[list] = None,
        keywords: Optional[list] = None
    ):
        """Record user selections (safe - no PII).
        
        Args:
            tone: Selected tone
            platforms: Selected platforms
            session_length: Session length
            goals: Content goals
            keywords: Keywords
        """
        selections = {}
        
        if tone:
            selections['tone'] = tone
        if platforms:
            selections['platforms'] = platforms
        if session_length is not None:
            selections['session_length'] = session_length
        if goals:
            selections['goals_count'] = len(goals)
            # Store first 2 goals as examples (usually safe)
            selections['goals_sample'] = goals[:2]
        if keywords:
            selections['keywords_count'] = len(keywords)
            # Store hashes of keywords to track uniqueness
            selections['keywords_hash'] = hash_text(','.join(keywords))
        
        self.metadata['selections'] = selections
    
    def set_voice_fingerprint_applied(self, applied: bool, sample_count: Optional[int] = None):
        """Record whether voice fingerprint was applied.
        
        Args:
            applied: Whether voice fingerprint was used
            sample_count: Number of voice samples (if available)
        """
        self.metadata['voice_fingerprint'] = {
            'applied': applied,
            'sample_count': sample_count
        }
    
    def set_template_used(self, template_name: Optional[str]):
        """Record template usage.
        
        Args:
            template_name: Name of template (or None)
        """
        self.metadata['template'] = {
            'used': bool(template_name),
            'name': template_name if template_name else None
        }
    
    def set_token_estimate(self, token_count: int):
        """Record estimated token count.
        
        Args:
            token_count: Estimated tokens in prompt
        """
        self.metadata['token_budget'] = token_count
    
    def set_model_info(self, model: str, provider: str = 'openai'):
        """Record model information.
        
        Args:
            model: Model name
            provider: Provider name
        """
        self.metadata['model'] = {
            'provider': provider,
            'model': model
        }
    
    def set_compilation_time_ms(self, time_ms: float):
        """Record compilation time.
        
        Args:
            time_ms: Compilation time in milliseconds
        """
        self.metadata['compilation_time_ms'] = round(time_ms, 2)
    
    def add_flag(self, flag_name: str, value: Any):
        """Add custom flag to trace.
        
        Args:
            flag_name: Flag name
            value: Flag value
        """
        if 'flags' not in self.metadata:
            self.metadata['flags'] = {}
        self.metadata['flags'][flag_name] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get trace summary (safe for logging).
        
        Returns:
            Redacted trace summary
        """
        return self.metadata.copy()
    
    def log_trace(self, level: str = 'info'):
        """Log trace summary.
        
        Args:
            level: Log level (info, debug, warning)
        """
        summary = self.get_summary()
        log_fn = getattr(logger, level, logger.info)
        log_fn(f"[{self.request_id}] Prompt trace: {summary}")


def create_trace_from_compiler_output(compiler_output: Dict[str, Any]) -> PromptTrace:
    """Create trace from compiler output.
    
    Args:
        compiler_output: Output from PromptCompiler
        
    Returns:
        PromptTrace instance
    """
    trace_summary = compiler_output.get('trace_summary', {})
    request_id = trace_summary.get('request_id', 'unknown')
    
    trace = PromptTrace(request_id)
    
    # Set content type
    if content_type := trace_summary.get('content_type'):
        trace.set_content_type(content_type)
    
    # Set selections
    if selections := trace_summary.get('selections'):
        trace.set_selections(
            tone=selections.get('tone'),
            platforms=selections.get('platforms'),
            session_length=selections.get('session_length')
        )
    
    # Set voice fingerprint
    if voice_applied := trace_summary.get('voice_fingerprint_applied'):
        trace.set_voice_fingerprint_applied(voice_applied)
    
    # Set template
    if template_name := trace_summary.get('template_used'):
        trace.set_template_used(template_name)
    
    # Set token estimate
    if token_estimate := trace_summary.get('token_budget_estimate'):
        trace.set_token_estimate(token_estimate)
    
    return trace
