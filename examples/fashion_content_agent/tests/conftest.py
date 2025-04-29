"""
Common fixtures for all tests in the Fashion Content Agent test suite.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
from PIL import Image
import io

# Common fixtures for all tests
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Automatically mock environment variables for all tests."""
    monkeypatch.setenv('TEST_MODE', 'true')
    monkeypatch.setenv('GOOGLE_CREDENTIALS_FILE', 'test_credentials.json')
    monkeypatch.setenv('GOOGLE_SHARE_EMAIL', 'test@example.com')

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

# Google Sheets fixtures
@pytest.fixture
def mock_google_sheets():
    """Mock Google Sheets service."""
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_service

@pytest.fixture
def mock_google_credentials():
    """Mock Google credentials."""
    with patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds:
        mock_creds.return_value = MagicMock()
        yield mock_creds

# HTTP request fixtures
@pytest.fixture
def mock_requests():
    """Mock requests.get for image downloads."""
    with patch('requests.get') as mock_get:
        yield mock_get

@pytest.fixture
def mock_image_response():
    """Create a mock image response."""
    def _create_mock_image(width=100, height=100):
        img = Image.new('RGB', (width, height), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        mock_response = MagicMock()
        mock_response.content = img_byte_arr
        mock_response.raise_for_status.return_value = None
        return mock_response
    return _create_mock_image

# Cache fixtures
@pytest.fixture
def mock_cache():
    """Mock cache operations."""
    with patch('utils.cache.ImageHashCache') as mock_cache:
        yield mock_cache

# Email notification fixtures
@pytest.fixture
def mock_email():
    """Mock email sending functionality."""
    with patch('utils.email_notification.send_email') as mock_send:
        yield mock_send

# Logging fixtures
@pytest.fixture
def mock_logging():
    """Mock logging functionality."""
    with patch('logging.getLogger') as mock_logger:
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        yield mock_log

# Test data fixtures
@pytest.fixture
def sample_image_urls():
    """Provide sample image URLs for testing."""
    return [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg"
    ]

@pytest.fixture
def sample_content():
    """Provide sample content data for testing."""
    return {
        "title": "Test Product",
        "description": "Test Description",
        "caption": "Test Caption",
        "hashtags": ["#test", "#product"],
        "alt_text": "Test Alt Text",
        "platform": "instagram",
        "image_url": "https://example.com/test.jpg"
    }

@pytest.fixture
def sample_vision_analysis():
    """Provide sample vision analysis data for testing."""
    return {
        "key_features": ["feature1", "feature2"],
        "colors": ["red", "blue"],
        "style": "casual",
        "confidence": 0.95
    } 