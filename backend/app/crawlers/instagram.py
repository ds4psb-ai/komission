"""
Instagram Reels Crawler

Uses either:
1. Instagram Graph API (requires Business/Creator account + App Review)
2. Apify actors as fallback

For MVP, we primarily use Apify for easier setup.
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


class InstagramCrawler(BaseCrawler):
    """
    Instagram Reels Crawler.
    
    Supports:
    1. Apify API (default, easier setup)
    2. Instagram Graph API (requires Business account)
    
    Requires:
    - APIFY_API_TOKEN for Apify mode
    - INSTAGRAM_ACCESS_TOKEN + IG_BUSINESS_ACCOUNT_ID for Graph API mode
    """
    
    APIFY_BASE_URL = "https://api.apify.com/v2"
    GRAPH_API_URL = "https://graph.facebook.com/v18.0"
    
    # Apify actors for Instagram
    ACTORS = {
        "reels": "apify/instagram-reel-scraper",
        "hashtag": "apidojo/instagram-hashtag-scraper",
        "profile": "apify/instagram-profile-scraper",
    }
    
    def __init__(
        self, 
        apify_token: Optional[str] = None,
        access_token: Optional[str] = None,
        business_account_id: Optional[str] = None,
    ):
        self.apify_token = apify_token or settings.APIFY_API_TOKEN
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.business_account_id = business_account_id or os.getenv("IG_BUSINESS_ACCOUNT_ID", "")
        
        self.client = httpx.Client(timeout=120.0)
        
        # Determine which mode to use
        self.use_graph_api = bool(self.access_token and self.business_account_id)
        
        if not self.apify_token and not self.use_graph_api:
            logger.warning("No Instagram credentials - will use mock data")
    
    def crawl(
        self, 
        limit: int = 30, 
        hashtags: Optional[List[str]] = None,
        category: str = "trending",
        **kwargs
    ) -> List[OutlierCrawlItem]:
        """
        Crawl Instagram Reels.
        
        Args:
            limit: Maximum number of Reels to return
            hashtags: Hashtags to search
            category: Category label for collected items
        """
        logger.info(f"Starting Instagram crawl: hashtags={hashtags}, limit={limit}")
        
        if not self.apify_token and not self.use_graph_api:
            logger.warning("No credentials - returning mock data")
            return self._get_mock_data(limit)
        
        try:
            if self.use_graph_api and hashtags:
                reels = self._crawl_via_graph_api(hashtags, limit)
            elif self.apify_token:
                reels = self._crawl_via_apify(hashtags or ["viral", "trending"], limit)
            else:
                reels = []
            
            items = [self._normalize_to_outlier_item(r, category) for r in reels[:limit]]
            logger.info(f"Instagram crawl complete: {len(items)} items collected")
            return items
            
        except Exception as e:
            logger.error(f"Instagram crawl failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def _crawl_via_graph_api(self, hashtags: List[str], limit: int) -> List[Dict[str, Any]]:
        """Crawl using Instagram Graph API (requires Business account)."""
        all_results = []
        
        for hashtag in hashtags[:3]:  # Limit to 3 hashtags (API limit: 30/week)
            try:
                # Step 1: Get hashtag ID
                search_response = self.client.get(
                    f"{self.GRAPH_API_URL}/ig_hashtag_search",
                    params={
                        "user_id": self.business_account_id,
                        "q": hashtag,
                        "access_token": self.access_token,
                    }
                )
                search_response.raise_for_status()
                
                hashtag_data = search_response.json().get("data", [])
                if not hashtag_data:
                    continue
                
                hashtag_id = hashtag_data[0]["id"]
                
                # Step 2: Get top media for hashtag
                media_response = self.client.get(
                    f"{self.GRAPH_API_URL}/{hashtag_id}/top_media",
                    params={
                        "user_id": self.business_account_id,
                        "fields": "id,media_type,media_url,permalink,like_count,comments_count,caption",
                        "limit": min(limit, 50),
                        "access_token": self.access_token,
                    }
                )
                media_response.raise_for_status()
                
                media = media_response.json().get("data", [])
                
                # Filter for Reels (VIDEO type)
                reels = [m for m in media if m.get("media_type") == "VIDEO"]
                all_results.extend(reels)
                
            except Exception as e:
                logger.warning(f"Failed to fetch hashtag {hashtag}: {e}")
                continue
        
        return all_results
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def _crawl_via_apify(self, hashtags: List[str], limit: int) -> List[Dict[str, Any]]:
        """Crawl using Apify actors."""
        actor_id = self.ACTORS["hashtag"]
        
        run_input = {
            "hashtags": hashtags,
            "resultsLimit": limit,
            "proxy": {"useApifyProxy": True},
        }
        
        response = self.client.post(
            f"{self.APIFY_BASE_URL}/acts/{actor_id}/runs",
            headers={"Authorization": f"Bearer {self.apify_token}"},
            json=run_input,
            params={"waitForFinish": 300},
        )
        response.raise_for_status()
        
        run_data = response.json()
        dataset_id = run_data.get("data", {}).get("defaultDatasetId")
        
        if not dataset_id:
            return []
        
        # Fetch results
        results_response = self.client.get(
            f"{self.APIFY_BASE_URL}/datasets/{dataset_id}/items",
            headers={"Authorization": f"Bearer {self.apify_token}"},
            params={"limit": limit},
        )
        results_response.raise_for_status()
        
        return results_response.json()
    
    def _normalize_to_outlier_item(
        self, 
        reel: Dict[str, Any],
        category: str
    ) -> OutlierCrawlItem:
        """Convert API response to OutlierCrawlItem."""
        # Handle different response formats
        reel_id = reel.get("id") or reel.get("shortcode") or reel.get("pk", "")
        
        # Views/plays might not be available via API
        view_count = reel.get("play_count") or reel.get("video_view_count") or 0
        like_count = reel.get("like_count") or reel.get("likes") or 0
        comment_count = reel.get("comments_count") or reel.get("comment_count") or 0
        
        # Calculate engagement if we have data
        engagement = None
        if view_count and view_count > 0:
            engagement = round((like_count + comment_count) / view_count * 100, 2)
        elif like_count > 0:
            # Use likes as proxy if no view count
            engagement = round(comment_count / like_count * 100, 2) if like_count else None
        
        # Get URL
        video_url = (
            reel.get("permalink") or 
            reel.get("url") or 
            f"https://www.instagram.com/reel/{reel_id}"
        )
        
        # Get thumbnail
        thumbnail = (
            reel.get("thumbnail_url") or
            reel.get("display_url") or
            reel.get("media_url")
        )
        
        # Get caption/title
        caption = reel.get("caption") or ""
        if isinstance(caption, dict):
            caption = caption.get("text", "")
        
        # Calculate engagement rate correct format (0.0-1.0)
        eng_rate_val = (engagement / 100.0) if engagement else 0.0

        return OutlierCrawlItem(
            source_name="instagram",
            external_id=str(reel_id),
            video_url=video_url,
            platform="instagram",
            category=category,
            title=caption[:100] if caption else "",
            thumbnail_url=thumbnail,
            view_count=int(view_count) if view_count else 0,
            like_count=int(like_count) if like_count else None,
            share_count=None,  # Not typically available
            growth_rate=f"{engagement}% engagement" if engagement else None,
            # Extended metrics
            outlier_score=0.0, # Placeholder until we can efficiently fetch creator baseline
            outlier_tier=None,
            creator_avg_views=0,
            engagement_rate=round(eng_rate_val, 4)
        )

    def _calculate_outlier_score(
        self, 
        view_count: int, 
        engagement_rate: float, 
        baseline_views: float
    ) -> Dict[str, Any]:
        """
        Calculate Instagram Outlier Score:
        Baseline Engagement: 10% (0.10)
        """
        if baseline_views <= 0:
            return {"score": 0.0, "tier": None}
            
        raw_multiplier = view_count / baseline_views
        # Instagram specific: 10% baseline
        engagement_modifier = 1 + (engagement_rate - 0.10)
        
        outlier_score = raw_multiplier * engagement_modifier
        
        tier = None
        if outlier_score >= 500: tier = "S"
        elif outlier_score >= 200: tier = "A"
        elif outlier_score >= 100: tier = "B"
        elif outlier_score >= 30: tier = "C" # Lower threshold for IG (30x)
        
        return {
            "score": round(outlier_score, 1),
            "tier": tier
        }
    
    def _get_mock_data(self, limit: int) -> List[OutlierCrawlItem]:
        """Return mock data when no credentials available."""
        return [
            OutlierCrawlItem(
                source_name="instagram_mock",
                external_id=f"mock_{i}",
                video_url=f"https://www.instagram.com/reel/mock{i}",
                platform="instagram",
                category="mock",
                title=f"Mock Instagram Reel {i}",
                view_count=50000 * (i + 1),
                like_count=2500 * (i + 1),
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
    
    parser = argparse.ArgumentParser(description="Instagram Reels Crawler")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--hashtags", nargs="+", default=["viral"], help="Hashtags to search")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    with InstagramCrawler() as crawler:
        items = crawler.crawl(limit=args.limit, hashtags=args.hashtags)
        
        for item in items:
            print(json.dumps(item.model_dump(), indent=2, ensure_ascii=False))
        
        print(f"\nTotal: {len(items)} items")
