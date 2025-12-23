"""OpenAI stub shim.

This repository will no longer use the OpenAI API. To make the removal safe and
reversible we'll provide a small shim that always reports OpenAI as unavailable
and returns None from create_client().

This prevents accidental outbound calls even when the `openai` package is
present in the environment. Modules throughout the codebase already handle
``openai_client is None`` cases and will fall back to deterministic/local
generation.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Force OpenAI to be treated as unavailable regardless of installed packages.
OPENAI_AVAILABLE = False


class OpenAIClient:
    """Placeholder OpenAIClient - instantiating is an explicit error.

    Keeping the class present lets older imports succeed but ensures any
    accidental instantiation fails loudly.
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError("OpenAI support has been removed from this build")


def create_client(api_key: Optional[str] = None, model: Optional[str] = None) -> Optional[OpenAIClient]:
    """Return None to indicate OpenAI is not available.

    Other modules should detect this and use fallback generation.
    """
    logger.info("OpenAI client requested but OpenAI support is disabled; returning None")
    return None
