"""
Validation and error handling utilities for the fashion content agent.
"""
from typing import Dict, Any, Tuple, List
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
    
    is_valid, error_msg = is_valid_image_url(url)
    if not is_valid:
        raise ImageValidationError(error_msg or f"Invalid image URL: {url}")

def validate_image_urls(urls: List[str]) -> List[str]:
    """
    Validate multiple image URLs.
    
    Args:
        urls (List[str]): List of URLs to validate
        
    Returns:
        List[str]: List of valid URLs
        
    Raises:
        ImageValidationError: If any URL is invalid
    """
    valid_urls = []
    for url in urls:
        try:
            validate_image_url(url)
            valid_urls.append(url)
        except ImageValidationError as e:
            raise ImageValidationError(f"Invalid URL {url}: {str(e)}")
    return valid_urls

async def validate_content_format(content: Dict[str, Any]) -> None:
    """
    Validate the content format.
    
    Args:
        content (Dict[str, Any]): Content to validate
        
    Raises:
        ContentValidationError: If content format is invalid
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
                raise ContentValidationError(f"Missing required field: {field}")
            if not isinstance(content[field], field_type):
                raise ContentValidationError(
                    f"Invalid type for field {field}. Expected {field_type.__name__}, got {type(content[field]).__name__}"
                )
        
        # Validate image URL if present
        if "image_url" in content:
            validate_image_url(content["image_url"])
            
    except ValidationError:
        raise
    except Exception as e:
        raise ContentValidationError(f"Validation error: {str(e)}") 