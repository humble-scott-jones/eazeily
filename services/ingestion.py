import os
import requests
from typing import Optional

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency
    genai = None


def ingest_url(url: str) -> str:
    """Fetch rendered markdown via the jina.ai markdown proxy.

    The caller should pass a URL path (or full url encoded path) that will be
    appended to the Jina lightweight renderer. Example: for `example.com` call
    `ingest_url('https://example.com')` which becomes requests.get('https://r.jina.ai/https://example.com').
    """
    try:
        target = f"https://r.jina.ai/{url}"
        resp = requests.get(target, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return ""


def ingest_file(path: str) -> Optional[dict]:
    """Upload a local file to Gemini's file API if available.

    Returns a small dict with any useful metadata (id/url) when possible.
    """
    if genai and hasattr(genai, 'upload_file'):
        try:
            # API shape may vary; many SDKs accept a path/file-like
            upload = getattr(genai, 'upload_file')
            result = upload(path)
            return result
        except Exception:
            pass

    # fallback: return basic file metadata
    try:
        size = os.path.getsize(path)
        return {"path": path, "size": size}
    except Exception:
        return None
