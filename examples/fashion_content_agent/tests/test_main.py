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
@patch('main.is_valid_image_url', return_value=True)  # Mock is_valid_image_url to always return True
async def test_process_image_duplicate_url(mock_valid_url, agent, mock_session):
    """Test processing an image that already exists in the sheet."""
    # Mock the sheets service and spreadsheet ID
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['header'], ['https://example.com/image.jpg']]
    }
    mock_session['storage']._get_sheets_service.return_value = mock_service
    mock_session['storage']._spreadsheet_cache = {"Fashion Content Agent": "test_id"}

    # Process the image
    result = await agent.process_image("https://example.com/image.jpg")

    # Check that vision and content generation were not called
    mock_session['vision_agent'].analyze_image.assert_not_called()
    mock_session['content_agent'].generate_content.assert_not_called()

    # Check the result
    assert result["message"] == "Image URL already exists in the sheet"
    assert result["content"]["image_url"] == "https://example.com/image.jpg"

@pytest.mark.asyncio
@patch('main.is_valid_image_url', return_value=True)  # Mock is_valid_image_url to always return True
async def test_process_image_new_url(mock_valid_url, agent, mock_session):
    """Test processing a new image."""
    # Mock the sheets service and spreadsheet ID
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['header']]
    }
    mock_session['storage']._get_sheets_service.return_value = mock_service
    mock_session['storage']._spreadsheet_cache = {"Fashion Content Agent": "test_id"}

    # Process the image
    result = await agent.process_image("https://example.com/new_image.jpg")

    # Check that vision and content generation were called
    mock_session['vision_agent'].analyze_image.assert_called_once_with("https://example.com/new_image.jpg")
    mock_session['content_agent'].generate_content.assert_called_once_with("https://example.com/new_image.jpg")

    # Check the result
    assert "vision_analysis" in result
    assert "content" in result
    assert result["content"]["image_url"] == "https://example.com/new_image.jpg"
    assert result["sheet_url"] == "https://example.com/sheet"

@pytest.mark.asyncio
@patch('main.is_valid_image_url', return_value=True)  # Mock is_valid_image_url to always return True
async def test_process_image_error_checking_duplicates(mock_valid_url, agent, mock_session):
    """Test processing an image when there's an error checking for duplicates."""
    # Mock the sheets service to raise an exception
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get.side_effect = Exception("Test error")
    mock_session['storage']._get_sheets_service.return_value = mock_service
    mock_session['storage']._spreadsheet_cache = {"Fashion Content Agent": "test_id"}

    # Process the image and expect an exception
    with pytest.raises(Exception) as exc_info:
        await agent.process_image("https://example.com/error_image.jpg")
    
    # Check the error message
    assert "Error checking for duplicate URLs" in str(exc_info.value)
    
    # Check that vision and content generation were not called
    mock_session['vision_agent'].analyze_image.assert_not_called()
    mock_session['content_agent'].generate_content.assert_not_called() 