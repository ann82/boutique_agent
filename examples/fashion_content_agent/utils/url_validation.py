"""
URL validation utilities for the Fashion Content Agent.
"""
import re
from urllib.parse import urlparse, parse_qs

def convert_google_drive_url(url: str) -> str:
    """
    Convert a Google Drive URL to its direct download form.
    
    Args:
        url: The Google Drive URL to convert
        
    Returns:
        The normalized URL
    """
    # Handle Google Drive sharing URLs
    if 'drive.google.com' in url:
        # Extract file ID from sharing URL
        file_id = None
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = parse_qs(urlparse(url).query).get('id', [None])[0]
        
        if file_id:
            return f'https://drive.google.com/uc?id={file_id}'
    
    # Return the original URL if it's not a Google Drive URL
    return url 