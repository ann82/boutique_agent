"""
Email notification functionality for the Fashion Content Agent.
"""
import re
import os
from typing import Optional
from googleapiclient.discovery import build
from .exceptions import EmailValidationError

def validate_email(email: Optional[str]) -> str:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        str: The validated email address
        
    Raises:
        EmailValidationError: If email is invalid
    """
    if not email:
        raise EmailValidationError("Email address is required")
        
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise EmailValidationError(f"Invalid email format: {email}")
    
    return email

def get_default_email() -> str:
    """Get default email from environment."""
    email = os.getenv('GOOGLE_SHARE_EMAIL')
    if not email:
        raise EmailValidationError("Default email not configured")
    return validate_email(email)

async def share_sheet_with_email(sheet_id: str, email: str) -> dict:
    """
    Share a Google Sheet with an email address.
    
    Args:
        sheet_id: ID of the Google Sheet
        email: Email address to share with
        
    Returns:
        dict: Result of the sharing operation
    """
    try:
        # Validate email
        validated_email = validate_email(email)
        
        # Build the Drive API service
        service = build('drive', 'v3', credentials=None)
        
        # Create permission
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': validated_email
        }
        
        # Share the sheet
        result = service.permissions().create(
            fileId=sheet_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()
        
        return {
            "success": True,
            "message": f"Sheet shared successfully with {email}. Permission ID: {result['id']}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to share sheet: {str(e)}"
        } 