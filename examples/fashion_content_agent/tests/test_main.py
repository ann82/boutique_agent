"""
Tests for the main FashionContentAgent class.
"""
import pytest
from unittest.mock import MagicMock, patch
import asyncio
from main import FashionContentAgent

@pytest.fixture
def mock_session():
    """Create a mock session with necessary components."""
    vision_agent = MagicMock()
    content_agent = MagicMock()
    storage = MagicMock()

    # Set up async mock methods
    async def mock_analyze_image(url):
        return {"vision_analysis": "test"}

    async def mock_generate_content(url):
        return {
            "title": "Test Title",
            "description": "Test Description",
            "caption": "Test Caption",
            "hashtags": ["#test"],
            "alt_text": "Test Alt Text",
            "platform": "Instagram"
        }

    async def mock_save(content, vision_analysis, sheet_name=None):
        return "https://example.com/sheet"

    vision_agent.analyze_image = MagicMock(side_effect=mock_analyze_image)
    content_agent.generate_content = MagicMock(side_effect=mock_generate_content)
    storage.save = MagicMock(side_effect=mock_save)

    session = {
        "vision_agent": vision_agent,
        "content_agent": content_agent,
        "storage": storage
    }
    return session

@pytest.fixture
def agent(mock_session):
    """Create an agent with mocked components."""
    with patch('main.get_session', return_value=mock_session):
        agent = FashionContentAgent()
        yield agent

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_image_invalid_url(mock_valid_url, agent, mock_session):
    """Test processing an invalid image URL."""
    # Mock is_valid_image_url to return invalid with error message
    mock_valid_url.return_value = (False, "This Google Drive file is not publicly accessible")
    
    # Process the image
    result = await agent.process_image("https://drive.google.com/invalid", "ImageToText Content")
    
    # Check that vision and content generation were not called
    mock_session['vision_agent'].analyze_image.assert_not_called()
    mock_session['content_agent'].generate_content.assert_not_called()
    
    # Check the result
    assert "error" in result
    assert result["error"] == "This Google Drive file is not publicly accessible"
    assert result["content"]["image_url"] == "https://drive.google.com/invalid"

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

    # Process the image
    result = await agent.process_image("https://example.com/new_image.jpg", "ImageToText Content")

    # Check that vision and content generation were called
    mock_session['vision_agent'].analyze_image.assert_called_once_with("https://example.com/new_image.jpg")
    mock_session['content_agent'].generate_content.assert_called_once_with("https://example.com/new_image.jpg")

    # Check the result
    assert "error" not in result
    assert "vision_analysis" in result
    assert "content" in result
    assert result["content"]["image_url"] == "https://example.com/new_image.jpg"
    assert result["sheet_url"] == "https://example.com/sheet"

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

    # Process multiple images
    urls = [
        "https://example.com/valid_image.jpg",
        "https://drive.google.com/invalid_image.jpg"
    ]
    results = await agent.process_images(urls, sheet_name="ImageToText Content")

    # Check results
    assert len(results) == 2
    valid_result = next(r for r in results if r["content"]["image_url"] == "https://example.com/valid_image.jpg")
    invalid_result = next(r for r in results if r["content"]["image_url"] == "https://drive.google.com/invalid_image.jpg")
    
    assert "error" not in valid_result
    assert "error" in invalid_result
    assert "This Google Drive file is not publicly accessible" in invalid_result["error"]

    # Check that vision and content generation were called only for valid URL
    mock_session['vision_agent'].analyze_image.assert_called_once_with("https://example.com/valid_image.jpg")
    mock_session['content_agent'].generate_content.assert_called_once_with("https://example.com/valid_image.jpg")

@pytest.mark.asyncio
@patch('main.is_valid_image_url')
async def test_process_images_all_invalid(mock_valid_url, agent, mock_session):
    """Test processing multiple images where all URLs are invalid."""
    # Mock URL validation to always return invalid
    mock_valid_url.return_value = (False, "This Google Drive file is not publicly accessible")
    
    urls = [
        "https://drive.google.com/invalid1.jpg",
        "https://drive.google.com/invalid2.jpg"
    ]
    results = await agent.process_images(urls, sheet_name="ImageToText Content")

    # Check that all URLs were marked as invalid
    assert len(results) == 2
    assert all("error" in r and "This Google Drive file is not publicly accessible" in r["error"] for r in results)

    # Check that vision and content generation were never called
    mock_session['vision_agent'].analyze_image.assert_not_called()
    mock_session['content_agent'].generate_content.assert_not_called()

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

    # Process multiple images
    urls = [
        "https://example.com/new.jpg",
        "https://example.com/duplicate.jpg"
    ]
    results = await agent.process_images(urls, sheet_name="ImageToText Content")

    # Check results
    assert len(results) == 2
    new_result = next(r for r in results if r["content"]["image_url"] == "https://example.com/new.jpg")
    duplicate_result = next(r for r in results if r["content"]["image_url"] == "https://example.com/duplicate.jpg")
    
    assert "error" not in new_result
    assert "error" in duplicate_result
    assert "already exists" in duplicate_result["error"]

    # Check that vision and content generation were called only for new URL
    mock_session['vision_agent'].analyze_image.assert_called_once_with("https://example.com/new.jpg")
    mock_session['content_agent'].generate_content.assert_called_once_with("https://example.com/new.jpg") 