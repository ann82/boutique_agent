"""
Session management for the fashion content agent.
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from utils.api_client import APIClient
from utils.rate_limiter import RateLimiter
from utils.cache import CacheManager
from utils.document_storage import GoogleSheetsStorage
from agents.vision_agent import VisionAgent
from agents.content_agent import ContentAgent
from config import Config

class SessionManager:
    """Manages the application session."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.api_client = None
        self.rate_limiter = None
        self.cache = None
        self.storage = None
        self.vision_agent = None
        self.content_agent = None
        self.session = None
        
    async def init_session(self):
        """Initialize the session."""
        try:
            # Initialize API client with connection pooling
            self.api_client = APIClient(
                base_url=Config.OPENAI_API_BASE,
                api_key=Config.OPENAI_API_KEY,
                timeout=Config.API_TIMEOUT,
                max_retries=Config.API_MAX_RETRIES,
                pool_size=Config.CONNECTION_POOL_SIZE
            )
            
            # Initialize rate limiter
            self.rate_limiter = RateLimiter(
                max_requests=Config.RATE_LIMITS["max_requests"],
                time_window=Config.RATE_LIMITS["time_window"]
            )
            
            # Initialize cache
            self.cache = CacheManager(
                cache_dir=Config.CACHE_DIR,
                max_size_mb=Config.CACHE_MAX_SIZE,
                expiration_hours=Config.CACHE_TTL // 3600  # Convert seconds to hours
            )
            
            # Initialize storage with batch processing
            self.storage = GoogleSheetsStorage(
                credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
                share_email=Config.GOOGLE_SHARE_EMAIL,
                batch_size=Config.GOOGLE_SHEETS_BATCH_SIZE
            )
            
            # Initialize agents
            self.vision_agent = VisionAgent(
                api_client=self.api_client,
                rate_limiter=self.rate_limiter,
                cache_manager=self.cache
            )
            
            self.content_agent = ContentAgent(
                api_client=self.api_client,
                rate_limiter=self.rate_limiter,
                cache_manager=self.cache
            )
            
            # Create session
            self.session = {
                "api_client": self.api_client,
                "rate_limiter": self.rate_limiter,
                "cache": self.cache,
                "storage": self.storage,
                "vision_agent": self.vision_agent,
                "content_agent": self.content_agent,
                "created_at": datetime.now()
            }
            
            return self.session
            
        except Exception as e:
            raise Exception(f"Error initializing session: {str(e)}")
            
    def get_session(self):
        """Get the current session."""
        if not self.session:
            raise Exception("Session not initialized")
        return self.session
        
    def close_session(self):
        """Close the session."""
        try:
            if self.api_client:
                asyncio.run(self.api_client.close())
            if self.storage:
                asyncio.run(self.storage.close())
            if self.vision_agent:
                asyncio.run(self.vision_agent.close())
            if self.content_agent:
                asyncio.run(self.content_agent.close())
                
            self.session = None
            
        except Exception as e:
            raise Exception(f"Error closing session: {str(e)}")

# Global session manager
session_manager = SessionManager()

async def init_session():
    """Initialize the session."""
    return await session_manager.init_session()

def get_session():
    """Get the current session."""
    return session_manager.get_session()

def cleanup():
    """Cleanup the session."""
    session_manager.close_session() 