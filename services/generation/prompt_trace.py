from __future__ import annotations
import hashlib
import re
from typing import Any, Dict

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d .-]{7,}\d)")
ADDRESS_RE = re.compile(r"\d+\s+\w+\s+(street|st|road|rd|avenue|ave|blvd|lane|ln)", re.I)


def redact_pii(text: str) -> str:
    if not text:
        return ""
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    text = ADDRESS_RE.sub("[ADDRESS]", text)
    return text


def hash_text(text: str, length: int = 8) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


class PromptTrace:
    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.selections: Dict[str, Any] = {}
        self.prompt_set: Dict[str, Any] = {}

    def set_selections(self, **kwargs) -> None:
        safe = {}
        for key, value in kwargs.items():
            if key in {"keywords", "goals"} and isinstance(value, list):
                safe[f"{key}_count"] = len(value)
            else:
                safe[key] = value
        self.selections.update(safe)

    def set_prompt_set(self, prompt_set: Dict[str, Any]) -> None:
        self.prompt_set = {k: redact_pii(str(v)) for k, v in (prompt_set or {}).items()}

    def get_summary(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "selections": self.selections,
            "prompt_set": self.prompt_set,
        }


def create_trace_from_compiler_output(request_id: str, compiler_output: Dict[str, Any]) -> PromptTrace:
    trace = PromptTrace(request_id)
    ctx = compiler_output.get("model_context", {})
    trace.set_selections(
        tone=ctx.get("tone"),
        platforms=ctx.get("platforms", []),
        session_length=ctx.get("session_length"),
        goals=ctx.get("goals", []),
        keywords=ctx.get("keywords", []),
    )
    trace.set_prompt_set(compiler_output.get("prompt_set", {}))
    return trace
