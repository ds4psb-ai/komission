"""
TikTok Metadata Extractor Service
Unified extraction for views, likes, comments, shares, author, hashtags, upload date.

Uses advanced parsing strategies (ported from simple-web-server.cjs):
1. UNIVERSAL_DATA JSON (webapp.video-detail) - Most reliable
2. SIGI_STATE JSON fallback
3. DOM data-e2e selectors
4. Open Graph meta tags fallback

Author: Ported from K-MEME Factory backup
"""
import os
import re
import json
import time
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TikTokMetadata:
    """Standardized TikTok metadata structure."""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    author: str = "Unknown"
    author_id: str = ""
    upload_date: Optional[str] = None
    hashtags: List[str] = None
    title: Optional[str] = None
    video_id: Optional[str] = None
    source: str = "unknown"
    extraction_quality: str = "unknown"
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TikTokMetadataExtractor:
    """
    Advanced TikTok metadata extraction service.
    
    Matches YouTube API quality for consistent pipeline integration.
    """
    
    # User-Agent rotation for anti-fingerprinting
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    # Advanced headers for UNIVERSAL_DATA JSON extraction
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    
    def __init__(self):
        self.timeout = float(os.getenv("TIKTOK_METADATA_TIMEOUT", "30"))
    
    async def extract(self, url: str) -> TikTokMetadata:
        """
        Extract TikTok metadata from video URL.
        
        Priority:
        1. Playwright with cookies (bypasses bot detection)
        2. httpx fallback
        
        Parsing strategies:
        1. UNIVERSAL_DATA JSON (webapp.video-detail)
        2. SIGI_STATE JSON fallback
        3. DOM data-e2e selectors
        4. Open Graph meta tags
        """
        print(f"🔍 TikTok metadata extraction: {url[:60]}...")
        
        # Try Playwright first (better success rate with cookies)
        html = await self._fetch_with_playwright(url)
        
        if not html:
            # Fallback to httpx
            html = await self._fetch_with_httpx(url)
        
        if not html:
            return TikTokMetadata(source="fetch_error")
        
        # Parse the HTML
        return self._parse_html(html, url)
    
    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch HTML using Playwright with cookies and stealth mode."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("⚠️ Playwright not available")
            return None
        
        import random
        
        # Get cookie file from comment extractor
        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")
        if not cookie_file or not os.path.exists(cookie_file):
            base_dir = Path(__file__).parent.parent.parent
            auto_cookie = base_dir / "tiktok_cookies_auto.json"
            if auto_cookie.exists():
                cookie_file = str(auto_cookie)
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                
                context = await browser.new_context(
                    user_agent=random.choice(self.USER_AGENTS),
                    viewport={"width": 1280, "height": 720},
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                )
                
                # Stealth mode
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
                    window.chrome = { runtime: {} };
                """)
                
                # Load cookies
                if cookie_file and os.path.exists(cookie_file):
                    try:
                        with open(cookie_file, 'r') as f:
                            data = json.load(f)
                        cookies = data.get('cookies', data) if isinstance(data, dict) else data
                        if isinstance(cookies, list) and cookies:
                            await context.add_cookies(cookies)
                    except Exception:
                        pass
                
                page = await context.new_page()
                
                try:
                    wait_until = os.getenv("TIKTOK_METADATA_WAIT_UNTIL", "domcontentloaded")
                    await page.goto(url, wait_until=wait_until, timeout=int(self.timeout * 1000))
                    await page.wait_for_timeout(2000)
                    html = await page.content()
                    print(f"📄 Playwright HTML: {len(html)} bytes")
                    return html
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"⚠️ Playwright fetch failed: {e}")
            return None
    
    async def _fetch_with_httpx(self, url: str) -> Optional[str]:
        """Fallback fetch using httpx."""
        import random
        
        headers = {**self.HEADERS, 'User-Agent': random.choice(self.USER_AGENTS)}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    print(f"📄 httpx HTML: {len(response.text)} bytes")
                    return response.text
        except Exception as e:
            print(f"⚠️ httpx fetch failed: {e}")
        
        return None
    
    def _parse_html(self, html: str, url: str) -> TikTokMetadata:
        """Parse HTML with all strategies."""
        is_video_page = '/video/' in url
        video_id = self._extract_video_id(url)
        author_id = self._extract_author_from_url(url)
        
        # Strategy 1: UNIVERSAL_DATA JSON (most reliable)
        result = self._parse_universal_data(html, is_video_page, video_id)
        if result:
            result.video_id = video_id
            result.author_id = result.author_id or author_id
            return result
        
        # Strategy 2: SIGI_STATE JSON fallback
        result = self._parse_sigi_state(html, is_video_page, video_id)
        if result:
            result.video_id = video_id
            result.author_id = result.author_id or author_id
            return result
        
        # Strategy 3: DOM data-e2e selectors
        result = self._parse_dom_selectors(html, is_video_page)
        if result:
            result.video_id = video_id
            result.author_id = result.author_id or author_id
            return result
        
        # Strategy 4: OG meta tags fallback
        result = self._parse_og_meta(html)
        result.video_id = video_id
        result.author_id = author_id
        return result
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from TikTok URL."""
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None
    
    def _extract_author_from_url(self, url: str) -> str:
        """Extract author username from URL."""
        match = re.search(r'@([^/]+)', url)
        return match.group(1) if match else ""
    
    def _parse_count(self, value: Any) -> int:
        """Parse count values (handles K, M, B suffixes and various formats)."""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        
        s = str(value).strip().upper()
        if not s:
            return 0
        
        try:
            # Remove commas
            s = s.replace(',', '')
            
            # Handle K/M/B suffixes
            if 'K' in s:
                return int(float(s.replace('K', '')) * 1000)
            elif 'M' in s:
                return int(float(s.replace('M', '')) * 1_000_000)
            elif 'B' in s:
                return int(float(s.replace('B', '')) * 1_000_000_000)
            else:
                return int(float(s))
        except (ValueError, TypeError):
            return 0
    
    def _parse_universal_data(self, html: str, is_video_page: bool, video_id: Optional[str]) -> Optional[TikTokMetadata]:
        """
        Parse __UNIVERSAL_DATA_FOR_REHYDRATION__ JSON.
        
        Most reliable extraction method - TikTok's hydration data.
        """
        pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\s\S]*?)</script>'
        match = re.search(pattern, html, re.IGNORECASE)
        
        if not match:
            print("⚠️ UNIVERSAL_DATA not found")
            return None
        
        try:
            data = json.loads(match.group(1).strip())
            print("✅ UNIVERSAL_DATA JSON parsed")
        except json.JSONDecodeError as e:
            print(f"⚠️ UNIVERSAL_DATA parse error: {e}")
            return None
        
        # Video page: webapp.video-detail
        if is_video_page:
            video_detail = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {})
            item = video_detail.get('itemInfo', {}).get('itemStruct', {})
            
            if not item:
                print("⚠️ webapp.video-detail not found")
                return None
            
            stats = item.get('stats', {})
            author = item.get('author', {})
            challenges = item.get('challenges', [])
            
            # Extract hashtags
            hashtags = []
            if isinstance(challenges, list):
                hashtags = [f"#{c.get('title', '')}" for c in challenges if c.get('title')]
            
            # Extract from description if no challenges
            desc = item.get('desc', '')
            if not hashtags and desc:
                hashtags = re.findall(r'#\w+', desc)
            
            # Upload date
            upload_date = None
            create_time = item.get('createTime')
            if create_time:
                try:
                    timestamp = int(create_time)
                    upload_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))
                except (ValueError, TypeError):
                    pass
            
            result = TikTokMetadata(
                view_count=self._parse_count(stats.get('playCount')),
                like_count=self._parse_count(stats.get('diggCount')),
                comment_count=self._parse_count(stats.get('commentCount')),
                share_count=self._parse_count(stats.get('shareCount')),
                author=author.get('nickname') or author.get('uniqueId') or 'Unknown',
                author_id=author.get('uniqueId', ''),
                upload_date=upload_date,
                hashtags=hashtags,
                title=desc if desc else None,
                source='universal_data',
                extraction_quality='complete',
            )
            
            print(f"✅ UNIVERSAL_DATA extracted: views={result.view_count}, likes={result.like_count}")
            return result
        
        return None
    
    def _parse_sigi_state(self, html: str, is_video_page: bool, video_id: Optional[str]) -> Optional[TikTokMetadata]:
        """
        Parse SIGI_STATE JSON fallback.
        """
        pattern = r'<script id="SIGI_STATE"[^>]*>([\s\S]*?)</script>'
        match = re.search(pattern, html, re.IGNORECASE)
        
        if not match:
            print("⚠️ SIGI_STATE not found")
            return None
        
        try:
            data = json.loads(match.group(1).strip())
            print("✅ SIGI_STATE JSON parsed")
        except json.JSONDecodeError:
            return None
        
        if is_video_page:
            item_module = data.get('ItemModule', {})
            
            # Try exact video ID
            if video_id and video_id in item_module:
                item = item_module[video_id]
            elif item_module:
                # Use first item
                item = next(iter(item_module.values()))
            else:
                return None
            
            stats = item.get('stats', {})
            author = item.get('author', {})
            
            upload_date = None
            create_time = item.get('createTime')
            if create_time:
                try:
                    timestamp = int(create_time)
                    upload_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))
                except (ValueError, TypeError):
                    pass
            
            desc = item.get('desc', '')
            hashtags = re.findall(r'#\w+', desc) if desc else []
            
            result = TikTokMetadata(
                view_count=self._parse_count(stats.get('playCount')),
                like_count=self._parse_count(stats.get('diggCount')),
                comment_count=self._parse_count(stats.get('commentCount')),
                share_count=self._parse_count(stats.get('shareCount')),
                author=author.get('nickname') or author.get('uniqueId') or 'Unknown',
                author_id=author.get('uniqueId', ''),
                upload_date=upload_date,
                hashtags=hashtags,
                title=desc if desc else None,
                source='sigi_state',
                extraction_quality='complete',
            )
            
            print(f"✅ SIGI_STATE extracted: views={result.view_count}, likes={result.like_count}")
            return result
        
        return None
    
    def _parse_dom_selectors(self, html: str, is_video_page: bool) -> Optional[TikTokMetadata]:
        """
        Parse using data-e2e DOM selectors.
        """
        if not is_video_page:
            return None
        
        # Multi-pattern extraction
        def extract_stat(patterns: List[str]) -> int:
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    return self._parse_count(match.group(1))
            return 0
        
        view_patterns = [
            r'"playCount":(\d+)',
            r'"view_count":(\d+)',
        ]
        
        like_patterns = [
            r'"diggCount":(\d+)',
            r'"digg_count":(\d+)',
        ]
        
        comment_patterns = [
            r'"commentCount":(\d+)',
            r'"comment_count":(\d+)',
        ]
        
        share_patterns = [
            r'"shareCount":(\d+)',
            r'"share_count":(\d+)',
        ]
        
        view_count = extract_stat(view_patterns)
        like_count = extract_stat(like_patterns)
        comment_count = extract_stat(comment_patterns)
        share_count = extract_stat(share_patterns)
        
        if not any([view_count, like_count, comment_count, share_count]):
            return None
        
        result = TikTokMetadata(
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            source='dom_selectors',
            extraction_quality='partial',
        )
        
        print(f"✅ DOM selectors extracted: views={result.view_count}, likes={result.like_count}")
        return result
    
    def _parse_og_meta(self, html: str) -> TikTokMetadata:
        """
        Parse Open Graph meta tags (last fallback).
        """
        og_title = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        og_desc = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        
        title = og_title.group(1) if og_title else None
        desc = og_desc.group(1) if og_desc else ""
        
        # Extract hashtags from description
        hashtags = re.findall(r'#\w+', desc) if desc else []
        
        print(f"⚠️ OG meta fallback: title={title[:30] if title else 'None'}...")
        
        return TikTokMetadata(
            title=title,
            hashtags=hashtags,
            source='og_meta',
            extraction_quality='minimal',
        )


# Singleton instance
tiktok_metadata_extractor = TikTokMetadataExtractor()


async def extract_tiktok_metadata(url: str) -> Dict[str, Any]:
    """
    Convenience function for TikTok metadata extraction.
    
    Returns dict matching YouTube API response format.
    """
    result = await tiktok_metadata_extractor.extract(url)
    return result.to_dict()
