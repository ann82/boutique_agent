"""
Main application module for the Fashion Content Agent.
"""
import os
import json
from typing import Dict, Any, Optional, List
from utils.image_utils import is_valid_image_url
from utils.validation import validate_content_format
from session_manager import get_session, init_session, cleanup
import asyncio

# Initialize session
async def init():
    await init_session()

class FashionContentAgent:
    """Main agent class for fashion content generation."""
    
    def __init__(self):
        """Initialize the agent with required components."""
        session = get_session()
        self.vision_agent = session["vision_agent"]
        self.content_agent = session["content_agent"]
        self.storage = session["storage"]
        
    async def process_image(self, image_url: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Process a single image URL and generate content."""
        try:
            # Validate image URL
            if not is_valid_image_url(image_url):
                raise ValueError("Invalid image URL")
            
            # Check for duplicate URL in the sheet before any processing
            try:
                # Get all existing image URLs from the sheet
                service = self.storage._get_sheets_service()
                spreadsheet_id = self.storage._spreadsheet_cache.get(sheet_name or "Fashion Content Agent")
                if not spreadsheet_id:
                    # If sheet doesn't exist yet, it's not a duplicate
                    pass
                else:
                    existing_urls = service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range='Sheet1!G:G'  # Column G contains image URLs
                    ).execute()
                    
                    if existing_urls.get('values'):
                        # Remove header row and flatten the list
                        existing_urls_list = [url[0] for url in existing_urls.get('values', [])[1:] if url]
                        if image_url in existing_urls_list:
                            return {
                                "content": {"image_url": image_url},
                                "vision_analysis": {},
                                "sheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
                                "message": f"Image URL already exists in sheet '{sheet_name or 'Fashion Content Agent'}'"
                            }
            except Exception as e:
                # If there's an error checking for duplicates, raise an exception
                raise Exception(f"Error checking for duplicate URLs in sheet '{sheet_name or 'Fashion Content Agent'}': {str(e)}")
            
            # Get vision analysis
            vision_analysis = await self.vision_agent.analyze_image(image_url)
            
            # Generate content
            content = await self.content_agent.generate_content(image_url)
            
            # Add image URL to content
            content["image_url"] = image_url
            
            # Validate content
            validate_content_format(content)
            
            # Save to Google Sheets
            sheet_url = await self.storage.save(content, vision_analysis, sheet_name)
            
            return {
                "content": content,
                "vision_analysis": vision_analysis,
                "sheet_url": sheet_url
            }
            
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")
    
    async def process_images(self, image_urls: List[str], sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Process multiple image URLs and generate content in batch."""
        try:
            # Validate number of images
            if len(image_urls) > 3:
                raise ValueError("Maximum 3 images can be processed at a time")
            
            # Check for duplicate URLs in the input
            unique_urls = list(set(image_urls))
            if len(unique_urls) < len(image_urls):
                raise ValueError("Duplicate image URLs are not allowed in the input")
            
            # Check for duplicate URLs in the sheet
            try:
                service = self.storage._get_sheets_service()
                spreadsheet_id = self.storage._spreadsheet_cache.get(sheet_name or "Fashion Content Agent")
                if not spreadsheet_id:
                    # If sheet doesn't exist yet, no duplicates to check
                    pass
                else:
                    existing_urls = service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range='Sheet1!G:G'  # Column G contains image URLs
                    ).execute()
                    
                    if existing_urls.get('values'):
                        # Remove header row and flatten the list
                        existing_urls_list = [url[0] for url in existing_urls.get('values', [])[1:] if url]
                        # Filter out URLs that already exist in the sheet
                        new_urls = [url for url in unique_urls if url not in existing_urls_list]
                        
                        if not new_urls:
                            return [{
                                "content": {"image_url": url},
                                "vision_analysis": {},
                                "sheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
                                "message": f"Image URL already exists in sheet '{sheet_name or 'Fashion Content Agent'}'"
                            } for url in unique_urls]
                        
                        # Update unique_urls to only include new URLs
                        unique_urls = new_urls
            except Exception as e:
                raise Exception(f"Error checking for duplicate URLs in sheet '{sheet_name or 'Fashion Content Agent'}': {str(e)}")
            
            # Process images concurrently
            tasks = []
            for url in unique_urls:
                # Validate image URL
                if not is_valid_image_url(url):
                    raise ValueError(f"Invalid image URL: {url}")
                
                # Get vision analysis
                vision_task = self.vision_agent.analyze_image(url)
                tasks.append(vision_task)
            
            # Get all vision analyses
            vision_analyses = await asyncio.gather(*tasks)
            
            # Generate content for all images
            content_tasks = []
            for url in unique_urls:
                content_task = self.content_agent.generate_content(url)
                content_tasks.append(content_task)
            
            # Get all content
            contents = await asyncio.gather(*content_tasks)
            
            # Add image URLs to content
            for content, url in zip(contents, unique_urls):
                content["image_url"] = url
                validate_content_format(content)
            
            # Save all content in a single batch
            sheet_url = await self.storage.save_batch(contents, vision_analyses, sheet_name)
            
            # Prepare results
            results = []
            for content, vision_analysis in zip(contents, vision_analyses):
                results.append({
                    "content": content,
                    "vision_analysis": vision_analysis,
                    "sheet_url": sheet_url
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Error processing images: {str(e)}")
            
    async def close(self) -> None:
        """Close all resources."""
        cleanup()

def extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from text."""
    try:
        # Find the first { and last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in text")
        return json.loads(text[start:end])
    except Exception as e:
        raise ValueError(f"Error extracting JSON: {str(e)}")

# Initialize the session
asyncio.run(init())
