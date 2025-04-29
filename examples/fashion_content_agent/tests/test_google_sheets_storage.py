"""
Tests for Google Sheets storage implementation.
"""
import pytest
from unittest.mock import MagicMock, patch
from utils.document_storage import GoogleSheetsStorage
from utils.image_utils import convert_google_drive_url

@pytest.fixture
def mock_services():
    with patch('utils.document_storage.service_account.Credentials') as mock_creds:
        with patch('utils.document_storage.build') as mock_build:
            mock_sheets = MagicMock()
            mock_drive = MagicMock()
            # build() returns different services based on args
            def build_side_effect(service_name, *args, **kwargs):
                if service_name == 'sheets':
                    return mock_sheets
                elif service_name == 'drive':
                    return mock_drive
            mock_build.side_effect = build_side_effect
            yield mock_sheets, mock_drive

@pytest.fixture
def storage(mock_services):
    mock_sheets, mock_drive = mock_services
    return GoogleSheetsStorage(credentials_file='dummy.json', share_email='test@example.com')

@pytest.mark.asyncio
async def test_create_spreadsheet_headers(storage, mock_services):
    mock_sheets, _ = mock_services
    # Simulate spreadsheet creation and header writing
    mock_sheets.spreadsheets().create().execute.return_value = {'spreadsheetId': 'sheet123'}
    result = storage._create_spreadsheet('ImageToText Content')
    # Check that headers are written correctly
    args, kwargs = mock_sheets.spreadsheets().values().update.call_args
    headers = kwargs['body']['values'][0]
    assert headers == [
        'Title', 'Description', 'Caption', 'Hashtags', 'Alt Text', 'Platform', 'Image URL', 'Key Features', 'Vision Analysis'
    ]
    
    # Check that header formatting was applied
    args, kwargs = mock_sheets.spreadsheets().batchUpdate.call_args
    format_request = kwargs['body']['requests'][0]['repeatCell']
    assert format_request['range']['endColumnIndex'] == len(headers)
    assert format_request['cell']['userEnteredFormat']['backgroundColor'] == {'red': 0.2, 'green': 0.2, 'blue': 0.2}
    assert format_request['cell']['userEnteredFormat']['horizontalAlignment'] == 'CENTER'
    assert format_request['cell']['userEnteredFormat']['textFormat']['bold'] == True
    assert format_request['cell']['userEnteredFormat']['textFormat']['fontSize'] == 12

