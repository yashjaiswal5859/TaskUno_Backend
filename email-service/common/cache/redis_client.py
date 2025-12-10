"""
Redis connection management for email service.
"""
from typing import Optional
import os

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Singleton Redis client instance
_redis_client: Optional[any] = None


def get_redis_client():
    """Get singleton Redis client instance."""
    global _redis_client
    if _redis_client is None:
        initialize_redis()
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis is available."""
    return REDIS_AVAILABLE and _redis_client is not None


def initialize_redis():
    """Initialize Redis client."""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        _redis_client = None
        return False
    
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=None  # No timeout for blocking operations like BLPOP
        )
        _redis_client.ping()
        print(f"✅ Redis connected: {redis_host}:{redis_port}")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        _redis_client = None
        return False

