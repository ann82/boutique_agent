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
    result = storage._create_spreadsheet('Test Sheet')
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
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'Test Sheet'}]}
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
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
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
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'Test Sheet'}]}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {
        'title': 'Test Title',
        'platform': 'Instagram'
    }
    vision_analysis = {
        'test': 'data',
        'key_features': []
    }
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
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
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'Test Sheet'}]}
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
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
    assert 'sheet123' in sheet_url
    
    # Check that extra fields are not written
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert len(row) == 9  # Now includes key features column

@pytest.mark.asyncio
async def test_save_content_empty(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'Test Sheet'}]}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {}
    vision_analysis = {}
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
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
        'files': [{'id': 'existing123', 'name': 'Test Sheet'}]
    }
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {'title': 'Test'}
    vision_analysis = {'test': 'data'}
    
    # First save should find existing sheet
    sheet_url1 = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
    assert 'existing123' in sheet_url1
    
    # Second save should use cached sheet ID
    sheet_url2 = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
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
    sheet_url = await storage.save(content, vision_analysis, sheet_name='New Sheet')
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
    sheet_url = await storage.save(content, vision_analysis, sheet_name='New Sheet')
    
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
        await storage.save({}, {}, sheet_name='Test Sheet')
    
    # Test sheets API error
    mock_drive.files().list().execute.side_effect = None
    mock_drive.files().list().execute.return_value = {'files': []}
    mock_sheets.spreadsheets().create().execute.side_effect = Exception('Sheets API error')
    with pytest.raises(Exception, match='Error saving to Google Sheets'):
        await storage.save({}, {}, sheet_name='Test Sheet')

@pytest.mark.asyncio
async def test_concurrent_sheet_access(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    
    # Simulate existing sheet
    mock_drive.files().list().execute.return_value = {
        'files': [{'id': 'existing123', 'name': 'Test Sheet'}]
    }
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {'title': 'Test'}
    vision_analysis = {'test': 'data'}
    
    # Run multiple saves concurrently
    import asyncio
    tasks = [
        storage.save(content, vision_analysis, sheet_name='Test Sheet')
        for _ in range(5)
    ]
    results = await asyncio.gather(*tasks)
    
    # All saves should use the same sheet ID
    assert all('existing123' in url for url in results)
    
    # Verify we only searched for the sheet once
    assert mock_drive.files().list().execute.call_count == 1

@pytest.mark.asyncio
async def test_duplicate_url_handling(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    
    # Mock existing spreadsheet
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'test123'}]}
    
    # Mock existing URLs in the sheet
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        'values': [
            ['Image URL'],  # Header
            ['https://example.com/image1.jpg'],
            ['https://example.com/image2.jpg']
        ]
    }
    
    # Test with a new URL
    content = {'image_url': 'https://example.com/image3.jpg'}
    vision_analysis = {'test': 'data'}
    sheet_url = await storage.save(content, vision_analysis)
    
    # Verify new URL was saved
    assert mock_sheets.spreadsheets().values().append.called
    
    # Test with a duplicate URL
    content = {'image_url': 'https://example.com/image1.jpg'}
    sheet_url = await storage.save(content, vision_analysis)
    
    # Verify no new append was made for duplicate URL
    assert mock_sheets.spreadsheets().values().append.call_count == 1

@pytest.mark.asyncio
async def test_duplicate_url_empty_sheet(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    
    # Mock empty spreadsheet
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'test123'}]}
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        'values': [['Image URL']]  # Only header
    }
    
    # Test with a new URL
    content = {'image_url': 'https://example.com/image1.jpg'}
    vision_analysis = {'test': 'data'}
    sheet_url = await storage.save(content, vision_analysis)
    
    # Verify URL was saved
    assert mock_sheets.spreadsheets().values().append.called

@pytest.mark.asyncio
async def test_duplicate_url_no_image_url(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    
    # Mock existing spreadsheet
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'test123'}]}
    
    # Test with content without image_url
    content = {'title': 'Test'}
    vision_analysis = {'test': 'data'}
    sheet_url = await storage.save(content, vision_analysis)
    
    # Verify save was attempted (no duplicate check needed)
    assert mock_sheets.spreadsheets().values().append.called

@pytest.mark.asyncio
async def test_duplicate_url_error_handling(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    
    # Mock existing spreadsheet
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'test123'}]}
    
    # Mock error when checking URLs
    mock_sheets.spreadsheets.return_value.values.return_value.get.side_effect = Exception("Failed to get values")
    
    # Mock Streamlit context
    with patch('utils.document_storage.st') as mock_st:
        # Test error handling
        content = {'image_url': 'https://example.com/image1.jpg'}
        vision_analysis = {'test': 'data'}
        
        with pytest.raises(Exception, match="Error checking for duplicate URLs"):
            await storage.save(content, vision_analysis)

