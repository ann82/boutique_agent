"""
Tests for email notification functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from utils.email_notification import share_sheet_with_email, validate_email
from utils.exceptions import EmailValidationError

class TestEmailNotification:
    """Test cases for email notification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_email = "test@example.com"
        self.invalid_emails = [
            "not_an_email",
            "@missing_username.com",
            "missing_domain@",
            "invalid@domain"
        ]
        self.test_sheet_id = "test_sheet_123"
    
    def test_email_validation(self):
        """Test validation of email format."""
        # Test valid email
        assert validate_email(self.valid_email) == self.valid_email

        # Test invalid emails
        for invalid_email in self.invalid_emails:
            with pytest.raises(EmailValidationError):
                validate_email(invalid_email)
    
    @pytest.mark.asyncio
    @patch('utils.email_notification.build')
    async def test_successful_sheet_sharing(self, mock_build):
        """Test successful sheet sharing."""
        # Set up mock Google Sheets API
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_permission = MagicMock()
        mock_service.permissions.return_value = mock_permission
        mock_permission.create.return_value.execute.return_value = {"id": "permission_123"}

        # Test successful sharing
        result = await share_sheet_with_email(self.test_sheet_id, self.valid_email)
        assert result["success"] is True
        assert "permission_123" in result["message"]
    
    @pytest.mark.asyncio
    @patch('utils.email_notification.build')
    async def test_failed_sheet_sharing(self, mock_build):
        """Test handling of sheet sharing failure."""
        # Set up mock to simulate API error
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_permission = MagicMock()
        mock_service.permissions.return_value = mock_permission
        mock_permission.create.return_value.execute.side_effect = Exception("API Error")

        # Test failed sharing
        result = await share_sheet_with_email(self.test_sheet_id, self.valid_email)
        assert result["success"] is False
        assert "Failed to share" in result["message"]
    
    def test_default_email_fallback(self):
        """Test fallback to default email when environment variable is not set."""
        with patch('os.getenv', return_value=None):
            with pytest.raises(EmailValidationError):
                validate_email(None) 