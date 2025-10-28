import os
import json
import types
import generator


class FakeChoices:
    def __init__(self, text):
        self.message = types.SimpleNamespace(content=text)


import os
import json
import types
import generator


class FakeChoices:
    def __init__(self, text):
        self.message = types.SimpleNamespace(content=text)


class FakeChat:
    class Completions:
        def __init__(self, text):
            self._text = text

        def create(self, **kwargs):
            return types.SimpleNamespace(choices=[FakeChoices(self._text)])

    def __init__(self, text):
        self.completions = FakeChat.Completions(text)


class FakeClient:
    def __init__(self, text):
        self.chat = FakeChat(text)


def test_fetch_trend_context_with_openai_and_caches(tmp_path, monkeypatch):
    # prepare a fake OpenAI response: include extra prose and JSON array
    fake_list = [
        {"topic": "plant-based menu", "rationale": "customers ask for options", "confidence": "high"},
        {"topic": "late-night delivery", "rationale": "local demand rising", "confidence": "medium"}
    ]
    response_text = "Here are some trends:\n" + json.dumps(fake_list)

    fake_client = FakeClient(response_text)
    monkeypatch.setattr(generator, '_openai_client', fake_client)
    # ensure module-level flag enables OpenAI path for this test
    monkeypatch.setattr(generator, 'USE_OPENAI_FOR_POSTS', True)

    # ensure we use a tmp cache directory by patching _trend_cache_path to use tmp_path
    def _tmp_trend_cache(industry: str):
        base = str(tmp_path)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, f"trends-{industry}.json")

    monkeypatch.setattr(generator, '_trend_cache_path', _tmp_trend_cache)

    # call with ttl_hours=0 to force fetch
    res = generator.fetch_trend_context('restaurant', ttl_hours=0)
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0]['topic'] == 'plant-based menu'
    # cache file should exist
    p = _tmp_trend_cache('restaurant')
    assert os.path.exists(p)


def test_fetch_trend_context_invalid_json(monkeypatch, tmp_path):
    # simulate a model that returns non-json garbage
    fake_text = "No JSON here, just text"
    fake_client = FakeClient(fake_text)
    monkeypatch.setattr(generator, '_openai_client', fake_client)
    monkeypatch.setattr(generator, 'USE_OPENAI_FOR_POSTS', True)

    # patch cache path
    def _tmp_trend_cache(industry: str):
        base = str(tmp_path)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, f"trends-{industry}.json")

    monkeypatch.setattr(generator, '_trend_cache_path', _tmp_trend_cache)

    res = generator.fetch_trend_context('weird', ttl_hours=0)
    # should return empty list and not raise
    assert isinstance(res, list)