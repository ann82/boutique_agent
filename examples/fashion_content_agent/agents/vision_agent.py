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
            Analyze the provided fashion image and generate a detailed product understanding.

            Focus mainly on the clothing — style, materials, patterns, cuts — and not on the person.
            Accessories (like jewelry, belts, bags, shoes) should be noted under key_features if visible, as optional add-ons.

            Use rich, boutique-style language (sensory, elegant but concise) in field values, targeting a boutique in rural South India that offers both Indian and Western designs.

            If a detail is unclear, use "unknown" or leave the array empty.

            Infer suitable occasion and season from the outfit's style and materials.

            Return this JSON:

            {{
              "style": "overall clothing style (traditional Indian, Indo-western fusion, modern western, etc.)",
              "colors": ["main visible colors"],
              "materials": ["materials with adjectives if visible"],
              "occasion": "best suited occasion (e.g., casual, festive, formal)",
              "season": "appropriate season (e.g., summer, festive season, winter)",
              "key_features": ["notable features and visible accessories"],
              "brand_style": "brand aesthetic description (e.g., earthy, regal, minimalist)"
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