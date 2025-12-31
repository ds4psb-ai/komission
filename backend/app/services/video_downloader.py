"""
Video Downloader Service - Using yt-dlp for TikTok/Reels/Shorts
Handles video download and metadata extraction from social media platforms
"""
import os
import re
import tempfile
import asyncio
from typing import Optional, Tuple
from dataclasses import dataclass, field
from typing import List


@dataclass
class VideoMetadata:
    """Extracted video metadata from social platforms"""
    id: str
    title: str
    duration: float
    view_count: int
    like_count: int
    uploader: str
    platform: str
    description: str
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None
    # v3.6 additions for metadata merge
    upload_date: Optional[str] = None  # YYYYMMDD format from yt-dlp
    comment_count: Optional[int] = None
    share_count: Optional[int] = None
    hashtags: List[str] = field(default_factory=list)



class VideoDownloader:
    """
    Downloads videos from TikTok, Instagram Reels, and YouTube Shorts
    using yt-dlp for reliable extraction.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or tempfile.gettempdir()
        
    def _get_platform(self, url: str) -> str:
        """Detect platform from URL"""
        if 'tiktok' in url:
            return 'tiktok'
        elif 'instagram' in url:
            return 'instagram'
        elif 'youtube.com/shorts' in url or 'youtu.be' in url:
            return 'youtube'
        else:
            return 'unknown'
    
    async def download(self, url: str) -> Tuple[str, VideoMetadata]:
        """
        Download video and extract metadata.
        
        Args:
            url: Video URL (TikTok, Reels, Shorts)
            
        Returns:
            Tuple of (local_file_path, metadata)
        """
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError(
                "yt-dlp not installed. Run: pip install yt-dlp"
            )
        
        platform = self._get_platform(url)

        # TikTok/Instagram/YouTube - all use yt-dlp
        
        # Configure yt-dlp options
        ydl_opts = {
            # Download video+audio (max 720p for faster download), merge to mp4
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            'merge_output_format': 'mp4',  # Ensure output is mp4
            'outtmpl': os.path.join(self.output_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Solve YouTube JS challenge using deno
            'remote_components': ['ejs:github'],
        }
        
        # Cookie support for authenticated content
        cookie_file = os.getenv("YTDLP_COOKIE_FILE")
        if cookie_file and os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file
        
        cookies_from_browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER")
        if cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (cookies_from_browser,)
        
        # Platform-specific options
        if platform == 'tiktok':
            ydl_opts.update({
                'format': 'best',
                # TikTok 봇 차단 우회: 브라우저 쿠키 필수
                'cookiesfrombrowser': ('chrome',) if not cookies_from_browser else None,
            })
        elif platform == 'instagram':
            ydl_opts.update({
                'format': 'best',
                # Instagram may require cookies for some content
            })
        
        # Run download in thread pool (yt-dlp is synchronous)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._sync_download(url, ydl_opts)
        )
        
        return result

    async def _download_tiktok_direct(self, url: str) -> Tuple[str, VideoMetadata]:
        """
        Download TikTok video directly by extracting playAddr/downloadAddr.
        Uses Playwright (cookies) via TikTokMetadataExtractor for higher success rate.
        """
        from app.services.tiktok_metadata import TikTokMetadataExtractor
        import httpx

        video_url = await self._capture_tiktok_video_url(url)

        extractor = TikTokMetadataExtractor()
        html = None
        if not video_url:
            html = await extractor._fetch_with_playwright(url)
            if not html:
                html = await extractor._fetch_with_httpx(url)
            if not html:
                raise RuntimeError("Failed to fetch TikTok HTML")
            video_url = self._extract_tiktok_video_url(html)
        if not video_url:
            raise RuntimeError("Failed to extract TikTok video URL")

        # Prepare output path
        video_id = self._extract_tiktok_id(url) or "tiktok_video"
        temp_path = os.path.join(self.output_dir, f"{video_id}.mp4")

        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            async with client.stream("GET", video_url) as resp:
                resp.raise_for_status()
                with open(temp_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)

        metadata = VideoMetadata(
            id=video_id,
            title=self._extract_og_title(html or "") or "TikTok Video",
            duration=0,
            view_count=0,
            like_count=0,
            uploader="unknown",
            platform="tiktok",
            description="",
            thumbnail_url=self._extract_og_thumbnail(html or ""),
            audio_url=video_url,
        )

        return temp_path, metadata

    async def _capture_tiktok_video_url(self, url: str) -> Optional[str]:
        """
        Capture the direct video URL from Playwright network responses.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return None

        import random
        from pathlib import Path

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

        cookie_file = os.getenv("TIKTOK_COOKIE_FILE")
        if not cookie_file or not os.path.exists(cookie_file):
            base_dir = Path(__file__).parent.parent.parent
            auto_cookie = base_dir / "tiktok_cookies_auto.json"
            if auto_cookie.exists():
                cookie_file = str(auto_cookie)

        video_url = None

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
                user_agent=random.choice(user_agents),
                viewport={"width": 1280, "height": 720},
                locale="ko-KR",
                timezone_id="Asia/Seoul",
            )

            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
                window.chrome = { runtime: {} };
            """)

            if cookie_file and os.path.exists(cookie_file):
                try:
                    import json as json_module
                    with open(cookie_file, "r") as f:
                        data = json_module.load(f)
                    cookies = data.get("cookies", data) if isinstance(data, dict) else data
                    if isinstance(cookies, list) and cookies:
                        await context.add_cookies(cookies)
                except Exception:
                    pass

            page = await context.new_page()

            def handle_response(response):
                nonlocal video_url
                if video_url:
                    return
                try:
                    ctype = response.headers.get("content-type", "")
                    if response.request.resource_type == "media" or "video" in ctype:
                        if "tiktok" in response.url or "video" in response.url:
                            video_url = response.url
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
                if not video_url:
                    try:
                        await page.eval_on_selector("video", "v => v.play()")
                    except Exception:
                        pass
                    await page.wait_for_timeout(3000)
            finally:
                await browser.close()

        return video_url

    def _extract_tiktok_video_url(self, html: str) -> Optional[str]:
        """
        Extract direct video URL from TikTok HTML.
        Prefers JSON payloads, falls back to regex.
        """
        import json

        def pick_video_url(video_obj: Optional[dict]) -> Optional[str]:
            if not isinstance(video_obj, dict):
                return None
            for key in ["playAddr", "downloadAddr", "playAddrByte", "downloadAddrByte"]:
                value = video_obj.get(key)
                if isinstance(value, str) and value.startswith("http"):
                    return value
            bitrate_info = video_obj.get("bitrateInfo") or []
            if isinstance(bitrate_info, list):
                for entry in bitrate_info:
                    addr = entry.get("PlayAddr") or entry.get("playAddr") or {}
                    if isinstance(addr, dict):
                        urls = addr.get("UrlList") or addr.get("url_list") or addr.get("urlList") or []
                        if isinstance(urls, list) and urls:
                            if isinstance(urls[0], str) and urls[0].startswith("http"):
                                return urls[0]
            return None

        # 1) UNIVERSAL_DATA JSON
        universal_match = re.search(
            r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\\s\\S]*?)</script>',
            html,
            re.IGNORECASE
        )
        if universal_match:
            try:
                data = json.loads(universal_match.group(1).strip())
                item = (
                    data.get("__DEFAULT_SCOPE__", {})
                    .get("webapp.video-detail", {})
                    .get("itemInfo", {})
                    .get("itemStruct", {})
                )
                url = pick_video_url(item.get("video"))
                if url:
                    return url
            except Exception:
                pass

        # 2) SIGI_STATE JSON
        sigi_match = re.search(
            r'<script id="SIGI_STATE"[^>]*>([\\s\\S]*?)</script>',
            html,
            re.IGNORECASE
        )
        if sigi_match:
            try:
                data = json.loads(sigi_match.group(1).strip())
                item_module = data.get("ItemModule", {}) or {}
                if item_module:
                    item = next(iter(item_module.values()))
                    url = pick_video_url(item.get("video"))
                    if url:
                        return url
            except Exception:
                pass

        # 3) Fallback regex
        patterns = [
            r'"playAddr":"(.*?)"',
            r'"downloadAddr":"(.*?)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if not match:
                continue
            raw = match.group(1)
            # Decode escaped sequences
            try:
                decoded = raw.encode("utf-8").decode("unicode_escape")
            except Exception:
                decoded = raw
            decoded = decoded.replace("\\/", "/")
            if decoded.startswith("http"):
                return decoded
        return None

    def _extract_og_title(self, html: str) -> Optional[str]:
        match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    def _extract_og_thumbnail(self, html: str) -> Optional[str]:
        match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if match:
            return match.group(1)
        return None
    
    def _sync_download(self, url: str, ydl_opts: dict) -> Tuple[str, VideoMetadata]:
        """Synchronous download helper"""
        import yt_dlp
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=True)
            
            # Get downloaded file path
            file_path = ydl.prepare_filename(info)
            
            # Handle case where extension might differ
            if not os.path.exists(file_path):
                # Try with mp4 extension
                base = os.path.splitext(file_path)[0]
                for ext in ['.mp4', '.webm', '.mkv']:
                    if os.path.exists(base + ext):
                        file_path = base + ext
                        break
            
            # Build metadata
            metadata = VideoMetadata(
                id=info.get('id', 'unknown'),
                title=info.get('title', 'Untitled'),
                duration=info.get('duration', 0) or 0,
                view_count=info.get('view_count', 0) or 0,
                like_count=info.get('like_count', 0) or 0,
                uploader=info.get('uploader', info.get('channel', 'Unknown')),
                platform=self._get_platform(url),
                description=info.get('description', ''),
                thumbnail_url=info.get('thumbnail'),
                audio_url=info.get('url'),
                # v3.6 additions
                upload_date=info.get('upload_date'),  # YYYYMMDD
                comment_count=info.get('comment_count'),
                share_count=info.get('repost_count'),  # TikTok uses repost_count
                hashtags=(info.get('tags') or [])[:10],  # Max 10 hashtags
            )
            
            return file_path, metadata
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube Video ID from URL"""
        pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    def _extract_tiktok_id(self, url: str) -> Optional[str]:
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None

    async def _fetch_youtube_metadata_api(self, video_id: str, api_key: str) -> Optional[VideoMetadata]:
        """Fetch metadata using YouTube Data API v3"""
        import httpx
        from datetime import timedelta

        # Simple ISO8601 duration parser
        def parse_duration(duration_str):
            match = re.match(
                r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str
            )
            if not match:
                return 0
            h, m, s = match.groups()
            return int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0)

        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id,
            "key": api_key
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    print(f"YouTube API Error: {resp.status_code}")
                    return None
                
                data = resp.json()
                if not data.get("items"):
                    return None
                    
                item = data["items"][0]
                snippet = item["snippet"]
                content = item["contentDetails"]
                stats = item["statistics"]
                
                duration_sec = parse_duration(content["duration"])
                
                # Best thumbnail
                thumbs = snippet.get("thumbnails", {})
                best_thumb = (
                    thumbs.get("maxres", {}).get("url") or 
                    thumbs.get("high", {}).get("url") or 
                    thumbs.get("default", {}).get("url")
                )

                return VideoMetadata(
                    id=item["id"],
                    title=snippet["title"],
                    duration=float(duration_sec),
                    view_count=int(stats.get("viewCount", 0)),
                    like_count=int(stats.get("likeCount", 0)),
                    uploader=snippet["channelTitle"],
                    platform="youtube",
                    description=snippet["description"],
                    thumbnail_url=best_thumb,
                    audio_url=f"https://www.youtube.com/watch?v={item['id']}" # Not direct link, but valid for yt-dlp later
                )
            except Exception as e:
                print(f"YouTube API Exception: {e}")
                return None

    async def extract_metadata_only(self, url: str) -> VideoMetadata:
        """
        Extract metadata without downloading.
        Prioritizes YouTube Data API for YouTube links if key is available.
        Falls back to yt-dlp.
        """
        
        # 1. Try YouTube API
        api_key = os.getenv("YOUTUBE_API_KEY")
        if api_key and self._get_platform(url) == "youtube":
            vid_id = self._extract_youtube_id(url)
            if vid_id:
                print(f"[YouTube API] Fetching metadata for {vid_id}")
                meta = await self._fetch_youtube_metadata_api(vid_id, api_key)
                if meta:
                    return meta
                print("[YouTube API] Failed, falling back to yt-dlp")

        # 2. Fallback to yt-dlp
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("yt-dlp not installed")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, # Need full metadata
            'skip_download': True,
            # 'cookiefile': '...' # Needed for some Age-gated content
        }
        
        loop = asyncio.get_event_loop()
        
        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # yt-dlp handles Shorts URLs automatically
                info = ydl.extract_info(url, download=False)
                return VideoMetadata(
                    id=info.get('id', 'unknown'),
                    title=info.get('title', 'Untitled'),
                    duration=info.get('duration', 0) or 0,
                    view_count=info.get('view_count', 0) or 0,
                    like_count=info.get('like_count', 0) or 0,
                    uploader=info.get('uploader', 'Unknown'),
                    platform=self._get_platform(url),
                    description=info.get('description', ''),
                    thumbnail_url=info.get('thumbnail'),
                )
        
        return await loop.run_in_executor(None, _extract)


# Singleton instance
video_downloader = VideoDownloader()
