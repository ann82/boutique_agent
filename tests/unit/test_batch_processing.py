"""
Tests for batch processing functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import asyncio
from utils.batch_processing import process_batch
from utils.validation import ImageValidationError

class TestBatchProcessing:
    """Test cases for batch processing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_urls = [
            "http://example.com/image1.jpg",
            "http://example.com/image2.jpg",
            "http://example.com/image3.jpg"
        ]
        self.invalid_urls = [
            "http://example.com/invalid.jpg",
            "not_a_url",
            "ftp://invalid.com/image.jpg"
        ]
    
    @pytest.mark.asyncio
    @patch('requests.head')
    @patch('utils.validation.validate_image_url')
    @patch('utils.duplicate_detection.is_duplicate_image')
    async def test_url_validation(self, mock_duplicate, mock_validate, mock_head):
        """Test URL validation in batch processing."""
        # Mock validation to return success
        mock_validate.return_value = (True, None)
        
        # Mock successful head request
        mock_response = MagicMock()
        mock_head.return_value = mock_response
        
        # Mock duplicate check to return not duplicate
        mock_duplicate.return_value = (False, None)
        
        # Test valid URLs
        results = await process_batch(self.valid_urls)
        assert len(results) == len(self.valid_urls)
        assert all(result["status"] == "success" for result in results)
    
    @pytest.mark.asyncio
    async def test_max_urls_limit(self):
        """Test maximum URLs limit in batch processing."""
        urls = ["https://example.com/image{}.jpg".format(i) for i in range(101)]
        with pytest.raises(ValueError) as exc_info:
            await process_batch(urls)
        assert "Maximum number of URLs exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('requests.head')
    @patch('utils.validation.validate_image_url')
    @patch('utils.duplicate_detection.is_duplicate_image')
    async def test_batch_processing(self, mock_duplicate, mock_validate, mock_head):
        """Test batch processing of multiple images."""
        # Mock validation to return success
        mock_validate.return_value = (True, None)
        
        # Mock successful head request
        mock_response = MagicMock()
        mock_head.return_value = mock_response
        
        # Mock duplicate check to return not duplicate
        mock_duplicate.return_value = (False, None)
        
        results = await process_batch(self.valid_urls)
        assert len(results) == len(self.valid_urls)
        assert all(result["status"] == "success" for result in results)
    
    @pytest.mark.asyncio
    @patch('requests.head')
    @patch('utils.validation.validate_image_url')
    @patch('utils.duplicate_detection.is_duplicate_image')
    async def test_partial_failure_handling(self, mock_duplicate, mock_validate, mock_head):
        """Test handling of partial failures in batch processing."""
        # Mock validation to succeed for some URLs and fail for others
        def mock_validate_func(url):
            if "image1" in url:
                return (False, "Invalid URL")
            return (True, None)
        
        mock_validate.side_effect = mock_validate_func
        
        # Mock successful head request
        mock_response = MagicMock()
        mock_head.return_value = mock_response
        
        # Mock duplicate check to return not duplicate
        mock_duplicate.return_value = (False, None)
        
        results = await process_batch(self.valid_urls)
        assert len(results) == len(self.valid_urls)
        assert any(result["status"] == "error" for result in results)
        assert any(result["status"] == "success" for result in results) 