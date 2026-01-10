"""Gemini-only generation flow tests mirroring legacy OpenAI cases."""

from generation_service import GenerationService


def _validator(payload):
    return {}


def _normalizer(payload):
    return payload


def _output_validator(data):
    return data


def test_gemini_success_returns_source_gemini():
    service = GenerationService()

    def working_gemini(payload):
        return {"posts": [{"date": "2024-01-01", "pillar": "Test", "cards": []}], "count": 1}

    resp = service.generate(
        endpoint="test",
        request_id="gem-1",
        payload={"test": "data"},
        validator=_validator,
        normalizer=_normalizer,
        output_validator=_output_validator,
        gemini_callable=working_gemini,
        use_gemini=True,
        disable_fallback=True,
    )

    assert resp.ok is True
    assert resp.body["ok"] is True
    assert resp.body["source"] == "gemini"
    assert resp.body["mode"] == "generated"
    assert resp.body.get("warnings") is None
    assert resp.body.get("gemini_used") is True
    assert resp.body.get("openai_used") is False


def test_gemini_failure_uses_fallback_when_available():
    service = GenerationService()

    def failing_gemini(payload):
        raise Exception("Gemini API error")

    def working_fallback(payload):
        return {"posts": [{"date": "2024-01-01", "pillar": "Test", "cards": []}], "count": 1}

    resp = service.generate(
        endpoint="test",
        request_id="gem-2",
        payload={"test": "data"},
        validator=_validator,
        normalizer=_normalizer,
        output_validator=_output_validator,
        gemini_callable=failing_gemini,
        fallback_callable=working_fallback,
        use_gemini=True,
        disable_fallback=False,
    )

    assert resp.ok is True
    assert resp.body["ok"] is True
    assert resp.body["source"] == "fallback"
    assert resp.body["mode"] == "fallback_suggestions"
    assert resp.body.get("warnings")
    assert resp.body.get("gemini_used") is True
    assert resp.body.get("fallback_used") is True


def test_gemini_failure_without_fallback_returns_error():
    service = GenerationService()

    def failing_gemini(payload):
        raise Exception("Gemini API error")

    resp = service.generate(
        endpoint="test",
        request_id="gem-3",
        payload={"test": "data"},
        validator=_validator,
        normalizer=_normalizer,
        output_validator=_output_validator,
        gemini_callable=failing_gemini,
        use_gemini=True,
        disable_fallback=True,
    )

    assert resp.ok is False
    assert resp.body["ok"] is False
    assert resp.body["source"] == "gemini"
    assert resp.body["mode"] == "error"


def test_no_gemini_callable_uses_fallback_when_present():
    service = GenerationService()

    def working_fallback(payload):
        return {"posts": [{"date": "2024-01-01", "pillar": "Test", "cards": []}], "count": 1}

    resp = service.generate(
        endpoint="test",
        request_id="gem-4",
        payload={"test": "data"},
        validator=_validator,
        normalizer=_normalizer,
        output_validator=_output_validator,
        gemini_callable=None,
        fallback_callable=working_fallback,
        use_gemini=True,
        disable_fallback=False,
    )

    assert resp.ok is True
    assert resp.body["ok"] is True
    assert resp.body["source"] == "fallback"
    assert resp.body["mode"] == "fallback_suggestions"
    assert resp.body.get("gemini_used") is False
    assert resp.body.get("fallback_used") is True