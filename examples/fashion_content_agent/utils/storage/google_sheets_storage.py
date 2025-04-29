import logging
from typing import Set, Dict, Any, Optional, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.url_validation import convert_google_drive_url
from datetime import datetime
import os

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
            logger.info(f"Checking for existing URLs in sheet: {sheet_name}")
            service = self._get_sheets_service()
            spreadsheet_id = self._spreadsheet_cache.get(sheet_name)
            
            if not spreadsheet_id:
                logger.info(f"No spreadsheet ID found in cache for sheet: {sheet_name}")
                return set()
                
            logger.info(f"Found spreadsheet ID: {spreadsheet_id} for sheet: {sheet_name}")
            logger.info("Fetching values from image URL column (G)")
            
            # Get all values from the image URL column (G)
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!G:G'  # Column G contains image URLs
            ).execute()
            
            if not result.get('values'):
                logger.info("No values found in the spreadsheet")
                return set()
                
            # Remove header row and normalize URLs
            urls = []
            for url in result.get('values', [])[1:]:
                if url:
                    original_url = url[0]
                    normalized_url = convert_google_drive_url(original_url)
                    urls.append(normalized_url)
                    logger.info(f"Found URL - Original: {original_url}, Normalized: {normalized_url}")
            
            unique_urls = set(urls)
            logger.info(f"Found {len(unique_urls)} unique URLs in sheet: {sheet_name}")
            return unique_urls
            
        except Exception as e:
            logger.error(f"Error getting existing URLs from sheet '{sheet_name}': {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            raise Exception(f"Error getting existing URLs from sheet '{sheet_name}': {str(e)}")
            
    def _share_spreadsheet(self, spreadsheet_id: str, email: str) -> None:
        """
        Share the spreadsheet with the specified email.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet to share
            email: The email address to share with
        """
        try:
            logger.info(f"Sharing spreadsheet {spreadsheet_id} with {email}")
            drive_service = self._get_drive_service()
            
            # Create permission
            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': email
            }
            
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            logger.info(f"Successfully shared spreadsheet with {email}")
            
        except Exception as e:
            logger.error(f"Error sharing spreadsheet: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            raise Exception(f"Error sharing spreadsheet: {str(e)}")

    async def save(self, content: Dict[str, Any], vision_analysis: Dict[str, Any], sheet_name: str) -> str:
        """
        Save content and vision analysis to Google Sheets.
        
        Args:
            content: The content to save
            vision_analysis: The vision analysis results
            sheet_name: The name of the sheet to save to
            
        Returns:
            str: The URL of the Google Sheet
        """
        try:
            logger.info(f"Attempting to save content to sheet: {sheet_name}")
            service = self._get_sheets_service()
            spreadsheet_id = self._spreadsheet_cache.get(sheet_name)
            
            if not spreadsheet_id:
                logger.info(f"Creating new spreadsheet: {sheet_name}")
                # Create new spreadsheet
                spreadsheet = {
                    'properties': {'title': sheet_name},
                    'sheets': [{'properties': {'title': 'Sheet1'}}]
                }
                spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
                spreadsheet_id = spreadsheet['spreadsheetId']
                self._spreadsheet_cache[sheet_name] = spreadsheet_id
                logger.info(f"Created new spreadsheet with ID: {spreadsheet_id}")
                
                # Share the spreadsheet with the user's email or default
                user_email = content.get('user_email') or os.environ.get('GOOGLE_SHARE_EMAIL')
                if user_email:
                    self._share_spreadsheet(spreadsheet_id, user_email)
                else:
                    logger.warning("No user email provided and GOOGLE_SHARE_EMAIL not set. Sheet will not be shared.")
                
                # Write headers
                headers = [
                    'Title', 'Description', 'Caption', 'Hashtags',
                    'Alt Text', 'Platform', 'Image URL', 'Key Features',
                    'Generated At', 'Vision Analysis'
                ]
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='Sheet1!A1:J1',  # Updated to include 10 columns
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
                logger.info("Headers written successfully")
            
            # Convert lists to strings
            hashtags_str = ', '.join(content.get('hashtags', []))
            key_features_str = ', '.join(content.get('key_features', []))
            
            # Get current timestamp
            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare row data
            row = [
                content.get('title', ''),
                content.get('description', ''),
                content.get('caption', ''),
                hashtags_str,
                content.get('alt_text', ''),
                content.get('platform', ''),
                content.get('image_url', ''),
                key_features_str,
                generated_at,
                str(vision_analysis)  # Convert vision analysis to string
            ]
            
            logger.info(f"Prepared row data: {row}")
            
            # Append row
            logger.info(f"Appending row to spreadsheet: {spreadsheet_id}")
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:J',
                valueInputOption='RAW',
                body={'values': [row]}
            ).execute()
            
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            logger.info(f"Successfully saved content. Sheet URL: {sheet_url}")
            return sheet_url
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            logger.error(f"Error details: {e.content.decode() if hasattr(e, 'content') else 'No content'}")
            raise Exception(f"Error saving content to sheet '{sheet_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error saving content to sheet '{sheet_name}': {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            raise Exception(f"Error saving content to sheet '{sheet_name}': {str(e)}")
            
    async def save_batch(self, contents: List[Dict[str, Any]], vision_analyses: List[Dict[str, Any]], sheet_name: str) -> str:
        """
        Save multiple contents and vision analyses to Google Sheets in a batch.
        
        Args:
            contents: List of content dictionaries
            vision_analyses: List of vision analysis dictionaries
            sheet_name: The name of the sheet to save to
            
        Returns:
            str: The URL of the Google Sheet
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
                
                # Share the spreadsheet with the user's email or default (only once)
                shared = False
                for content in contents:
                    user_email = content.get('user_email') or os.environ.get('GOOGLE_SHARE_EMAIL')
                    if user_email and not shared:
                        self._share_spreadsheet(spreadsheet_id, user_email)
                        shared = True
                        break
                if not shared:
                    logger.warning("No user email provided in batch and GOOGLE_SHARE_EMAIL not set. Sheet will not be shared.")
                
                # Write headers
                headers = [
                    'Title', 'Description', 'Caption', 'Hashtags',
                    'Alt Text', 'Platform', 'Image URL', 'Key Features',
                    'Generated At', 'Vision Analysis'
                ]
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='Sheet1!A1:J1',  # Updated to include 10 columns
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
            
            # Prepare batch data
            rows = []
            for content, vision_analysis in zip(contents, vision_analyses):
                # Convert lists to strings
                hashtags_str = ', '.join(content.get('hashtags', []))
                key_features_str = ', '.join(content.get('key_features', []))
                
                # Get current timestamp
                generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                row = [
                    content.get('title', ''),
                    content.get('description', ''),
                    content.get('caption', ''),
                    hashtags_str,
                    content.get('alt_text', ''),
                    content.get('platform', ''),
                    content.get('image_url', ''),
                    key_features_str,
                    generated_at,
                    str(vision_analysis)  # Convert vision analysis to string
                ]
                rows.append(row)
            
            # Append batch
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:J',
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()
            
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
        except Exception as e:
            logger.error(f"Error saving batch to sheet '{sheet_name}': {str(e)}")
            raise Exception(f"Error saving batch to sheet '{sheet_name}': {str(e)}")
            
    async def close(self) -> None:
        """Close all resources."""
        if self._sheets_service:
            self._sheets_service = None
        if self._drive_service:
            self._drive_service = None 