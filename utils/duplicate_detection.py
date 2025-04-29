"""
Duplicate detection functionality for the Fashion Content Agent.
"""
import time
import requests
from typing import Tuple, Optional, Dict
import imagehash
from PIL import Image
import io
from .exceptions import DuplicateImageError

# Cache for storing image hashes
_image_hash_cache: Dict[str, Tuple[str, float]] = {}
CACHE_EXPIRY = 3600  # 1 hour

def generate_image_hash(image_url: str) -> str:
    """
    Generate a perceptual hash for an image.
    
    Args:
        image_url: URL of the image
        
    Returns:
        str: Hexadecimal representation of the image hash
        
    Raises:
        Exception: If image hash generation fails
    """
    try:
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        hash_value = imagehash.average_hash(img)
        return str(hash_value)
    except Exception as e:
        raise Exception(f"Failed to generate image hash: {str(e)}")

def cleanup_cache() -> None:
    """Remove expired entries from the cache."""
    current_time = time.time()
    expired_urls = [
        url for url, (_, timestamp) in _image_hash_cache.items()
        if current_time - timestamp > CACHE_EXPIRY
    ]
    for url in expired_urls:
        del _image_hash_cache[url]

def is_duplicate_image(image_url: str, threshold: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if an image is a duplicate based on perceptual hashing.
    
    Args:
        image_url: URL of the image to check
        threshold: Maximum hash difference to consider as duplicate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_duplicate, matching_url)
    """
    try:
        # Clean up expired cache entries
        cleanup_cache()
        
        # Generate hash for new image
        current_hash = generate_image_hash(image_url)
        current_time = time.time()
        
        # Compare with existing hashes
        for url, (hash_value, _) in _image_hash_cache.items():
            if url != image_url:
                # Convert hex strings to integers for comparison
                current_int = int(current_hash, 16)
                existing_int = int(hash_value, 16)
                hash_diff = bin(current_int ^ existing_int).count('1')
                if hash_diff <= threshold:
                    return True, url
        
        # Store in cache if not a duplicate
        _image_hash_cache[image_url] = (current_hash, current_time)
        return False, None
        
    except Exception as e:
        raise Exception(f"Failed to check for duplicate image: {str(e)}") 