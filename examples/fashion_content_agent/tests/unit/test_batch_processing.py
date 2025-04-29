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
    @patch('utils.batch_processing.validate_image_url')
    @patch('utils.batch_processing.is_duplicate_image')
    @patch('requests.head')
    async def test_url_validation(self, mock_head, mock_duplicate, mock_validate):
        """Test URL validation in batch processing."""
        mock_validate.return_value = (True, None)
        mock_duplicate.return_value = (False, None)
        
        # Mock successful head request
        mock_response = MagicMock()
        mock_head.return_value = mock_response
        
        # Test valid URLs
        results = await process_batch(self.valid_urls)
        assert len(results) == len(self.valid_urls)
        assert all(result["status"] == "success" for result in results)
        
        # Test invalid URL
        mock_validate.return_value = (False, "Invalid URL")
        results = await process_batch(["invalid_url"])
        assert len(results) == 1
        assert results[0]["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_max_urls_limit(self):
        """Test maximum URLs limit in batch processing."""
        urls = ["https://example.com/image{}.jpg".format(i) for i in range(101)]
        with pytest.raises(ValueError) as exc_info:
            await process_batch(urls)
        assert "Maximum number of URLs exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('utils.batch_processing.validate_image_url')
    @patch('utils.batch_processing.is_duplicate_image')
    @patch('requests.head')
    async def test_batch_processing(self, mock_head, mock_duplicate, mock_validate):
        """Test batch processing of multiple images."""
        mock_validate.return_value = (True, None)
        mock_duplicate.return_value = (False, None)
        
        # Mock successful head request
        mock_response = MagicMock()
        mock_head.return_value = mock_response
        
        results = await process_batch(self.valid_urls)
        assert len(results) == len(self.valid_urls)
        assert all(result["status"] == "success" for result in results)
    
    @pytest.mark.asyncio
    @patch('utils.batch_processing.validate_image_url')
    @patch('utils.batch_processing.is_duplicate_image')
    @patch('requests.head')
    async def test_partial_failure_handling(self, mock_head, mock_duplicate, mock_validate):
        """Test handling of partial failures in batch processing."""
        # Simulate one valid and one invalid
        mock_validate.side_effect = [(True, None), (False, "Invalid URL")]
        mock_duplicate.side_effect = [(False, None), (False, None)]
        
        # Mock successful head request
        mock_response = MagicMock()
        mock_head.return_value = mock_response
        
        results = await process_batch(self.valid_urls)
        assert len(results) == len(self.valid_urls)
        assert any(result["status"] == "error" for result in results)
        assert any(result["status"] == "success" for result in results)

    def _run_batch_processing(self):
        # This should call your actual batch processing function with test data
        # Replace this with the real call and test data
        return [{"status": "success"}, {"status": "success"}] 