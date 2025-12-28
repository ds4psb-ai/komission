"""
TikTok Unified Extractor
Combines metadata + comments extraction in a single optimized call.

Features:
- Single Playwright session for both metadata and comments
- Cookie-based authentication
- All extraction strategies
- Production-ready hardening

Output matches YouTube API format for pipeline compatibility.
"""
import os
import re
import json
import time
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class TikTokVideoData:
    """Complete TikTok video data structure."""
    # Video identifiers
    video_id: str = ""
    url: str = ""
    
    # Statistics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    
    # Content info
    author: str = "Unknown"
    author_id: str = ""
    upload_date: Optional[str] = None
    title: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    
    # Comments (top comments by likes)
    top_comments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Extraction info
    source: str = "unknown"
    extraction_quality: str = "unknown"
    extracted_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TikTokUnifiedExtractor:
    """
    Unified TikTok extraction: metadata + comments in one session.
    
    Uses single Playwright browser instance for efficiency.
    Matches YouTube API response format.
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    
    def __init__(self):
        self.timeout_ms = int(os.getenv("TIKTOK_TIMEOUT_MS", "30000"))
        self.max_comments = int(os.getenv("TIKTOK_MAX_COMMENTS", "10"))
        self.max_retries = int(os.getenv("TIKTOK_MAX_RETRIES", "2"))
    
    async def extract(self, url: str, include_comments: bool = True) -> TikTokVideoData:
        """
        Extract complete TikTok video data.
        
        Args:
            url: TikTok video URL
            include_comments: Whether to extract comments (default: True)
        
        Returns:
            TikTokVideoData with metadata and optionally comments
        """
        print(f"🔍 TikTok unified extraction: {url[:60]}...")
        
        result = TikTokVideoData(
            url=url,
            video_id=self._extract_video_id(url) or "",
            author_id=self._extract_author_from_url(url),
            extracted_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        )
        
        # Try Playwright extraction
        for attempt in range(self.max_retries + 1):
            try:
                html, comments = await self._extract_with_playwright(url, include_comments)
                
                if html:
                    # Parse metadata from HTML
                    self._parse_metadata(html, result)
                    
                    # Add comments - try from JSON first, then DOM, then dedicated extractor
                    if include_comments:
                        # First try extracting comments from UNIVERSAL_DATA JSON
                        json_comments = self._extract_comments_from_json(html)
                        if json_comments:
                            result.top_comments = json_comments
                            print(f"💬 JSON comments: {len(json_comments)}")
                        elif comments:
                            result.top_comments = comments
                            print(f"💬 DOM comments: {len(comments)}")
                        
                        # If still no comments, try dedicated comment extractor
                        if not result.top_comments and result.view_count:
                            print("💬 Trying dedicated comment extractor...")
                            try:
                                from app.services.comment_extractor import extract_best_comments
                                dedicated_comments = await extract_best_comments(url, "tiktok", self.max_comments)
                                if dedicated_comments:
                                    result.top_comments = dedicated_comments
                                    print(f"💬 Dedicated extractor: {len(dedicated_comments)}")
                            except Exception as ce:
                                print(f"⚠️ Dedicated extractor failed: {ce}")
                    
                    if result.view_count or result.like_count:
                        print(f"✅ Extraction complete: views={result.view_count}, likes={result.like_count}, comments={len(result.top_comments)}")
                        return result
                
                if attempt < self.max_retries:
                    wait = (attempt + 1) * 2
                    print(f"⏳ Retry {attempt + 1}/{self.max_retries} in {wait}s...")
                    await asyncio.sleep(wait)
                    
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep((attempt + 1) * 2)
        
        print("⚠️ Extraction incomplete")
        return result
    
    async def _extract_with_playwright(self, url: str, include_comments: bool) -> tuple:
        """Extract using Playwright with cookies and stealth mode."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("⚠️ Playwright not installed")
            return None, []
        
        import random
        
        # Get cookie file
        cookie_file = self._get_cookie_file()
        
        html = None
        comments = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=VizDisplayCompositor",
                    ],
                )
                
                context_options = {
                    "user_agent": random.choice(self.USER_AGENTS),
                    "viewport": {"width": 1280, "height": 720},
                    "locale": "ko-KR",
                    "timezone_id": "Asia/Seoul",
                    "extra_http_headers": {
                        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
                        "dnt": "1",
                    },
                }
                
                # Add proxy if configured
                proxy_url = os.getenv("TIKTOK_PROXY")
                if proxy_url:
                    context_options["proxy"] = {"server": proxy_url}
                    print(f"🔀 Using proxy: {proxy_url}")
                
                context = await browser.new_context(**context_options)

                
                # Enhanced stealth
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
                    window.chrome = { runtime: {}, loadTimes: () => ({}) };
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
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
                    # Navigate and wait for content
                    wait_until = os.getenv("TIKTOK_WAIT_UNTIL", "domcontentloaded")
                    await page.goto(url, wait_until=wait_until, timeout=self.timeout_ms)
                    await page.wait_for_timeout(3000)
                    
                    # Get HTML for metadata
                    html = await page.content()
                    print(f"📄 HTML: {len(html)} bytes")
                    
                    # Extract comments if requested
                    if include_comments:
                        comments = await self._extract_comments_from_page(page)
                        print(f"💬 Comments: {len(comments)}")
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"⚠️ Playwright error: {e}")
        
        return html, comments
    
    async def _extract_comments_from_page(self, page) -> List[Dict]:
        """Extract comments from loaded page."""
        # Try to open comments panel
        for selector in ['[data-e2e="comment-icon"]', '[data-e2e="browse-comment"]']:
            try:
                loc = page.locator(selector)
                if await loc.first.is_visible(timeout=2000):
                    await loc.first.click(timeout=3000)
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                continue
        
        # Scroll to load more comments
        for _ in range(2):
            try:
                await page.mouse.wheel(0, 800)
                await page.wait_for_timeout(500)
            except Exception:
                break
        
        # Extract comments via JavaScript
        try:
            raw_comments = await page.evaluate("""(maxComments) => {
                const selectors = [
                    '[class*="DivCommentItemWrapper"]',
                    '[class*="CommentItem"]',
                    '[data-e2e="comment-item"]',
                    '[class*="Comment"]'
                ];
                
                let elements = [];
                for (const sel of selectors) {
                    const found = Array.from(document.querySelectorAll(sel));
                    if (found.length) { elements = found; break; }
                }
                
                const getText = (el, sels) => {
                    for (const s of sels) {
                        const n = el.querySelector(s);
                        if (n?.textContent?.trim()) return n.textContent.trim();
                    }
                    return "";
                };
                
                const results = [];
                for (const el of elements) {
                    if (results.length >= maxComments) break;
                    const text = getText(el, ['[data-e2e="comment-text"]', 'p', '[class*="content"]']);
                    if (!text || text.length < 5) continue;
                    results.push({
                        text,
                        author: getText(el, ['[data-e2e="comment-username"]', 'strong', '[class*="author"]']),
                        likes_text: getText(el, ['[data-e2e="comment-like-count"]', '[class*="like"]'])
                    });
                }
                return results;
            }""", self.max_comments * 2)
            
            # Parse and format comments
            comments = []
            for item in raw_comments:
                text = item.get('text', '').strip()
                if not text or len(text) < 5:
                    continue
                
                likes = self._parse_count(item.get('likes_text', ''))
                comments.append({
                    'text': text,
                    'author': item.get('author', ''),
                    'likes': likes,
                    'lang': self._detect_language(text),
                })
            
            # Sort by likes and limit
            comments.sort(key=lambda x: x['likes'], reverse=True)
            return comments[:self.max_comments]
            
        except Exception as e:
            print(f"⚠️ Comment extraction error: {e}")
            return []
    
    def _parse_metadata(self, html: str, result: TikTokVideoData):
        """Parse metadata from HTML."""
        # Strategy 1: UNIVERSAL_DATA JSON
        if self._parse_universal_data(html, result):
            return
        
        # Strategy 2: SIGI_STATE JSON
        if self._parse_sigi_state(html, result):
            return
        
        # Strategy 3: DOM patterns
        self._parse_dom_patterns(html, result)
    
    def _parse_universal_data(self, html: str, result: TikTokVideoData) -> bool:
        """Parse UNIVERSAL_DATA JSON."""
        pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\s\S]*?)</script>'
        match = re.search(pattern, html, re.IGNORECASE)
        
        if not match:
            return False
        
        try:
            data = json.loads(match.group(1).strip())
            video_detail = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {})
            item = video_detail.get('itemInfo', {}).get('itemStruct', {})
            
            if not item:
                return False
            
            stats = item.get('stats', {})
            author = item.get('author', {})
            
            result.view_count = self._parse_count(stats.get('playCount'))
            result.like_count = self._parse_count(stats.get('diggCount'))
            result.comment_count = self._parse_count(stats.get('commentCount'))
            result.share_count = self._parse_count(stats.get('shareCount'))
            result.author = author.get('nickname') or author.get('uniqueId') or result.author
            result.author_id = author.get('uniqueId') or result.author_id
            
            # Upload date
            create_time = item.get('createTime')
            if create_time:
                try:
                    result.upload_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(int(create_time)))
                except (ValueError, TypeError):
                    pass
            
            # Title/description
            result.title = item.get('desc', '')
            
            # Hashtags
            challenges = item.get('challenges', [])
            if isinstance(challenges, list):
                result.hashtags = [f"#{c.get('title', '')}" for c in challenges if c.get('title')]
            if not result.hashtags and result.title:
                result.hashtags = re.findall(r'#\w+', result.title)
            
            result.source = 'universal_data'
            result.extraction_quality = 'complete'
            
            print("✅ UNIVERSAL_DATA parsed")
            return True
            
        except Exception as e:
            print(f"⚠️ UNIVERSAL_DATA error: {e}")
            return False
    
    def _extract_comments_from_json(self, html: str) -> List[Dict]:
        """Extract comments from UNIVERSAL_DATA JSON (preloaded comments)."""
        pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\s\S]*?)</script>'
        match = re.search(pattern, html, re.IGNORECASE)
        
        if not match:
            return []
        
        try:
            data = json.loads(match.group(1).strip())
            video_detail = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {})
            
            # Try to find comments in different locations
            comments_data = None
            
            # Location 1: itemInfo.commentList
            comments_data = video_detail.get('commentList', [])
            
            # Location 2: itemInfo.itemStruct.comments (older format)
            if not comments_data:
                item = video_detail.get('itemInfo', {}).get('itemStruct', {})
                comments_data = item.get('comments', [])
            
            # Location 3: Search for comment-like structures
            if not comments_data:
                # Try searching in the entire JSON for comment arrays
                def find_comments(obj, depth=0):
                    if depth > 5:
                        return []
                    if isinstance(obj, list):
                        for item in obj:
                            if isinstance(item, dict) and 'text' in item and ('user' in item or 'author' in item):
                                return obj
                            result = find_comments(item, depth + 1)
                            if result:
                                return result
                    elif isinstance(obj, dict):
                        if 'comments' in obj and isinstance(obj['comments'], list):
                            return obj['comments']
                        for value in obj.values():
                            result = find_comments(value, depth + 1)
                            if result:
                                return result
                    return []
                
                comments_data = find_comments(data)
            
            if not comments_data:
                return []
            
            comments = []
            for item in comments_data[:self.max_comments * 2]:
                if not isinstance(item, dict):
                    continue
                
                text = item.get('text', '').strip()
                if not text or len(text) < 3:
                    continue
                
                # Get author info
                user = item.get('user', {}) or item.get('author', {})
                if isinstance(user, str):
                    author = user
                else:
                    author = user.get('nickname') or user.get('uniqueId') or user.get('username', '')
                
                # Get like count
                likes = item.get('diggCount', 0) or item.get('likes', 0) or item.get('likeCount', 0)
                
                comments.append({
                    'text': text,
                    'author': author,
                    'likes': self._parse_count(likes),
                    'lang': self._detect_language(text),
                })
            
            # Sort by likes
            comments.sort(key=lambda x: x['likes'], reverse=True)
            return comments[:self.max_comments]
            
        except Exception as e:
            print(f"⚠️ JSON comment extraction error: {e}")
            return []
    
    def _parse_sigi_state(self, html: str, result: TikTokVideoData) -> bool:
        """Parse SIGI_STATE JSON."""
        pattern = r'<script id="SIGI_STATE"[^>]*>([\s\S]*?)</script>'
        match = re.search(pattern, html, re.IGNORECASE)
        
        if not match:
            return False
        
        try:
            data = json.loads(match.group(1).strip())
            item_module = data.get('ItemModule', {})
            
            if result.video_id and result.video_id in item_module:
                item = item_module[result.video_id]
            elif item_module:
                item = next(iter(item_module.values()))
            else:
                return False
            
            stats = item.get('stats', {})
            
            result.view_count = self._parse_count(stats.get('playCount'))
            result.like_count = self._parse_count(stats.get('diggCount'))
            result.comment_count = self._parse_count(stats.get('commentCount'))
            result.share_count = self._parse_count(stats.get('shareCount'))
            result.title = item.get('desc', '')
            result.source = 'sigi_state'
            result.extraction_quality = 'complete'
            
            print("✅ SIGI_STATE parsed")
            return True
            
        except Exception:
            return False
    
    def _parse_dom_patterns(self, html: str, result: TikTokVideoData):
        """Parse using DOM patterns."""
        patterns = {
            'view_count': [r'"playCount":(\d+)', r'"view_count":(\d+)'],
            'like_count': [r'"diggCount":(\d+)', r'"digg_count":(\d+)'],
            'comment_count': [r'"commentCount":(\d+)'],
            'share_count': [r'"shareCount":(\d+)'],
        }
        
        for field, pats in patterns.items():
            for pat in pats:
                match = re.search(pat, html)
                if match:
                    setattr(result, field, self._parse_count(match.group(1)))
                    break
        
        if result.view_count or result.like_count:
            result.source = 'dom_patterns'
            result.extraction_quality = 'partial'
    
    def _get_cookie_file(self) -> Optional[str]:
        """Get cookie file path."""
        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")
        if cookie_file and os.path.exists(cookie_file):
            return cookie_file
        
        base_dir = Path(__file__).parent.parent.parent
        auto_cookie = base_dir / "tiktok_cookies_auto.json"
        if auto_cookie.exists():
            return str(auto_cookie)
        
        return None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None
    
    def _extract_author_from_url(self, url: str) -> str:
        match = re.search(r'@([^/]+)', url)
        return match.group(1) if match else ""
    
    def _parse_count(self, value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        
        s = str(value).strip().upper().replace(',', '')
        if not s:
            return 0
        
        try:
            if 'K' in s:
                return int(float(s.replace('K', '')) * 1000)
            elif 'M' in s:
                return int(float(s.replace('M', '')) * 1_000_000)
            elif 'B' in s:
                return int(float(s.replace('B', '')) * 1_000_000_000)
            return int(float(s))
        except (ValueError, TypeError):
            return 0
    
    def _detect_language(self, text: str) -> str:
        if not text:
            return "unknown"
        
        korean_chars = len(re.findall(r'[\uAC00-\uD7AF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if korean_chars > english_chars:
            return "ko"
        elif english_chars > 0:
            return "en"
        return "other"


# Singleton instance
tiktok_extractor = TikTokUnifiedExtractor()


async def extract_tiktok_complete(url: str, include_comments: bool = True) -> Dict[str, Any]:
    """
    Extract complete TikTok data (metadata + comments).
    
    Returns dict with:
    - video_id, url
    - view_count, like_count, comment_count, share_count
    - author, author_id, upload_date, title, hashtags
    - top_comments (list of {text, author, likes, lang})
    - source, extraction_quality, extracted_at
    """
    result = await tiktok_extractor.extract(url, include_comments)
    return result.to_dict()
