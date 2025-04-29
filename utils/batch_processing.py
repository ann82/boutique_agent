"""
Batch processing functionality for the Fashion Content Agent.
"""
import asyncio
from typing import List, Dict, Any
import requests
from .validation import validate_image_url
from .logging import log_batch_operation, log_error, log_success
from .duplicate_detection import is_duplicate_image
from .exceptions import ImageValidationError

MAX_BATCH_SIZE = 100

async def process_batch(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Process a batch of image URLs.
    
    Args:
        urls: List of image URLs to process
        
    Returns:
        List of dictionaries containing processing results
        
    Raises:
        ValueError: If the number of URLs exceeds MAX_BATCH_SIZE
    """
    if len(urls) > MAX_BATCH_SIZE:
        raise ValueError(f"Maximum number of URLs exceeded. Maximum is {MAX_BATCH_SIZE}")
    
    total_urls = len(urls)
    successful = 0
    failed = 0
    results = []
    
    log_batch_operation("processing", total_urls)
    
    for url in urls:
        try:
            # Validate URL format and accessibility
            valid, error_msg = validate_image_url(url)
            if not valid:
                raise ImageValidationError(error_msg or "Invalid image URL")
            
            # Check if image exists and is accessible
            response = requests.head(url)
            response.raise_for_status()
            
            # Check for duplicates
            is_duplicate, matching_url = is_duplicate_image(url)
            if is_duplicate:
                results.append({
                    "status": "skipped",
                    "url": url,
                    "reason": f"Duplicate of {matching_url}"
                })
                continue
            
            # Process the image
            log_success(f"Successfully processed {url}")
            results.append({
                "status": "success",
                "url": url
            })
            successful += 1
            
        except ImageValidationError as e:
            log_error(f"Failed to process image {url}", e)
            results.append({
                "status": "error",
                "url": url,
                "error": str(e)
            })
            failed += 1
        except Exception as e:
            log_error(f"Failed to process image {url}", e)
            results.append({
                "status": "error",
                "url": url,
                "error": str(e)
            })
            failed += 1
    
    log_batch_operation("processing", total_urls, successful, failed)
    return results 