"""
Tests for validation utilities.
"""
import pytest
import sys
import os
from unittest.mock import patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    mock_is_valid.return_value = True
    validate_image_url("https://example.com/image.jpg")
    
    # Test empty URL
    with pytest.raises(ImageValidationError):
        validate_image_url("")
        
    # Test invalid URL
    mock_is_valid.return_value = False
    with pytest.raises(ImageValidationError):
        validate_image_url("not_a_url")

def test_validate_content_format():
    """Test content format validation."""
    # Valid content
    valid_content = {
        "title": "Test Title",
        "description": "Test Description",
        "caption": "Test Caption",
        "hashtags": ["#test", "#fashion"],
        "alt_text": "Test Alt Text"
    }
    validate_content_format(valid_content)
    
    # Missing field
    invalid_content = valid_content.copy()
    del invalid_content["title"]
    with pytest.raises(ContentValidationError):
        validate_content_format(invalid_content)
        
    # Wrong type
    invalid_content = valid_content.copy()
    invalid_content["hashtags"] = "not_a_list"
    with pytest.raises(ContentValidationError):
        validate_content_format(invalid_content) 