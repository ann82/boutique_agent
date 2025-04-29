import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestLogging(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_log_file = "test.log"
        
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    @patch('logging.getLogger')
    def test_logger_configuration(self, mock_get_logger):
        """Test logger configuration with correct settings."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        from app import setup_logging
        logger = setup_logging()
        
        self.assertEqual(logger.level, logging.INFO)
        mock_logger.addHandler.assert_called()

    def test_log_file_creation(self):
        """Test that log file is created and writable."""
        from app import setup_logging
        logger = setup_logging(self.test_log_file)
        
        logger.info("Test log message")
        
        self.assertTrue(os.path.exists(self.test_log_file))
        with open(self.test_log_file, 'r') as f:
            content = f.read()
            self.assertIn("Test log message", content)

    @patch('logging.getLogger')
    def test_error_logging(self, mock_get_logger):
        """Test error logging functionality."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        from app import log_error
        error_msg = "Test error message"
        log_error(error_msg)
        
        mock_logger.error.assert_called_once_with(error_msg)

    @patch('logging.getLogger')
    def test_batch_operation_logging(self, mock_get_logger):
        """Test logging of batch operations."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        from app import log_batch_operation
        urls = ["url1", "url2", "url3"]
        log_batch_operation(urls)
        
        expected_calls = [
            call("Starting batch operation"),
            call(f"Processing {len(urls)} images"),
            call("Batch operation completed")
        ]
        mock_logger.info.assert_has_calls(expected_calls)

    @patch('logging.getLogger')
    def test_success_message_logging(self, mock_get_logger):
        """Test logging of success messages."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        from app import log_success
        sheet_id = "test_sheet_id"
        log_success(sheet_id)
        
        mock_logger.info.assert_called_with(f"Successfully processed and saved to sheet: {sheet_id}")

if __name__ == '__main__':
    unittest.main() 