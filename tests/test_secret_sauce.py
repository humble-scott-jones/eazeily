import pytest
from unittest import mock

from services.voice_engine import VoiceAnalyzer


def test_analyze_style_returns_system_instruction():
    va = VoiceAnalyzer(api_key="test-key")

    mocked_output = "Write like a friendly expert: short sentences, casual tone, one emoji occasionally."

    with mock.patch.object(VoiceAnalyzer, "_call_model", return_value=mocked_output) as m:
        result = va.analyze_style("This is a sample text to analyze.")
        assert result == mocked_output
        m.assert_called_once()


def test_generate_with_voice_model_selection():
    va = VoiceAnalyzer(api_key="test-key")

    # capture calls and return a dummy generated text
    def fake_call(self, model, prompt, system_instruction=None, temperature=0.7, max_output_tokens=512):
        return f"[MODEL:{model}] Generated for prompt: {prompt[:30]}"

    with mock.patch.object(VoiceAnalyzer, "_call_model", new=fake_call):
        res_free = va.generate_with_voice(user_tier="free", style_instruction="inst", topic="dogs", platform="twitter")
        assert res_free["ok"] is True
        assert res_free["model"] == "gemini-1.5-flash"
        assert res_free["output"].startswith("[MODEL:gemini-1.5-flash]")

        res_pro = va.generate_with_voice(user_tier="pro", style_instruction="inst", topic="cats", platform="linkedin")
        assert res_pro["ok"] is True
        assert res_pro["model"] == "gemini-1.5-pro"
        assert res_pro["output"].startswith("[MODEL:gemini-1.5-pro]")
