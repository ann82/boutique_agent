"""
Configuration settings for the fashion content agent.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    
    # Model Settings
    VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")
    CONTENT_MODEL = os.getenv("CONTENT_MODEL", "gpt-4o")
    
    # Default Content Settings
    DEFAULT_TONE = os.getenv("DEFAULT_TONE", "Trendy")
    DEFAULT_PLATFORM = os.getenv("DEFAULT_PLATFORM", "Instagram")
    
    # Rate Limiting
    RATE_LIMITS = {
        "max_requests": int(os.getenv("MAX_REQUESTS", "60")),
        "time_window": int(os.getenv("TIME_WINDOW", "60"))  # 60 seconds
    }
    
    # API Request Settings
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))
    CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
    
    # Google Sheets Settings
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
    GOOGLE_SHARE_EMAIL = os.getenv("GOOGLE_SHARE_EMAIL")
    GOOGLE_SHEETS_BATCH_SIZE = int(os.getenv("GOOGLE_SHEETS_BATCH_SIZE", "100"))
    
    # Cache Settings
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))

# Output format
OUTPUT_FORMAT = {
    "title": str,
    "description": str,
    "caption": str,
    "hashtags": list,
    "alt_text": str
} 