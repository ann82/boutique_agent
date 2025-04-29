"""
Streamlit application for the Fashion Content Agent.
"""
import streamlit as st
import asyncio
import logging
from typing import Dict, Any, Optional, List
from main import FashionContentAgent, extract_json, init
from utils.image_utils import is_valid_image_url, convert_google_drive_url
from utils.validation import validate_content_format
from config import Config
from session_manager import cleanup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fashion_agent_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Set page config - MUST be first Streamlit command
logger.info("Setting up Streamlit page configuration")
st.set_page_config(
    page_title="Fashion Content Agent",
    page_icon="👗",
    layout="wide"
)

# Initialize session and agent only if not already in session state
if 'initialized' not in st.session_state:
    logger.info("Initializing application session")
    asyncio.run(init())
    logger.info("Initializing FashionContentAgent")
    st.session_state.agent = FashionContentAgent()
    st.session_state.initialized = True

agent = st.session_state.agent

# App title and description
logger.info("Setting up application UI")
st.title("Fashion Content Agent")
st.markdown("""
    Generate marketing content for fashion images using AI.
    Upload up to 3 images at a time to get started.
""")

# Sidebar for sheet selection
st.sidebar.title("Sheet Management")
sheet_name = st.sidebar.text_input("Sheet Name", "ImageToText Content")
user_email = st.sidebar.text_input("Your Email", 
                                 value=Config.GOOGLE_SHARE_EMAIL or "",
                                 placeholder="Enter your email to receive access to the sheet")

# Main content area
st.header("Image Input")
st.markdown("Enter up to 3 image URLs (one per line):")

# Create a text area for multiple image URLs
image_urls_input = st.text_area(
    "Image URLs",
    placeholder="Enter image URLs (one per line)\nExample:\nhttps://example.com/image1.jpg\nhttps://example.com/image2.jpg",
    height=150
)

if st.button("Process Images"):
    logger.info("Process Images button clicked")
    if not image_urls_input:
        logger.warning("No image URLs provided")
        st.error("Please enter at least one image URL")
    else:
        # Process each URL
        urls = [url.strip() for url in image_urls_input.split('\n') if url.strip()]
        logger.info(f"Processing {len(urls)} image URLs")
        
        if len(urls) > 3:
            st.error("Please enter no more than 3 image URLs")
        else:
            try:
                # First validate URLs
                valid_urls = []
                for url in urls:
                    is_valid, error_message = is_valid_image_url(url)
                    if not is_valid:
                        logger.warning(f"Invalid image URL: {url} - {error_message}")
                        st.warning(f"Invalid image URL: {error_message}")
                    else:
                        valid_urls.append(url)

                if not valid_urls:
                    st.error("No valid image URLs provided")
                else:
                    # Check for duplicates
                    with st.spinner("Checking for duplicates..."):
                        duplicate_results = []
                        urls_to_process = []
                        
                        for url in valid_urls:
                            try:
                                check_result = asyncio.run(agent.process_image(
                                    image_url=url,
                                    sheet_name=sheet_name,
                                    check_duplicate_only=True
                                ))
                                if "error" in check_result and "already exists" in check_result["error"]:
                                    duplicate_results.append({"url": url, "error": check_result["error"]})
                                else:
                                    urls_to_process.append(url)
                            except Exception as e:
                                logger.error(f"Error checking duplicate for URL {url}: {str(e)}")
                                st.warning(f"Error checking URL {url}: {str(e)}")
                        
                        # Show duplicate warnings first
                        for result in duplicate_results:
                            st.warning(result["error"])
                        
                        # Process remaining valid URLs
                        if urls_to_process:
                            with st.spinner("Processing images..."):
                                logger.info(f"Processing valid URLs in batch: {urls_to_process}")
                                results = asyncio.run(agent.process_images(
                                    image_urls=urls_to_process,
                                    sheet_name=sheet_name,
                                    user_email=user_email if user_email else None
                                ))
                                logger.info("Batch processing completed")
                                
                                # Count successful and failed results
                                successful_results = [r for r in results if "error" not in r]
                                failed_results = [r for r in results if "error" in r]
                                
                                # Display errors if any
                                for result in failed_results:
                                    st.error(result["error"])
                                
                                # Display single success message if there were successful results
                                if successful_results:
                                    # Get the sheet URL from the first successful result
                                    sheet_url = successful_results[0]['sheet_url']
                                    num_processed = len(successful_results)
                                    
                                    st.markdown(f"""
                                        <div class="success-message">
                                            ✅ Successfully processed {num_processed} image{'s' if num_processed > 1 else ''}!
                                            <br><br>
                                            <a href="{sheet_url}" target="_blank" class="sheet-link">View Results in Google Sheet</a>
                                        </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.info("No new images to process - all URLs were either invalid or already exist in the sheet.")
                            
            except Exception as e:
                logger.error(f"Error in processing: {str(e)}")
                st.error(f"An error occurred: {str(e)}")

# Cleanup on exit
logger.info("Cleaning up resources")
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
    .success-message {
        padding: 1rem;
        background-color: #e6f7e6;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .sheet-link {
        color: #1a73e8;
        text-decoration: none;
        font-weight: bold;
    }
    .sheet-link:hover {
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
Made with ❤️ by the Fashion Content Agent team
""") 