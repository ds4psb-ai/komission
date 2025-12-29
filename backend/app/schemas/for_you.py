"""
For You API - Answer-First UX 패턴 추천
MCP Resources 준비 레이어
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ==================
# Response Schemas
# ==================

class Comment(BaseModel):
    """베스트 댓글"""
    text: str
    likes: int = 0
    lang: str = "ko"
    translation_en: Optional[str] = None


class EvidenceSummary(BaseModel):
    """Evidence 요약 (MCP Resource용)"""
    best_comments: List[Comment] = Field(default_factory=list)
    total_views: int = 0
    engagement_rate: Optional[float] = None
    growth_rate: Optional[str] = None


class RecurrenceInfo(BaseModel):
    """재등장 정보"""
    ancestor_cluster_id: Optional[str] = None
    recurrence_score: Optional[float] = None
    recurrence_count: int = 0
    origin_cluster_id: Optional[str] = None
    last_recurrence_at: Optional[datetime] = None


class PatternRecommendation(BaseModel):
    """For You 추천 패턴"""
    id: UUID
    outlier_id: UUID
    
    # 기본 정보 - None 방어 (DB에 값 없을 수 있음)
    title: Optional[str] = None
    video_url: Optional[str] = None  # 필수지만 DB 누락 대비
    thumbnail_url: Optional[str] = None
    platform: str = "unknown"  # tiktok/youtube/instagram
    category: str = "general"  # beauty/meme/food...
    
    # Tier & Score
    tier: str = "C"  # S/A/B/C - 기본값 C로 변경
    outlier_score: Optional[float] = None
    
    # Evidence
    evidence: Optional[EvidenceSummary] = None  # None 허용
    
    # Recurrence (패턴 재등장)
    recurrence: Optional[RecurrenceInfo] = None
    
    # 클러스터 정보
    cluster_id: Optional[str] = None
    cluster_name: Optional[str] = None


class ForYouResponse(BaseModel):
    """For You 페이지 응답"""
    recommendations: List[PatternRecommendation]
    total_count: int
    has_more: bool = False


class ForYouFilters(BaseModel):
    """필터 옵션"""
    category: Optional[str] = None  # beauty, meme, food...
    platform: Optional[str] = None  # tiktok, youtube, instagram
    min_tier: str = "C"  # 최소 티어 (S/A/B/C)
    limit: int = Field(default=10, le=50)
    offset: int = 0
