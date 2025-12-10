"""
Cache service for Redis operations.
"""
import json
from typing import Optional, Any
from common.cache.redis_client import get_redis_client, is_redis_available

ORG_CACHE_TTL = 1800  # 30 minutes


class CacheService:
    """Service for cache operations."""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        if not is_redis_available():
            return None
        try:
            client = get_redis_client()
            value = client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            print(f"Redis GET error for key '{key}': {e}")
            return None
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = ORG_CACHE_TTL) -> bool:
        """Set value in cache with TTL."""
        if not is_redis_available():
            return False
        try:
            client = get_redis_client()
            serialized = json.dumps(value, default=str)
            client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Redis SET error for key '{key}': {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache."""
        if not is_redis_available():
            return False
        try:
            client = get_redis_client()
            client.delete(key)
            return True
        except Exception as e:
            print(f"Redis DELETE error for key '{key}': {e}")
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> bool:
        """Delete all keys matching pattern."""
        if not is_redis_available():
            return False
        try:
            client = get_redis_client()
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis DELETE_PATTERN error for '{pattern}': {e}")
            return False



