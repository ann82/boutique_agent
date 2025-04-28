"""
Streamlit application for the Fashion Content Agent.
"""
import streamlit as st
import asyncio
from typing import Dict, Any, Optional, List
from main import FashionContentAgent, extract_json, init
from utils.image_utils import is_valid_image_url, convert_google_drive_url
from utils.validation import validate_content_format
from config import Config
from session_manager import cleanup

# Set page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Fashion Content Agent",
    page_icon="👗",
    layout="wide"
)

# Initialize session
asyncio.run(init())

# Initialize agent
agent = FashionContentAgent()

# App title and description
st.title("Fashion Content Agent")
st.markdown("""
    Generate marketing content for fashion images using AI.
    Upload up to 3 images at a time to get started.
""")

# Sidebar for sheet selection
st.sidebar.title("Sheet Management")
sheet_name = st.sidebar.text_input("Sheet Name", "Fashion Content")

# Main content area
st.header("Image Input")
st.markdown("Enter up to 3 image URLs (one per line):")

# Create a text area for multiple image URLs
image_urls_input = st.text_area(
    "Image URLs",
    placeholder="Enter image URLs (one per line)\nExample:\nhttps://example.com/image1.jpg\nhttps://example.com/image2.jpg",
    height=150
)

if st.button("Generate Content"):
    if not image_urls_input:
        st.error("Please enter at least one image URL")
    else:
        # Process each URL
        urls = [url.strip() for url in image_urls_input.split('\n') if url.strip()]
        valid_urls = []
        invalid_urls = []
        
        for url in urls:
            if is_valid_image_url(url):
                valid_urls.append(url)
            else:
                invalid_urls.append(url)
        
        if invalid_urls:
            st.error(f"Invalid URLs found: {', '.join(invalid_urls)}")
        
        if valid_urls:
            with st.spinner("Generating content..."):
                try:
                    # Process each valid URL
                    for url in valid_urls:
                        # Generate content for this URL
                        result = asyncio.run(agent.process_image(
                            image_url=url,
                            sheet_name=sheet_name
                        ))
                        
                        # Display results
                        st.subheader(f"Results for {url}")
                        st.json(result)
                        
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

# Cleanup on exit
cleanup()

# Add custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .output-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
Made with ❤️ by the Fashion Content Agent team
""") 