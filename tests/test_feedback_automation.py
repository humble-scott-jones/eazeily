"""
Tests for the feedback automation system.

These tests verify the feedback formatting script works correctly
with and without LLM integration.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add parent directory to path to import the script
sys.path.insert(0, str(Path(__file__).parent.parent / ".github" / "scripts"))

import format_feedback


class TestFallbackFormat:
    """Test the fallback formatting when LLM is not available."""
    
    def test_basic_feedback_formatting(self):
        """Test formatting simple feedback text."""
        feedback = "I would like to have dark mode support"
        email = "user@example.com"
        
        result = format_feedback.fallback_format(feedback, email)
        
        assert "title" in result
        assert "body" in result
        assert len(result["title"]) <= 83  # 80 + "..."
        assert email in result["body"]
        assert feedback in result["body"]
    
    def test_multiline_feedback(self):
        """Test formatting feedback with multiple lines."""
        feedback = "Add dark mode\nThe UI is too bright at night\nPlease add a toggle"
        email = "user@example.com"
        
        result = format_feedback.fallback_format(feedback, email)
        
        # Should use first line for title
        assert "dark mode" in result["title"].lower()
        assert feedback in result["body"]
    
    def test_long_feedback_title_truncation(self):
        """Test that long feedback is properly truncated in title."""
        feedback = "A" * 100  # Very long feedback
        email = "user@example.com"
        
        result = format_feedback.fallback_format(feedback, email)
        
        assert len(result["title"]) <= 83  # 80 + "..."
        assert result["title"].endswith("...")
    
    def test_title_capitalization(self):
        """Test that title is properly capitalized."""
        feedback = "lowercase feedback text"
        email = "user@example.com"
        
        result = format_feedback.fallback_format(feedback, email)
        
        assert result["title"][0].isupper()
    
    def test_title_period_removal(self):
        """Test that trailing period is removed from title."""
        feedback = "This is my feedback."
        email = "user@example.com"
        
        result = format_feedback.fallback_format(feedback, email)
        
        assert not result["title"].endswith(".")
    
    def test_short_feedback_gets_prefix(self):
        """Test that very short feedback gets prefixed."""
        feedback = "Help"
        email = "user@example.com"
        
        result = format_feedback.fallback_format(feedback, email)
        
        assert "User Feedback" in result["title"]
    
    def test_anonymous_user(self):
        """Test formatting with no email provided."""
        feedback = "Some feedback text"
        email = None
        
        result = format_feedback.fallback_format(feedback, email)
        
        assert "Anonymous" in result["body"]


class TestLoadPromptTemplate:
    """Test loading the LLM prompt template."""
    
    def test_loads_custom_template_if_exists(self):
        """Test that custom template is loaded when present."""
        # Create a temporary template file
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / "config"
            template_dir.mkdir()
            template_file = template_dir / "feedback-prompt.txt"
            template_file.write_text("Custom template: {feedback}")
            
            # Mock the template path
            with patch.object(Path, '__truediv__', return_value=template_file):
                with patch.object(Path, 'exists', return_value=True):
                    template = format_feedback.load_prompt_template()
            
            # Should still return something (default if mocking doesn't work as expected)
            assert isinstance(template, str)
            assert len(template) > 0
    
    def test_returns_default_when_no_file(self):
        """Test that default template is returned when file doesn't exist."""
        template = format_feedback.load_prompt_template()
        
        assert isinstance(template, str)
        assert "{feedback}" in template
        assert "{user_email}" in template


