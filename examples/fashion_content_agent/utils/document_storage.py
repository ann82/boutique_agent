"""
Google Sheets storage functionality for the Fashion Content Agent.
"""
import os
import json
from typing import Dict, Any, Optional, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config
import streamlit as st
from utils.image_utils import convert_google_drive_url
from utils.cache import SpreadsheetCache

class GoogleSheetsStorage:
    """Google Sheets storage implementation."""
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        share_email: Optional[str] = None,
        batch_size: int = 100
    ):
        """
        Initialize Google Sheets storage.
        
        Args:
            credentials_file: Path to Google API credentials file
            share_email: Email to share spreadsheets with (optional)
            batch_size: Number of items to save in a single batch
        """
        self.credentials_file = credentials_file or Config.GOOGLE_CREDENTIALS_FILE
        self.share_email = share_email or Config.GOOGLE_SHARE_EMAIL
        self.batch_size = batch_size
        self._sheets_service = None
        self._drive_service = None
        self._spreadsheet_id = None
        self._spreadsheet_cache = SpreadsheetCache()

    def _get_sheets_service(self):
        """Get or create the Google Sheets service."""
        if self._sheets_service is None:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/drive.metadata'
                ]
            )
            self._sheets_service = build('sheets', 'v4', credentials=credentials)
        return self._sheets_service

    def _get_drive_service(self):
        """Get or create the Google Drive service."""
        if self._drive_service is None:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=[
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/drive.metadata',
                    'https://www.googleapis.com/auth/drive.appdata'
                ]
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
            
            # Get spreadsheet ID from cache or search for existing
            spreadsheet_id = self._spreadsheet_cache.get(sheet_name)
            if not spreadsheet_id:
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
                    spreadsheet_id = results['files'][0]['id']
                    self._spreadsheet_cache.set(sheet_name, spreadsheet_id)
                else:
                    # Create new spreadsheet
                    spreadsheet = self._create_spreadsheet(sheet_name)
                    spreadsheet_id = spreadsheet['spreadsheetId']
                    self._spreadsheet_cache.set(sheet_name, spreadsheet_id)
                    
                    # Share with user
                    if self.share_email:
                        self._share_spreadsheet(spreadsheet_id)
            
            # Check for duplicate image URLs
            current_image_url = content.get('image_url', '')
            if current_image_url:
                # Normalize the current URL
                normalized_current_url = convert_google_drive_url(current_image_url)
                
                try:
                    # Get all existing image URLs from column G (7th column)
                    existing_urls = service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range='Sheet1!G:G'
                    ).execute()
                    
                    if existing_urls.get('values'):
                        # Remove header row and flatten the list
                        existing_urls_list = []
                        for url in existing_urls.get('values', [])[1:]:
                            if url and url[0]:
                                normalized_url = convert_google_drive_url(url[0])
                                existing_urls_list.append(normalized_url)
                        
                        if normalized_current_url in existing_urls_list:
                            raise ValueError(f"Image URL already exists in sheet '{sheet_name}'")
                except Exception as e:
                    if isinstance(e, ValueError):
                        raise
                    raise Exception(f"Error checking for duplicate URLs in sheet '{sheet_name}': {str(e)}")
            
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
                    ', '.join(vision_analysis.get('key_features', [])),
                    json.dumps(vision_analysis) if vision_analysis else '{}'
                ]
            ]
            
            # Append data
            body = {
                'values': values
            }
            
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:I',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error saving to Google Sheets: {str(e)}")

    async def save_batch(
        self,
        contents: List[Dict[str, Any]],
        vision_analyses: List[Dict[str, Any]],
        sheet_name: Optional[str] = None
    ) -> str:
        """Save multiple content items to Google Sheets in a single batch."""
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
                    self._spreadsheet_cache.set(sheet_name, results['files'][0]['id'])
                else:
                    # Create new spreadsheet
                    spreadsheet = self._create_spreadsheet(sheet_name)
                    self._spreadsheet_cache.set(sheet_name, spreadsheet['spreadsheetId'])
                    
                    # Share with user
                    if self.share_email:
                        self._share_spreadsheet(spreadsheet['spreadsheetId'])
            
            # Get spreadsheet ID from cache
            spreadsheet_id = self._spreadsheet_cache.get(sheet_name)
            
            # Prepare batch data
            values = []
            for content, vision_analysis in zip(contents, vision_analyses):
                values.append([
                    content.get('title', ''),
                    content.get('description', ''),
                    content.get('caption', ''),
                    ', '.join(content.get('hashtags', [])),
                    content.get('alt_text', ''),
                    content.get('platform', ''),
                    content.get('image_url', ''),
                    ', '.join(vision_analysis.get('key_features', [])),
                    json.dumps(vision_analysis) if vision_analysis else '{}'
                ])
            
            # Append batch data
            body = {
                'values': values
            }
            
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:I',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
        except Exception as e:
            raise Exception(f"Error saving batch to Google Sheets: {str(e)}")

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
                'Key Features',
                'Vision Analysis'
            ]
            
            # Create spreadsheet with basic structure
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            # Create spreadsheet
            spreadsheet = service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            # Add headers
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet['spreadsheetId'],
                range='Sheet1!A1:I1',
                valueInputOption='RAW',
                body={
                    'values': [headers]
                }
            ).execute()
            
            # Get the sheet ID
            sheet_metadata = service.spreadsheets().get(
                spreadsheetId=spreadsheet['spreadsheetId'],
                ranges=['Sheet1'],
                fields='sheets.properties'
            ).execute()
            
            sheet_id = sheet_metadata['sheets'][0]['properties']['sheetId']
            
            # Apply formatting
            header_format = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': len(headers)
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.2,
                                        'green': 0.2,
                                        'blue': 0.2
                                    },
                                    'horizontalAlignment': 'CENTER',
                                    'textFormat': {
                                        'foregroundColor': {
                                            'red': 1.0,
                                            'green': 1.0,
                                            'blue': 1.0
                                        },
                                        'fontSize': 12,
                                        'bold': True
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                        }
                    }
                ]
            }
            
            # Apply the formatting
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet['spreadsheetId'],
                body=header_format
            ).execute()
            
            return spreadsheet
            
        except HttpError as error:
            raise Exception(f"Error creating spreadsheet: {error}")

    def _share_spreadsheet(self, spreadsheet_id: str) -> None:
        """Share spreadsheet with specified email."""
        try:
            drive_service = self._get_drive_service()
            
            # First try to transfer ownership
            try:
                permission = {
                    'type': 'user',
                    'role': 'owner',
                    'emailAddress': self.share_email,
                    'transferOwnership': True
                }
                
                drive_service.permissions().create(
                    fileId=spreadsheet_id,
                    body=permission,
                    transferOwnership=True,
                    fields='id'
                ).execute()
            except HttpError:
                # If ownership transfer fails, try making them an editor
                try:
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': self.share_email
                    }
                    
                    drive_service.permissions().create(
                        fileId=spreadsheet_id,
                        body=permission,
                        fields='id',
                        sendNotificationEmail=True
                    ).execute()
                except HttpError:
                    pass
            
            # Make the file accessible via link as a fallback
            try:
                drive_service.files().update(
                    fileId=spreadsheet_id,
                    body={
                        'writersCanShare': True,
                        'copyRequiresWriterPermission': False
                    },
                    fields='id'
                ).execute()
            except HttpError:
                pass
            
        except Exception as error:
            raise Exception(f"Error sharing spreadsheet: {error}")

    async def close(self) -> None:
        """Close the services."""
        if self._sheets_service:
            self._sheets_service.close()
            self._sheets_service = None
        if self._drive_service:
            self._drive_service.close()
            self._drive_service = None

    async def _get_existing_urls(self, sheet_name: str) -> List[str]:
        """Get all existing image URLs from the sheet."""
        try:
            service = self._get_sheets_service()
            
            # Get spreadsheet ID
            spreadsheet_id = self._spreadsheet_cache.get(sheet_name)
            if not spreadsheet_id:
                # Search for existing spreadsheet
                drive_service = self._get_drive_service()
                query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
                results = drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)'
                ).execute()
                
                if results.get('files'):
                    spreadsheet_id = results['files'][0]['id']
                    self._spreadsheet_cache.set(sheet_name, spreadsheet_id)
                else:
                    return []  # No spreadsheet exists yet
            
            # Get all existing image URLs from column G (7th column)
            existing_urls = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!G:G'
            ).execute()
            
            if existing_urls.get('values'):
                # Remove header row and normalize URLs
                normalized_urls = []
                for url in existing_urls.get('values', [])[1:]:
                    if url and url[0]:
                        normalized_url = convert_google_drive_url(url[0])
                        normalized_urls.append(normalized_url)
                return normalized_urls
            
            return []
            
        except Exception as e:
            raise Exception(f"Error getting existing URLs: {str(e)}") 