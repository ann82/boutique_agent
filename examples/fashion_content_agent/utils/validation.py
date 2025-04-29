"""
Validation and error handling utilities for the fashion content agent.
"""
from typing import Dict, Any
from .image_utils import is_valid_image_url

class ValidationError(Exception):
    """Base class for validation errors."""
    pass

class ImageValidationError(ValidationError):
    """Raised when image validation fails."""
    pass

class ContentValidationError(ValidationError):
    """Raised when content validation fails."""
    pass

def validate_image_url(url: str) -> None:
    """
    Validate an image URL.
    
    Args:
        url (str): URL to validate
        
    Raises:
        ImageValidationError: If URL is invalid
    """
    if not url:
        raise ImageValidationError("Image URL cannot be empty")
    
    if not is_valid_image_url(url):
        raise ImageValidationError(f"Invalid image URL: {url}")

def validate_content_format(content: Dict[str, Any]) -> bool:
    """
    Validate the content format.
    
    Args:
        content (Dict[str, Any]): Content to validate
        
    Returns:
        bool: True if content format is valid, False otherwise
    """
    required_fields = {
        "title": str,
        "description": str,
        "caption": str,
        "hashtags": list,
        "alt_text": str,
        "platform": str
    }
    
    try:
        for field, field_type in required_fields.items():
            if field not in content:
                return False
            if not isinstance(content[field], field_type):
                return False
        return True
    except Exception:
        return False 