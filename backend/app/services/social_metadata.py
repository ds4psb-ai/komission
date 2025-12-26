"""
Social metadata utilities.
Core logic extracted from legacy ingester flows, adapted for Komission backend.
"""
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import httpx


SHORT_TIKTOK_DOMAINS = ("vt.tiktok.com", "vm.tiktok.com")


def _expand_short_url(url: str) -> str:
    """Resolve short URLs (best-effort)."""
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            resp = client.get(url)
            return str(resp.url)
    except Exception:
        return url


def _detect_platform(url: str) -> str:
    lower = url.lower()
    if "tiktok.com" in lower:
        return "tiktok"
    if "instagram.com" in lower:
        return "instagram"
    if "youtube.com" in lower or "youtu.be" in lower:
        return "youtube"
    return "unknown"


def _extract_content_id(url: str, platform: str) -> Optional[str]:
    if platform == "youtube":
        match = re.search(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", url)
        return match.group(1) if match else None
    if platform == "instagram":
        match = re.search(r"/(reel|p|tv)/([A-Za-z0-9_-]+)/?", url)
        return match.group(2) if match else None
    if platform == "tiktok":
        match = re.search(r"/video/(\d+)", url)
        if match:
            return match.group(1)
    return None


def normalize_url(url: str, expand_short: bool = True) -> Dict[str, Any]:
    """Normalize URL, detect platform, and extract content_id."""
    resolved = url.strip()
    if expand_short and any(domain in resolved for domain in SHORT_TIKTOK_DOMAINS):
        resolved = _expand_short_url(resolved)

    platform = _detect_platform(resolved)
    content_id = _extract_content_id(resolved, platform)

    return {
        "platform": platform,
        "content_id": content_id,
        "canonical_url": resolved,
    }


def _format_upload_date(info: Dict[str, Any]) -> Optional[str]:
    upload_date = info.get("upload_date")
    if upload_date and len(upload_date) == 8:
        try:
            dt = datetime.strptime(upload_date, "%Y%m%d")
            return dt.isoformat()
        except ValueError:
            pass
    if info.get("timestamp"):
        try:
            return datetime.utcfromtimestamp(int(info["timestamp"])).isoformat()
        except Exception:
            return None
    return None


def _map_platform(info: Dict[str, Any], fallback: str) -> str:
    extractor = (info.get("extractor_key") or "").lower()
    if "tiktok" in extractor:
        return "tiktok"
    if "instagram" in extractor:
        return "instagram"
    if "youtube" in extractor:
        return "youtube"
    return fallback


def extract_social_metadata(
    url: str,
    platform: Optional[str] = None,
    cookie_file: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Extract metadata using yt-dlp (no download).
    Returns (platform, metadata).
    """
    try:
        import yt_dlp  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"yt-dlp not available: {exc}") from exc

    detected = platform or _detect_platform(url)
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    if cookie_file or os.getenv("SOCIAL_COOKIE_FILE"):
        ydl_opts["cookiefile"] = cookie_file or os.getenv("SOCIAL_COOKIE_FILE")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    platform_final = _map_platform(info, detected)
    metadata = {
        "platform": platform_final,
        "content_id": info.get("id"),
        "title": info.get("title"),
        "author": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
        "view_count": info.get("view_count") or 0,
        "like_count": info.get("like_count") or 0,
        "comment_count": info.get("comment_count") or 0,
        "share_count": info.get("share_count") or 0,
        "upload_date": _format_upload_date(info),
        "hashtags": info.get("tags") or [],
        "thumbnail_url": info.get("thumbnail"),
        "duration": info.get("duration"),
        "description": info.get("description"),
        "source": "yt_dlp",
    }

    return platform_final, metadata
