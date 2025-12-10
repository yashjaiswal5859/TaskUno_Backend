"""
Shared Redis connection management - Singleton pattern.
"""
from typing import Optional
from common.config.settings import settings

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
    """Get singleton Redis client instance. Initializes if not already initialized."""
    global _redis_client
    if _redis_client is None:
        initialize_redis()
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis singleton is available."""
    return _redis_client is not None


def initialize_redis():
    """Initialize Redis singleton at application startup."""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        _redis_client = None
        return False
    
    try:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            retry_on_timeout=False
        )
        _redis_client.ping()
        return True
    except Exception as e:
        _redis_client = None
        return False

