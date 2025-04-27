"""
Optimized API client with connection pooling.
"""
import aiohttp
from typing import Dict, Any, Optional
from config import Config

class APIClient:
    """Client for making API requests with connection pooling."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com",
        timeout: int = 30,
        max_retries: int = 3,
        pool_size: int = 10
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.pool_size = pool_size
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a session with connection pooling."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                connector=aiohttp.TCPConnector(limit=self.pool_size)
            )
        return self._session

    async def post(self, endpoint: str, json: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request with retries."""
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Check if the request contains an image
        if "messages" in json:
            for message in json["messages"]:
                if "content" in message:
                    for content in message["content"]:
                        if content.get("type") == "image_url" and "image_url" in content:
                            # Ensure the image URL is properly formatted
                            if not content["image_url"]["url"].startswith("data:image/jpeg;base64,"):
                                content["image_url"]["url"] = f"data:image/jpeg;base64,{content['image_url']['url']}"
        
        for attempt in range(self.max_retries):
            try:
                async with session.post(
                    endpoint,
                    json=json,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"API error: {response.status} - {error_text}")
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                continue
                
        raise Exception("Max retries exceeded")

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None 