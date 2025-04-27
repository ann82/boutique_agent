"""
Main application module for the Fashion Content Agent.
"""
import os
import json
import streamlit as st
from typing import Dict, Any, Optional
from utils.image_utils import is_valid_image_url
from utils.validation import validate_content_format
from session_manager import get_session, init_session, cleanup
import asyncio

# Initialize session
init_session()

class FashionContentAgent:
    """Main agent class for fashion content generation."""
    
    def __init__(self):
        """Initialize the agent with required components."""
        session = get_session()
        self.vision_agent = session["vision_agent"]
        self.content_agent = session["content_agent"]
        self.storage = session["storage"]
        
    async def process_image(self, image_url: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Process an image URL and generate content."""
        try:
            # Validate image URL
            if not is_valid_image_url(image_url):
                raise ValueError("Invalid image URL")
            
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

# Streamlit UI
st.set_page_config(
    page_title="Fashion Content Agent",
    page_icon="👗",
    layout="wide"
)

st.title("Fashion Content Agent")
st.markdown("Generate marketing content for fashion images using AI")

# Initialize agent
agent = FashionContentAgent()

# Image URL input
image_url = st.text_input("Enter image URL", placeholder="https://example.com/image.jpg")

# Sheet selection
sheet_name = st.text_input("Enter sheet name (optional)", placeholder="My Fashion Content")

# Process button
if st.button("Generate Content"):
    if not image_url:
        st.error("Please enter an image URL")
    else:
        try:
            with st.spinner("Processing image..."):
                result = asyncio.run(agent.process_image(image_url, sheet_name))
                
                # Display results
                st.success("Content generated successfully!")
                
                # Display content
                st.subheader("Generated Content")
                st.json(result["content"])
                
                # Display vision analysis
                st.subheader("Vision Analysis")
                st.json(result["vision_analysis"])
                
                # Display sheet URL
                st.subheader("Google Sheet")
                st.markdown(f"[View Sheet]({result['sheet_url']})")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Cleanup on exit
cleanup()
