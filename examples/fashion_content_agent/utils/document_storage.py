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
import streamlit as st

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
            st.write(f"Using sheet name: {sheet_name}")
            
            # Check if we already have a spreadsheet for this name
            if sheet_name not in self._spreadsheet_cache:
                # Search for existing spreadsheet
                drive_service = self._get_drive_service()
                query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
                st.write(f"Searching for existing spreadsheet with name: {sheet_name}")
                results = drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)'
                ).execute()
                
                if results.get('files'):
                    # Use existing spreadsheet
                    st.write("Found existing spreadsheet")
                    self._spreadsheet_cache[sheet_name] = results['files'][0]['id']
                    st.write(f"Using existing spreadsheet ID: {self._spreadsheet_cache[sheet_name]}")
                else:
                    # Create new spreadsheet
                    st.write("No existing spreadsheet found, creating new one")
                    spreadsheet = self._create_spreadsheet(sheet_name)
                    self._spreadsheet_cache[sheet_name] = spreadsheet['spreadsheetId']
                    st.write(f"Created new spreadsheet with ID: {self._spreadsheet_cache[sheet_name]}")
                    
                    # Share with user
                    if self.share_email:
                        st.write(f"Attempting to share spreadsheet with: {self.share_email}")
                        self._share_spreadsheet(spreadsheet['spreadsheetId'])
            
            # Get spreadsheet ID from cache
            spreadsheet_id = self._spreadsheet_cache[sheet_name]
            
            # Check for duplicate image URLs
            current_image_url = content.get('image_url', '')
            if current_image_url:
                st.write(f"Checking for duplicate image URL: {current_image_url}")
                try:
                    # Get all existing image URLs from column G (7th column)
                    existing_urls = service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range='Sheet1!G:G'
                    ).execute()
                    
                    if existing_urls.get('values'):
                        # Remove header row and flatten the list
                        existing_urls_list = [url[0] for url in existing_urls.get('values', [])[1:] if url]
                        if current_image_url in existing_urls_list:
                            st.write(f"Duplicate image URL found, skipping: {current_image_url}")
                            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                        st.write("No duplicate found, proceeding with save")
                    else:
                        st.write("No existing entries found in spreadsheet")
                except Exception as e:
                    st.write(f"Error checking for duplicate URLs: {str(e)}")
                    raise Exception(f"Error checking for duplicate URLs: {str(e)}")
            
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
            st.write("Successfully saved new entry to spreadsheet")
            
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
        except Exception as e:
            st.write(f"Error saving to Google Sheets: {str(e)}")
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
            
            # Log the current service account details
            st.write("Current service account details:")
            about = drive_service.about().get(fields="user").execute()
            st.write(f"Service Account Email: {about.get('user', {}).get('emailAddress')}")
            
            # First try to transfer ownership
            try:
                permission = {
                    'type': 'user',
                    'role': 'owner',  # Try to make them an owner
                    'emailAddress': self.share_email,
                    'transferOwnership': True
                }
                
                st.write(f"Attempting to transfer ownership to: {self.share_email}")
                transfer_result = drive_service.permissions().create(
                    fileId=spreadsheet_id,
                    body=permission,
                    transferOwnership=True,
                    fields='id'
                ).execute()
                st.write("Ownership transfer successful")
            except HttpError as e:
                st.write(f"Could not transfer ownership: {str(e)}")
                # If ownership transfer fails, try making them an editor
                try:
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': self.share_email
                    }
                    
                    st.write("Attempting to grant editor access...")
                    drive_service.permissions().create(
                        fileId=spreadsheet_id,
                        body=permission,
                        fields='id',
                        sendNotificationEmail=True
                    ).execute()
                    st.write("Editor access granted successfully")
                except HttpError as e2:
                    st.write(f"Could not grant editor access: {str(e2)}")
            
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
                st.write("File made accessible via link")
            except HttpError as e:
                st.write(f"Could not update file settings: {str(e)}")
            
            # Verify final permissions
            try:
                permissions = drive_service.permissions().list(
                    fileId=spreadsheet_id,
                    fields='permissions(id,type,role,emailAddress)'
                ).execute()
                
                st.write("\nFinal permissions configuration:")
                for p in permissions.get('permissions', []):
                    st.write(f"- Type: {p.get('type')}, Role: {p.get('role')}, Email: {p.get('emailAddress', 'N/A')}")
                
                # Get and display the sharing URL
                file = drive_service.files().get(
                    fileId=spreadsheet_id,
                    fields='webViewLink'
                ).execute()
                st.write(f"\nDirect sharing link: {file.get('webViewLink')}")
                
            except HttpError as e:
                st.write(f"Could not verify final permissions: {str(e)}")
            
        except Exception as error:
            st.write(f"Error details: {str(error)}")
            raise Exception(f"Error sharing spreadsheet: {error}")

    async def close(self) -> None:
        """Close the services."""
        if self._sheets_service:
            self._sheets_service.close()
            self._sheets_service = None
        if self._drive_service:
            self._drive_service.close()
            self._drive_service = None 