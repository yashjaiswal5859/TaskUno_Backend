"""
Rate limiting middleware for FastAPI services.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI

# Global limiter instance
_limiter = None

def get_limiter():
    """Get or create limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = Limiter(key_func=get_remote_address)
    return _limiter

def setup_rate_limiter(app: FastAPI):
    """Setup rate limiting for FastAPI app."""
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    return limiter

# Export limiter for use in controllers
limiter = get_limiter()



