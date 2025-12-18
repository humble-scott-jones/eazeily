import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

JsonDict = Dict[str, Any]


@dataclass
class GenerationResponse:
    ok: bool
    status: int
    body: JsonDict
    gemini_used: bool
    outcome: str


class GenerationService:
    def __init__(self, *, logger: Optional[logging.Logger] = None, timeout_seconds: float = 15.0):
        self.logger = logger or logging.getLogger(__name__)
        self.timeout_seconds = timeout_seconds
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _run_with_timeout(self, func: Callable[[], Any]):
        future = self._executor.submit(func)
        try:
            return future.result(timeout=self.timeout_seconds)
        except FutureTimeout:
            future.cancel()
            raise TimeoutError("Generation timed out")

    def _classify_gemini_error(self, exc: Exception) -> str:
        message = f"{type(exc).__name__}: {exc}".lower()
        if isinstance(exc, TimeoutError) or "timeout" in message:
            return "timeout"
        if "rate" in message and "limit" in message:
            return "rate_limit"
        if "auth" in message or "unauthorized" in message or "api key" in message:
            return "auth"
        if isinstance(exc, ValueError):
            return "bad_output"
        return "unknown"

    def _build_error(self, *, code: str, request_id: str, message: str, status: int, gemini_used: bool, outcome: str, source: str = "fallback") -> GenerationResponse:
        body = {
            "ok": False,
            "request_id": request_id,
            "source": source,
            "mode": "error",
            "error": {
                "code": code,
                "message": message,
            },
        }
        return GenerationResponse(ok=False, status=status, body=body, gemini_used=gemini_used, outcome=outcome)

    def generate(
        self,
        *,
        endpoint: str,
        request_id: str,
        payload: Mapping[str, Any],
        validator: Callable[[Mapping[str, Any]], Mapping[str, str]],
        normalizer: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        output_validator: Callable[[Any], Any],
        gemini_callable: Optional[Callable[[Mapping[str, Any]], Any]] = None,
        fallback_callable: Optional[Callable[[Mapping[str, Any]], Any]] = None,
        use_gemini: bool = False,
        disable_fallback: bool = False,
    ) -> GenerationResponse:
        start_ts = time.time()
        gemini_used = False
        try:
            validation_errors = validator(payload)
            if validation_errors:
                first_error = next(iter(validation_errors.values()))
                return self._build_error(
                    code="validation_error",
                    request_id=request_id,
                    message=str(first_error),
                    status=400,
                    gemini_used=False,
                    outcome="validation_error",
                )
            normalized = normalizer(payload)
        except Exception:
            self.logger.exception("generation.validation_failed", extra={"request_id": request_id, "endpoint": endpoint})
            return self._build_error(
                code="validation_error",
                request_id=request_id,
                message="Invalid request.",
                status=400,
                gemini_used=False,
                outcome="validation_exception",
            )

        source = "fallback"
        data = None
        error_code = "unknown"

        if use_gemini and gemini_callable:
            try:
                data = self._run_with_timeout(lambda: gemini_callable(normalized))
                source = "gemini"
                gemini_used = True
            except Exception as exc:
                gemini_used = True
                error_code = self._classify_gemini_error(exc)
                if error_code == "timeout":
                    self._log_outcome(endpoint, request_id, start_ts, outcome="timeout", gemini_used=gemini_used)
                    return self._build_error(
                        code="timeout",
                        request_id=request_id,
                        message="Generation timed out.",
                        status=504,
                        gemini_used=gemini_used,
                        outcome="timeout",
                    )
                self.logger.warning(
                    "generation.gemini_failed",
                    extra={"request_id": request_id, "endpoint": endpoint, "error_code": error_code},
                )
                
                # If fallback is disabled, return error immediately
                if disable_fallback:
                    return self._build_error(
                        code=error_code,
                        request_id=request_id,
                        message="AI generation failed and fallback is disabled.",
                        status=503,
                        gemini_used=gemini_used,
                        outcome=error_code,
                        source="gemini",
                    )

        if data is None and fallback_callable and not disable_fallback:
            try:
                data = self._run_with_timeout(lambda: fallback_callable(normalized))
                source = "fallback"
            except Exception as exc:
                self.logger.exception(
                    "generation.fallback_failed",
                    extra={"request_id": request_id, "endpoint": endpoint, "gemini_used": gemini_used},
                )
                if isinstance(exc, TimeoutError):
                    return self._build_error(
                        code="timeout",
                        request_id=request_id,
                        message="Generation timed out.",
                        status=504,
                        gemini_used=gemini_used,
                        outcome="timeout",
                    )

                outcome = error_code or "unknown"
                return self._build_error(
                    code=outcome or "unknown",
                    request_id=request_id,
                    message="Generation failed.",
                    status=500,
                    gemini_used=gemini_used,
                    outcome=outcome,
                )

        if data is None:
            return self._build_error(
                code="unknown",
                request_id=request_id,
                message="Generation failed.",
                status=500,
                gemini_used=gemini_used,
                outcome="no_data",
            )

        try:
            validated_data = output_validator(data)
        except Exception:
            self.logger.warning(
                "generation.bad_output",
                extra={"request_id": request_id, "endpoint": endpoint, "source": source},
            )
            if source == "gemini" and fallback_callable:
                try:
                    data = self._run_with_timeout(lambda: fallback_callable(normalized))
                    validated_data = output_validator(data)
                    source = "fallback"
                except Exception:
                    return self._build_error(
                        code="bad_output",
                        request_id=request_id,
                        message="Generation produced invalid output.",
                        status=500,
                        gemini_used=gemini_used,
                        outcome="bad_output",
                    )
            else:
                return self._build_error(
                    code="bad_output",
                    request_id=request_id,
                    message="Generation produced invalid output.",
                    status=500,
                    gemini_used=gemini_used,
                    outcome="bad_output",
                )

        latency_ms = int((time.time() - start_ts) * 1000)
        self._log_outcome(
            endpoint,
            request_id,
            start_ts,
            outcome="success",
            gemini_used=gemini_used,
            extra={"source": source, "latency_ms": latency_ms},
        )

        # Build response with source and mode
        mode = "generated" if source == "gemini" else "fallback_suggestions"
        body = {
            "ok": True,
            "request_id": request_id,
            "source": source,
            "mode": mode,
            "data": validated_data
        }
        
        # Add warnings if using fallback
        if source == "fallback":
            body["warnings"] = ["AI generation temporarily unavailable - showing template suggestions"]
        
        return GenerationResponse(
            ok=True,
            status=200,
            body=body,
            gemini_used=gemini_used,
            outcome="success",
        )

    def _log_outcome(self, endpoint: str, request_id: str, start_ts: float, *, outcome: str, gemini_used: bool, extra: Optional[dict] = None):
        latency_ms = int((time.time() - start_ts) * 1000)
        payload = {
            "endpoint": endpoint,
            "request_id": request_id,
            "latency_ms": latency_ms,
            "outcome": outcome,
            "gemini_used": gemini_used,
        }
        if extra:
            payload.update(extra)
        self.logger.info("generation.outcome", extra=payload)
