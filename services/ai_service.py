import os
import logging

# Prefer the new google.genai package; fall back gracefully if unavailable
try:
    import google.genai as genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore

logger = logging.getLogger(__name__)

# Preferred models in order of priority
PREFERRED_MODELS = [
    'gemini-1.5-flash',
    'gemini-1.5-flash-001',
    'gemini-1.5-pro',
    'gemini-pro',
]


def _get_client():
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or not genai:
        return None

    # google.genai exposes Client; older google.generativeai exposed configure/list_models
    if hasattr(genai, "Client"):
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:  # pragma: no cover - best-effort
            logger.error(f"Failed to init genai.Client: {e}")
            return None

    # Compatibility: if legacy interface still exists, configure globally
    try:
        if hasattr(genai, "configure"):
            genai.configure(api_key=api_key)
        return genai
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to configure genai: {e}")
        return None


def get_best_available_model():
    """Find the best available Gemini model with a safe fallback."""
    client = _get_client()
    if client is None:
        logger.error("No API key configured for AI service or genai client unavailable.")
        return 'gemini-1.5-flash'  # Default expectation

    try:
        available_models = []

        # New google.genai client: models.list(); legacy: list_models()
        if hasattr(client, "models") and hasattr(client.models, "list"):
            for m in client.models.list():
                name = getattr(m, "name", "")
                methods = getattr(m, "supported_generation_methods", []) or []
                if any("generateContent" in str(method) for method in methods):
                    available_models.append(name)
        elif hasattr(client, "list_models"):
            for m in client.list_models():
                name = getattr(m, "name", "")
                methods = getattr(m, "supported_generation_methods", []) or []
                if any("generateContent" in str(method) for method in methods):
                    available_models.append(name)

        logger.info(f"Available Gemini Models: {available_models}")

        for preference in PREFERRED_MODELS:
            if preference in available_models or f"models/{preference}" in available_models:
                logger.info(f"Selected AI Model: {preference}")
                return preference

        for m in available_models:
            if 'gemini' in m:
                logger.warning(f"Preferred models not found. Falling back to: {m}")
                return m

    except Exception as e:
        logger.error(f"Failed to list models: {e}. Defaulting to gemini-1.5-flash")

    return 'gemini-1.5-flash'


def get_generative_model(model_name=None, system_instruction=None):
    """Factory returning an object with generate_content compatible interface."""
    client = _get_client()
    if not client:
        return None

    if not model_name:
        model_name = get_best_available_model()

    # google.genai uses client.models.generate_content; provide a thin adapter with generate_content
    if hasattr(client, "models") and hasattr(client.models, "generate_content"):
        model = model_name

        class _ModelAdapter:  # pragma: no cover - simple proxy
            def __init__(self, client_ref, model_ref, system_instruction_ref):
                self._client = client_ref
                self._model = model_ref
                self._system_instruction = system_instruction_ref

            def generate_content(self, contents):
                return self._client.models.generate_content(
                    model=self._model,
                    contents=contents,
                    system_instruction=self._system_instruction,
                )

        return _ModelAdapter(client, model, system_instruction)

    # Legacy compatibility if genai exposes GenerativeModel
    if hasattr(client, "GenerativeModel"):
        return client.GenerativeModel(model_name, system_instruction=system_instruction)

    return None
