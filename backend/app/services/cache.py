"""
Redis Cache Service
Centralized caching layer for Komission
"""
import json
from typing import Optional, Any, Callable
from functools import wraps
import redis.asyncio as redis

from app.config import settings


class RedisCache:
    """
    Async Redis cache service.
    Implements cache-aside pattern with TTL.
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """Initialize Redis connection"""
        if not self._client:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()
            print(f"✅ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    # ---- Basic Operations ----

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600):
        """Set value with TTL (default 1 hour)"""
        await self.client.setex(key, ttl, value)

    async def delete(self, key: str):
        """Delete a key"""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key) > 0

    async def incr(self, key: str) -> int:
        """Increment a counter"""
        return await self.client.incr(key)

    # ---- JSON Operations ----

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value"""
        data = await self.get(key)
        return json.loads(data) if data else None

    async def set_json(self, key: str, value: Any, ttl: int = 3600):
        """Set JSON value"""
        await self.set(key, json.dumps(value), ttl)

    # ---- Komission Specific Methods ----

    async def cache_gemini_analysis(self, video_url: str, analysis: dict, ttl: int = 86400):
        """
        Cache Gemini analysis result (24 hours default)
        Prevents re-analyzing the same video
        """
        key = f"gemini:{video_url}"
        await self.set_json(key, analysis, ttl)

    async def get_gemini_analysis(self, video_url: str) -> Optional[dict]:
        """Get cached Gemini analysis"""
        return await self.get_json(f"gemini:{video_url}")

    # ---- VDG v4 Cache (Comments-aware) ----
    
    def _make_vdg_cache_key(self, video_url: str, comments_hash: str) -> str:
        """Generate VDG v4 cache key with comments hash"""
        import hashlib
        url_hash = hashlib.md5(video_url.encode()).hexdigest()[:12]
        return f"vdg_v4:{url_hash}:{comments_hash[:8]}"

    async def cache_vdg_v4(
        self, 
        video_url: str, 
        comments_hash: str,
        vdg_data: dict, 
        ttl: int = 86400
    ):
        """
        Cache VDG v4 analysis result (24 hours default)
        Key includes comments hash to distinguish same video with different comments
        """
        key = self._make_vdg_cache_key(video_url, comments_hash)
        await self.set_json(key, vdg_data, ttl)

    async def get_vdg_v4(self, video_url: str, comments_hash: str) -> Optional[dict]:
        """Get cached VDG v4 analysis"""
        key = self._make_vdg_cache_key(video_url, comments_hash)
        return await self.get_json(key)


    async def cache_recipe_view(self, node_id: str, html: str, ttl: int = 3600):
        """
        Cache rendered recipe view (1 hour default)
        For popular nodes with frequent access
        """
        key = f"recipe:{node_id}"
        await self.set(key, html, ttl)

    async def get_recipe_view(self, node_id: str) -> Optional[str]:
        """Get cached recipe view"""
        return await self.get(f"recipe:{node_id}")

    async def invalidate_recipe(self, node_id: str):
        """Invalidate recipe cache when node is updated"""
        await self.delete(f"recipe:{node_id}")

    async def check_user_quota(self, user_id: str, daily_limit: int = 50) -> dict:
        """
        Check and increment user's daily quota.
        Returns remaining quota info.
        """
        key = f"quota:{user_id}:daily"
        current = await self.get(key)
        current_count = int(current) if current else 0

        if current_count >= daily_limit:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": daily_limit,
                "message": "Daily quota exceeded"
            }

        # Increment and set expiry (24 hours from first use)
        new_count = await self.incr(key)
        if new_count == 1:
            await self.client.expire(key, 86400)  # 24 hours

        return {
            "allowed": True,
            "remaining": daily_limit - new_count,
            "limit": daily_limit
        }


# Singleton instance
cache = RedisCache()


# ---- Cache Decorator ----

def cached(key_prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results.
    
    Usage:
        @cached("user", ttl=1800)
        async def get_user(user_id: str): ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            cache_key = f"{key_prefix}:{':'.join(str(a) for a in args)}"

            # Try cache first
            cached_result = await cache.get_json(cache_key)
            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set_json(cache_key, result, ttl)
            return result

        return wrapper
    return decorator
