"""
Comment Extractor Service
Extracts best comments from YouTube/TikTok/Instagram for viral analysis context.

Uses multiple approaches:
- YouTube: YouTube Data API v3 (best quality)
- TikTok/Instagram: yt-dlp with --write-comments (universal)
"""
import os
import re
import json
import time
import tempfile
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from pathlib import Path

# Try to import YouTube API
try:
    from googleapiclient.discovery import build
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False


class CommentExtractor:
    """
    Extracts best comments from video platforms.
    
    Supported platforms:
    - YouTube: via YouTube Data API v3 (priority) or yt-dlp fallback
    - TikTok: via comment/list API (Playwright capture) -> yt-dlp -> Playwright DOM
    - Instagram: via yt-dlp --write-comments
    """
    
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._youtube_service = None
    
    @property
    def youtube_service(self):
        """Lazy init YouTube service"""
        if not self._youtube_service and YOUTUBE_API_AVAILABLE and self.youtube_api_key:
            self._youtube_service = build("youtube", "v3", developerKey=self.youtube_api_key)
        return self._youtube_service
    
    async def extract_best_comments(
        self,
        video_url: str,
        platform: str,
        limit: int = 10,
        method: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract top comments by likes from video.
        
        Returns:
            List of comments: [{"text": "...", "likes": 123, "lang": "en", ...}, ...]
        """
        platform = platform.lower()

        if platform == "tiktok" and ("vt.tiktok.com" in video_url or "vm.tiktok.com" in video_url):
            try:
                from app.services.social_metadata import normalize_url
                normalized = normalize_url(video_url, expand_short=True)
                video_url = normalized.get("canonical_url") or video_url
            except Exception:
                pass
        
        method = (method or os.getenv("TIKTOK_COMMENTS_PROVIDER", "auto")).lower()

        # YouTube: prefer API if available
        if platform == "youtube" and self.youtube_service:
            comments = await self._extract_youtube_api(video_url, limit)
            if comments:
                return comments

        # TikTok: Playwright (with auto-cookie) → yt-dlp fallback
        if platform == "tiktok":
            env_limit = os.getenv("TIKTOK_MAX_COMMENTS")
            if env_limit:
                try:
                    limit = min(limit, int(env_limit))
                except ValueError:
                    pass
            # 명시적 method 지정 시
            if method == "playwright":
                return await self._extract_tiktok_playwright(video_url, limit)
            if method == "ytdlp":
                return await self._extract_via_ytdlp(video_url, platform, limit)
            if method == "comment_list":
                return await self._extract_tiktok_comment_list(video_url, limit)

            # Auto mode: Playwright (optimized) → yt-dlp
            comments = await self._extract_tiktok_playwright(video_url, limit)
            if comments:
                return comments
            
            # Fallback to yt-dlp
            comments = await self._extract_via_ytdlp(video_url, platform, limit)
            if comments:
                return comments
            
            return []

        # Universal fallback: yt-dlp for Instagram and others
        return await self._extract_via_ytdlp(video_url, platform, limit)
    
    def _prioritize_by_language(
        self, 
        comments: List[Dict], 
        preferred_langs: List[str] = ["ko", "en"],
        limit: int = 10
    ) -> List[Dict]:
        """
        Sort comments by language preference: ko > en > others.
        Within same language priority, sort by likes.
        
        This ensures Korean and English comments appear first,
        avoiding situations where Russian/Thai/etc comments dominate.
        """
        def lang_priority(c: Dict) -> tuple:
            lang = c.get("lang", "unknown")
            if lang in preferred_langs:
                priority = preferred_langs.index(lang)
            else:
                priority = 999  # Other languages go last
            likes = c.get("likes", 0)
            return (priority, -likes)  # Lower priority first, then higher likes
        
        sorted_comments = sorted(comments, key=lang_priority)
        return sorted_comments[:limit]
    
    
    async def _extract_youtube_api(self, video_url: str, limit: int) -> List[Dict]:
        """Extract YouTube comments via Data API v3"""
        video_id = self._extract_youtube_video_id(video_url)
        if not video_id:
            return []
        
        try:
            response = self.youtube_service.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=limit * 2,
                order="relevance",
                textFormat="plainText"
            ).execute()
            
            comments = []
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "text": snippet["textDisplay"],
                    "likes": snippet.get("likeCount", 0),
                    "author": snippet.get("authorDisplayName", ""),
                    "lang": self._detect_language(snippet["textDisplay"]),
                    "source": "youtube_api"
                })
            
            comments.sort(key=lambda x: x["likes"], reverse=True)
            # Apply language prioritization (ko > en > others)
            return self._prioritize_by_language(comments, limit=limit)
            
        except Exception as e:
            print(f"⚠️ YouTube API failed, falling back to yt-dlp: {e}")
            return []
    
    async def _extract_via_ytdlp(self, video_url: str, platform: str, limit: int) -> List[Dict]:
        """
        Extract comments using yt-dlp --write-comments
        
        Works for:
        - TikTok
        - Instagram Reels
        - YouTube (fallback)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "%(id)s")
            info_file = None
            
            try:
                # Run yt-dlp with comment extraction
                cmd = [
                    "yt-dlp",
                    "--skip-download",  # Don't download video
                    "--write-comments",  # Extract comments
                    "--write-info-json",  # Write metadata to JSON
                    "--no-warnings",
                    "-o", output_template,
                    video_url
                ]

                cookie_file = os.getenv("YTDLP_COOKIE_FILE")
                if cookie_file:
                    cmd.extend(["--cookies", cookie_file])

                cookie_browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER")
                if cookie_browser:
                    cmd.extend(["--cookies-from-browser", cookie_browser])

                user_agent = os.getenv("YTDLP_USER_AGENT")
                if user_agent:
                    cmd.extend(["--user-agent", user_agent])
                
                print(f"📝 Extracting comments for {platform}: {video_url[:50]}...")
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=60
                )
                
                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    print(f"⚠️ yt-dlp comment extraction failed: {error_msg[:200]}")
                    return []
                
                # Find the info.json file
                json_files = list(Path(tmpdir).glob("*.info.json"))
                if not json_files:
                    print("⚠️ No info.json generated")
                    return []
                
                info_file = json_files[0]
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                
                # Extract comments from info.json
                raw_comments = info.get("comments", [])
                if not raw_comments:
                    print(f"ℹ️ No comments found for {platform} video")
                    return []
                
                # Parse and sort by likes
                comments = []
                for c in raw_comments:
                    comments.append({
                        "text": c.get("text", ""),
                        "likes": c.get("like_count", 0) or 0,
                        "author": c.get("author", "") or c.get("author_id", ""),
                        "lang": self._detect_language(c.get("text", "")),
                        "source": f"ytdlp_{platform}"
                    })
                
                # Sort by likes (highest first) and apply language prioritization
                comments.sort(key=lambda x: x["likes"], reverse=True)
                result = self._prioritize_by_language(comments, limit=limit)
                
                print(f"✅ Extracted {len(result)} best comments from {platform}")
                return result
                
            except asyncio.TimeoutError:
                print(f"⚠️ yt-dlp comment extraction timed out")
                return []
            except Exception as e:
                print(f"❌ Comment extraction error: {e}")
                return []

    def _parse_count(self, value: str) -> int:
        """Parse social count strings like 1.2K/3.4M into ints."""
        if not value:
            return 0
        raw = value.strip().upper()
        try:
            if raw.endswith("K"):
                return int(float(raw[:-1]) * 1_000)
            if raw.endswith("M"):
                return int(float(raw[:-1]) * 1_000_000)
            if raw.endswith("B"):
                return int(float(raw[:-1]) * 1_000_000_000)
            return int(re.sub(r"[^\d]", "", raw) or 0)
        except ValueError:
            return 0

    async def _extract_tiktok_playwright(self, video_url: str, limit: int) -> List[Dict]:
        """
        Extract TikTok comments using Playwright DOM scraping.
        
        Production features:
        - Proxy support (TIKTOK_PROXY env var)
        - User-Agent rotation
        - Enhanced stealth mode
        - Automatic cookie refresh
        - Retry logic with exponential backoff
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("⚠️ Playwright not installed")
            return []

        import random
        
        # Config
        timeout_ms = int(os.getenv("TIKTOK_PLAYWRIGHT_TIMEOUT_MS", "30000"))
        wait_ms = int(os.getenv("TIKTOK_PLAYWRIGHT_WAIT_MS", "3000"))
        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")
        max_retries = int(os.getenv("TIKTOK_MAX_RETRIES", "2"))
        proxy_url = os.getenv("TIKTOK_PROXY")  # e.g., "http://user:pass@host:port"
        
        # User-Agent rotation for anti-fingerprinting
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
        
        # Auto-refresh cookies from browser if available
        if not cookie_file or not os.path.exists(cookie_file):
            cookie_file = await self._try_export_chrome_cookies()

        async def _attempt_extraction():
            async with async_playwright() as p:
                # Browser launch options
                launch_options = {
                    "headless": True,
                    "args": [
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-blink-features=AutomationControlled",
                    ],
                }
                
                # Add proxy if configured
                if proxy_url:
                    launch_options["proxy"] = {"server": proxy_url}
                
                browser = await p.chromium.launch(**launch_options)
                
                # Context with rotating User-Agent
                context = await browser.new_context(
                    user_agent=random.choice(user_agents),
                    viewport={"width": 1280, "height": 720},
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                    extra_http_headers={
                        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                        "dnt": "1",
                    },
                )
                
                # Enhanced stealth mode
                await context.add_init_script("""
                    // Hide webdriver
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    
                    // Realistic languages
                    Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
                    
                    // Chrome runtime
                    window.chrome = { runtime: {}, loadTimes: () => ({}) };
                    
                    // Plugin count
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    
                    // Hardware concurrency
                    Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                    
                    // Device memory
                    Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                    
                    // Permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                """)
                
                # Load cookies if available
                if cookie_file and os.path.exists(cookie_file):
                    try:
                        with open(cookie_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        cookies = data.get("cookies", data) if isinstance(data, dict) else data
                        if isinstance(cookies, list) and cookies:
                            await context.add_cookies(cookies)
                    except Exception:
                        pass

                try:
                    page = await context.new_page()
                    wait_until = os.getenv("TIKTOK_COMMENT_WAIT_UNTIL", "domcontentloaded")
                    await page.goto(video_url, wait_until=wait_until, timeout=timeout_ms)
                    await page.wait_for_timeout(wait_ms)
                    
                    # Try to click comment icon
                    for sel in ['[data-e2e="comment-icon"]', '[data-e2e="browse-comment"]']:
                        try:
                            loc = page.locator(sel)
                            if await loc.first.is_visible(timeout=2000):
                                await loc.first.click(timeout=3000)
                                await page.wait_for_timeout(1500)
                                break
                        except Exception:
                            continue
                    
                    # Scroll to load comments
                    for _ in range(2):
                        await page.mouse.wheel(0, 800)
                        await page.wait_for_timeout(500)
                    
                    # Extract comments
                    raw_comments = await page.evaluate("""(limit) => {
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
                            if (results.length >= limit) break;
                            const text = getText(el, ['[data-e2e="comment-text"]', 'p', '[class*="content"]']);
                            if (!text) continue;
                            results.push({
                                text,
                                author: getText(el, ['[data-e2e="comment-username"]', 'strong', '[class*="author"]']),
                                likes_text: getText(el, ['[data-e2e="comment-like-count"]', '[class*="like"]'])
                            });
                        }
                        return results;
                    }""", limit * 2)
                    
                    return raw_comments
                finally:
                    await browser.close()
        
        # Retry logic
        for attempt in range(max_retries + 1):
            try:
                raw_comments = await _attempt_extraction()
                if raw_comments:
                    comments = []
                    for item in raw_comments:
                        text = item.get("text", "").strip()
                        if not text:
                            continue
                        comments.append({
                            "text": text,
                            "likes": self._parse_count(item.get("likes_text", "")),
                            "author": item.get("author", ""),
                            "lang": self._detect_language(text),
                            "source": "playwright_tiktok",
                        })
                    
                    if comments:
                        comments.sort(key=lambda x: x["likes"], reverse=True)
                        return self._prioritize_by_language(comments, limit=limit)
                
                if attempt < max_retries:
                    wait = (attempt + 1) * 2
                    print(f"⏳ Retry {attempt + 1}/{max_retries} in {wait}s...")
                    await asyncio.sleep(wait)
                    
            except Exception as e:
                if attempt < max_retries:
                    print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep((attempt + 1) * 2)
                else:
                    print(f"⚠️ All attempts failed: {e}")
        
        return []
    
    async def _try_export_chrome_cookies(self) -> Optional[str]:
        """
        Export TikTok cookies from installed browsers.
        
        Features:
        - Tries Chrome → Edge → Firefox in order
        - Tracks cookie age (refreshes if > 1 hour old)
        - Saves with metadata for session management
        """
        base_dir = Path(__file__).parent.parent.parent
        cookie_path = base_dir / "tiktok_cookies_auto.json"
        
        # Check if existing cookies are still fresh (< 1 hour old)
        if cookie_path.exists():
            try:
                with open(cookie_path, 'r') as f:
                    data = json.load(f)
                
                # Check metadata
                if isinstance(data, dict) and data.get("metadata"):
                    exported_at = data["metadata"].get("exported_at", 0)
                    age_hours = (time.time() - exported_at) / 3600
                    
                    if age_hours < 1.0:  # Fresh cookies < 1 hour old
                        cookies = data.get("cookies", [])
                        if cookies:
                            return str(cookie_path)
            except Exception:
                pass
        
        # Export fresh cookies from browsers
        try:
            import browser_cookie3
        except ImportError:
            return None
        
        cookie_list = []
        source_browser = None
        
        # Try multiple browsers in order
        browsers = [
            ("chrome", browser_cookie3.chrome),
            ("edge", browser_cookie3.edge),
            ("firefox", browser_cookie3.firefox),
        ]
        
        for browser_name, browser_func in browsers:
            try:
                cookies = browser_func(domain_name='.tiktok.com')
                for c in cookies:
                    cookie_list.append({
                        'name': c.name,
                        'value': c.value,
                        'domain': c.domain,
                        'path': c.path,
                        'secure': bool(c.secure),
                        'httpOnly': False,
                        'sameSite': 'Lax'
                    })
                
                if cookie_list:
                    source_browser = browser_name
                    break
            except Exception:
                continue
        
        if not cookie_list:
            return None
        
        # Save with metadata
        import time
        data = {
            "metadata": {
                "exported_at": time.time(),
                "source": source_browser,
                "count": len(cookie_list),
            },
            "cookies": cookie_list
        }
        
        with open(cookie_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Exported {len(cookie_list)} TikTok cookies from {source_browser}")
        return str(cookie_path)
    
    def get_cookie_status(self) -> Dict[str, Any]:
        """Get status of current TikTok cookie file."""
        base_dir = Path(__file__).parent.parent.parent
        cookie_path = base_dir / "tiktok_cookies_auto.json"
        
        if not cookie_path.exists():
            return {"status": "missing", "cookie_file": str(cookie_path)}
        
        try:
            with open(cookie_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and data.get("metadata"):
                metadata = data["metadata"]
                import time
                age_seconds = time.time() - metadata.get("exported_at", 0)
                age_hours = age_seconds / 3600
                
                return {
                    "status": "fresh" if age_hours < 1.0 else "stale",
                    "age_hours": round(age_hours, 2),
                    "source": metadata.get("source"),
                    "count": metadata.get("count"),
                    "cookie_file": str(cookie_path),
                    "needs_refresh": age_hours >= 1.0,
                }
            else:
                # Legacy format without metadata
                cookies = data if isinstance(data, list) else data.get("cookies", [])
                return {
                    "status": "legacy",
                    "count": len(cookies),
                    "cookie_file": str(cookie_path),
                    "needs_refresh": True,
                }
        except Exception as e:
            return {"status": "error", "error": str(e), "cookie_file": str(cookie_path)}

    async def _extract_tiktok_comment_list(self, video_url: str, limit: int) -> List[Dict]:
        """
        Extract TikTok comments by capturing the comment/list API response via Playwright.
        
        2025-12-27 개선:
        - API 응답 수집 방식 개선 (page.on("response") 사용)
        - 스크롤 전략 개선
        - 다양한 쿠키/세션 지원
        
        API Endpoint: /api/comment/list/
        Required params: aweme_id, cursor, count, aid
        Response: { comments: [{ text, digg_count, user: { unique_id, nickname } }, ...] }
        """
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            print(f"⚠️ Playwright not available for TikTok comment list: {exc}")
            return []

        timeout_sec = int(os.getenv("TIKTOK_PLAYWRIGHT_TIMEOUT_SEC", "60"))
        wait_sec = int(os.getenv("TIKTOK_PLAYWRIGHT_WAIT_SEC", "5"))
        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")
        user_data_dir = os.getenv("TIKTOK_PLAYWRIGHT_USER_DATA_DIR")
        channel = os.getenv("TIKTOK_PLAYWRIGHT_CHANNEL")
        headless = os.getenv("TIKTOK_PLAYWRIGHT_HEADFUL", "false").lower() not in ("1", "true", "yes")
        proxy_url = os.getenv("TIKTOK_PROXY")

        async def _load_cookies(path: Optional[str]) -> List[Dict[str, Any]]:
            if not path or not os.path.exists(path):
                return []
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "cookies" in data:
                    return data["cookies"]
                if isinstance(data, list):
                    return data
            except Exception as exc:
                print(f"⚠️ Failed to read TikTok cookie file: {exc}")
            return []

        # 수집된 댓글 저장
        collected_comments = []

        # First try direct comment/list API with cookies (faster, no UI needed)
        import httpx
        aweme_match = re.search(r"/video/(\d+)", video_url)
        aweme_id = aweme_match.group(1) if aweme_match else None
        cookies = await _load_cookies(cookie_file)
        cookie_jar = {c.get("name"): c.get("value") for c in cookies if c.get("name") and c.get("value")}
        
        if cookie_jar:
            print(f"✅ Loaded {len(cookie_jar)} TikTok cookies")
        else:
            print("⚠️ No TikTok cookies available")

        if aweme_id:
            headers = {
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "referer": "https://www.tiktok.com/",
                "accept": "application/json",
            }
            params = {
                "aweme_id": aweme_id,
                "cursor": 0,
                "count": min(limit, 20),
                "aid": 1988,
            }
            if "msToken" in cookie_jar:
                params["msToken"] = cookie_jar["msToken"]

            if proxy_url:
                print(f"🔀 Using proxy for comment list: {proxy_url}")

            # Retry logic with exponential backoff
            max_retries = int(os.getenv("TIKTOK_API_MAX_RETRIES", "3"))
            
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(
                        headers=headers,
                        cookies=cookie_jar or None,
                        timeout=timeout_sec,
                        follow_redirects=True,
                        proxy=proxy_url if proxy_url else None,
                    ) as client:
                        cursor = 0
                        has_more = True
                        while has_more and len(collected_comments) < limit:
                            params["cursor"] = cursor
                            params["count"] = min(limit - len(collected_comments), 20)
                            resp = await client.get("https://www.tiktok.com/api/comment/list/", params=params)
                            
                            # Validate response is JSON (not HTML challenge)
                            content_type = resp.headers.get("content-type", "")
                            if "application/json" not in content_type:
                                print(f"⚠️ TikTok returned non-JSON response: {content_type[:50]}")
                                print(f"   Response preview: {resp.text[:200]}...")
                                raise ValueError(f"Expected JSON, got {content_type}")
                            
                            try:
                                data = resp.json()
                            except Exception as e:
                                print(f"⚠️ Failed to parse comment/list response: {e}")
                                raise
                            
                            if data.get("status_code") not in (0, None):
                                print(f"⚠️ TikTok API error: status_code={data.get('status_code')}")
                                break
                            
                            comments = data.get("comments") or []
                            for item in comments:
                                text = item.get("text") or item.get("share_info", {}).get("desc") or ""
                                if not text:
                                    continue
                                user = item.get("user") or {}
                                author = user.get("unique_id") or user.get("nickname") or ""
                                likes = (
                                    item.get("digg_count")
                                    or item.get("like_count")
                                    or item.get("diggCount")
                                    or 0
                                )
                                collected_comments.append({
                                    "text": text,
                                    "likes": likes,
                                    "author": author,
                                    "lang": self._detect_language(text),
                                    "source": "tiktok_comment_list_api",
                                })
                            has_more = bool(data.get("has_more"))
                            cursor = data.get("cursor", cursor + params["count"])

                    if collected_comments:
                        collected_comments.sort(key=lambda x: x["likes"], reverse=True)
                        result = self._prioritize_by_language(collected_comments, limit=limit)
                        print(f"✅ TikTok comment list API: {len(result)} comments")
                        return result
                    break  # No comments but no error, don't retry
                    
                except (httpx.RequestError, ValueError) as exc:
                    wait_time = (2 ** attempt) + 1  # 2, 3, 5 seconds
                    print(f"⚠️ TikTok API attempt {attempt + 1}/{max_retries} failed: {exc}")
                    if attempt < max_retries - 1:
                        print(f"   Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"❌ TikTok comment list API failed after {max_retries} attempts")
                        

        async def handle_response(response):
            """API 응답 핸들러 - comment/list 응답 캡처"""
            try:
                if "api/comment/list" in response.url:
                    try:
                        data = await response.json()
                        comments = data.get("comments") or data.get("data", {}).get("comments") or []
                        for item in comments:
                            text = item.get("text") or item.get("share_info", {}).get("desc") or ""
                            if not text:
                                continue
                            user = item.get("user") or {}
                            author = user.get("unique_id") or user.get("nickname") or ""
                            likes = (
                                item.get("digg_count")
                                or item.get("like_count")
                                or item.get("diggCount")
                                or 0
                            )
                            collected_comments.append({
                                "text": text,
                                "likes": likes,
                                "author": author,
                                "lang": self._detect_language(text),
                                "source": "tiktok_comment_list_v2",
                            })
                        print(f"📝 Captured {len(comments)} comments from TikTok API")
                    except Exception as e:
                        print(f"⚠️ Failed to parse comment/list response: {e}")
            except Exception:
                pass

        try:
            async with async_playwright() as p:
                browser = None
                if user_data_dir:
                    if proxy_url:
                        print(f"🔀 Using proxy for comment list: {proxy_url}")
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir,
                        headless=headless,
                        channel=channel or None,
                        proxy={"server": proxy_url} if proxy_url else None,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-web-security",
                            "--disable-features=VizDisplayCompositor",
                        ],
                        viewport={"width": 1280, "height": 720},
                        locale="ko-KR",
                    )
                else:
                    launch_options = {
                        "headless": headless,
                        "channel": channel or None,
                        "args": [
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-web-security",
                            "--disable-features=VizDisplayCompositor",
                        ],
                    }
                    if proxy_url:
                        print(f"🔀 Using proxy for comment list: {proxy_url}")
                        launch_options["proxy"] = {"server": proxy_url}
                    browser = await p.chromium.launch(**launch_options)
                    context = await browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                        viewport={"width": 1280, "height": 720},
                        locale="ko-KR",
                    )

                # Stealth mode 설정
                try:
                    await context.add_init_script(
                        """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                        window.chrome = { runtime: {} };
                        """
                    )
                except Exception:
                    pass

                # 쿠키 로드
                cookies = await _load_cookies(cookie_file)
                if cookies:
                    try:
                        await context.add_cookies(cookies)
                        print(f"✅ Loaded {len(cookies)} TikTok cookies")
                    except Exception as exc:
                        print(f"⚠️ Failed to add TikTok cookies: {exc}")

                page = await context.new_page()
                
                # API 응답 핸들러 등록
                page.on("response", handle_response)
                
                # 페이지 로드
                print(f"🌐 Loading TikTok page: {video_url[:60]}...")
                await page.goto(video_url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
                await page.wait_for_timeout(wait_sec * 1000)

                # 모달 닫기 시도
                for modal_selector in [
                    'button:has-text("나중에")',
                    'button:has-text("Not now")',
                    '[data-e2e="modal-close-inner-button"]',
                    'button[aria-label="Close"]',
                ]:
                    try:
                        locator = page.locator(modal_selector)
                        if await locator.first.is_visible(timeout=2000):
                            await locator.first.click(timeout=3000)
                            await page.wait_for_timeout(500)
                            break
                    except Exception:
                        continue

                # 댓글 버튼 클릭
                for selector in [
                    '[data-e2e="comment-icon"]',
                    '[data-e2e="browse-comment"]',
                    'button[aria-label*="Comment"]',
                    'button[aria-label*="댓글"]',
                    'button:has-text("Comments")',
                    'button:has-text("댓글")',
                ]:
                    try:
                        locator = page.locator(selector)
                        if await locator.first.is_visible(timeout=2000):
                            await locator.first.click(timeout=3000)
                            await page.wait_for_timeout(2000)
                            print(f"✅ Clicked comment button: {selector}")
                            break
                    except Exception:
                        continue

                # 스크롤로 더 많은 댓글 로드 (최대 5회)
                for i in range(5):
                    try:
                        await page.mouse.wheel(0, 2000)
                        await page.wait_for_timeout(1500)
                        print(f"📜 Scrolled comments ({i+1}/5), collected: {len(collected_comments)}")
                        if len(collected_comments) >= limit:
                            break
                    except Exception:
                        break

                # 정리
                if browser:
                    await browser.close()
                else:
                    await context.close()

                # 결과 정렬 및 반환
                if collected_comments:
                    collected_comments.sort(key=lambda x: x["likes"], reverse=True)
                    result = self._prioritize_by_language(collected_comments, limit=limit)
                    print(f"✅ TikTok comment extraction complete: {len(result)} comments")
                    return result
                else:
                    print("⚠️ No comments captured from TikTok API")
                    return []

        except Exception as exc:
            print(f"⚠️ TikTok comment/list extraction failed: {exc}")
            return []
    
    
    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character ranges"""
        if not text:
            return "unknown"
        # Korean
        if any('\uAC00' <= char <= '\uD7A3' for char in text):
            return "ko"
        # Japanese
        if any('\u3040' <= char <= '\u30FF' for char in text):
            return "ja"
        # Chinese
        if any('\u4E00' <= char <= '\u9FFF' for char in text):
            return "zh"
        # Thai
        if any('\u0E00' <= char <= '\u0E7F' for char in text):
            return "th"
        # Arabic
        if any('\u0600' <= char <= '\u06FF' for char in text):
            return "ar"
        return "en"


# Singleton instance
comment_extractor = CommentExtractor()


async def extract_best_comments(
    video_url: str,
    platform: str,
    limit: int = 10,
    method: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to extract best comments.
    
    Supported platforms: youtube, tiktok, instagram
    
    Usage:
        comments = await extract_best_comments(
            "https://www.tiktok.com/@user/video/123",
            "tiktok",
            limit=10
        )
    """
    return await comment_extractor.extract_best_comments(video_url, platform, limit, method=method)
