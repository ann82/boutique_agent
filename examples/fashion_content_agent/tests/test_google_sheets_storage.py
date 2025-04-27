import pytest
from unittest.mock import MagicMock, patch
from utils.document_storage import GoogleSheetsStorage

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
        'Title', 'Description', 'Caption', 'Hashtags', 'Alt Text', 'Platform', 'Image URL', 'Vision Analysis'
    ]

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
    vision_analysis = {'test': 'data'}
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
    assert 'sheet123' in sheet_url
    
    # Check that content is written correctly
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert row[0] == 'Test Title'
    assert row[3] == '#tag'

@pytest.mark.asyncio
async def test_save_content_missing_fields(storage, mock_services):
    mock_sheets, mock_drive = mock_services
    mock_drive.files().list().execute.return_value = {'files': [{'id': 'sheet123', 'name': 'Test Sheet'}]}
    mock_sheets.spreadsheets().values().append().execute.return_value = {}
    
    content = {
        'title': 'Test Title',
        'platform': 'Instagram'
    }
    vision_analysis = {'test': 'data'}
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
    assert 'sheet123' in sheet_url
    
    # Check that missing fields are empty
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert row[0] == 'Test Title'
    assert row[5] == 'Instagram'
    assert all(cell == '' for i, cell in enumerate(row) if i not in [0, 5, 7])

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
    vision_analysis = {'test': 'data'}
    
    sheet_url = await storage.save(content, vision_analysis, sheet_name='Test Sheet')
    assert 'sheet123' in sheet_url
    
    # Check that extra fields are not written
    args, kwargs = mock_sheets.spreadsheets().values().append.call_args
    row = kwargs['body']['values'][0]
    assert len(row) == 8

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
    assert all(cell == '' for i, cell in enumerate(row) if i != 7)
    assert row[7] == '{}'

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
    vision_analysis = {'test': 'data'}
    
    # Save should create new sheet with headers
    sheet_url = await storage.save(content, vision_analysis, sheet_name='New Sheet')
    assert 'new123' in sheet_url
    
    # Verify headers were written
    args, kwargs = mock_sheets.spreadsheets().values().update.call_args
    assert kwargs['range'] == 'Sheet1!A1:H1'
    assert len(kwargs['body']['values'][0]) == 8

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
    with pytest.raises(Exception, match='Error creating spreadsheet'):
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