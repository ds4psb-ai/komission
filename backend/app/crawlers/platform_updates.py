"""
Platform Updates Crawler - News & Blog monitoring
Based on 13_PERIODIC_CRAWLING_SPEC.md (L396-486)

Collects platform updates from:
- YouTube Creator Blog (RSS)
- TikTok Newsroom (scraping)
- Instagram for Creators (scraping)
- Social Media Today (RSS)
"""
import os
import logging
import httpx
import feedparser
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field

from app.utils.time import utcnow

logger = logging.getLogger(__name__)


@dataclass
class PlatformUpdate:
    """Represents a platform update/news item."""
    update_id: str
    platform: str  # youtube, tiktok, instagram, general
    source_url: str
    title: str
    published_at: Optional[datetime] = None
    crawled_at: datetime = field(default_factory=utcnow)
    raw_content: Optional[str] = None
    summary_kr: Optional[str] = None
    category: Optional[str] = None  # algorithm, monetization, policy, feature
    impact_level: Optional[str] = None  # high, medium, low
    action_required: bool = False
    action_summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)


class PlatformUpdatesCrawler:
    """
    Crawler for platform news and updates.
    
    Usage:
        crawler = PlatformUpdatesCrawler()
        updates = await crawler.crawl_all()
        for update in updates:
            print(update.title)
    """
    
    # RSS Feeds (spec L406-414)
    RSS_FEEDS = {
        "youtube": "https://blog.youtube/rss/",
        "general": [
            "https://www.socialmediatoday.com/rss.xml",
            # "https://www.theverge.com/rss/tech/index.xml",  # May have CORS issues
        ]
    }
    
    # Scrape sources (for platforms without RSS)
    SCRAPE_SOURCES = {
        "tiktok": "https://newsroom.tiktok.com/en-us/",
        "instagram": "https://creators.instagram.com/blog"
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def crawl_all(self, limit: int = 10) -> List[PlatformUpdate]:
        """
        Crawl updates from all platforms.
        
        Args:
            limit: Max items per platform
            
        Returns:
            List of PlatformUpdate objects
        """
        all_updates = []
        
        # YouTube (RSS)
        try:
            youtube_updates = await self.fetch_youtube_updates(limit)
            all_updates.extend(youtube_updates)
            logger.info(f"Fetched {len(youtube_updates)} YouTube updates")
        except Exception as e:
            logger.error(f"YouTube updates failed: {e}")
        
        # TikTok (scraping - disabled by default due to rate limits)
        # tiktok_updates = await self.scrape_tiktok_newsroom(limit)
        # all_updates.extend(tiktok_updates)
        
        # General RSS (Social Media Today)
        try:
            general_updates = await self.fetch_general_updates(limit)
            all_updates.extend(general_updates)
            logger.info(f"Fetched {len(general_updates)} general updates")
        except Exception as e:
            logger.error(f"General updates failed: {e}")
        
        return all_updates
    
    async def fetch_youtube_updates(self, limit: int = 10) -> List[PlatformUpdate]:
        """
        Fetch updates from YouTube Creator Blog RSS.
        
        Returns:
            List of PlatformUpdate objects
        """
        updates = []
        
        try:
            response = await self.client.get(self.RSS_FEEDS["youtube"])
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:limit]:
                update_id = f"yt_update_{self._hash_url(entry.link)}"
                
                # Parse published date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                
                updates.append(PlatformUpdate(
                    update_id=update_id,
                    platform="youtube",
                    source_url=entry.link,
                    title=entry.title,
                    published_at=published,
                    raw_content=entry.get('summary', '')[:2000],  # Truncate
                    category=self._infer_category(entry.title),
                ))
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch YouTube RSS: {e}")
        
        return updates
    
    async def fetch_general_updates(self, limit: int = 10) -> List[PlatformUpdate]:
        """Fetch from general RSS feeds (Social Media Today, etc.)"""
        updates = []
        
        for feed_url in self.RSS_FEEDS.get("general", []):
            try:
                response = await self.client.get(feed_url)
                response.raise_for_status()
                
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:limit]:
                    # Filter for platform-related content
                    title_lower = entry.title.lower()
                    if not any(kw in title_lower for kw in ['youtube', 'tiktok', 'instagram', 'reels', 'shorts', 'creator']):
                        continue
                    
                    update_id = f"gen_update_{self._hash_url(entry.link)}"
                    
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    
                    updates.append(PlatformUpdate(
                        update_id=update_id,
                        platform="general",
                        source_url=entry.link,
                        title=entry.title,
                        published_at=published,
                        raw_content=entry.get('summary', '')[:2000],
                        category=self._infer_category(entry.title),
                    ))
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch RSS {feed_url}: {e}")
        
        return updates
    
    async def scrape_tiktok_newsroom(self, limit: int = 10) -> List[PlatformUpdate]:
        """
        Scrape TikTok Newsroom (disabled by default).
        
        Note: Requires Playwright for JavaScript rendering.
        """
        updates = []
        
        try:
            # Simple HTML fetch (may not work due to JS rendering)
            response = await self.client.get(self.SCRAPE_SOURCES["tiktok"])
            response.raise_for_status()
            
            # Would need BeautifulSoup or Playwright for proper parsing
            # Left as stub for future implementation
            logger.warning("TikTok scraping requires Playwright for full rendering")
            
        except httpx.HTTPError as e:
            logger.error(f"TikTok newsroom fetch failed: {e}")
        
        return updates
    
    async def summarize_with_ai(self, update: PlatformUpdate) -> PlatformUpdate:
        """
        Use Gemini to summarize and analyze an update.
        
        Args:
            update: PlatformUpdate to summarize
            
        Returns:
            Updated PlatformUpdate with AI-generated summary
        """
        try:
            from google import genai
            
            client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
            
            prompt = f"""
            다음 소셜 미디어 플랫폼 업데이트 기사를 분석하세요.
            
            Title: {update.title}
            Content: {update.raw_content or '(no content)'}
            
            응답 형식 (JSON):
            {{
                "summary_kr": "한국어 요약 (2-3문장)",
                "category": "algorithm|monetization|policy|feature",
                "impact_level": "high|medium|low",
                "action_required": true/false,
                "action_summary": "크리에이터가 취해야 할 액션 (있다면, 없으면 null)"
            }}
            """
            
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            import json
            result = json.loads(response.text)
            
            update.summary_kr = result.get("summary_kr")
            update.category = result.get("category")
            update.impact_level = result.get("impact_level")
            update.action_required = result.get("action_required", False)
            update.action_summary = result.get("action_summary")
            
        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
        
        return update
    
    def _hash_url(self, url: str) -> str:
        """Create short hash from URL for unique ID."""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    def _infer_category(self, title: str) -> str:
        """Infer category from title keywords."""
        title_lower = title.lower()
        
        if any(kw in title_lower for kw in ['algorithm', 'recommendation', 'feed', 'discover']):
            return "algorithm"
        elif any(kw in title_lower for kw in ['monetization', 'money', 'revenue', 'earn', 'fund', 'payment']):
            return "monetization"
        elif any(kw in title_lower for kw in ['policy', 'rule', 'guideline', 'terms', 'ban', 'restriction']):
            return "policy"
        else:
            return "feature"


# Factory function for consistent interface
def create_platform_updates_crawler() -> PlatformUpdatesCrawler:
    """Create a new Platform Updates crawler instance."""
    return PlatformUpdatesCrawler()
