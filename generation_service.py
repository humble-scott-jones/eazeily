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
    openai_used: bool
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

    def _classify_openai_error(self, exc: Exception) -> str:
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

    def _build_error(self, *, code: str, request_id: str, message: str, status: int, openai_used: bool, outcome: str) -> GenerationResponse:
        body = {
            "ok": False,
            "request_id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }
        return GenerationResponse(ok=False, status=status, body=body, openai_used=openai_used, outcome=outcome)

    def generate(
        self,
        *,
        endpoint: str,
        request_id: str,
        payload: Mapping[str, Any],
        validator: Callable[[Mapping[str, Any]], Mapping[str, str]],
        normalizer: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        output_validator: Callable[[Any], Any],
        openai_callable: Optional[Callable[[Mapping[str, Any]], Any]] = None,
        fallback_callable: Optional[Callable[[Mapping[str, Any]], Any]] = None,
        use_openai: bool = False,
    ) -> GenerationResponse:
        start_ts = time.time()
        openai_used = False
        try:
            validation_errors = validator(payload)
            if validation_errors:
                first_error = next(iter(validation_errors.values()))
                return self._build_error(
                    code="validation_error",
                    request_id=request_id,
                    message=str(first_error),
                    status=400,
                    openai_used=False,
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
                openai_used=False,
                outcome="validation_exception",
            )

        source = "fallback"
        data = None
        error_code = "unknown"

        if use_openai and openai_callable:
            try:
                data = self._run_with_timeout(lambda: openai_callable(normalized))
                source = "openai"
                openai_used = True
            except Exception as exc:
                openai_used = True
                error_code = self._classify_openai_error(exc)
                if error_code == "timeout":
                    self._log_outcome(endpoint, request_id, start_ts, outcome="timeout", openai_used=openai_used)
                    return self._build_error(
                        code="timeout",
                        request_id=request_id,
                        message="Generation timed out.",
                        status=504,
                        openai_used=openai_used,
                        outcome="timeout",
                    )
                self.logger.warning(
                    "generation.openai_failed",
                    extra={"request_id": request_id, "endpoint": endpoint, "error_code": error_code},
                )

        if data is None and fallback_callable:
            try:
                data = self._run_with_timeout(lambda: fallback_callable(normalized))
                source = "fallback"
            except Exception as exc:
                self.logger.exception(
                    "generation.fallback_failed",
                    extra={"request_id": request_id, "endpoint": endpoint, "openai_used": openai_used},
                )
                if isinstance(exc, TimeoutError):
                    return self._build_error(
                        code="timeout",
                        request_id=request_id,
                        message="Generation timed out.",
                        status=504,
                        openai_used=openai_used,
                        outcome="timeout",
                    )

                outcome = error_code or "unknown"
                return self._build_error(
                    code=outcome or "unknown",
                    request_id=request_id,
                    message="Generation failed.",
                    status=500,
                    openai_used=openai_used,
                    outcome=outcome,
                )

        if data is None:
            return self._build_error(
                code="unknown",
                request_id=request_id,
                message="Generation failed.",
                status=500,
                openai_used=openai_used,
                outcome="no_data",
            )

        try:
            validated_data = output_validator(data)
        except Exception:
            self.logger.warning(
                "generation.bad_output",
                extra={"request_id": request_id, "endpoint": endpoint, "source": source},
            )
            if source == "openai" and fallback_callable:
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
                        openai_used=openai_used,
                        outcome="bad_output",
                    )
            else:
                return self._build_error(
                    code="bad_output",
                    request_id=request_id,
                    message="Generation produced invalid output.",
                    status=500,
                    openai_used=openai_used,
                    outcome="bad_output",
                )

        latency_ms = int((time.time() - start_ts) * 1000)
        self._log_outcome(
            endpoint,
            request_id,
            start_ts,
            outcome="success",
            openai_used=openai_used,
            extra={"source": source, "latency_ms": latency_ms},
        )

        body = {"ok": True, "request_id": request_id, "data": validated_data}
        return GenerationResponse(
            ok=True,
            status=200,
            body=body,
            openai_used=openai_used,
            outcome="success",
        )

    def _log_outcome(self, endpoint: str, request_id: str, start_ts: float, *, outcome: str, openai_used: bool, extra: Optional[dict] = None):
        latency_ms = int((time.time() - start_ts) * 1000)
        payload = {
            "endpoint": endpoint,
            "request_id": request_id,
            "latency_ms": latency_ms,
            "outcome": outcome,
            "openai_used": openai_used,
        }
        if extra:
            payload.update(extra)
        self.logger.info("generation.outcome", extra=payload)
