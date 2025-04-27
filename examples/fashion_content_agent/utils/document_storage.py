"""
Google Sheets storage implementation.
"""
import os
import json
from typing import Dict, Any, Optional, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config

class GoogleSheetsStorage:
    """Storage implementation using Google Sheets."""
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        share_email: Optional[str] = None,
        batch_size: int = 100
    ):
        self.credentials_file = credentials_file or Config.GOOGLE_CREDENTIALS_FILE
        self.share_email = share_email or Config.GOOGLE_SHARE_EMAIL
        self.batch_size = batch_size
        self._sheets_service = None
        self._drive_service = None
        self._spreadsheet_id = None
        self._spreadsheet_cache = {}  # Cache for spreadsheet IDs

    def _get_sheets_service(self):
        """Get or create the Google Sheets service."""
        if self._sheets_service is None:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self._sheets_service = build('sheets', 'v4', credentials=credentials)
        return self._sheets_service

    def _get_drive_service(self):
        """Get or create the Google Drive service."""
        if self._drive_service is None:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self._drive_service = build('drive', 'v3', credentials=credentials)
        return self._drive_service

    async def save(
        self,
        content: Dict[str, Any],
        vision_analysis: Dict[str, Any],
        sheet_name: Optional[str] = None
    ) -> str:
        """Save content to Google Sheets."""
        try:
            service = self._get_sheets_service()
            
            # Use default name if none provided
            sheet_name = sheet_name or "Fashion Content Agent"
            
            # Check if we already have a spreadsheet for this name
            if sheet_name not in self._spreadsheet_cache:
                # Search for existing spreadsheet
                drive_service = self._get_drive_service()
                query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
                results = drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)'
                ).execute()
                
                if results.get('files'):
                    # Use existing spreadsheet
                    self._spreadsheet_cache[sheet_name] = results['files'][0]['id']
                else:
                    # Create new spreadsheet
                    spreadsheet = self._create_spreadsheet(sheet_name)
                    self._spreadsheet_cache[sheet_name] = spreadsheet['spreadsheetId']
                    
                    # Share with user
                    if self.share_email:
                        self._share_spreadsheet(spreadsheet['spreadsheetId'])
            
            # Get spreadsheet ID from cache
            spreadsheet_id = self._spreadsheet_cache[sheet_name]
            
            # Prepare data
            values = [
                [
                    content.get('title', ''),
                    content.get('description', ''),
                    content.get('caption', ''),
                    ', '.join(content.get('hashtags', [])),
                    content.get('alt_text', ''),
                    content.get('platform', ''),
                    content.get('image_url', ''),
                    json.dumps(vision_analysis)
                ]
            ]
            
            # Append data
            body = {
                'values': values
            }
            
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:H',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
        except Exception as e:
            raise Exception(f"Error saving to Google Sheets: {str(e)}")

    def _create_spreadsheet(self, title: str) -> Dict[str, Any]:
        """Create a new Google Sheet."""
        try:
            service = self._get_sheets_service()
            
            # Define headers
            headers = [
                'Title',
                'Description',
                'Caption',
                'Hashtags',
                'Alt Text',
                'Platform',
                'Image URL',
                'Vision Analysis'
            ]
            
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'Sheet1',
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 8
                            }
                        }
                    }
                ]
            }
            
            # Create spreadsheet
            spreadsheet = service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            # Add headers
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet['spreadsheetId'],
                range='Sheet1!A1:H1',
                valueInputOption='RAW',
                body={
                    'values': [headers]
                }
            ).execute()
            
            return spreadsheet
            
        except HttpError as error:
            raise Exception(f"Error creating spreadsheet: {error}")

    def _share_spreadsheet(self, spreadsheet_id: str) -> None:
        """Share the spreadsheet with the specified email."""
        try:
            drive_service = self._get_drive_service()
            
            # Create permission
            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': self.share_email
            }
            
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                fields='id'
            ).execute()
            
        except HttpError as error:
            raise Exception(f"Error sharing spreadsheet: {error}")

    async def close(self) -> None:
        """Close the services."""
        if self._sheets_service:
            self._sheets_service.close()
            self._sheets_service = None
        if self._drive_service:
            self._drive_service.close()
            self._drive_service = None 