@pytest.mark.asyncio
async def test_save_content_minimal_fields(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate existing sheet
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {
        'title': 'Test Title',
        'description': 'Test Desc',
        'caption': 'Test Cap',
        'hashtags': ['#tag'],
        'alt_text': 'Alt',
        'platform': 'Instagram',
        'image_url': 'http://img'
    }
    vision_analysis = {
        'test': 'data',
        'key_features': ['feature1', 'feature2']
    }
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'sheet123' in sheet_url
    
    # Check that content is written correctly
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert row[0] == 'Test Title'
    assert row[3] == '#tag'
    assert row[7] == 'feature1, feature2'  # Check key features

@pytest.mark.asyncio
async def test_save_content_missing_fields(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {
        'title': 'Test Title',
        'platform': 'Instagram'
    }
    vision_analysis = {
        'test': 'data',
        'key_features': []
    }
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'sheet123' in sheet_url
    
    # Check that missing fields are empty
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert row[0] == 'Test Title'
    assert row[5] == 'Instagram'
    assert row[7] == ''  # Empty key features
    assert all(cell == '' for i, cell in enumerate(row) if i not in [0, 5, 7, 8])

@pytest.mark.asyncio
async def test_save_content_extra_fields(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {
        'title': 'Test Title',
        'description': 'Test Desc',
        'caption': 'Test Cap',
        'hashtags': ['#tag'],
        'alt_text': 'Alt',
        'platform': 'Instagram',
        'image_url': 'http://img',
        'extra_field': 'should be ignored'
    }
    vision_analysis = {
        'test': 'data',
        'key_features': ['feature1']
    }
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'sheet123' in sheet_url
    
    # Check that extra fields are not written
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert len(row) == 9  # Now includes key features column

@pytest.mark.asyncio
async def test_save_content_empty(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {}
    vision_analysis = {}
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'sheet123' in sheet_url
    
    # Check that all fields are empty
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert all(cell == '' for i, cell in enumerate(row) if i not in [7, 8])  # Skip key features and vision analysis columns
    assert row[7] == ''  # Empty key features
    assert row[8] == '{}'  # Empty vision analysis as JSON

@pytest.mark.asyncio
async def test_sheet_reuse(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate existing sheet
    mock_drive.files().list().execute.return_value = {
        'files': [{'id': 'existing123', 'name': 'ImageToText Content'}]
    }
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {'title': 'Test'}
    vision_analysis = {'test': 'data'}
    
    # First save should find existing sheet
    sheet_url1 = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'existing123' in sheet_url1
    
    # Second save should use cached sheet ID
    sheet_url2 = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'existing123' in sheet_url2
    
    # Verify we only searched for the sheet once
    assert mock_drive.files().list().execute.call_count == 1

@pytest.mark.asyncio
async def test_sheet_creation_with_headers(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate no existing sheet
    mock_drive.files().list().execute.return_value = {'files': []}
    mock_sheets.spreadsheets().create().execute.return_value = {'spreadsheetId': 'new123'}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {'title': 'Test'}
    vision_analysis = {'test': 'data', 'key_features': []}
    
    # Save should create new sheet with headers
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'new123' in sheet_url
    
    # Verify headers were written
    args, kwargs = mock_sheets.spreadsheets().values().update.call_args
    assert kwargs['range'] == 'Sheet1!A1:I1'  # Updated range to include key features
    assert len(kwargs['body']['values'][0]) == 9  # Now includes key features column

@pytest.mark.asyncio
async def test_sheet_sharing(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate new sheet creation
    mock_drive.files().list().execute.return_value = {'files': []}
    mock_sheets.spreadsheets().create().execute.return_value = {'spreadsheetId': 'new123'}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {'title': 'Test'}
    vision_analysis = {'test': 'data'}
    
    # Save with sharing enabled
    storage.share_email = 'test@example.com'
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    
    # Verify sharing was attempted
    args, kwargs = mock_drive.permissions().create.call_args
    assert kwargs['fileId'] == 'new123'
    assert kwargs['body']['emailAddress'] == 'test@example.com'

@pytest.mark.asyncio
async def test_sheet_error_handling(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    
    # Test drive API error
    mock_drive.files().list().execute.side_effect = Exception('Drive API error')
    with pytest.raises(Exception, match='Error saving to Google Sheets'):
        await storage.save({}, {}, sheet_name='ImageToText Content')
    
    # Test sheets API error
    mock_drive.files().list().execute.side_effect = None
    mock_drive.files().list().execute.return_value = {'files': []}
    mock_sheets.spreadsheets().create().execute.side_effect = Exception('Sheets API error')
    with pytest.raises(Exception, match='Error saving to Google Sheets'):
        await storage.save({}, {}, sheet_name='ImageToText Content')

@pytest.mark.asyncio
async def test_concurrent_sheet_access(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    
    # Simulate existing sheet
    mock_drive.files().list().execute.return_value = {
        'files': [{'id': 'existing123', 'name': 'ImageToText Content'}]
    }
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {'title': 'Test'}
    vision_analysis = {'test': 'data'}
    
    # Run multiple saves concurrently
    import asyncio
    tasks = [
        storage.save(content, vision_analysis, sheet_name='ImageToText Content')
        for _ in range(5)
    ]
    results = await asyncio.gather(*tasks)
    
    # Verify all saves used the same sheet
    assert all('existing123' in url for url in results)
    
    # Verify we only searched for the sheet once
    assert mock_drive.files().list().execute.call_count == 1

@pytest.mark.asyncio
async def test_duplicate_url_handling(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate existing sheet with URLs
    mock_drive.files().list().execute.return_value = {
        'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]
    }
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        'values': [['header'], ['https://example.com/image.jpg']]
    }
    
    content = {
        'title': 'Test Title',
        'image_url': 'https://example.com/image.jpg'
    }
    vision_analysis = {'test': 'data'}
    
    # Try to save duplicate URL
    with pytest.raises(ValueError, match="Image URL already exists in sheet 'ImageToText Content'"):
        await storage.save(content, vision_analysis, sheet_name='ImageToText Content')

@pytest.mark.asyncio
async def test_duplicate_url_empty_sheet(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate empty sheet
    mock_drive.files().list().execute.return_value = {
        'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]
    }
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        'values': [['header']]
    }
    
    content = {
        'title': 'Test Title',
        'image_url': 'https://example.com/image.jpg'
    }
    vision_analysis = {'test': 'data'}
    
    # Should not raise error for empty sheet
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'sheet123' in sheet_url

@pytest.mark.asyncio
async def test_duplicate_url_no_image_url(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate existing sheet
    mock_drive.files().list().execute.return_value = {
        'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]
    }
    
    content = {
        'title': 'Test Title'
    }
    vision_analysis = {'test': 'data'}
    
    # Should not check for duplicates if no image_url
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'sheet123' in sheet_url
    mock_sheets.spreadsheets().values().get().assert_not_called()

@pytest.mark.asyncio
async def test_duplicate_url_error_handling(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate error checking for duplicates
    mock_drive.files().list().execute.return_value = {
        'files': [{'id': 'sheet123', 'name': 'ImageToText Content'}]
    }
    mock_sheets.spreadsheets().values().get().execute.side_effect = Exception('API error')
    
    content = {
        'title': 'Test Title',
        'image_url': 'https://example.com/image.jpg'
    }
    vision_analysis = {'test': 'data'}
    
    # Should raise error with sheet name in message
    with pytest.raises(Exception, match="Error checking for duplicate URLs in sheet 'ImageToText Content'"):
        await storage.save(content, vision_analysis, sheet_name='ImageToText Content')

@pytest.mark.asyncio
async def test_duplicate_url_nonexistent_sheet(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    # Simulate nonexistent sheet
    mock_drive.files().list().execute.return_value = {'files': []}
    mock_sheets.spreadsheets().create().execute.return_value = {'spreadsheetId': 'new123'}
    
    content = {
        'title': 'Test Title',
        'image_url': 'https://example.com/image.jpg'
    }
    vision_analysis = {'test': 'data'}
    
    # Should create new sheet without checking for duplicates
    sheet_url = await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
    assert 'new123' in sheet_url
    mock_sheets.spreadsheets().values().get().assert_not_called()

@pytest.mark.asyncio
async def test_duplicate_url_early_check():
    """Test that duplicate URL check happens before any other operations."""
    with patch('utils.document_storage.GoogleSheetsStorage._get_sheets_service') as mock_service:
        with patch('utils.document_storage.GoogleSheetsStorage._create_spreadsheet') as mock_create:
            storage = GoogleSheetsStorage(credentials_file='dummy.json')
            
            # Simulate existing sheet with URL
            mock_service.return_value.spreadsheets().values().get().execute.return_value = {
                'values': [['header'], ['https://example.com/image.jpg']]
            }
            storage._spreadsheet_cache = {"ImageToText Content": "sheet123"}
            
            content = {
                'title': 'Test Title',
                'image_url': 'https://example.com/image.jpg'
            }
            vision_analysis = {'test': 'data'}
            
            # Try to save duplicate URL
            with pytest.raises(ValueError, match="Image URL already exists in sheet 'ImageToText Content'"):
                await storage.save(content, vision_analysis, sheet_name='ImageToText Content')
            
            # Verify no other operations were attempted
            mock_create.assert_not_called() 