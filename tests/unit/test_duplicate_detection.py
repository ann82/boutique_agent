import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestDuplicateDetection(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_url = "https://example.com/image.jpg"
        self.test_content = b"test image content"
        self.test_hash = hashlib.md5(self.test_content).hexdigest()

    @patch('requests.get')
    def test_image_hash_generation(self, mock_get):
        """Test generation of image hash."""
        mock_response = MagicMock()
        mock_response.content = self.test_content
        mock_get.return_value = mock_response
        
        from app import generate_image_hash
        hash_value = generate_image_hash(self.test_url)
        
        self.assertEqual(hash_value, self.test_hash)

    @patch('app.generate_image_hash')
    def test_duplicate_detection(self, mock_hash):
        """Test detection of duplicate images."""
        mock_hash.return_value = self.test_hash
        
        from app import is_duplicate
        
        # First attempt should not be a duplicate
        result1 = is_duplicate(self.test_url)
        self.assertFalse(result1)
        
        # Second attempt with same hash should be a duplicate
        result2 = is_duplicate(self.test_url)
        self.assertTrue(result2)

    @patch('app.generate_image_hash')
    def test_different_images(self, mock_hash):
        """Test handling of different images."""
        mock_hash.side_effect = ["hash1", "hash2", "hash3"]
        
        from app import is_duplicate
        
        result1 = is_duplicate("url1")
        result2 = is_duplicate("url2")
        result3 = is_duplicate("url3")
        
        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)

    @patch('requests.get')
    def test_invalid_image_handling(self, mock_get):
        """Test handling of invalid images for duplicate detection."""
        mock_get.side_effect = Exception("Failed to fetch image")
        
        from app import generate_image_hash
        with self.assertRaises(ValueError):
            generate_image_hash(self.test_url)

    def test_cache_cleanup(self):
        """Test cleanup of old cache entries."""
        from app import cleanup_cache
        
        # Add some test entries
        from app import image_cache
        image_cache["test1"] = {"timestamp": 0, "hash": "hash1"}
        image_cache["test2"] = {"timestamp": 999999999999, "hash": "hash2"}
        
        cleanup_cache()
        
        self.assertNotIn("test1", image_cache)
        self.assertIn("test2", image_cache)

if __name__ == '__main__':
    unittest.main() 