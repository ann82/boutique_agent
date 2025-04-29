"""
Utility functions for image processing.
"""
import base64
import requests
from urllib.parse import urlparse, parse_qs
from PIL import Image
from io import BytesIO
import tempfile
import re
from typing import Optional

def convert_google_drive_url(url: str) -> str:
    """
    Convert Google Drive URL to direct download URL.
    
    Args:
        url (str): Google Drive URL
        
    Returns:
        str: Direct download URL
    """
    try:
        # Handle Google Drive URLs
        if 'drive.google.com' in url:
            # Extract file ID from different Google Drive URL formats
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in url:
                file_id = url.split('id=')[1].split('&')[0]
            else:
                raise ValueError("Invalid Google Drive URL format")
            
            # Return direct download URL
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        return url
    except Exception as e:
        raise ValueError(f"Failed to convert Google Drive URL: {str(e)}")

def get_image_from_url(url: str) -> str:
    """
    Get image data from a URL and convert it to base64.
    
    Args:
        url (str): URL of the image
        
    Returns:
        str: Base64 encoded image data
    """
    try:
        # Convert Google Drive URL if necessary
        url = convert_google_drive_url(url)
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://drive.google.com/'
        }
        
        # Stream the response to handle large files
        with requests.get(url, headers=headers, allow_redirects=True, stream=True) as response:
            response.raise_for_status()
            
            # Check if the response is actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"URL does not point to an image. Content type: {content_type}")
            
            # Get content length
            content_length = int(response.headers.get('content-length', 0))
            if content_length > 10 * 1024 * 1024:  # If larger than 10MB
                # Download to temporary file
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            tmp.write(chunk)
                    tmp.flush()
                    
                    # Open with Pillow and compress
                    with Image.open(tmp.name) as img:
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        
                        # Calculate new size while maintaining aspect ratio
                        max_size = (800, 800)
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # Save compressed image to BytesIO
                        buffer = BytesIO()
                        img.save(buffer, format='JPEG', quality=85)
                        buffer.seek(0)
                        
                        # Convert to base64
                        return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # For smaller images, read directly into memory
            buffer = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
            buffer.seek(0)
            
            # Convert to base64
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
    except Exception as e:
        raise ValueError(f"Failed to get image from URL: {str(e)}")

def is_valid_image_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Check if a URL points to a valid image.
    
    Args:
        url (str): URL to check
        
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
        - is_valid: True if URL points to a valid image, False otherwise
        - error_message: None if valid, error description if invalid
    """
    try:
        # Check for Google Drive URL
        if 'drive.google.com' in url:
            if not ('/file/d/' in url or 'id=' in url):
                return False, "Invalid Google Drive URL format. URL must be a direct file link."
            try:
                # Try to convert the URL
                url = convert_google_drive_url(url)
            except ValueError:
                return False, "Invalid Google Drive URL. Please make sure the file exists and is publicly accessible."
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://drive.google.com/'
        }
        
        # Make a HEAD request to check content type
        response = requests.head(url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        # Check if content type is an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return False, f"URL does not point to an image. Content type: {content_type}"
        
        return True, None
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            if 'drive.google.com' in url:
                return False, "This Google Drive file is not publicly accessible. Please update the sharing settings to 'Anyone with the link'."
            return False, "Access to this file is forbidden. Please check the file permissions."
        elif e.response.status_code == 404:
            return False, "File not found. Please check if the URL is correct."
        else:
            return False, f"HTTP error occurred: {str(e)}"
    except requests.exceptions.RequestException as e:
        return False, f"Failed to validate URL: {str(e)}"
    except Exception as e:
        return False, f"Invalid image URL: {str(e)}"

def convert_gdrive_url(url: str) -> str:
    """
    Convert Google Drive URL to direct download URL.
    
    Args:
        url (str): Google Drive URL
        
    Returns:
        str: Direct download URL
    """
    try:
        # Handle Google Drive URLs
        if 'drive.google.com' in url:
            # Extract file ID from different Google Drive URL formats
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in url:
                file_id = url.split('id=')[1].split('&')[0]
            else:
                raise ValueError("Invalid Google Drive URL format")
            
            # Return direct download URL
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        return url
    except Exception as e:
        raise ValueError(f"Failed to convert Google Drive URL: {str(e)}")

def download_image(url: str) -> Optional[bytes]:
    """
    Download an image from a URL.
    
    Args:
        url (str): URL of the image
        
    Returns:
        Optional[bytes]: Image data as bytes if successful, None otherwise
    """
    try:
        # Convert Google Drive URL if necessary
        url = convert_google_drive_url(url)
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://drive.google.com/'
        }
        
        # Stream the response to handle large files
        with requests.get(url, headers=headers, allow_redirects=True, stream=True) as response:
            response.raise_for_status()
            
            # Check if the response is actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"URL does not point to an image. Content type: {content_type}")
            
            # Read the image data
            buffer = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
            return buffer.getvalue()
            
    except Exception:
        return None 