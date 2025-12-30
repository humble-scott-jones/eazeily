from typing import Callable, Any, Optional


def make_openai_callable(generation_service: Any, openai_client: Optional[Any] = None) -> Optional[Callable]:
    """Return a callable that mimics an OpenAI-like client call.

    For now this returns None (no-op) unless an `openai_client` is provided.
    Keeping the adapter lightweight avoids importing the real OpenAI SDK at
    startup in constrained environments.
    """
    if openai_client is None:
        return None

    def _call(payload: dict) -> Any:
        # A thin wrapper that delegates to the provided client if possible.
        try:
            return openai_client(**payload)
        except Exception:
            return None

    return _call
"""Compatibility adapter for legacy OpenAI call sites.

Provides a small helper that returns a callable compatible with legacy
`openai_callable` usage. When a real OpenAI client is provided the
callable will attempt to call it; when no OpenAI client is present the
callable will delegate to a Gemini client or a provided GenerationService
helper so code paths remain deterministic in this branch.

The goal is to avoid sprinkling OpenAI-specific call patterns across the
codebase while preserving test hooks that may monkeypatch an OpenAI
client object.
"""
from typing import Any, Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def make_openai_callable(
    gen_service: Optional[Any] = None,
    *,
    openai_client: Optional[Any] = None,
    gemini_client: Optional[Any] = None,
) -> Optional[Callable[[Dict[str, Any]], Any]]:
    """Return a callable compatible with legacy `openai_callable(normalized)`.

    The returned callable will try, in order:
    1. Use the provided `openai_client` (if present) with common call shapes.
    2. Use the provided `gemini_client` if it exposes a `generate_structured` or
       `chat.completions.create` API.
    3. Use the `gen_service.generate_text` helper if a GenerationService was
       provided.

    If none of the backends are available, return None.
    """

    if not (openai_client or gemini_client or gen_service):
        return None

    def _call(normalized: Dict[str, Any]) -> Any:
        # First, prefer explicit OpenAI client if available
        if openai_client:
            try:
                # Common OpenAI v1 style: client.chat.completions.create(...)
                chat = getattr(openai_client, 'chat', None)
                if chat and hasattr(chat, 'completions'):
                    return chat.completions.create(**normalized)

                # Some test doubles are callables
                if callable(openai_client):
                    return openai_client(normalized)

                # Fallback: direct create method
                if hasattr(openai_client, 'create'):
                    return openai_client.create(**normalized)
            except Exception:
                logger.exception('openai_adapter: openai_client call failed')
                raise

        # Next, try gemini client if present
        if gemini_client:
            try:
                # try structured API first
                if hasattr(gemini_client, 'generate_structured'):
                    # Many callers pass `messages` and `system_instruction`
                    msgs = normalized.get('messages') if isinstance(normalized, dict) else None
                    system_instruction = normalized.get('system_instruction') if isinstance(normalized, dict) else None
                    if msgs:
                        return gemini_client.generate_structured(msgs, system_instruction=system_instruction)
                    # If no messages, try passing raw prompt
                    prompt = normalized.get('prompt') if isinstance(normalized, dict) else None
                    if prompt:
                        return gemini_client.generate_structured([{'role': 'user', 'content': prompt}], system_instruction=system_instruction)

                # Try chat.completions.create shape
                chat = getattr(gemini_client, 'chat', None)
                if chat and hasattr(chat, 'completions'):
                    return chat.completions.create(**normalized)
            except Exception:
                logger.exception('openai_adapter: gemini_client call failed')
                raise

        # Finally, fallback to GenerationService helper if available
        if gen_service and hasattr(gen_service, 'generate_text'):
            try:
                msgs = normalized.get('messages') if isinstance(normalized, dict) else None
                system_instruction = normalized.get('system_instruction') if isinstance(normalized, dict) else None
                if msgs:
                    return gen_service.generate_text(messages=msgs, system_instruction=system_instruction, temperature=normalized.get('temperature', 0.3))
                # If normalized contains a 'prompt' or 'request' string, coerce to messages
                prompt = normalized.get('prompt') if isinstance(normalized, dict) else None
                if prompt:
                    return gen_service.generate_text(messages=[{'role': 'user', 'content': prompt}], system_instruction=system_instruction, temperature=normalized.get('temperature', 0.3))
                # As a last resort, stringify normalized payload
                return gen_service.generate_text(messages=[{'role': 'user', 'content': str(normalized)}], system_instruction=system_instruction)
            except Exception:
                logger.exception('openai_adapter: gen_service.generate_text failed')
                raise

        # No backend could handle the request
        raise RuntimeError('No AI backend available')

    return _call
