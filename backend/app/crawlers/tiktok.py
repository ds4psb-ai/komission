"""
TikTok Crawler using Apify API

Since TikTok Research API requires academic affiliation,
we use Apify's TikTok actors for trending content collection.

Actors used:
- clockworks/tiktok-trending-videos
- apidojo/tiktok-scraper
"""
import os
import logging
from typing import List, Optional, Dict, Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.crawlers.base import BaseCrawler
from app.schemas.evidence import OutlierCrawlItem
from app.config import settings

logger = logging.getLogger(__name__)


class TikTokCrawler(BaseCrawler):
    """
    TikTok Crawler using Apify API.
    
    Requires:
    - APIFY_API_TOKEN environment variable
    
    Uses Apify actors for data collection since TikTok's official
    Research API requires academic institution affiliation.
    """
    
    APIFY_BASE_URL = "https://api.apify.com/v2"
    
    # Popular Apify actors for TikTok
    ACTORS = {
        "trending": "clockworks/tiktok-trending-videos",
        "hashtag": "novi/tiktok-hashtag-scraper",
        "search": "apidojo/tiktok-scraper",
    }
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or settings.APIFY_API_TOKEN
        if not self.api_token:
            logger.warning("APIFY_API_TOKEN not set - TikTok crawling will use mock data")
        
        self.client = httpx.Client(timeout=120.0)
    
    def crawl(
        self, 
        limit: int = 50, 
        region: str = "KR",
        category: str = "trending",
        hashtags: Optional[List[str]] = None,
        **kwargs
    ) -> List[OutlierCrawlItem]:
        """
        Crawl trending TikTok videos.
        
        Args:
            limit: Maximum number of videos to return
            region: Country code for regional trends
            category: trending, hashtag, or search
            hashtags: List of hashtags to search (for hashtag mode)
        """
        logger.info(f"Starting TikTok crawl: region={region}, category={category}, limit={limit}")
        
        if not self.api_token:
            logger.warning("No API token - returning mock data")
            return self._get_mock_data(limit)
        
        try:
            if category == "hashtag" and hashtags:
                videos = self._crawl_by_hashtags(hashtags, limit)
            else:
                videos = self._crawl_trending(region, limit)
            
            items = [self._normalize_to_outlier_item(v) for v in videos[:limit]]
            logger.info(f"TikTok crawl complete: {len(items)} items collected")
            return items
            
        except Exception as e:
            logger.error(f"TikTok crawl failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def _crawl_trending(self, region: str, limit: int) -> List[Dict[str, Any]]:
        """Crawl trending videos using Apify actor."""
        actor_id = self.ACTORS["trending"]
        
        # Run Apify actor
        run_input = {
            "country": region.lower(),
            "maxItems": limit,
            "proxy": {"useApifyProxy": True},
        }
        
        response = self.client.post(
            f"{self.APIFY_BASE_URL}/acts/{actor_id}/runs",
            headers={"Authorization": f"Bearer {self.api_token}"},
            json=run_input,
            params={"waitForFinish": 300},  # Wait up to 5 minutes
        )
        response.raise_for_status()
        
        run_data = response.json()
        dataset_id = run_data.get("data", {}).get("defaultDatasetId")
        
        if not dataset_id:
            logger.warning("No dataset ID returned from Apify run")
            return []
        
        # Fetch results from dataset
        return self._fetch_dataset(dataset_id, limit)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def _crawl_by_hashtags(self, hashtags: List[str], limit: int) -> List[Dict[str, Any]]:
        """Crawl videos by hashtags using Apify actor."""
        actor_id = self.ACTORS["hashtag"]
        
        run_input = {
            "hashtags": hashtags,
            "maxItems": limit,
            "proxy": {"useApifyProxy": True},
        }
        
        response = self.client.post(
            f"{self.APIFY_BASE_URL}/acts/{actor_id}/runs",
            headers={"Authorization": f"Bearer {self.api_token}"},
            json=run_input,
            params={"waitForFinish": 300},
        )
        response.raise_for_status()
        
        run_data = response.json()
        dataset_id = run_data.get("data", {}).get("defaultDatasetId")
        
        if not dataset_id:
            return []
        
        return self._fetch_dataset(dataset_id, limit)
    
    def _fetch_dataset(self, dataset_id: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch results from Apify dataset."""
        response = self.client.get(
            f"{self.APIFY_BASE_URL}/datasets/{dataset_id}/items",
            headers={"Authorization": f"Bearer {self.api_token}"},
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()
    
    def _normalize_to_outlier_item(self, video: Dict[str, Any]) -> OutlierCrawlItem:
        """Convert Apify response to OutlierCrawlItem."""
        # Handle different response formats from various Apify actors
        video_id = video.get("id") or video.get("videoId") or video.get("aweme_id", "")
        
        # Try different field names used by different actors
        view_count = (
            video.get("playCount") or 
            video.get("views") or 
            video.get("play_count") or 
            video.get("statistics", {}).get("playCount", 0)
        )
        
        like_count = (
            video.get("diggCount") or 
            video.get("likes") or 
            video.get("digg_count") or
            video.get("statistics", {}).get("diggCount")
        )
        
        share_count = (
            video.get("shareCount") or 
            video.get("shares") or 
            video.get("share_count") or
            video.get("statistics", {}).get("shareCount")
        )
        
        comment_count = (
            video.get("commentCount") or 
            video.get("comments") or 
            video.get("comment_count") or
            video.get("statistics", {}).get("commentCount", 0)
        )
        
        # Calculate engagement
        engagement = None
        if view_count and view_count > 0:
            total_engagement = (like_count or 0) + (comment_count or 0)
            engagement = round(total_engagement / view_count * 100, 2)
        
        # Get video URL
        video_url = (
            video.get("url") or 
            video.get("webVideoUrl") or 
            f"https://www.tiktok.com/@user/video/{video_id}"
        )
        
        # Get author handle
        author = video.get("author", {})
        if isinstance(author, dict):
            author_name = author.get("uniqueId") or author.get("nickname", "")
        else:
            author_name = str(author) if author else ""
        
        return OutlierCrawlItem(
            source_name="tiktok",
            external_id=str(video_id),
            video_url=video_url,
            platform="tiktok",
            category=video.get("hashtags", ["trending"])[0] if video.get("hashtags") else "trending",
            title=video.get("desc") or video.get("text") or video.get("description", ""),
            thumbnail_url=video.get("cover") or video.get("thumbnail"),
            view_count=int(view_count) if view_count else 0,
            like_count=int(like_count) if like_count else None,
            share_count=int(share_count) if share_count else None,
            growth_rate=f"{int(engagement*100) if engagement else 0}% engagement",
            # Extended metrics
            outlier_score=0.0,  # Placeholder until we can efficiently fetch creator baseline
            outlier_tier=None,
            creator_avg_views=0,
            engagement_rate=round(engagement / 100.0, 4) if engagement else 0.0
        )

    def _calculate_outlier_score(
        self, 
        view_count: int, 
        engagement_rate: float, 
        baseline_views: float
    ) -> Dict[str, Any]:
        """
        Calculate TikTok Outlier Score:
        Baseline Engagement: 8% (0.08)
        """
        if baseline_views <= 0:
            return {"score": 0.0, "tier": None}
            
        raw_multiplier = view_count / baseline_views
        # TikTok specific: 8% baseline
        engagement_modifier = 1 + (engagement_rate - 0.08)
        
        outlier_score = raw_multiplier * engagement_modifier
        
        tier = None
        if outlier_score >= 500: tier = "S"
        elif outlier_score >= 200: tier = "A"
        elif outlier_score >= 100: tier = "B"
        elif outlier_score >= 50: tier = "C"
        
        return {
            "score": round(outlier_score, 1),
            "tier": tier
        }
    
    def _get_mock_data(self, limit: int) -> List[OutlierCrawlItem]:
        """Return mock data when API token is not available."""
        return [
            OutlierCrawlItem(
                source_name="tiktok_mock",
                external_id=f"mock_{i}",
                video_url=f"https://www.tiktok.com/@mock/video/{i}",
                platform="tiktok",
                category="mock",
                title=f"Mock TikTok Video {i}",
                view_count=100000 * (i + 1),
                like_count=5000 * (i + 1),
            )
            for i in range(min(limit, 5))
        ]
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# CLI entry point
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="TikTok Crawler")
    parser.add_argument("--region", default="KR", help="Country code")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--hashtags", nargs="+", help="Hashtags to search")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    with TikTokCrawler() as crawler:
        if args.hashtags:
            items = crawler.crawl(
                limit=args.limit,
                category="hashtag",
                hashtags=args.hashtags,
            )
        else:
            items = crawler.crawl(limit=args.limit, region=args.region)
        
        for item in items:
            print(json.dumps(item.model_dump(), indent=2, ensure_ascii=False))
        
        print(f"\nTotal: {len(items)} items")
