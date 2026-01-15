"""Tests for caption generation with image upload functionality."""
import base64
import pytest
from unittest.mock import patch, MagicMock


def test_caption_generation_accepts_image_data(authenticated_client):
    """Test that caption generation endpoint accepts image data."""
    # Create a simple 1x1 pixel PNG
    tiny_png = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    ).decode('utf-8')
    
    image_data_url = f'data:image/png;base64,{tiny_png}'
    
    # Mock the voice engine to avoid actual API calls
    with patch('routes.generate_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Beautiful sunset over the city skyline. 🌆 #sunset #cityscape"
        
        response = authenticated_client.post('/api/generate', 
            json={
                'task_type': 'caption',
                'topic': 'Describe this beautiful sunset photo',
                'image_data': image_data_url,
                'image_filename': 'sunset.png'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'content' in data
        
        # Verify that image data was passed to the engine
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert 'image_data' in call_kwargs
        assert call_kwargs['image_data'] == image_data_url


def test_caption_generation_without_image_still_works(authenticated_client):
    """Test that caption generation works without image (text-only)."""
    with patch('routes.generate_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Perfect caption for your amazing photo! ✨ #photography"
        
        response = authenticated_client.post('/api/generate',
            json={
                'task_type': 'caption',
                'topic': 'A beautiful landscape photo with mountains and lakes'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'content' in data
        
        # Verify that no image data was passed
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert 'image_data' not in call_kwargs or call_kwargs.get('image_data') is None


def test_caption_rejects_invalid_image_format(authenticated_client):
    """Test that invalid image data formats are handled gracefully."""
    with patch('routes.generate_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Caption generated"
        
        # Image data without proper data URL format
        response = authenticated_client.post('/api/generate',
            json={
                'task_type': 'caption',
                'topic': 'Test photo',
                'image_data': 'not-a-valid-data-url'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        # Should still work but image_data should be filtered out
        # because it doesn't start with 'data:image/'
        assert response.status_code == 200


def test_image_data_only_included_for_caption_task(authenticated_client):
    """Test that image_data is only processed for caption task type."""
    tiny_png = base64.b64encode(b'\x89PNG\r\n\x1a\n').decode('utf-8')
    image_data_url = f'data:image/png;base64,{tiny_png}'
    
    with patch('routes.generate_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Blog post content"
        
        # Try to send image data with non-caption task
        response = authenticated_client.post('/api/generate',
            json={
                'task_type': 'blog',
                'topic': 'How to take better photos',
                'image_data': image_data_url
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        
        # Image data should not be passed for non-caption tasks
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        # For blog task, image_data should not be in context
        assert 'image_data' not in call_kwargs or call_kwargs.get('image_data') is None


def test_gemini_multimodal_adapter_handles_image():
    """Test that the Gemini multimodal adapter can handle image data."""
    from services.generation.gemini_adapter import call_gemini_with_image
    
    # Create a complete minimal 1x1 pixel PNG (transparent)
    # This is a valid PNG file with proper header, IHDR, IDAT, and IEND chunks
    tiny_png = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    ).decode('utf-8')
    
    image_data_url = f'data:image/png;base64,{tiny_png}'
    
    # Mock the Gemini client
    with patch('services.generation.gemini_adapter._get_client') as mock_get_client:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "A beautiful image caption"
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = call_gemini_with_image(
            prompt="Describe this image",
            image_data=image_data_url
        )
        
        # Verify the function processes the image data
        assert result is not None
        assert 'text' in result


def test_gemini_multimodal_rejects_invalid_data_url():
    """Test that multimodal adapter rejects invalid data URLs."""
    from services.generation.gemini_adapter import call_gemini_with_image
    
    with patch('services.generation.gemini_adapter._get_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Invalid data URL format
        result = call_gemini_with_image(
            prompt="Describe this",
            image_data="not-a-valid-data-url"
        )
        
        # Should return None for invalid data
        assert result is None
        
        # Gemini API should not have been called
        mock_client.models.generate_content.assert_not_called()
