"""
Quota Manager - Redis-based API quota tracking
Based on 13_PERIODIC_CRAWLING_SPEC.md (L519-542)

Manages daily API quotas for each platform to prevent exceeding limits.
"""
import os
import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)


class QuotaManager:
    """
    Redis-based quota manager for platform API rate limiting.
    
    Usage:
        quota_mgr = QuotaManager(redis_client)
        if quota_mgr.check_and_consume("youtube", cost=100):
            # proceed with API call
        else:
            # quota exceeded, skip
    """
    
    # Default daily limits per platform (from spec L36-40)
    DEFAULT_LIMITS = {
        "youtube": 10000,   # YouTube Data API: 10,000 units/day
        "tiktok": 1000,     # TikTok Research API: 1,000 req/day
        "instagram": 200,   # Instagram Graph API: ~200 effective req/day (30/hour)
    }
    
    KEY_PREFIX = "komission:quota:"
    TTL_SECONDS = 86400  # 24 hours
    
    def __init__(self, redis_client=None, limits: Optional[dict] = None):
        """
        Initialize quota manager.
        
        Args:
            redis_client: Redis client instance (optional, uses in-memory fallback)
            limits: Override default limits
        """
        self.redis = redis_client
        self.limits = limits or self.DEFAULT_LIMITS.copy()
        
        # In-memory fallback for when Redis is unavailable
        self._local_store: dict[str, int] = {}
        self._local_date: Optional[date] = None
    
    def _get_key(self, platform: str) -> str:
        """Generate Redis key for today's quota."""
        today = datetime.utcnow().strftime("%Y%m%d")
        return f"{self.KEY_PREFIX}{platform}:{today}"
    
    def _reset_local_if_new_day(self):
        """Reset local store if day has changed."""
        today = date.today()
        if self._local_date != today:
            self._local_store = {}
            self._local_date = today
    
    async def check_and_consume(self, platform: str, cost: int = 1) -> bool:
        """
        Check quota and consume if available.
        
        Args:
            platform: Platform name (youtube, tiktok, instagram)
            cost: Number of quota units to consume
            
        Returns:
            True if quota consumed successfully, False if exceeded
        """
        limit = self.limits.get(platform, 1000)
        
        if self.redis:
            try:
                key = self._get_key(platform)
                current = int(await self.redis.get(key) or 0)
                
                if current + cost > limit:
                    logger.warning(f"Quota exceeded for {platform}: {current}/{limit}")
                    return False
                
                await self.redis.incrby(key, cost)
                await self.redis.expire(key, self.TTL_SECONDS)
                return True
            except Exception as e:
                logger.error(f"Redis error, falling back to local: {e}")
        
        # In-memory fallback
        self._reset_local_if_new_day()
        current = self._local_store.get(platform, 0)
        
        if current + cost > limit:
            logger.warning(f"Quota exceeded for {platform}: {current}/{limit}")
            return False
        
        self._local_store[platform] = current + cost
        return True
    
    async def get_remaining(self, platform: str) -> int:
        """
        Get remaining quota for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Number of remaining quota units
        """
        limit = self.limits.get(platform, 1000)
        
        if self.redis:
            try:
                key = self._get_key(platform)
                used = int(await self.redis.get(key) or 0)
                return max(0, limit - used)
            except Exception as e:
                logger.error(f"Redis error, falling back to local: {e}")
        
        # In-memory fallback
        self._reset_local_if_new_day()
        used = self._local_store.get(platform, 0)
        return max(0, limit - used)
    
    async def get_usage(self, platform: str) -> dict:
        """
        Get detailed usage info for platform.
        
        Returns:
            Dict with used, remaining, limit, percentage
        """
        limit = self.limits.get(platform, 1000)
        remaining = await self.get_remaining(platform)
        used = limit - remaining
        
        return {
            "platform": platform,
            "used": used,
            "remaining": remaining,
            "limit": limit,
            "percentage": round(used / limit * 100, 1) if limit > 0 else 0,
        }
    
    async def get_all_quotas(self) -> dict:
        """
        Get quota status for all platforms.
        
        Returns:
            Dict mapping platform -> remaining quota
        """
        quotas = {}
        for platform in self.limits.keys():
            quotas[platform] = await self.get_remaining(platform)
        return quotas
    
    def sync_check_and_consume(self, platform: str, cost: int = 1) -> bool:
        """Synchronous version for non-async contexts."""
        limit = self.limits.get(platform, 1000)
        
        self._reset_local_if_new_day()
        current = self._local_store.get(platform, 0)
        
        if current + cost > limit:
            return False
        
        self._local_store[platform] = current + cost
        return True
    
    def sync_get_remaining(self, platform: str) -> int:
        """Synchronous version of get_remaining."""
        limit = self.limits.get(platform, 1000)
        self._reset_local_if_new_day()
        used = self._local_store.get(platform, 0)
        return max(0, limit - used)


# Singleton instance (uses in-memory by default, can inject Redis later)
quota_manager = QuotaManager()


def get_quota_manager() -> QuotaManager:
    """Get the singleton quota manager instance."""
    return quota_manager
