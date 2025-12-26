"""
YouTube Shorts Crawler using YouTube Data API v3

Fetches trending YouTube Shorts and calculates outlier scores based on:
- View count vs channel average
- Engagement rate (likes + comments / views)
"""
import os
import re
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.crawlers.base import BaseCrawler
from app.schemas.evidence import OutlierCrawlItem
from app.config import settings

logger = logging.getLogger(__name__)


class YouTubeCrawler(BaseCrawler):
    """
    YouTube Shorts Crawler using YouTube Data API v3.
    
    Requires:
    - YOUTUBE_API_KEY environment variable
    
    Rate Limits:
    - 10,000 units/day
    - search.list: 100 units per call
    - videos.list: 1 unit per video ID
    """
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    # YouTube category IDs for popular content
    CATEGORY_MAP = {
        "entertainment": "24",
        "gaming": "20",
        "music": "10",
        "comedy": "23",
        "howto": "26",
        "education": "27",
        "sports": "17",
        "news": "25",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is required for YouTubeCrawler")
        
        self.client = httpx.Client(timeout=30.0)
        self.quota_used = 0
    
    def crawl(
        self, 
        limit: int = 50, 
        region_code: str = "KR",
        category: str = "entertainment",
        shorts_only: bool = True,
        **kwargs
    ) -> List[OutlierCrawlItem]:
        """
        Crawl trending YouTube videos/Shorts.
        
        Args:
            limit: Maximum number of videos to return
            region_code: ISO 3166-1 alpha-2 country code
            category: Video category (entertainment, gaming, etc.)
            shorts_only: Filter for Shorts only (duration < 60s)
        """
        logger.info(f"Starting YouTube crawl: region={region_code}, category={category}, limit={limit}")
        
        try:
            # Step 1: Fetch trending videos
            video_ids = self._fetch_trending_videos(
                region_code=region_code,
                category=category,
                max_results=min(limit * 2, 50)  # Fetch more to filter
            )
            
            if not video_ids:
                logger.warning("No trending videos found")
                return []
            
            # Step 2: Get detailed stats for videos
            videos = self._get_video_details(video_ids)
            
            # Step 3: Filter Shorts if requested
            if shorts_only:
                videos = [v for v in videos if self._is_shorts(v)]
            
            # Step 4: Calculate outlier scores and normalize
            items = []
            for video in videos[:limit]:
                try:
                    # Optimization: Only calculate baseline for videos with > 100k views
                    # to save API quota (100 units per channel search)
                    view_count = int(video.get("statistics", {}).get("viewCount", 0))
                    
                    baseline_views = 0.0
                    if view_count >= 100000:
                        channel_id = video.get("snippet", {}).get("channelId")
                        if channel_id:
                            baseline_views = self.get_channel_baseline(channel_id)
                    
                    item = self._normalize_to_outlier_item(video, category, baseline_views)
                    
                    # Only include if it meets minimum criteria or we want to log it
                    # (For now we return all processed items, let consumer filter)
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Failed to normalize video {video.get('id')}: {e}")
                    continue
            
            logger.info(f"YouTube crawl complete: {len(items)} items collected")
            return items
            
        except Exception as e:
            logger.error(f"YouTube crawl failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _fetch_trending_videos(
        self, 
        region_code: str, 
        category: str,
        max_results: int = 50
    ) -> List[str]:
        """Fetch trending video IDs using videos.list with chart=mostPopular."""
        category_id = self.CATEGORY_MAP.get(category.lower(), "24")
        
        response = self.client.get(
            f"{self.BASE_URL}/videos",
            params={
                "part": "id",
                "chart": "mostPopular",
                "regionCode": region_code,
                "videoCategoryId": category_id,
                "maxResults": max_results,
                "key": self.api_key,
            }
        )
        response.raise_for_status()
        self.quota_used += 1  # videos.list costs 1 unit
        
        data = response.json()
        return [item["id"] for item in data.get("items", [])]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed statistics for videos."""
        if not video_ids:
            return []
        
        # API allows max 50 IDs per request
        all_videos = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            
            response = self.client.get(
                f"{self.BASE_URL}/videos",
                params={
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(batch),
                    "key": self.api_key,
                }
            )
            response.raise_for_status()
            self.quota_used += len(batch)  # 1 unit per ID
            
            data = response.json()
            all_videos.extend(data.get("items", []))
        
        return all_videos
    
    def _is_shorts(self, video: Dict[str, Any]) -> bool:
        """Check if video is a YouTube Short (< 60s or has #shorts)."""
        # Check duration
        duration_str = video.get("contentDetails", {}).get("duration", "")
        duration_seconds = self._parse_duration(duration_str)
        
        if duration_seconds <= 60:
            return True
        
        # Check for #shorts in title or description
        snippet = video.get("snippet", {})
        title = snippet.get("title", "").lower()
        description = snippet.get("description", "").lower()
        
        return "#shorts" in title or "#shorts" in description
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration (PT1M30S) to seconds."""
        if not duration_str:
            return 0
        
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _normalize_to_outlier_item(
        self, 
        video: Dict[str, Any],
        category: str,
        baseline_views: float = 0
    ) -> OutlierCrawlItem:
        """Convert YouTube API response to OutlierCrawlItem with outlier scoring."""
        video_id = video.get("id", "")
        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        
        # Parse view count safely
        view_count = int(statistics.get("viewCount", 0))
        like_count = int(statistics.get("likeCount", 0)) if statistics.get("likeCount") else None
        comment_count = int(statistics.get("commentCount", 0)) if statistics.get("commentCount") else None
        
        # Calculate stats
        engagement_rate = 0.0
        if view_count > 0 and like_count:
            engagement_rate = (like_count + (comment_count or 0)) / view_count
            
        # Calculate outlier score
        score_data = self._calculate_outlier_score(
            view_count=view_count,
            engagement_rate=engagement_rate,
            baseline_views=baseline_views
        )
        
        return OutlierCrawlItem(
            source_name="youtube",
            external_id=video_id,
            video_url=f"https://www.youtube.com/shorts/{video_id}",
            platform="youtube",
            category=category,
            title=snippet.get("title", ""),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
            view_count=view_count,
            like_count=like_count,
            share_count=None,  # Not available via API
            growth_rate=f"{int(engagement_rate*100)}% engagement",
            # Extended metrics
            outlier_score=score_data["score"],
            outlier_tier=score_data["tier"],
            creator_avg_views=int(baseline_views),
            engagement_rate=round(engagement_rate, 4)
        )

    def _calculate_outlier_score(
        self, 
        view_count: int, 
        engagement_rate: float, 
        baseline_views: float
    ) -> Dict[str, Any]:
        """
        Calculate Outlier Score based on spec:
        Score = (Views / Baseline) * (1 + (Engagement - 0.05))
        """
        if baseline_views <= 0:
            return {"score": 0.0, "tier": None}
            
        raw_multiplier = view_count / baseline_views
        # Engagement modifier: +10% score for every 10% engagement above 5%
        # Spec says: 1 + (engagement - 0.05)
        # Low engagement (<5%) punishment is also applied
        engagement_modifier = 1 + (engagement_rate - 0.05)
        
        outlier_score = raw_multiplier * engagement_modifier
        
        # Tier Classification
        tier = None
        if outlier_score >= 500: tier = "S"
        elif outlier_score >= 200: tier = "A"
        elif outlier_score >= 100: tier = "B"
        elif outlier_score >= 50: tier = "C"
        
        return {
            "score": round(outlier_score, 1),
            "tier": tier
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_channel_baseline(self, channel_id: str) -> float:
        """
        Calculate channel's average views from recent 20 videos.
        """
        try:
            response = self.client.get(
                f"{self.BASE_URL}/search",
                params={
                    "part": "id",
                    "channelId": channel_id,
                    "type": "video",
                    "order": "date",
                    "maxResults": 20,
                    "key": self.api_key,
                }
            )
            response.raise_for_status()
            self.quota_used += 100 # search.list cost
            
            data = response.json()
            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            
            if not video_ids:
                return 0.0
                
            videos = self._get_video_details(video_ids)
            views = [int(v["statistics"].get("viewCount", 0)) for v in videos]
            
            if not views:
                return 0.0
                
            # Exclude top/bottom outliers for robust mean ? (Optional, sticking to simple mean per spec)
            return sum(views) / len(views)
            
        except Exception as e:
            logger.warning(f"Failed to get baseline for channel {channel_id}: {e}")
            return 0.0
    
    def search_shorts_by_keyword(
        self,
        keyword: str,
        limit: int = 25,
        published_after_days: int = 14,
    ) -> List[OutlierCrawlItem]:
        """
        Search for Shorts by keyword (alternative to trending).
        Uses search.list which costs 100 units per call.
        """
        published_after = (datetime.utcnow() - timedelta(days=published_after_days)).isoformat() + "Z"
        
        response = self.client.get(
            f"{self.BASE_URL}/search",
            params={
                "part": "snippet",
                "q": f"{keyword} #shorts",
                "type": "video",
                "videoDuration": "short",
                "order": "viewCount",
                "publishedAfter": published_after,
                "maxResults": min(limit, 50),
                "key": self.api_key,
            }
        )
        response.raise_for_status()
        self.quota_used += 100  # search.list costs 100 units
        
        data = response.json()
        video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
        
        if not video_ids:
            return []
        
        videos = self._get_video_details(video_ids)
        return [
            self._normalize_to_outlier_item(v, "search")
            for v in videos
        ]
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# CLI entry point for testing
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="YouTube Shorts Crawler")
    parser.add_argument("--category", default="entertainment", help="Video category")
    parser.add_argument("--region", default="KR", help="Region code")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--keyword", help="Search by keyword instead of trending")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    with YouTubeCrawler() as crawler:
        if args.keyword:
            items = crawler.search_shorts_by_keyword(args.keyword, limit=args.limit)
        else:
            items = crawler.crawl(
                limit=args.limit,
                region_code=args.region,
                category=args.category,
            )
        
        for item in items:
            print(json.dumps(item.model_dump(), indent=2, ensure_ascii=False))
        
        print(f"\nTotal: {len(items)} items, Quota used: {crawler.quota_used} units")
