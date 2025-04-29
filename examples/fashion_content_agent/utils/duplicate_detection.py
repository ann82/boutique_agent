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
from utils.cache import ImageHashCache

# Initialize cache
image_hash_cache = ImageHashCache()

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
        response.raise_for_status()
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

def is_duplicate_image(url: str, threshold: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if an image is a duplicate of an existing image.
    
    Args:
        url: URL of the image to check
        threshold: Maximum Hamming distance to consider as duplicate (default: 5)
    
    Returns:
        Tuple of (is_duplicate, matching_url)
        
    Raises:
        Exception: If image processing fails
    """
    try:
        # Get image content
        response = requests.get(url)
        response.raise_for_status()
        image_content = response.content
        
        # Generate hash
        image = Image.open(io.BytesIO(image_content))
        current_hash = str(imagehash.average_hash(image))
        
        # Check cache for duplicates
        for cached_hash, cached_url in image_hash_cache._cache.items():
            if cached_url[0] != url:  # Don't compare with self
                # Calculate Hamming distance between hashes
                current_int = int(current_hash, 16)
                cached_int = int(cached_hash, 16)
                hamming_distance = bin(current_int ^ cached_int).count('1')
                
                if hamming_distance <= threshold:
                    return True, cached_url[0]
        
        # Store hash in cache
        image_hash_cache.set(current_hash, url)
        return False, None
        
    except Exception as e:
        raise Exception(f"Failed to check for duplicate image: {str(e)}") 