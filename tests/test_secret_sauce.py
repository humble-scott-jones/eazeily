import pytest
from unittest import mock
import os
import json
from services.voice_engine import VoiceEngine

# Mock google.genai to avoid actual API calls during tests
@pytest.fixture
def mock_genai():
    # We patch where it is imported in services.voice_engine
    with mock.patch("services.voice_engine.genai") as mock_genai_mod:
        # CRITICAL: Ensure legacy GenerativeModel is NOT present
        if hasattr(mock_genai_mod, "GenerativeModel"):
            del mock_genai_mod.GenerativeModel

        # Mock Client structure
        mock_client = mock.Mock()
        mock_genai_mod.Client.return_value = mock_client
        
        # Setup models accessor
        mock_models = mock.Mock()
        mock_client.models = mock_models
        # Explicitly ensure hasattr works for 'generate_content'
        mock_models.generate_content = mock.Mock()
        
        # Setup default response logic
        mock_response = mock.Mock()
        mock_response.text = "Generated content"
        mock_models.generate_content.return_value = mock_response
        
        yield mock_genai_mod

def test_analyze_style_uses_correct_model(mock_genai):
    """Verify that analyze_style uses the engine's model."""
    with mock.patch.dict(os.environ, {"GENAI_API_KEY": "fake_key"}):
        # We need to make sure the mock client is returned when Client() is called
        # The fixture does this, but verify execution
        engine = VoiceEngine()
        
        # If engine.model is None, we failed to initialize
        assert engine.model is not None, "VoiceEngine failed to initialize model with mock"
        
        # Setup mock response for this specific call
        mock_client = mock_genai.Client.return_value
        mock_response = mock.Mock()
        # Return valid JSON for analyze_style
        mock_response.text = '{"style_guide": "Professional", "examples": ["ex1"]}'
        mock_client.models.generate_content.return_value = mock_response
        
        result = engine.analyze_style("Some text")
        
        # Assertions on result parsing
        assert result.get("style_guide") == "Professional"
        assert result.get("examples") == ["ex1"]
        
        # Check that the model called was correct
        call_args = mock_client.models.generate_content.call_args
        assert call_args is not None
        _, kwargs = call_args
        assert kwargs["model"] == "gemini-2.0-flash"

def test_generate_post_params(mock_genai):
    """Verify generate_post constructs prompt and calls gemini-2.0-flash."""
    with mock.patch.dict(os.environ, {"GENAI_API_KEY": "fake_key"}):
        engine = VoiceEngine()
        
        mock_profile = mock.Mock()
        mock_profile.style_guide = "Friendly"
        mock_profile.get_examples.return_value = ["Sample 1"]
        
        result = engine.generate_post(user_profile=mock_profile, topic="Project Launch")
        
        mock_client = mock_genai.Client.return_value
        call_args = mock_client.models.generate_content.call_args
        assert call_args is not None
        _, kwargs = call_args
        
        assert kwargs["model"] == "gemini-2.0-flash"
        assert "Friendly" in kwargs["contents"]
        assert "Project Launch" in kwargs["contents"]

def test_generate_expert_content_params(mock_genai):
    """Verify generate_expert_content uses correct model and structure."""
    with mock.patch.dict(os.environ, {"GENAI_API_KEY": "fake_key"}):
        engine = VoiceEngine()
        
        mock_profile = mock.Mock()
        mock_profile.industry = "Tech"
        mock_profile.business_name = "Acme"
        # Ensure regex/f-string/list operations don't fail on Mocks
        mock_profile.brand_voice = "Friendly"
        mock_profile.target_audience = "Devs"
        mock_profile.key_offer = "API"
        mock_profile.voice_rules = "No jargon"
        
        # Mock getters
        mock_profile.get_brand_keywords.return_value = []
        mock_profile.get_niche_keywords.return_value = []
        mock_profile.get_customers.return_value = []
        mock_profile.get_scraped_meta.return_value = {}
        mock_profile.get_writing_samples.return_value = []
        
        result = engine.generate_expert_content(
            user_profile=mock_profile,
            topic="Innovation",
            platform="LinkedIn"
        )
        
        mock_client = mock_genai.Client.return_value
        call_args = mock_client.models.generate_content.call_args
        _, kwargs = call_args
        
        assert kwargs["model"] == "gemini-2.0-flash"
        assert "Acme" in kwargs["contents"]
        assert "Innovation" in kwargs["contents"]
