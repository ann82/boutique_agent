"""
Streamlit application for the Fashion Content Agent.
"""
import streamlit as st
import asyncio
from typing import Dict, Any, Optional
from main import FashionContentAgent, extract_json
from utils.image_utils import is_valid_image_url
from utils.validation import validate_content_format
from config import Config
from session_manager import init_session, cleanup

# Initialize session
init_session()

# Set page config
st.set_page_config(
    page_title="Fashion Content Agent",
    page_icon="👗",
    layout="wide"
)

# Initialize agent
agent = FashionContentAgent()

# App title and description
st.title("Fashion Content Agent")
st.markdown("""
    Generate marketing content for fashion images using AI.
    Upload an image or provide a URL to get started.
""")

# Sidebar for sheet selection
st.sidebar.title("Sheet Management")
sheet_name = st.sidebar.text_input("Sheet Name", "Fashion Content")

# Main content area
st.header("Image Input")
image_url = st.text_input("Image URL", placeholder="Enter image URL or Google Drive link")

if st.button("Generate Content"):
    if not image_url:
        st.error("Please enter an image URL")
    else:
        try:
            # Validate image URL
            if not is_valid_image_url(image_url):
                st.error("Invalid image URL")
            else:
                # Process image
                with st.spinner("Generating content..."):
                    result = asyncio.run(agent.process_image(image_url))
                    
                    # Display results
                    st.success("Content generated successfully!")
                    
                    # Show content
                    st.subheader("Generated Content")
                    st.json(result["content"])
                    
                    # Show vision analysis
                    st.subheader("Vision Analysis")
                    st.json(result["vision_analysis"])
                    
                    # Show sheet URL
                    st.subheader("Google Sheet")
                    st.markdown(f"[Open Sheet]({result['sheet_url']})")
                    
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