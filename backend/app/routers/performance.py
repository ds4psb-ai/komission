"""
Performance Tracking Router
영상 URL로 성과(조회수/좋아요) 추출
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user
from app.models import User
from app.services.tiktok_extractor import extract_tiktok_complete

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# === Schemas ===

class ExtractPerformanceRequest(BaseModel):
    """영상 URL로 성과 추출 요청"""
    url: str  # TikTok or YouTube Shorts URL
    session_id: Optional[str] = None  # 연결할 세션 ID


class PerformanceData(BaseModel):
    """추출된 성과 데이터"""
    platform: str  # "tiktok" | "youtube"
    video_id: str
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    title: Optional[str] = None
    author: Optional[str] = None
    upload_date: Optional[str] = None
    extracted_at: str


class ExtractPerformanceResponse(BaseModel):
    success: bool
    data: Optional[PerformanceData] = None
    error: Optional[str] = None


# === Helpers ===

def detect_platform(url: str) -> Optional[str]:
    """URL에서 플랫폼 감지"""
    url_lower = url.lower()
    if "tiktok.com" in url_lower:
        return "tiktok"
    if "youtube.com/shorts" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    if "instagram.com" in url_lower:
        return "instagram"
    return None


async def extract_youtube_shorts(url: str) -> Optional[PerformanceData]:
    """
    YouTube Shorts 메타데이터 추출
    yt-dlp 사용
    """
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return None
            
            return PerformanceData(
                platform="youtube",
                video_id=info.get("id", ""),
                view_count=info.get("view_count", 0) or 0,
                like_count=info.get("like_count", 0) or 0,
                comment_count=info.get("comment_count", 0) or 0,
                share_count=0,  # YouTube doesn't expose share count
                title=info.get("title"),
                author=info.get("uploader"),
                upload_date=info.get("upload_date"),
                extracted_at=datetime.utcnow().isoformat(),
            )
    except Exception as e:
        logger.error(f"YouTube extraction failed: {e}")
        return None


# === Endpoints ===

@router.post("/extract", response_model=ExtractPerformanceResponse)
async def extract_performance(
    data: ExtractPerformanceRequest,
    current_user: User = Depends(get_current_user),
):
    """
    영상 URL에서 성과 데이터 추출
    
    지원 플랫폼:
    - TikTok: 조회수, 좋아요, 댓글, 공유
    - YouTube Shorts: 조회수, 좋아요, 댓글
    """
    platform = detect_platform(data.url)
    
    if not platform:
        return ExtractPerformanceResponse(
            success=False,
            error="지원하지 않는 URL입니다. TikTok 또는 YouTube Shorts URL을 입력해주세요."
        )
    
    try:
        if platform == "tiktok":
            # TikTok 추출 (기존 서비스 사용)
            result = await extract_tiktok_complete(data.url, include_comments=False)
            
            if not result or not result.get("view_count"):
                return ExtractPerformanceResponse(
                    success=False,
                    error="TikTok 영상 정보를 가져올 수 없습니다. URL을 확인해주세요."
                )
            
            performance = PerformanceData(
                platform="tiktok",
                video_id=result.get("video_id", ""),
                view_count=result.get("view_count", 0),
                like_count=result.get("like_count", 0),
                comment_count=result.get("comment_count", 0),
                share_count=result.get("share_count", 0),
                title=result.get("title"),
                author=result.get("author"),
                upload_date=result.get("upload_date"),
                extracted_at=result.get("extracted_at", datetime.utcnow().isoformat()),
            )
            
            return ExtractPerformanceResponse(success=True, data=performance)
        
        elif platform == "youtube":
            # YouTube Shorts 추출
            performance = await extract_youtube_shorts(data.url)
            
            if not performance:
                return ExtractPerformanceResponse(
                    success=False,
                    error="YouTube 영상 정보를 가져올 수 없습니다. URL을 확인해주세요."
                )
            
            return ExtractPerformanceResponse(success=True, data=performance)
        
        else:
            return ExtractPerformanceResponse(
                success=False,
                error=f"{platform} 플랫폼은 아직 지원되지 않습니다."
            )
    
    except Exception as e:
        logger.error(f"Performance extraction failed: {e}")
        return ExtractPerformanceResponse(
            success=False,
            error="성과 추출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.get("/compare/{pattern_id}")
async def compare_with_pattern(
    pattern_id: str,
    view_count: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 성과를 패턴 평균과 비교
    
    Returns:
    - pattern_avg: 패턴 평균 조회수
    - user_performance: 사용자 조회수
    - percentile: 상위 몇 %인지
    - verdict: "above_average" | "average" | "below_average"
    """
    # TODO: 실제 패턴 데이터 조회
    # 현재는 목 데이터
    pattern_avg = 150000  # 15만 평균
    
    diff_percent = ((view_count - pattern_avg) / pattern_avg) * 100
    
    if diff_percent >= 50:
        verdict = "exceptional"
        message = "🔥 상위 5%! 대박 영상이에요!"
    elif diff_percent >= 0:
        verdict = "above_average"
        message = f"✨ 평균보다 {diff_percent:.0f}% 높아요!"
    elif diff_percent >= -30:
        verdict = "average"
        message = "👍 평균 수준이에요. 다음엔 더 잘할 수 있어요!"
    else:
        verdict = "below_average"
        message = "📈 조금 아쉽지만, 팁을 확인해보세요!"
    
    return {
        "pattern_id": pattern_id,
        "pattern_avg_views": pattern_avg,
        "user_views": view_count,
        "diff_percent": round(diff_percent, 1),
        "verdict": verdict,
        "message": message,
    }
