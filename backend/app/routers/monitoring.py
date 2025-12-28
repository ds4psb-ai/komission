"""
Monitoring & Health Check Routes (PEGL v1.0)

운영 모니터링 API
"""
from fastapi import APIRouter

from app.services.monitoring import health_checker, metrics_collector

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@router.get("/health")
async def detailed_health_check():
    """
    상세 헬스 체크
    
    모든 서비스 연결 상태 및 레이턴시 반환
    """
    return await health_checker.check_all()


@router.get("/metrics")
async def get_metrics():
    """
    성능 메트릭 (관리자 전용)
    
    - 업타임
    - 요청 수
    - 에러율
    - 레이턴시 통계
    """
    return metrics_collector.get_metrics()


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes readiness probe
    """
    health = await health_checker.check_all()
    if health["overall"] == "healthy":
        return {"ready": True}
    return {"ready": False, "details": health["services"]}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe
    """
    return {"alive": True}


@router.get("/tiktok/cookies")
async def tiktok_cookie_status():
    """
    TikTok 쿠키 상태 확인
    
    Returns:
        - status: fresh | stale | legacy | missing
        - age_hours: 쿠키 경과 시간
        - count: 쿠키 개수
        - needs_refresh: 갱신 필요 여부
    """
    from app.services.comment_extractor import comment_extractor
    return comment_extractor.get_cookie_status()


@router.post("/tiktok/cookies/refresh")
async def refresh_tiktok_cookies():
    """
    TikTok 쿠키 강제 갱신
    
    브라우저(Chrome/Edge/Firefox)에서 쿠키를 새로 export
    """
    from app.services.comment_extractor import comment_extractor
    import os
    
    # Force refresh by removing existing file
    cookie_status = comment_extractor.get_cookie_status()
    if cookie_status.get("cookie_file"):
        try:
            os.remove(cookie_status["cookie_file"])
        except Exception:
            pass
    
    # Export fresh cookies
    cookie_path = await comment_extractor._try_export_chrome_cookies()
    
    if cookie_path:
        return {
            "success": True,
            "message": "Cookies refreshed",
            **comment_extractor.get_cookie_status()
        }
    else:
        return {
            "success": False,
            "message": "Failed to refresh cookies - browser may not be available"
        }


@router.post("/tiktok/metadata")
async def extract_tiktok_metadata_endpoint(url: str):
    """
    TikTok 메타데이터 추출 (YouTube API 수준)
    
    조회수, 좋아요, 댓글수, 공유수, 작성자, 해시태그, 업로드 날짜 추출
    
    Extraction priority:
    1. UNIVERSAL_DATA JSON (webapp.video-detail)
    2. SIGI_STATE JSON fallback
    3. DOM data-e2e selectors
    4. Open Graph meta tags
    """
    from app.services.tiktok_metadata import extract_tiktok_metadata
    
    result = await extract_tiktok_metadata(url)
    return {
        "success": result.get("source") not in ["http_error", "request_error", "fetch_error", "unknown"],
        "data": result
    }


@router.post("/tiktok/extract")
async def extract_tiktok_complete_endpoint(url: str, include_comments: bool = True):
    """
    TikTok 통합 추출 (메타데이터 + 댓글)
    
    단일 세션으로 모든 데이터 추출:
    - 조회수, 좋아요, 댓글수, 공유수
    - 작성자, 업로드 날짜, 해시태그, 제목
    - 인기 댓글 (좋아요순)
    
    Returns:
        {
            "success": true,
            "data": {
                "video_id": "...",
                "view_count": 1000000,
                "like_count": 50000,
                "comment_count": 1000,
                "share_count": 500,
                "author": "username",
                "upload_date": "2025-12-25T12:00:00Z",
                "hashtags": ["#tag1", "#tag2"],
                "title": "Video title",
                "top_comments": [{"text": "...", "author": "...", "likes": 100}],
                "source": "universal_data",
                "extraction_quality": "complete"
            }
        }
    """
    from app.services.tiktok_extractor import extract_tiktok_complete
    
    result = await extract_tiktok_complete(url, include_comments)
    return {
        "success": result.get("source") not in ["fetch_error", "unknown"],
        "data": result
    }
