"""
Tests for logging functionality.
"""
import os
import pytest
from unittest.mock import patch, mock_open
from utils.logging import setup_logging, log_error, log_success, log_batch_operation

class TestLogging:
    """Test cases for logging functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.log_dir = "logs"
        self.log_file = os.path.join(self.log_dir, "fashion_agent.log")
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_log_file_creation(self, mock_file, mock_makedirs, mock_exists):
        """Test log file creation and directory setup."""
        # Mock directory does not exist
        mock_exists.return_value = False
        
        # Call setup logging with default log file
        setup_logging(self.log_file)
        
        # Verify directory creation
        mock_makedirs.assert_called_once_with(self.log_dir, exist_ok=True)
        mock_file.assert_called_with(self.log_file, 'a')
    
    @patch('logging.Logger.error')
    def test_log_error(self, mock_error):
        """Test error logging."""
        error_message = "Test error message"
        test_error = Exception("Test error")
        log_error(error_message, test_error)
        mock_error.assert_called_once_with(f"{error_message}: {str(test_error)}")
    
    @patch('logging.Logger.info')
    def test_log_success(self, mock_info):
        """Test success logging."""
        success_message = "Test success message"
        log_success(success_message)
        mock_info.assert_called_once_with(success_message)
    
    @patch('logging.Logger.info')
    def test_log_batch_operation(self, mock_info):
        """Test batch operation logging."""
        operation = "test_operation"
        total = 10
        
        # Test initial batch operation logging
        log_batch_operation(operation, total)
        mock_info.assert_called_once_with(f"Batch {operation}: Processing {total} items")
        mock_info.reset_mock()
        
        # Test completion logging
        successful = 8
        failed = 2
        log_batch_operation(operation, total, successful, failed)
        mock_info.assert_called_once_with(f"Batch {operation} completed: {successful}/{total} successful, {failed} failed") 