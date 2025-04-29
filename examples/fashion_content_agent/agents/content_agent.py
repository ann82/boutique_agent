"""
Content generation agent using GPT-4.
"""
import json
from typing import Dict, Any
from config import Config
from utils.image_utils import get_image_from_url

class ContentAgent:
    def __init__(self, api_client, rate_limiter, cache_manager):
        self.api_client = api_client
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager
        
    async def generate_content(self, image_url: str) -> Dict[str, Any]:
        """Generate marketing content based on the image URL."""
        try:
            # Convert image to base64
            base64_image = get_image_from_url(image_url)
            
            # Prepare the prompt
            prompt = f"""
            Using the extracted details, generate marketing content to promote the item online and in the boutique.

            Return this JSON:

            {{
              "title": "catchy, boutique-style title for the product",
              "description": "elegant 3–5 sentence product description highlighting style, material, key features, and brand feel",
              "caption": "engaging social media caption (emojis welcome but optional)",
              "hashtags": ["array of relevant and trendy fashion hashtags"],
              "alt_text": "accessible image description focused on clothing and accessories",
              "platform": "suggested best-fit platform (e.g., Instagram, Facebook, Pinterest)",
              "key_features": ["list of 3-5 key product features, materials, or unique selling points"]
            }}
            """
            
            # Make API call
            response = await self.api_client.post(
                "/v1/chat/completions",
                json={
                    "model": Config.CONTENT_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    "max_tokens": 1000
                }
            )
            
            # Extract and parse JSON from response
            content = response["choices"][0]["message"]["content"]
            try:
                # Try to find JSON in the response
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    result = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON from response: {str(e)}")
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error generating content: {str(e)}")
    
    async def close(self):
        """Close the client."""
        await self.api_client.close() 