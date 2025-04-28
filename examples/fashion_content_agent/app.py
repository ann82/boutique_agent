"""
Streamlit application for the Fashion Content Agent.
"""
import streamlit as st
import asyncio
from typing import Dict, Any, Optional, List
from main import FashionContentAgent, extract_json, init
from utils.image_utils import is_valid_image_url
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
        try:
            # Split input into lines and clean up
            image_urls = [url.strip() for url in image_urls_input.split('\n') if url.strip()]
            
            # Validate number of images
            if len(image_urls) > 3:
                st.error("Please enter a maximum of 3 image URLs")
            else:
                # Check for duplicate URLs
                unique_urls = list(set(image_urls))
                if len(unique_urls) < len(image_urls):
                    st.error("Duplicate image URLs are not allowed. Please remove duplicates.")
                else:
                    # Validate each URL
                    invalid_urls = [url for url in image_urls if not is_valid_image_url(url)]
                    if invalid_urls:
                        st.error(f"Invalid image URLs: {', '.join(invalid_urls)}")
                    else:
                        # Process images
                        with st.spinner("Generating content..."):
                            results = asyncio.run(agent.process_images(image_urls, sheet_name))
                            
                            # Display results
                            st.success(f"Successfully processed {len(results)} images!")
                            
                            # Show results for each image
                            for i, result in enumerate(results, 1):
                                st.subheader(f"Image {i}")
                                
                                # Check if this is a duplicate URL
                                if "message" in result and result["message"] == "Image URL already exists in the sheet":
                                    st.warning(f"Image URL already exists in the sheet: {result['content']['image_url']}")
                                    st.markdown(f"[Open Sheet]({result['sheet_url']})")
                                    st.markdown("---")
                                    continue
                                
                                # Show content
                                st.markdown("**Generated Content**")
                                st.json(result["content"])
                                
                                # Show vision analysis
                                st.markdown("**Vision Analysis**")
                                st.json(result["vision_analysis"])
                                
                                st.markdown("---")
                            
                            # Show sheet URL
                            st.subheader("Google Sheet")
                            st.markdown(f"[Open Sheet]({results[0]['sheet_url']})")
                        
        except Exception as e:
            st.error(f"Error: {str(e)}")

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