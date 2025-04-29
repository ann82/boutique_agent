"""
Custom exceptions for the Fashion Content Agent.
"""

class EmailValidationError(Exception):
    """Raised when email validation fails."""
    pass

class ImageValidationError(Exception):
    """Raised when image validation fails."""
    pass

class ContentValidationError(Exception):
    """Raised when content validation fails."""
    pass

class DuplicateImageError(Exception):
    """Raised when a duplicate image is detected."""
    pass

class StorageError(Exception):
    """Raised when there is an error with storage operations."""
    pass 