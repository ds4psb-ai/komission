"""
For You Router - Answer-First UX 패턴 추천 API
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import OutlierItem, OutlierItemStatus, PatternCluster
from app.schemas.for_you import (
    ForYouResponse,
    ForYouFilters,
    PatternRecommendation,
    EvidenceSummary,
    RecurrenceInfo,
    Comment,
)

router = APIRouter(prefix="/for-you", tags=["For You"])


# Tier 우선순위 매핑
TIER_PRIORITY = {"S": 1, "A": 2, "B": 3, "C": 4}


@router.get("", response_model=ForYouResponse)
async def get_for_you_recommendations(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    platform: Optional[str] = Query(None, description="플랫폼 필터"),
    min_tier: str = Query("C", description="최소 티어 (S/A/B/C)"),
    limit: int = Query(10, le=50, description="결과 개수"),
    offset: int = Query(0, description="오프셋"),
    db: AsyncSession = Depends(get_db),
) -> ForYouResponse:
    """
    For You 패턴 추천 목록
    
    Answer-First UX: 사용자 입력 없이 즉시 추천 제공
    - Tier 기반 정렬 (S > A > B > C)
    - Evidence (댓글, 지표) 포함
    - Recurrence (재등장) 정보 포함
    """
    # 1. 기본 쿼리: 분석 완료된 Outlier만
    query = select(OutlierItem).where(
        OutlierItem.analysis_status == "completed",
        OutlierItem.outlier_tier.isnot(None),
    )
    
    # 2. 필터 적용
    if category:
        query = query.where(OutlierItem.category == category)
    if platform:
        query = query.where(OutlierItem.platform == platform)
    
    # 3. Tier 필터
    min_priority = TIER_PRIORITY.get(min_tier, 4)
    allowed_tiers = [t for t, p in TIER_PRIORITY.items() if p <= min_priority]
    query = query.where(OutlierItem.outlier_tier.in_(allowed_tiers))
    
    # 4. Tier 우선순위로 정렬 (S > A > B > C), outlier_score 높은 순
    query = query.order_by(
        # PostgreSQL CASE 표현식으로 Tier 우선순위
        func.array_position(['S', 'A', 'B', 'C'], OutlierItem.outlier_tier),
        desc(OutlierItem.outlier_score),
        desc(OutlierItem.view_count),
    )
    
    # 5. 페이지네이션
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total_count = total_result.scalar() or 0
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    outliers = result.scalars().all()
    
    # 6. PatternCluster 정보 조회 (있으면)
    cluster_map = {}
    # TODO: OutlierItem과 PatternCluster 연결 시 활성화
    
    # 7. 응답 구성
    recommendations = []
    for outlier in outliers:
        # Evidence 구성
        comments = []
        if outlier.best_comments:
            for c in outlier.best_comments[:5]:
                comments.append(Comment(
                    text=c.get("text", ""),
                    likes=c.get("likes", 0),
                    lang=c.get("lang", "ko"),
                    translation_en=c.get("translation_en"),
                ))
        
        evidence = EvidenceSummary(
            best_comments=comments,
            total_views=outlier.view_count or 0,
            engagement_rate=outlier.engagement_rate,
            growth_rate=outlier.growth_rate,
        )
        
        # Recurrence 정보 (클러스터 있으면)
        recurrence = None
        # TODO: 클러스터 연결 시 활성화
        
        recommendations.append(PatternRecommendation(
            id=outlier.id,
            outlier_id=outlier.id,
            title=outlier.title,
            video_url=outlier.video_url or "",
            thumbnail_url=outlier.thumbnail_url,
            platform=outlier.platform or "unknown",
            category=outlier.category or "general",
            tier=outlier.outlier_tier or "C",
            outlier_score=outlier.outlier_score,
            evidence=evidence,
            recurrence=recurrence,
        ))
    
    return ForYouResponse(
        recommendations=recommendations,
        total_count=total_count,
        has_more=(offset + limit) < total_count,
    )


@router.get("/{outlier_id}", response_model=PatternRecommendation)
async def get_pattern_detail(
    outlier_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PatternRecommendation:
    """
    단일 패턴 상세 조회
    """
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == outlier_id)
    )
    outlier = result.scalar_one_or_none()
    
    if not outlier:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # Evidence 구성
    comments = []
    if outlier.best_comments:
        for c in outlier.best_comments[:5]:
            comments.append(Comment(
                text=c.get("text", ""),
                likes=c.get("likes", 0),
                lang=c.get("lang", "ko"),
                translation_en=c.get("translation_en"),
            ))
    
    evidence = EvidenceSummary(
        best_comments=comments,
        total_views=outlier.view_count or 0,
        engagement_rate=outlier.engagement_rate,
        growth_rate=outlier.growth_rate,
    )
    
    return PatternRecommendation(
        id=outlier.id,
        outlier_id=outlier.id,
        title=outlier.title,
        video_url=outlier.video_url or "",
        thumbnail_url=outlier.thumbnail_url,
        platform=outlier.platform or "unknown",
        category=outlier.category or "general",
        tier=outlier.outlier_tier or "C",
        outlier_score=outlier.outlier_score,
        evidence=evidence,
        recurrence=None,
    )
