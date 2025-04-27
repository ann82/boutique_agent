"""
Caching utilities for the fashion content agent.
"""
import json
import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CacheManager:
    def __init__(self, cache_dir=".cache", max_size_mb=100, expiration_hours=24):
        """Initialize the cache manager."""
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.expiration_hours = expiration_hours
        self.stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'size_bytes': 0
        }
        self._setup_logging()
        
        # Verify cache directory can be created
        try:
            os.makedirs(cache_dir, exist_ok=True)
            # Test write permissions by creating a test file
            test_file = os.path.join(cache_dir, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except (OSError, IOError) as e:
            raise Exception(f"Failed to cache data: {str(e)}")
    
    def _setup_logging(self):
        """Setup logging for cache operations."""
        self.logger = logging.getLogger('cache_manager')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
    
    def _get_semantic_key(self, data: dict | str) -> str:
        """Generate a semantic cache key based on clothing characteristics."""
        if data is None:
            raise ValueError("Cannot generate key for None data")
        
        # Validate data type
        if not isinstance(data, (dict, str)):
            raise ValueError("Data must be a dictionary or valid JSON string")
        
        # For string data, try to parse as JSON if it looks like JSON
        if isinstance(data, str):
            if data.strip().startswith('{'):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON string provided")
            else:
                return hashlib.md5(data.encode()).hexdigest()
        
        # For dict data, use semantic characteristics
        key_parts = []
        
        # Clothing items and their types
        if 'clothing_items' in data:
            items = sorted([item.get('type', '') for item in data['clothing_items']])
            key_parts.extend(items)
        
        # Colors
        if 'colors' in data:
            colors = sorted(data['colors'])
            key_parts.extend(colors)
        
        # Materials
        if 'materials' in data:
            materials = sorted(data['materials'])
            key_parts.extend(materials)
        
        # Style
        if 'style' in data:
            key_parts.append(data['style'])
        
        # If no semantic characteristics found, use the whole dict
        if not key_parts:
            key_parts = [str(sorted(data.items()))]
        
        # Create a unique but semantic key
        semantic_string = '|'.join(key_parts)
        return hashlib.md5(semantic_string.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key."""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, data: str | dict) -> Optional[dict]:
        """Get cached data if it exists and is not expired."""
        key = self._get_semantic_key(data)
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            self.stats['misses'] += 1
            self.logger.info(f"Cache miss for key: {key}")
            return None
            
        try:
            with open(cache_path, 'r') as f:
                content = f.read().strip()
                if not content:  # Check if file is empty
                    self.logger.warning(f"Empty cache file found: {cache_path}")
                    return None
                
                try:
                    cache_data = json.loads(content)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON in cache file {cache_path}: {str(e)}")
                    # Remove the invalid cache file
                    os.remove(cache_path)
                    return None
                
                # Check if cache is expired
                if datetime.fromisoformat(cache_data['timestamp']) + timedelta(hours=self.expiration_hours) > datetime.now():
                    self.stats['hits'] += 1
                    self.logger.info(f"Cache hit for key: {key}")
                    return cache_data['data']
                else:
                    # Remove expired cache file
                    os.remove(cache_path)
                    self.stats['misses'] += 1
                    self.logger.info(f"Removed expired cache entry: {cache_path}")
                    return None
                    
        except Exception as e:
            self.logger.warning(f"Error reading cache file {cache_path}: {str(e)}")
            # Remove the problematic cache file
            try:
                os.remove(cache_path)
            except:
                pass
            return None
        
        self.stats['misses'] += 1
        self.logger.info(f"Cache miss for key: {key}")
        return None
    
    def set(self, data: str | dict, result: dict) -> None:
        """Cache the result for the given data."""
        if data is None:
            raise ValueError("Cannot cache None data")
        if result is None:
            raise ValueError("Cannot cache None result")
        
        try:
            key = self._get_semantic_key(data)
            cache_path = self._get_cache_path(key)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': result,
                'semantic_key': key
            }
            
            # Check cache size before adding new entry
            self._enforce_size_limit()
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            
            self.stats['size_bytes'] += os.path.getsize(cache_path)
            self.logger.info(f"Cached new entry with key: {key}")
        except (OSError, IOError) as e:
            raise Exception(f"Failed to cache data: {str(e)}")
        except ValueError as e:
            raise  # Re-raise ValueError without wrapping
        except Exception as e:
            raise Exception(f"Cache operation failed: {str(e)}")
    
    def _enforce_size_limit(self) -> None:
        """Enforce maximum cache size by removing oldest entries."""
        while self.stats['size_bytes'] > self.max_size_mb * 1024 * 1024:
            oldest_file = min(
                (f for f in os.listdir(self.cache_dir) if f.endswith('.json')),
                key=lambda f: os.path.getmtime(os.path.join(self.cache_dir, f))
            )
            oldest_path = os.path.join(self.cache_dir, oldest_file)
            self.stats['size_bytes'] -= os.path.getsize(oldest_path)
            os.remove(oldest_path)
            self.logger.info(f"Removed oldest cache entry to maintain size limit: {oldest_file}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self.stats

# Create a global cache manager instance
cache_manager = CacheManager() 