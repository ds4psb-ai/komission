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
import tempfile
import asyncio
from typing import List, Optional, Dict, Any
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

        # TikTok: try multiple methods (comment/list -> yt-dlp -> playwright)
        if platform == "tiktok":
            if method == "comment_list":
                return await self._extract_tiktok_comment_list(video_url, limit)
            if method == "ytdlp":
                return await self._extract_via_ytdlp(video_url, platform, limit)
            if method == "playwright":
                return await self._extract_tiktok_playwright(video_url, limit)

            comments = await self._extract_tiktok_comment_list(video_url, limit)
            if comments:
                return comments
            comments = await self._extract_via_ytdlp(video_url, platform, limit)
            if comments:
                return comments
            return await self._extract_tiktok_playwright(video_url, limit)

        # Universal fallback: yt-dlp for Instagram and others
        return await self._extract_via_ytdlp(video_url, platform, limit)
    
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
            return comments[:limit]
            
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
                
                # Sort by likes (highest first) and take top N
                comments.sort(key=lambda x: x["likes"], reverse=True)
                result = comments[:limit]
                
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
        Extract TikTok comments using Playwright (legacy fallback).
        Requires playwright + chromium installed.
        """
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            print(f"⚠️ Playwright not available for TikTok comments: {exc}")
            return []

        timeout_sec = int(os.getenv("TIKTOK_PLAYWRIGHT_TIMEOUT_SEC", "45"))
        wait_sec = int(os.getenv("TIKTOK_PLAYWRIGHT_WAIT_SEC", "4"))
        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                    ],
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 720},
                )

                if cookie_file and os.path.exists(cookie_file):
                    try:
                        with open(cookie_file, "r", encoding="utf-8") as f:
                            cookies = json.load(f)
                        if isinstance(cookies, list):
                            await context.add_cookies(cookies)
                    except Exception as exc:
                        print(f"⚠️ Failed to load TikTok cookies: {exc}")

                page = await context.new_page()
                await page.goto(video_url, wait_until="networkidle", timeout=timeout_sec * 1000)
                await page.wait_for_timeout(wait_sec * 1000)

                # Try to open comment panel (some layouts hide it)
                for selector in [
                    '[data-e2e="comment-icon"]',
                    '[data-e2e="browse-comment"]',
                    'button[aria-label*="Comment"]',
                    'button:has-text("Comments")',
                    'button:has-text("댓글")',
                ]:
                    try:
                        locator = page.locator(selector)
                        if await locator.is_visible():
                            await locator.click()
                            await page.wait_for_timeout(1200)
                            break
                    except Exception:
                        continue

                # Scroll to force lazy-loading of comments
                for _ in range(3):
                    try:
                        await page.mouse.wheel(0, 1200)
                        await page.wait_for_timeout(800)
                    except Exception:
                        break

                # Try to expand comment section if needed
                for selector in [
                    '[data-e2e="comment-load-more"]',
                    'button:has-text("View more comments")',
                    'button:has-text("More comments")',
                    'button:has-text("댓글 더보기")',
                ]:
                    try:
                        locator = page.locator(selector)
                        if await locator.is_visible():
                            await locator.click()
                            await page.wait_for_timeout(1500)
                            break
                    except Exception:
                        continue

                raw_comments = await page.evaluate(
                    """(limit) => {
                        const selectors = [
                            '[data-e2e="comment-item"]',
                            '[class*="comment-item"]',
                            '[class*="Comment"]',
                            '.comment-container',
                            '[data-testid="comment"]'
                        ];
                        let elements = [];
                        for (const sel of selectors) {
                            const found = Array.from(document.querySelectorAll(sel));
                            if (found.length) {
                                elements = found;
                                break;
                            }
                        }

                        const getText = (root, sels) => {
                            for (const sel of sels) {
                                const node = root.querySelector(sel);
                                if (node && node.textContent) {
                                    const text = node.textContent.trim();
                                    if (text) return text;
                                }
                            }
                            return "";
                        };

                        const results = [];
                        for (const el of elements) {
                            if (results.length >= limit) break;
                            const author = getText(el, [
                                '[data-e2e="comment-username"]',
                                '[class*="username"]',
                                '[class*="author"]',
                                'strong',
                                '.user-name',
                                '[data-testid="author"]'
                            ]);
                            const text = getText(el, [
                                '[data-e2e="comment-text"]',
                                '[class*="comment-text"]',
                                '[class*="content"]',
                                'p',
                                'span[class*="text"]'
                            ]);
                            const likesText = getText(el, [
                                '[data-e2e="comment-like-count"]',
                                '[class*="like"]',
                                '[class*="heart"]',
                                '[aria-label*="like"]'
                            ]);

                            if (!text) continue;
                            results.push({
                                author,
                                text,
                                likes_text: likesText
                            });
                        }
                        return results;
                    }""",
                    limit,
                )

                # Detect common "comments off" messages
                try:
                    disabled = await page.locator('text=/comments? (are|is) turned off/i').first.is_visible()
                    if disabled:
                        print("ℹ️ TikTok comments appear disabled for this video")
                except Exception:
                    pass

                await browser.close()

                comments = []
                for item in raw_comments:
                    likes = self._parse_count(item.get("likes_text", ""))
                    text = item.get("text", "").strip()
                    if not text:
                        continue
                    comments.append({
                        "text": text,
                        "likes": likes,
                        "author": item.get("author", ""),
                        "lang": self._detect_language(text),
                        "source": "playwright_tiktok",
                    })

                comments.sort(key=lambda x: x["likes"], reverse=True)
                return comments[:limit]

        except Exception as exc:
            print(f"⚠️ Playwright TikTok comment extraction failed: {exc}")
            return []

    async def _extract_tiktok_comment_list(self, video_url: str, limit: int) -> List[Dict]:
        """
        Extract TikTok comments by capturing the comment/list API response via Playwright.
        This is more reliable than DOM scraping when it works, but can be blocked by TikTok's
        verification challenge (bdturing).
        """
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            print(f"⚠️ Playwright not available for TikTok comment list: {exc}")
            return []

        timeout_sec = int(os.getenv("TIKTOK_PLAYWRIGHT_TIMEOUT_SEC", "45"))
        wait_sec = int(os.getenv("TIKTOK_PLAYWRIGHT_WAIT_SEC", "4"))
        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")
        user_data_dir = os.getenv("TIKTOK_PLAYWRIGHT_USER_DATA_DIR")
        channel = os.getenv("TIKTOK_PLAYWRIGHT_CHANNEL")
        headless = os.getenv("TIKTOK_PLAYWRIGHT_HEADFUL", "false").lower() not in ("1", "true", "yes")

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

        try:
            async with async_playwright() as p:
                browser = None
                if user_data_dir:
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir,
                        headless=headless,
                        channel=channel or None,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-web-security",
                            "--disable-features=VizDisplayCompositor",
                        ],
                        viewport={"width": 1280, "height": 720},
                        locale="en-US",
                    )
                else:
                    browser = await p.chromium.launch(
                        headless=headless,
                        channel=channel or None,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-web-security",
                            "--disable-features=VizDisplayCompositor",
                        ],
                    )
                    context = await browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                        viewport={"width": 1280, "height": 720},
                        locale="en-US",
                    )

                # Minimal stealth hints to reduce automation flags.
                try:
                    await context.add_init_script(
                        """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                        window.chrome = { runtime: {} };
                        """
                    )
                except Exception:
                    pass

                cookies = await _load_cookies(cookie_file)
                if cookies:
                    try:
                        await context.add_cookies(cookies)
                    except Exception as exc:
                        print(f"⚠️ Failed to add TikTok cookies: {exc}")

                page = await context.new_page()
                await page.goto(video_url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
                await page.wait_for_timeout(wait_sec * 1000)

                response = None
                try:
                    async with page.expect_response(
                        lambda r: "api/comment/list" in r.url, timeout=timeout_sec * 1000
                    ) as resp_info:
                        for selector in [
                            '[data-e2e="comment-icon"]',
                            '[data-e2e="browse-comment"]',
                            'button[aria-label*="Comment"]',
                            'button:has-text("Comments")',
                            'button:has-text("댓글")',
                        ]:
                            try:
                                locator = page.locator(selector)
                                if await locator.first.is_visible():
                                    await locator.first.click()
                                    await page.wait_for_timeout(1200)
                                    break
                            except Exception:
                                continue

                        for _ in range(4):
                            try:
                                await page.mouse.wheel(0, 1200)
                            except Exception:
                                pass
                            await page.wait_for_timeout(900)

                    response = await resp_info.value
                except Exception as exc:
                    print(f"⚠️ TikTok comment/list response not captured: {exc}")

                if response is None:
                    if browser:
                        await browser.close()
                    else:
                        await context.close()
                    return []

                text = await response.text()
                headers = await response.all_headers()
                if not text or headers.get("bdturing-verify"):
                    print("⚠️ TikTok comment/list blocked (bdturing).")
                    if browser:
                        await browser.close()
                    else:
                        await context.close()
                    return []

                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    print("⚠️ TikTok comment/list JSON parse failed")
                    if browser:
                        await browser.close()
                    else:
                        await context.close()
                    return []

                raw_comments = payload.get("comments") or payload.get("data", {}).get("comments") or []
                comments = []
                for item in raw_comments:
                    text = item.get("text") or item.get("share_info", {}).get("desc") or ""
                    if not text:
                        continue
                    user = item.get("user") or {}
                    author = user.get("unique_id") or user.get("nickname") or item.get("author") or ""
                    likes = (
                        item.get("digg_count")
                        or item.get("like_count")
                        or item.get("diggCount")
                        or 0
                    )
                    comments.append(
                        {
                            "text": text,
                            "likes": likes,
                            "author": author,
                            "lang": self._detect_language(text),
                            "source": "tiktok_comment_list",
                        }
                    )

                comments.sort(key=lambda x: x["likes"], reverse=True)

                if browser:
                    await browser.close()
                else:
                    await context.close()

                return comments[:limit]

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
