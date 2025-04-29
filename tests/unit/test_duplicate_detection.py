import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from PIL import Image
import io
import pytest
from utils.duplicate_detection import generate_image_hash, is_duplicate_image, cleanup_cache

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestDuplicateDetection(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_url = "http://example.com/test.jpg"
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.test_image_bytes = io.BytesIO()
        self.test_image.save(self.test_image_bytes, format='JPEG')
        self.test_image_bytes.seek(0)
        self.test_content = self.test_image_bytes.getvalue()
        self.test_hash = "0000000000000000"  # Example hash value

    @patch('requests.get')
    @patch('imagehash.average_hash')
    def test_image_hash_generation(self, mock_hash, mock_get):
        """Test generation of image hash."""
        mock_response = MagicMock()
        mock_response.content = self.test_content
        mock_get.return_value = mock_response
        
        mock_hash.return_value = self.test_hash
        
        result = generate_image_hash(self.test_url)
        
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 16)  # Average hash is 16 characters
        mock_get.assert_called_once_with(self.test_url)

    @patch('requests.get')
    @patch('imagehash.average_hash')
    def test_duplicate_detection(self, mock_hash, mock_get):
        """Test detection of duplicate images."""
        mock_response = MagicMock()
        mock_response.content = self.test_content
        mock_get.return_value = mock_response
        
        mock_hash.return_value = self.test_hash
        
        is_duplicate, _ = is_duplicate_image(self.test_url)
        self.assertFalse(is_duplicate)
        
        is_duplicate, matching_url = is_duplicate_image(self.test_url)
        self.assertTrue(is_duplicate)
        self.assertEqual(matching_url, self.test_url)

    @patch('requests.get')
    @patch('imagehash.average_hash')
    def test_different_images(self, mock_hash, mock_get):
        """Test handling of different images."""
        mock_response = MagicMock()
        mock_response.content = self.test_content
        mock_get.return_value = mock_response
        
        mock_hash.side_effect = ["0000000000000000", "1111111111111111"]
        
        is_duplicate, _ = is_duplicate_image("http://example.com/image1.jpg")
        self.assertFalse(is_duplicate)
        
        is_duplicate, _ = is_duplicate_image("http://example.com/image2.jpg")
        self.assertFalse(is_duplicate)

    @patch('requests.get')
    def test_invalid_image_handling(self, mock_get):
        """Test handling of invalid images."""
        mock_get.side_effect = Exception("Failed to fetch image")
        
        with pytest.raises(Exception) as exc_info:
            is_duplicate_image(self.test_url)
        assert "Failed to check for duplicate image" in str(exc_info.value)

    def test_cache_cleanup(self):
        """Test cleanup of expired cache entries."""
        import time
        from utils.duplicate_detection import _image_hash_cache, CACHE_EXPIRY
        
        _image_hash_cache.clear()
        current_time = time.time()
        _image_hash_cache["url1"] = ("hash1", current_time - CACHE_EXPIRY - 10)  # Expired
        _image_hash_cache["url2"] = ("hash2", current_time)  # Not expired
        
        cleanup_cache()
        
        self.assertNotIn("url1", _image_hash_cache)
        self.assertIn("url2", _image_hash_cache)

if __name__ == '__main__':
    unittest.main() 