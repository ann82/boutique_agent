"""
Main application module for the Fashion Content Agent.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from utils.image_utils import is_valid_image_url
from utils.validation import validate_content_format
from utils.url_validation import convert_google_drive_url
from session_manager import get_session, init_session, cleanup
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fashion_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize session
async def init():
    logger.info("Initializing session...")
    await init_session()
    logger.info("Session initialized successfully")

class FashionContentAgent:
    """Main agent class for fashion content generation."""
    
    def __init__(self):
        """Initialize the agent with required components."""
        logger.info("Initializing FashionContentAgent...")
        session = get_session()
        self.vision_agent = session["vision_agent"]
        self.content_agent = session["content_agent"]
        self.storage = session["storage"]
        logger.info("FashionContentAgent initialized successfully")
        
    async def process_image(
        self,
        image_url: str,
        sheet_name: str,
        check_duplicate_only: bool = False,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single image URL.
        
        Args:
            image_url: The URL of the image to process
            sheet_name: The name of the sheet to save to
            check_duplicate_only: If True, only check for duplicates
            user_email: Optional email to share the sheet with
            
        Returns:
            Dict containing the results or error message
        """
        try:
            logger.info(f"Processing image URL: {image_url}")
            
            # Validate image URL
            is_valid, error_message = is_valid_image_url(image_url)
            if not is_valid:
                return {
                    "error": error_message,
                    "content": {"image_url": image_url}
                }
            
            # Check for duplicates
            existing_urls = await self.storage._get_existing_urls(sheet_name)
            normalized_url = convert_google_drive_url(image_url)
            
            if normalized_url in existing_urls:
                error_msg = f"Image URL already exists in sheet '{sheet_name}': {image_url}"
                logger.warning(error_msg)
                return {"error": error_msg}
            
            if check_duplicate_only:
                return {"status": "not_duplicate"}
            
            # Perform vision analysis
            logger.info("Performing vision analysis")
            vision_analysis = await self.vision_agent.analyze_image(image_url)
            
            # Generate content
            logger.info("Generating content")
            content = await self.content_agent.generate_content(image_url)
            
            # Add image URL and user email to content
            content['image_url'] = image_url
            if user_email:
                content['user_email'] = user_email
            
            # Save to Google Sheets
            logger.info(f"Saving content to sheet: {sheet_name}")
            sheet_url = await self.storage.save(content, vision_analysis, sheet_name)
            
            return {
                "content": content,
                "vision_analysis": vision_analysis,
                "sheet_url": sheet_url
            }
            
        except Exception as e:
            error_msg = f"Error processing image {image_url}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    async def process_images(self, image_urls: List[str], sheet_name: str = None, user_email: str = None) -> List[Dict[str, Any]]:
        """Process multiple image URLs concurrently."""
        try:
            results = []
            for url in image_urls:
                # Validate image URL
                is_valid, error_message = is_valid_image_url(url)
                if not is_valid:
                    results.append({
                        "error": error_message,
                        "content": {"image_url": url}
                    })
                    continue

                try:
                    result = await self.process_image(url, sheet_name)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "error": str(e),
                        "content": {"image_url": url}
                    })

            return results

        except Exception as e:
            logger.error(f"Error processing images: {str(e)}")
            raise Exception(f"Error processing images: {str(e)}")
            
    async def close(self) -> None:
        """Close all resources."""
        logger.info("Closing FashionContentAgent resources...")
        cleanup()
        logger.info("Resources closed successfully")

def extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from text."""
    try:
        # Find the first { and last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            logger.error("No JSON found in text")
            raise ValueError("No JSON found in text")
        return json.loads(text[start:end])
    except Exception as e:
        logger.error(f"Error extracting JSON: {str(e)}")
        raise ValueError(f"Error extracting JSON: {str(e)}")

# Initialize the session
asyncio.run(init())
