import logging
from typing import Set, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.url_validation import convert_google_drive_url

logger = logging.getLogger(__name__)

class GoogleSheetsStorage:
    def __init__(self, credentials_path: str):
        """
        Initialize Google Sheets storage.
        
        Args:
            credentials_path: Path to the Google service account credentials JSON file
        """
        self.credentials_path = credentials_path
        self._spreadsheet_cache = {}  # Cache for spreadsheet IDs
        self._sheets_service = None
        self._drive_service = None
        
    def _get_sheets_service(self):
        """Get or create Google Sheets service."""
        if not self._sheets_service:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self._sheets_service = build('sheets', 'v4', credentials=credentials)
        return self._sheets_service
        
    def _get_drive_service(self):
        """Get or create Google Drive service."""
        if not self._drive_service:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self._drive_service = build('drive', 'v3', credentials=credentials)
        return self._drive_service
        
    async def _get_existing_urls(self, sheet_name: str) -> Set[str]:
        """
        Get all existing image URLs from a sheet.
        
        Args:
            sheet_name: The name of the sheet to check
            
        Returns:
            Set of normalized image URLs
        """
        try:
            service = self._get_sheets_service()
            spreadsheet_id = self._spreadsheet_cache.get(sheet_name)
            
            if not spreadsheet_id:
                return set()
                
            # Get all values from the image URL column (G)
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!G:G'  # Column G contains image URLs
            ).execute()
            
            if not result.get('values'):
                return set()
                
            # Remove header row and normalize URLs
            urls = [convert_google_drive_url(url[0]) for url in result.get('values', [])[1:] if url]
            return set(urls)
            
        except Exception as e:
            logger.error(f"Error getting existing URLs from sheet '{sheet_name}': {str(e)}")
            raise Exception(f"Error getting existing URLs from sheet '{sheet_name}': {str(e)}")
            
    async def save_content(self, sheet_name: str, content: Dict[str, Any]) -> bool:
        """
        Save content to Google Sheets.
        
        Args:
            sheet_name: The name of the sheet to save to
            content: The content to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            service = self._get_sheets_service()
            spreadsheet_id = self._spreadsheet_cache.get(sheet_name)
            
            if not spreadsheet_id:
                # Create new spreadsheet
                spreadsheet = {
                    'properties': {'title': sheet_name},
                    'sheets': [{'properties': {'title': 'Sheet1'}}]
                }
                spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
                spreadsheet_id = spreadsheet['spreadsheetId']
                self._spreadsheet_cache[sheet_name] = spreadsheet_id
                
                # Write headers
                headers = [
                    'Title', 'Description', 'Hashtags', 'Keywords',
                    'Brand', 'Category', 'Image URL', 'Generated At'
                ]
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='Sheet1!A1:H1',
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
            
            # Prepare row data
            row = [
                content.get('title', ''),
                content.get('description', ''),
                content.get('hashtags', ''),
                content.get('keywords', ''),
                content.get('brand', ''),
                content.get('category', ''),
                content.get('image_url', ''),
                content.get('generated_at', '')
            ]
            
            # Append row
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:H',
                valueInputOption='RAW',
                body={'values': [row]}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving content to sheet '{sheet_name}': {str(e)}")
            return False 