@pytest.mark.asyncio
async def test_duplicate_url_nonexistent_sheet(storage, mock_services):
    """Test handling of duplicate URLs when the sheet doesn't exist yet."""
    mock_sheets, mock_drive = mock_services
    
    # Mock no existing spreadsheet
    mock_drive.files().list().execute.return_value = {'files': []}
    mock_sheets.spreadsheets().create().execute.return_value = {'spreadsheetId': 'new123'}
    
    # Mock the values().get() call to return empty values for first save
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        'values': [['Image URL']]  # Only header row
    }
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    # Test with a new URL
    content = {'image_url': 'https://example.com/image1.jpg'}
    vision_analysis = {'test': 'data'}
    
    # Reset the append call counter
    mock_sheets.spreadsheets().values().append.reset_mock()
    
    # First save should create the sheet
    sheet_url = await storage.save(content, vision_analysis, sheet_name='New Sheet')
    assert 'new123' in sheet_url
    
    # Verify sheet was created and first URL was saved
    assert mock_sheets.spreadsheets().create.called
    assert mock_sheets.spreadsheets().values().append.call_count == 1
    
    # Mock the values().get() call to return the first URL for second save
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        'values': [
            ['Image URL'],  # Header row
            ['https://example.com/image1.jpg']  # First URL
        ]
    }
    
    # Reset the append call counter again
    mock_sheets.spreadsheets().values().append.reset_mock()
    
    # Second save with same URL should detect duplicate
    sheet_url2 = await storage.save(content, vision_analysis, sheet_name='New Sheet')
    assert 'new123' in sheet_url2
    
    # Verify no new append was made
    assert mock_sheets.spreadsheets().values().append.call_count == 0

@pytest.mark.asyncio
async def test_duplicate_url_early_check():
    """Test early duplicate URL check before processing."""
    # Mock the storage
    storage = GoogleSheetsStorage()
    storage._get_sheets_service = MagicMock()
    storage._get_drive_service = MagicMock()
    
    # Mock the service
    service = MagicMock()
    storage._get_sheets_service.return_value = service
    
    # Mock the drive service and its chained methods
    drive_service = MagicMock()
    files_mock = MagicMock()
    list_mock = MagicMock()
    drive_service.files.return_value = files_mock
    files_mock.list.return_value = list_mock
    list_mock.execute.return_value = {
        'files': [{'id': 'test_spreadsheet_id', 'name': 'Test Sheet'}]
    }
    storage._get_drive_service.return_value = drive_service
    
    # Mock the sheets service and its chained methods
    sheets_mock = MagicMock()
    values_mock = MagicMock()
    get_mock = MagicMock()
    service.spreadsheets.return_value = sheets_mock
    sheets_mock.values.return_value = values_mock
    values_mock.get.return_value = get_mock
    get_mock.execute.return_value = {
        'values': [
            ['Image URL'],  # Header
            ['https://drive.google.com/file/d/123/view'],
            ['https://drive.google.com/uc?export=download&id=456']
        ]
    }
    
    # Test URLs
    test_urls = [
        'https://drive.google.com/file/d/123/view',  # Duplicate (same as first existing URL)
        'https://drive.google.com/uc?export=download&id=789',  # New URL
        'https://drive.google.com/uc?export=download&id=456'  # Duplicate (same as second existing URL)
    ]
    
    # Get existing URLs
    existing_urls = await storage._get_existing_urls('Test Sheet')
    
    # Check for duplicates
    duplicate_urls = []
    valid_urls = []
    
    for url in test_urls:
        normalized_url = convert_google_drive_url(url)
        if normalized_url in existing_urls:
            duplicate_urls.append(url)
        else:
            valid_urls.append(url)
    
    # Verify results
    assert len(duplicate_urls) == 2
    assert len(valid_urls) == 1
    assert 'https://drive.google.com/file/d/123/view' in duplicate_urls
    assert 'https://drive.google.com/uc?export=download&id=456' in duplicate_urls
    assert 'https://drive.google.com/uc?export=download&id=789' in valid_urls
    
    # Verify service calls
    files_mock.list.assert_called_once_with(
        q="name='Test Sheet' and mimeType='application/vnd.google-apps.spreadsheet'",
        spaces='drive',
        fields='files(id, name)'
    )
    values_mock.get.assert_called_once_with(
        spreadsheetId='test_spreadsheet_id',
        range='Sheet1!G:G'
    ) 