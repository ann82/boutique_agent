"""
Rate limiting utilities for the fashion content agent.
"""
import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class RateLimiter:
    """
    Simple rate limiter for API calls.
    """
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests (int): Maximum number of requests allowed in the time window
            time_window (int): Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = {}
        self.lock = asyncio.Lock()
        
    async def can_make_request(self, model: str) -> bool:
        """
        Check if a request can be made for the given model.
        
        Args:
            model (str): Name of the model
            
        Returns:
            bool: True if request can be made, False otherwise
        """
        async with self.lock:
            now = time.time()
            if model not in self.requests:
                self.requests[model] = []
            
            # Remove expired requests
            self.requests[model] = [t for t in self.requests[model] if now - t < self.time_window]
            
            return len(self.requests[model]) < self.max_requests
        
    async def record_request(self, model: str) -> None:
        """
        Record a request for the given model.
        
        Args:
            model (str): Name of the model
        """
        async with self.lock:
            if model not in self.requests:
                self.requests[model] = []
            self.requests[model].append(time.time())
        
    async def get_remaining_requests(self, model: str) -> int:
        """
        Get the number of remaining requests for the given model.
        
        Args:
            model (str): Name of the model
            
        Returns:
            int: Number of remaining requests
        """
        async with self.lock:
            now = time.time()
            if model not in self.requests:
                return self.max_requests
            
            # Remove expired requests
            self.requests[model] = [t for t in self.requests[model] if now - t < self.time_window]
            
            return self.max_requests - len(self.requests[model])
        
    async def get_reset_time(self, model: str) -> datetime:
        """
        Get the time when the rate limit will reset for the given model.
        
        Args:
            model (str): Name of the model
            
        Returns:
            datetime: Time when rate limit will reset
        """
        async with self.lock:
            if model not in self.requests or not self.requests[model]:
                return datetime.now()
            
            oldest_request = min(self.requests[model])
            return datetime.fromtimestamp(oldest_request + self.time_window) 