"""
Test suite for the caching functionality.
"""
import os
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from utils.cache import CacheManager
import time

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create a cache manager instance with temporary directory."""
    return CacheManager(cache_dir=temp_cache_dir, max_size_mb=1, expiration_hours=1)

@pytest.fixture
def sample_fashion_data():
    """Sample fashion data for testing."""
    return {
        "clothing_items": [
            {"type": "saree", "color": "red"},
            {"type": "blouse", "color": "white"}
        ],
        "colors": ["red", "white"],
        "materials": ["silk"],
        "style": "traditional"
    }

@pytest.fixture
def cache_dir(tmp_path):
    return str(tmp_path / "test_cache")

@pytest.fixture
def cache(cache_dir):
    return CacheManager(cache_dir=cache_dir, max_size_mb=1, expiration_hours=1)

def test_semantic_key_generation(cache_manager, sample_fashion_data):
    """Test that semantic keys are generated consistently for similar items."""
    key1 = cache_manager._get_semantic_key(sample_fashion_data)
    
    # Same data should generate same key
    key2 = cache_manager._get_semantic_key(sample_fashion_data)
    assert key1 == key2
    
    # Different order of items should generate same key
    shuffled_data = sample_fashion_data.copy()
    shuffled_data["clothing_items"].reverse()
    key3 = cache_manager._get_semantic_key(shuffled_data)
    assert key1 == key3

def test_cache_set_get(cache_manager, sample_fashion_data):
    """Test basic cache set and get operations."""
    # Set data in cache
    cache_manager.set(sample_fashion_data, {"result": "test"})
    
    # Get data from cache
    result = cache_manager.get(sample_fashion_data)
    assert result == {"result": "test"}
    
    # Check stats
    stats = cache_manager.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 0

def test_cache_expiration(cache_manager, sample_fashion_data):
    """Test cache expiration functionality."""
    # Set data with short expiration
    cache_manager.expiration_hours = 0.0001  # ~0.36 seconds
    cache_manager.set(sample_fashion_data, {"result": "test"})
    
    # Wait for expiration
    time.sleep(1)
    
    # Data should be expired
    result = cache_manager.get(sample_fashion_data)
    assert result is None
    
    # Check stats
    stats = cache_manager.get_stats()
    assert stats["misses"] == 1

def test_cache_size_limit(cache_manager, sample_fashion_data):
    """Test cache size limit enforcement."""
    # Set small size limit (1KB)
    cache_manager.max_size_mb = 0.001  # 1KB
    
    # Add multiple entries with smaller data
    for i in range(5):
        data = sample_fashion_data.copy()
        data["id"] = i
        cache_manager.set(data, {"result": "test" * 10})  # Smaller result
    
    # Check that cache size is within limit
    stats = cache_manager.get_stats()
    assert stats["size_bytes"] <= cache_manager.max_size_mb * 1024 * 1024

def test_cache_error_handling(cache_manager, temp_cache_dir):
    """Test cache error handling."""
    # Test with None data
    with pytest.raises(ValueError, match="Cannot cache None data"):
        cache_manager.set(None, {"result": "test"})
    
    # Test with invalid JSON string
    with pytest.raises(ValueError, match="Invalid JSON string provided"):
        cache_manager.set("{invalid json}", {"result": "test"})
    
    # Test with invalid data type
    with pytest.raises(ValueError, match="Data must be a dictionary or valid JSON string"):
        cache_manager.set(123, {"result": "test"})
    
    # Test with None result
    with pytest.raises(ValueError, match="Cannot cache None result"):
        cache_manager.set({"test": "data"}, None)
    
    # Test with invalid cache directory (use a path that requires root permissions)
    invalid_path = "/root/cache"
    with pytest.raises(Exception, match="Failed to cache data"):
        CacheManager(cache_dir=invalid_path)

def test_cache_concurrent_access(cache_manager, sample_fashion_data):
    """Test cache behavior with concurrent access."""
    import threading
    
    results = []
    
    def worker():
        result = cache_manager.get(sample_fashion_data)
        results.append(result)
    
    # Set initial data
    cache_manager.set(sample_fashion_data, {"result": "test"})
    
    # Create multiple threads
    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    # Start threads
    for thread in threads:
        thread.start()
    
    # Wait for threads to complete
    for thread in threads:
        thread.join()
    
    # All threads should get the same result
    assert all(r == {"result": "test"} for r in results)

def test_cache_performance(cache_manager, sample_fashion_data):
    """Test cache performance with multiple operations."""
    import time
    
    # Time multiple set operations
    start_time = time.time()
    for i in range(100):
        data = sample_fashion_data.copy()
        data["id"] = i
        cache_manager.set(data, {"result": "test"})
    set_time = time.time() - start_time
    
    # Time multiple get operations
    start_time = time.time()
    for i in range(100):
        data = sample_fashion_data.copy()
        data["id"] = i
        cache_manager.get(data)
    get_time = time.time() - start_time
    
    # Assert reasonable performance
    assert set_time < 1.0  # Should take less than 1 second for 100 sets
    assert get_time < 0.5  # Should take less than 0.5 seconds for 100 gets

def test_sheet_id_caching(cache):
    # Test caching sheet IDs
    sheet_name = "Test Sheet"
    sheet_id = "sheet123"
    
    # Cache the sheet ID
    cache.set(f"sheet:{sheet_name}", sheet_id)
    
    # Retrieve the sheet ID
    cached_id = cache.get(f"sheet:{sheet_name}")
    assert cached_id == sheet_id

def test_concurrent_sheet_id_access(cache):
    import threading
    
    sheet_name = "Test Sheet"
    sheet_id = "sheet123"
    results = []
    
    def worker():
        try:
            # Try to get or set the sheet ID
            cached_id = cache.get(f"sheet:{sheet_name}")
            if cached_id is None:
                cache.set(f"sheet:{sheet_name}", sheet_id)
                cached_id = sheet_id
            results.append(cached_id)
        except Exception as e:
            results.append(str(e))
    
    # Create multiple threads
    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    # Start threads
    for thread in threads:
        thread.start()
    
    # Wait for threads to complete
    for thread in threads:
        thread.join()
    
    # All threads should get the same sheet ID
    assert all(r == sheet_id for r in results)

def test_sheet_id_cache_size_limit(cache):
    # Test sheet ID cache size limit
    # Create large sheet IDs to test size limit
    large_sheet_id = "x" * 1000000  # 1MB
    
    # Try to cache multiple large sheet IDs
    for i in range(5):
        sheet_name = f"Test Sheet {i}"
        cache.set(f"sheet:{sheet_name}", large_sheet_id)
    
    # Verify some entries were evicted due to size limit
    cache_files = os.listdir(cache.cache_dir)
    assert len(cache_files) < 5  # Some entries should have been evicted

def test_sheet_id_cache_error_handling(cache):
    # Test error handling in sheet ID caching
    sheet_name = "Test Sheet"
    sheet_id = "sheet123"
    
    # Create invalid cache file
    invalid_cache_file = os.path.join(cache.cache_dir, f"sheet:{sheet_name}.json")
    with open(invalid_cache_file, 'w') as f:
        f.write("invalid json")
    
    # Should handle invalid cache file gracefully
    assert cache.get(f"sheet:{sheet_name}") is None
    
    # Should be able to set new value
    cache.set(f"sheet:{sheet_name}", sheet_id)
    assert cache.get(f"sheet:{sheet_name}") == sheet_id 