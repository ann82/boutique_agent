"""
Unit tests for duplicate detection functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from utils.duplicate_detection import generate_image_hash, is_duplicate_image
from utils.cache import ImageHashCache

@pytest.mark.unit
@pytest.mark.duplicate_detection
class TestDuplicateDetection:
    """Test suite for duplicate detection functionality."""

    @pytest.mark.asyncio
    async def test_image_hash_generation(self, mock_requests, mock_image_response):
        """Test image hash generation."""
        # Setup
        url = "https://example.com/test.jpg"
        mock_requests.return_value = mock_image_response()
        
        # Test
        hash_value = generate_image_hash(url)
        
        # Verify
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0
        mock_requests.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_duplicate_detection(self, mock_requests, mock_image_response, mock_cache):
        """Test duplicate image detection."""
        # Setup
        url1 = "https://example.com/image1.jpg"
        url2 = "https://example.com/image2.jpg"
        mock_requests.return_value = mock_image_response()
        
        # Configure mock cache
        mock_cache_instance = MagicMock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance._cache = {url1: (url1, 0)}
        
        # Test
        is_duplicate, matching_url = is_duplicate_image(url2)
        
        # Verify
        assert not is_duplicate
        assert matching_url is None
        mock_requests.assert_called_once_with(url2)

    @pytest.mark.asyncio
    async def test_different_images(self, mock_requests, mock_image_response, mock_cache):
        """Test detection of different images."""
        # Setup
        url1 = "https://example.com/image1.jpg"
        url2 = "https://example.com/image2.jpg"
        mock_requests.return_value = mock_image_response()
        
        # Configure mock cache
        mock_cache_instance = MagicMock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance._cache = {url1: (url1, 0)}
        
        # Test
        is_duplicate, matching_url = is_duplicate_image(url2)
        
        # Verify
        assert not is_duplicate
        assert matching_url is None
        mock_requests.assert_called_once_with(url2)

    @pytest.mark.asyncio
    async def test_invalid_image_handling(self, mock_requests):
        """Test handling of invalid images."""
        # Setup
        url = "https://example.com/invalid.jpg"
        mock_requests.side_effect = Exception("Invalid image")
        
        # Test and Verify
        with pytest.raises(Exception) as exc_info:
            is_duplicate_image(url)
        assert "Invalid image" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_cleanup(self, mock_cache):
        """Test cache cleanup functionality."""
        # Setup
        mock_cache_instance = MagicMock()
        mock_cache.return_value = mock_cache_instance
        
        # Test
        mock_cache_instance.cleanup()
        
        # Verify
        mock_cache_instance.cleanup.assert_called_once() 