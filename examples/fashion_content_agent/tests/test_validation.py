"""
Tests for validation functions.
"""
import pytest
from unittest.mock import patch
from utils.validation import (
    validate_image_url,
    validate_content_format,
    ImageValidationError,
    ContentValidationError
)

@patch('utils.validation.is_valid_image_url')
def test_validate_image_url(mock_is_valid):
    """Test image URL validation."""
    # Test valid URL
    mock_is_valid.return_value = (True, None)
    validate_image_url("https://example.com/image.jpg")
    
    # Test empty URL
    with pytest.raises(ImageValidationError):
        validate_image_url("")
        
    # Test invalid URL
    mock_is_valid.return_value = (False, "Invalid URL")
    with pytest.raises(ImageValidationError):
        validate_image_url("not_a_url")

@pytest.mark.asyncio
@patch('utils.validation.is_valid_image_url')
async def test_validate_content_format_valid_url(mock_valid_url):
    """Test validation with valid URL."""
    # Mock is_valid_image_url to return valid
    mock_valid_url.return_value = (True, None)
    
    content = {
        'title': 'Test Title',
        'description': 'Test Description',
        'caption': 'Test Caption',
        'hashtags': ['#test'],
        'alt_text': 'Test Alt Text',
        'platform': 'Instagram',
        'image_url': 'https://example.com/image.jpg'
    }
    
    # Should not raise any exceptions
    await validate_content_format(content)

@pytest.mark.asyncio
@patch('utils.validation.is_valid_image_url')
async def test_validate_content_format_invalid_url(mock_valid_url):
    """Test validation with invalid URL."""
    # Mock is_valid_image_url to return invalid with error message
    mock_valid_url.return_value = (False, "Invalid image URL")
    
    content = {
        'title': 'Test Title',
        'description': 'Test Description',
        'caption': 'Test Caption',
        'hashtags': ['#test'],
        'alt_text': 'Test Alt Text',
        'platform': 'Instagram',
        'image_url': 'invalid_url'
    }
    
    # Should raise ImageValidationError
    with pytest.raises(ImageValidationError) as exc_info:
        await validate_content_format(content)
    assert "Invalid image URL" in str(exc_info.value)

@pytest.mark.asyncio
async def test_validate_content_format_missing_fields():
    """Test validation with missing required fields."""
    content = {
        'title': 'Test Title',
        'description': 'Test Description'
    }
    
    # Should raise ContentValidationError
    with pytest.raises(ContentValidationError) as exc_info:
        await validate_content_format(content)
    assert "Missing required field" in str(exc_info.value) 