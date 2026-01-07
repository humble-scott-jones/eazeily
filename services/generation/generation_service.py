from __future__ import annotations

"""Lightweight shim to keep imports working under ``services.generation``.

The real implementation lives at repository root in ``generation_service.py``.
This proxy simply re-exports the public classes so callers importing from
``services.generation.generation_service`` continue to work without duplication.
"""

from generation_service import GenerationService, GenerationResponse

__all__ = ["GenerationService", "GenerationResponse"]
