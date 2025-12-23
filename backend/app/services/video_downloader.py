"""
Video Downloader Service - Using yt-dlp for TikTok/Reels/Shorts
Handles video download and metadata extraction from social media platforms
"""
import os
import re
import tempfile
import asyncio
from typing import Optional, Tuple
from dataclasses import dataclass


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
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Cookies for authenticated content (optional)
            # 'cookiefile': '/path/to/cookies.txt',
        }
        
        # Platform-specific options
        if platform == 'tiktok':
            ydl_opts.update({
                'format': 'best',
                # TikTok often needs specific handling
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
                audio_url=info.get('url'),  # For audio extraction if needed
            )
            
            return file_path, metadata
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube Video ID from URL"""
        pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    async def _fetch_youtube_metadata_api(self, video_id: str, api_key: str) -> Optional[VideoMetadata]:
        """Fetch metadata using YouTube Data API v3"""
        import httpx
        from datetime import timedelta
        import isodate  # ISO 8601 duration parser (usually standard or simple regex override)

        # Simple ISO8601 parser fallback if isodate not present
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
