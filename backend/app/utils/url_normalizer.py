"""
URL Normalizer (PEGL v1.0 Phase 1)

비디오 URL 정규화 유틸리티

기능:
- 플랫폼별 정규 URL 생성
- 쿼리 파라미터 정리
- 중복 방지용 canonical URL

Usage:
    from app.utils.url_normalizer import normalize_video_url, extract_video_id
    
    canonical_url = normalize_video_url("https://www.tiktok.com/@user/video/12345?some=param")
    # => "https://www.tiktok.com/@user/video/12345"
    
    video_id, platform = extract_video_id("https://youtu.be/abc123")
    # => ("abc123", "youtube")
"""
import re
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode

logger = logging.getLogger(__name__)


# 플랫폼별 정규 URL 패턴
PLATFORM_PATTERNS = {
    "youtube": [
        r"youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})",  # ?v= 또는 &v=
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ],
    "tiktok": [
        r"tiktok\.com/@[^/]+/video/(\d+)",
        r"tiktok\.com/t/([a-zA-Z0-9]+)",
        r"vm\.tiktok\.com/([a-zA-Z0-9]+)",
    ],
    "instagram": [
        r"instagram\.com/(?:p|reel)/([a-zA-Z0-9_-]+)",
    ],
    "twitter": [
        r"(?:twitter|x)\.com/[^/]+/status/(\d+)",
    ],
}


def extract_video_id(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    URL에서 비디오 ID와 플랫폼 추출
    
    Args:
        url: 비디오 URL
        
    Returns:
        (video_id, platform) 튜플. 추출 실패 시 (None, None)
    """
    if not url:
        return None, None
    
    url = url.strip()
    
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1), platform
    
    # 패턴 매칭 실패 - URL 파싱으로 힌트 추출
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if "youtube" in domain or "youtu.be" in domain:
            return None, "youtube"
        elif "tiktok" in domain:
            return None, "tiktok"
        elif "instagram" in domain:
            return None, "instagram"
        elif "twitter" in domain or "x.com" in domain:
            return None, "twitter"
    except Exception:
        pass
    
    return None, None


def normalize_video_url(url: str, platform: Optional[str] = None) -> str:
    """
    비디오 URL 정규화
    
    - 불필요한 쿼리 파라미터 제거
    - 플랫폼별 정규 형식으로 변환
    
    Args:
        url: 원본 URL
        platform: 플랫폼 (자동 감지 가능)
        
    Returns:
        정규화된 URL (정규화 실패 시 원본 반환)
    """
    if not url:
        return url
    
    url = url.strip()
    video_id, detected_platform = extract_video_id(url)
    platform = platform or detected_platform
    
    if not platform:
        # 플랫폼 감지 불가 - 쿼리만 정리
        return _strip_tracking_params(url)
    
    if not video_id:
        # ID 추출 불가 - 쿼리만 정리
        return _strip_tracking_params(url)
    
    # 플랫폼별 정규 URL 생성
    if platform == "youtube":
        return f"https://www.youtube.com/watch?v={video_id}"
    
    elif platform == "tiktok":
        # TikTok은 @username이 필요하므로 원본에서 추출 시도
        username_match = re.search(r"tiktok\.com/@([^/]+)/", url)
        if username_match:
            return f"https://www.tiktok.com/@{username_match.group(1)}/video/{video_id}"
        return f"https://www.tiktok.com/video/{video_id}"
    
    elif platform == "instagram":
        # reel 또는 post 구분
        if "/reel/" in url:
            return f"https://www.instagram.com/reel/{video_id}/"
        return f"https://www.instagram.com/p/{video_id}/"
    
    elif platform == "twitter":
        # 원본 username 추출 시도
        user_match = re.search(r"(?:twitter|x)\.com/([^/]+)/status/", url)
        if user_match:
            return f"https://x.com/{user_match.group(1)}/status/{video_id}"
        return f"https://x.com/i/status/{video_id}"
    
    return _strip_tracking_params(url)


def _strip_tracking_params(url: str) -> str:
    """
    추적 파라미터 제거
    
    유지할 파라미터: v (YouTube), id
    제거할 파라미터: utm_*, fbclid, ref, etc.
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # 유지할 파라미터만 필터링
        keep_params = ["v", "id", "list"]
        filtered = {k: v for k, v in params.items() if k in keep_params}
        
        new_query = urlencode(filtered, doseq=True)
        
        # URL 재조립
        result = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if new_query:
            result += f"?{new_query}"
        
        return result
    except Exception as e:
        logger.warning(f"URL normalization failed: {e}")
        return url


def normalize_platform_name(platform: str) -> str:
    """
    플랫폼 이름 정규화
    
    "YouTube" -> "youtube"
    "TikTok" -> "tiktok"
    "IG" -> "instagram"
    """
    if not platform:
        return ""
    
    platform = platform.strip().lower()
    
    # 별칭 처리
    aliases = {
        "yt": "youtube",
        "ig": "instagram",
        "insta": "instagram",
        "tt": "tiktok",
        "x": "twitter",
    }
    
    return aliases.get(platform, platform)


def get_external_id(url: str) -> Optional[str]:
    """
    URL에서 external_id 추출 (upsert용)
    
    Returns:
        "{platform}_{video_id}" 형식 또는 None
    """
    video_id, platform = extract_video_id(url)
    
    if video_id and platform:
        return f"{platform}_{video_id}"
    
    return None
