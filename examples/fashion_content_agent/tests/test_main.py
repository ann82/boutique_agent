"""
Tests for the main FashionContentAgent class.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from main import FashionContentAgent

@pytest.fixture
def mock_session():
    """Create a mock session with all required components."""
    return {
        'vision_agent': AsyncMock(),
        'content_agent': AsyncMock(),
        'storage': AsyncMock()
    }

@pytest.fixture
def agent(mock_session):
    """Create an agent instance with mock session."""
    with patch('main.get_session', return_value=mock_session):
        return FashionContentAgent()

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_image_invalid_url(mock_valid_url, agent, mock_session):
    """Test processing an invalid image URL."""
    # Mock is_valid_image_url to return invalid
    mock_valid_url.return_value = (False, "Invalid URL")
    
    # Process the image
    result = await agent.process_image("https://example.com/invalid.jpg", "ImageToText Content")
    
    # Check the result
    assert "error" in result
    assert "Invalid URL" in result["error"]

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_image_duplicate_url(mock_valid_url, agent, mock_session):
    """Test processing an image that already exists in the sheet."""
    # Mock is_valid_image_url to return valid
    mock_valid_url.return_value = (True, None)
    
    # Mock the sheets service and spreadsheet ID
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['header'], ['https://example.com/image.jpg']]
    }
    mock_session['storage']._get_sheets_service.return_value = mock_service
    mock_session['storage']._spreadsheet_cache = {"ImageToText Content": "test_id"}
    mock_session['storage']._get_existing_urls.return_value = ["https://example.com/image.jpg"]
    
    # Process the image
    result = await agent.process_image("https://example.com/image.jpg", "ImageToText Content")
    
    # Check that vision and content generation were not called
    mock_session['vision_agent'].analyze_image.assert_not_called()
    mock_session['content_agent'].generate_content.assert_not_called()
    
    # Check the result
    assert "error" in result
    assert "already exists in sheet" in result["error"]

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_image_new_url(mock_valid_url, agent, mock_session):
    """Test processing a new image."""
    # Mock is_valid_image_url to return valid
    mock_valid_url.return_value = (True, None)
    
    # Mock the sheets service and spreadsheet ID
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['header']]
    }
    mock_session['storage']._get_sheets_service.return_value = mock_service
    mock_session['storage']._spreadsheet_cache = {"ImageToText Content": "test_id"}
    mock_session['storage']._get_existing_urls.return_value = []
    
    # Mock vision analysis and content generation
    mock_session['vision_agent'].analyze_image.return_value = {"analysis": "test"}
    mock_session['content_agent'].generate_content.return_value = {"content": "test"}
    mock_session['storage'].save.return_value = "https://example.com/sheet"
    
    # Process the image
    result = await agent.process_image("https://example.com/new_image.jpg", "ImageToText Content")
    
    # Check that vision and content generation were called
    mock_session['vision_agent'].analyze_image.assert_called_once_with("https://example.com/new_image.jpg")
    mock_session['content_agent'].generate_content.assert_called_once_with("https://example.com/new_image.jpg")
    
    # Check the result
    assert "content" in result
    assert "vision_analysis" in result
    assert "sheet_url" in result

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_images_mixed_validity(mock_valid_url, agent, mock_session):
    """Test processing multiple images with mix of valid and invalid URLs."""
    # Mock URL validation to return different results for different URLs
    def mock_validation(url):
        if url == "https://example.com/valid_image.jpg":
            return (True, None)
        return (False, "This Google Drive file is not publicly accessible")
    
    mock_valid_url.side_effect = mock_validation
    
    # Mock the sheets service
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['header']]
    }
    mock_session['storage']._get_sheets_service.return_value = mock_service
    mock_session['storage']._spreadsheet_cache = {"ImageToText Content": "test_id"}
    mock_session['storage']._get_existing_urls.return_value = []
    
    # Mock vision analysis and content generation
    mock_session['vision_agent'].analyze_image.return_value = {"analysis": "test"}
    mock_session['content_agent'].generate_content.return_value = {"content": "test"}
    mock_session['storage'].save.return_value = "https://example.com/sheet"
    
    # Process multiple images
    urls = [
        "https://example.com/valid_image.jpg",
        "https://drive.google.com/invalid_image.jpg"
    ]
    results = await agent.process_images(urls, sheet_name="ImageToText Content")
    
    # Check results
    assert len(results) == 2
    valid_result = next(r for r in results if "content" in r and r["content"]["image_url"] == "https://example.com/valid_image.jpg")
    invalid_result = next(r for r in results if "error" in r and r["content"]["image_url"] == "https://drive.google.com/invalid_image.jpg")
    
    assert "content" in valid_result
    assert "error" in invalid_result

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_images_all_invalid(mock_valid_url, agent, mock_session):
    """Test processing multiple invalid image URLs."""
    # Mock URL validation to always return invalid
    mock_valid_url.return_value = (False, "Invalid URL")
    
    # Process multiple images
    urls = [
        "https://example.com/invalid1.jpg",
        "https://example.com/invalid2.jpg"
    ]
    results = await agent.process_images(urls, sheet_name="ImageToText Content")
    
    # Check results
    assert len(results) == 2
    assert all("error" in r for r in results)
    assert all("Invalid URL" in r["error"] for r in results)

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_images_mixed_duplicates(mock_valid_url, agent, mock_session):
    """Test processing multiple images with mix of new and duplicate URLs."""
    # Mock URL validation to always return valid
    mock_valid_url.return_value = (True, None)
    
    # Mock the sheets service to return one URL as existing
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['header'], ['https://example.com/duplicate.jpg']]
    }
    mock_session['storage']._get_sheets_service.return_value = mock_service
    mock_session['storage']._spreadsheet_cache = {"ImageToText Content": "test_id"}
    
    def mock_existing_urls(sheet_name):
        if sheet_name == "ImageToText Content":
            return ["https://example.com/duplicate.jpg"]
        return []
    
    mock_session['storage']._get_existing_urls.side_effect = mock_existing_urls
    
    # Mock vision analysis and content generation
    mock_session['vision_agent'].analyze_image.return_value = {"analysis": "test"}
    mock_session['content_agent'].generate_content.return_value = {"content": "test"}
    mock_session['storage'].save.return_value = "https://example.com/sheet"
    
    # Process multiple images
    urls = [
        "https://example.com/new.jpg",
        "https://example.com/duplicate.jpg"
    ]
    results = await agent.process_images(urls, sheet_name="ImageToText Content")
    
    # Check results
    assert len(results) == 2
    new_result = next(r for r in results if "content" in r and r["content"]["image_url"] == "https://example.com/new.jpg")
    duplicate_result = next(r for r in results if "error" in r and "already exists in sheet" in r["error"])
    
    assert "content" in new_result
    assert "error" in duplicate_result
    assert "https://example.com/duplicate.jpg" in duplicate_result["error"] 