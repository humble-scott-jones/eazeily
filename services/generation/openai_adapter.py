from __future__ import annotations
from typing import Any, Callable, Mapping, Optional

"""OpenAI path removed: return None to force Gemini-only execution."""


def make_openai_callable(service: Any = None, openai_client: Any = None) -> Optional[Callable[[Mapping[str, Any]], Any]]:
    return None
