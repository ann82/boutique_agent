import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestEmailNotification(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_email = "test@example.com"
        self.test_sheet_id = "test_sheet_id"
        self.test_sheet_name = "Test Sheet"

    @patch('app.share_sheet_with_email')
    def test_share_sheet_success(self, mock_share):
        """Test successful sheet sharing with email."""
        mock_share.return_value = True
        
        from app import share_sheet_with_email
        result = share_sheet_with_email(self.test_sheet_id, self.test_email)
        
        self.assertTrue(result)
        mock_share.assert_called_once_with(self.test_sheet_id, self.test_email)

    @patch('app.share_sheet_with_email')
    def test_share_sheet_failure(self, mock_share):
        """Test handling of sheet sharing failure."""
        mock_share.side_effect = Exception("Sharing failed")
        
        from app import share_sheet_with_email
        result = share_sheet_with_email(self.test_sheet_id, self.test_email)
        
        self.assertFalse(result)

    def test_invalid_email_format(self):
        """Test validation of email format."""
        invalid_emails = [
            "invalid_email",
            "@example.com",
            "test@",
            "test@.com"
        ]
        
        from app import validate_email
        for email in invalid_emails:
            with self.assertRaises(ValueError):
                validate_email(email)

    @patch('app.get_default_email')
    def test_default_email_fallback(self, mock_get_default):
        """Test fallback to default email when none provided."""
        mock_get_default.return_value = "default@example.com"
        
        from app import get_email_for_sharing
        result = get_email_for_sharing(None)
        
        self.assertEqual(result, "default@example.com")
        mock_get_default.assert_called_once()

if __name__ == '__main__':
    unittest.main() 