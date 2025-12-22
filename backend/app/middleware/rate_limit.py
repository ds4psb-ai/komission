"""
Rate Limiting Middleware using slowapi
Protects API endpoints from abuse
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Create limiter instance with Redis backend (fallback to memory)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    # storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",  # Enable for Redis
)


def setup_rate_limiting(app):
    """
    Setup rate limiting for the FastAPI app.
    Call this in main.py after creating the app.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


# Decorator examples for routes:
# @limiter.limit("10/minute")  # 10 requests per minute per IP
# @limiter.limit("5/minute", key_func=lambda r: r.state.user_id)  # Per user
