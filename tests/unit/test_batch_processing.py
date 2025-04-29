import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestBatchProcessing(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]
        self.invalid_urls = [
            "https://example.com/nonexistent.jpg",
            "invalid_url",
            "https://example.com/image.txt"
        ]

    @patch('requests.get')
    def test_url_validation(self, mock_get):
        """Test URL validation for multiple images."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_get.return_value = mock_response

        from app import validate_image_urls
        valid_urls = validate_image_urls(self.valid_urls)
        self.assertEqual(len(valid_urls), 3)

    @patch('app.process_single_image')
    def test_batch_processing(self, mock_process):
        """Test processing multiple images in batch."""
        mock_process.return_value = {'status': 'success'}
        
        from app import process_images
        results = process_images(self.valid_urls)
        
        self.assertEqual(len(results), 3)
        mock_process.assert_called()
        self.assertEqual(mock_process.call_count, 3)

    def test_max_urls_limit(self):
        """Test that batch processing respects the maximum URL limit."""
        too_many_urls = self.valid_urls + ["https://example.com/image4.jpg"]
        
        from app import validate_image_urls
        with self.assertRaises(ValueError):
            validate_image_urls(too_many_urls)

    @patch('app.process_single_image')
    def test_partial_failure_handling(self, mock_process):
        """Test handling of partial failures in batch processing."""
        def side_effect(url):
            if url == self.valid_urls[1]:
                raise Exception("Processing failed")
            return {'status': 'success'}
        
        mock_process.side_effect = side_effect
        
        from app import process_images
        results = process_images(self.valid_urls)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['status'], 'success')
        self.assertEqual(results[1]['status'], 'error')
        self.assertEqual(results[2]['status'], 'success')

if __name__ == '__main__':
    unittest.main() 