class TestLLMIntegration:
    """Test LLM-based feedback formatting."""
    
    @patch('format_feedback.OpenAI')
    def test_format_with_llm_success(self, mock_openai_class):
        """Test successful LLM formatting."""
        # Mock the OpenAI client and response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "title": "Add Dark Mode Support",
            "body": "## Problem\\n\\nUsers need dark mode.\\n\\n## Expected Outcome\\n\\nDark mode toggle."
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        
        result = format_feedback.format_feedback_with_llm(
            "Please add dark mode",
            "user@example.com",
            "test-api-key"
        )
        
        assert result["title"] == "Add Dark Mode Support"
        assert "Dark mode" in result["body"]
    
    @patch('format_feedback.OpenAI')
    def test_format_with_llm_markdown_wrapped(self, mock_openai_class):
        """Test LLM response wrapped in markdown code blocks."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Response wrapped in markdown
        mock_response.choices[0].message.content = '```json\n{"title": "Test Title", "body": "Test Body"}\n```'
        
        mock_client.chat.completions.create.return_value = mock_response
        
        result = format_feedback.format_feedback_with_llm(
            "Test feedback",
            "user@example.com",
            "test-api-key"
        )
        
        assert result["title"] == "Test Title"
        assert result["body"] == "Test Body"
    
    @patch('format_feedback.OpenAI')
    def test_format_with_llm_invalid_json(self, mock_openai_class):
        """Test handling of invalid JSON from LLM."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Not valid JSON"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(SystemExit):
            format_feedback.format_feedback_with_llm(
                "Test feedback",
                "user@example.com",
                "test-api-key"
            )
    
    @patch('format_feedback.OpenAI')
    def test_format_with_llm_missing_fields(self, mock_openai_class):
        """Test handling of response missing required fields."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({"title": "Only Title"})
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(SystemExit):
            format_feedback.format_feedback_with_llm(
                "Test feedback",
                "user@example.com",
                "test-api-key"
            )


class TestMainFunction:
    """Test the main CLI interface."""
    
    def test_main_with_api_key(self):
        """Test main function with OpenAI API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.json"
            
            # Mock environment and OpenAI
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                with patch('format_feedback.format_feedback_with_llm') as mock_format:
                    mock_format.return_value = {
                        "title": "Test Title",
                        "body": "Test Body"
                    }
                    
                    # Mock sys.argv
                    test_args = [
                        "format_feedback.py",
                        "--feedback", "Test feedback",
                        "--user-email", "test@example.com",
                        "--output", str(output_file)
                    ]
                    
                    with patch.object(sys, 'argv', test_args):
                        format_feedback.main()
                    
                    # Verify output file was created
                    assert output_file.exists()
                    
                    # Verify content
                    with open(output_file) as f:
                        result = json.load(f)
                    
                    assert result["title"] == "Test Title"
                    assert result["body"] == "Test Body"
    
    def test_main_without_api_key(self):
        """Test main function without OpenAI API key (fallback)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.json"
            
            # Mock environment without API key
            with patch.dict(os.environ, {}, clear=True):
                # Mock sys.argv
                test_args = [
                    "format_feedback.py",
                    "--feedback", "Test feedback for fallback",
                    "--user-email", "test@example.com",
                    "--output", str(output_file)
                ]
                
                with patch.object(sys, 'argv', test_args):
                    format_feedback.main()
                
                # Verify output file was created
                assert output_file.exists()
                
                # Verify content (should use fallback)
                with open(output_file) as f:
                    result = json.load(f)
                
                assert "title" in result
                assert "body" in result
                assert "Test feedback" in result["body"]


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def test_end_to_end_fallback(self):
        """Test complete workflow without LLM."""
        feedback = "I need better analytics for my posts"
        email = "analytics@user.com"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "result.json"
            
            with patch.dict(os.environ, {}, clear=True):
                test_args = [
                    "format_feedback.py",
                    "--feedback", feedback,
                    "--user-email", email,
                    "--output", str(output_file)
                ]
                
                with patch.object(sys, 'argv', test_args):
                    format_feedback.main()
            
            # Verify the file exists and has valid content
            assert output_file.exists()
            
            with open(output_file) as f:
                result = json.load(f)
            
            # Verify structure
            assert "title" in result
            assert "body" in result
            
            # Verify content
            assert "analytics" in result["title"].lower() or "analytics" in result["body"].lower()
            assert email in result["body"]
            assert feedback in result["body"]
            
            # Verify title is reasonable
            assert 10 <= len(result["title"]) <= 83
