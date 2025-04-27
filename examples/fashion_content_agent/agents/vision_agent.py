"""
Vision analysis agent using GPT-4 Vision.
"""
import json
from typing import Dict, Any
from config import Config
from utils.image_utils import get_image_from_url

class VisionAgent:
    def __init__(self, api_client, rate_limiter, cache_manager):
        self.api_client = api_client
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager

    async def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """Analyze a fashion image using GPT-4 Vision."""
        try:
            # Validate image URL
            from utils.validation import validate_image_url
            validate_image_url(image_url)
            
            # Convert image to base64
            base64_image = get_image_from_url(image_url)
            
            # Prepare the prompt
            prompt = f"""
            Analyze this fashion image and provide a detailed description in JSON format with the following structure:
            {{
                "style": "string describing the overall style",
                "colors": ["array of main colors"],
                "materials": ["array of materials"],
                "occasion": "suitable occasion",
                "season": "appropriate season",
                "key_features": ["array of notable features"],
                "brand_style": "description of brand aesthetic if visible"
            }}
            """
            
            # Make API call
            response = await self.api_client.post(
                "/v1/chat/completions",
                json={
                    "model": Config.VISION_MODEL,
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
            raise ValueError(f"Error analyzing image: {str(e)}")
    
    async def close(self):
        """Close the client."""
        await self.api_client.close() 