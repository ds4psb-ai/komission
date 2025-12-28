"""
Creator Usage Tracking API

크리에이터 활용 추적 엔드포인트:
- 가이드 뷰 이벤트 로깅
- remix_suggestions 활용 추적
- 영상 제작 연결 추적
- 활용률 메트릭 계산

고객 가치 지표:
- 크리에이터 활용률 (30%+ 목표)
- 변주 성공률 (50%+ 목표)
- 재방문율 (40%+ 목표)
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, CreatorBehaviorEvent, BehaviorEventType
from app.routers.auth import get_current_user_optional

router = APIRouter(prefix="/usage", tags=["usage"])


# ==================== Schemas ====================

class UsageEventCreate(BaseModel):
    """활용 이벤트 생성"""
    event_type: str  # guide_view, remix_guide_click, etc.
    node_id: Optional[str] = None
    outlier_id: Optional[str] = None
    payload: Optional[dict] = Field(default_factory=dict)


class UsageEventResponse(BaseModel):
    """활용 이벤트 응답"""
    id: str
    event_type: str
    creator_id: str
    node_id: Optional[str]
    created_at: datetime


class UsageMetricsResponse(BaseModel):
    """활용률 메트릭"""
    period_days: int
    total_guide_views: int
    unique_creators: int
    remix_clicks: int
    production_starts: int
    production_completes: int
    # 계산된 비율
    guide_to_remix_rate: float  # 가이드 뷰 → 변주 클릭
    remix_to_production_rate: float  # 변주 클릭 → 제작 시작
    production_completion_rate: float  # 제작 시작 → 완료


# ==================== Endpoints ====================

@router.post("/events", response_model=UsageEventResponse)
async def log_usage_event(
    event: UsageEventCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    활용 이벤트 로깅
    
    event_type:
    - guide_view: 가이드 페이지 방문
    - remix_guide_click: remix_suggestions 클릭
    - capsule_brief_view: capsule_brief 상세 뷰
    - video_production_start: 영상 제작 시작
    - video_production_complete: 영상 제작 완료
    """
    # 비로그인도 허용 (익명 추적)
    creator_id = current_user.id if current_user else None
    
    if not creator_id:
        # 익명 사용자는 간단히 기록만
        return UsageEventResponse(
            id="anonymous",
            event_type=event.event_type,
            creator_id="anonymous",
            node_id=event.node_id,
            created_at=datetime.utcnow()
        )
    
    # 이벤트 타입 검증
    try:
        event_type_enum = BehaviorEventType(event.event_type)
    except ValueError:
        # 알 수 없는 타입도 허용 (확장성)
        event_type_enum = BehaviorEventType.GUIDE_VIEW
    
    # 이벤트 저장
    db_event = CreatorBehaviorEvent(
        creator_id=creator_id,
        event_type=event_type_enum,
        node_id=UUID(event.node_id) if event.node_id else None,
        payload_json={
            **event.payload,
            "outlier_id": event.outlier_id,
        }
    )
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    
    return UsageEventResponse(
        id=str(db_event.id),
        event_type=event.event_type,
        creator_id=str(creator_id),
        node_id=event.node_id,
        created_at=db_event.created_at
    )


@router.get("/metrics", response_model=UsageMetricsResponse)
async def get_usage_metrics(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    활용률 메트릭 조회
    
    고객 가치 지표 계산:
    - guide_to_remix_rate: 가이드 뷰 → 변주 클릭 전환율
    - remix_to_production_rate: 변주 클릭 → 제작 시작 전환율
    - production_completion_rate: 제작 시작 → 완료율
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    # 이벤트 타입별 집계
    stats = {}
    for event_type in [
        BehaviorEventType.GUIDE_VIEW,
        BehaviorEventType.REMIX_GUIDE_CLICK,
        BehaviorEventType.CAPSULE_BRIEF_VIEW,
        BehaviorEventType.VIDEO_PRODUCTION_START,
        BehaviorEventType.VIDEO_PRODUCTION_COMPLETE,
    ]:
        count_result = await db.execute(
            select(func.count(CreatorBehaviorEvent.id))
            .where(CreatorBehaviorEvent.event_type == event_type)
            .where(CreatorBehaviorEvent.created_at >= since)
        )
        stats[event_type.value] = count_result.scalar() or 0
    
    # Unique creators
    unique_result = await db.execute(
        select(func.count(func.distinct(CreatorBehaviorEvent.creator_id)))
        .where(CreatorBehaviorEvent.created_at >= since)
    )
    unique_creators = unique_result.scalar() or 0
    
    # 비율 계산 (0 division 방지)
    guide_views = stats.get("guide_view", 0)
    remix_clicks = stats.get("remix_guide_click", 0)
    production_starts = stats.get("video_production_start", 0)
    production_completes = stats.get("video_production_complete", 0)
    
    guide_to_remix = remix_clicks / guide_views if guide_views > 0 else 0.0
    remix_to_production = production_starts / remix_clicks if remix_clicks > 0 else 0.0
    completion_rate = production_completes / production_starts if production_starts > 0 else 0.0
    
    return UsageMetricsResponse(
        period_days=days,
        total_guide_views=guide_views,
        unique_creators=unique_creators,
        remix_clicks=remix_clicks,
        production_starts=production_starts,
        production_completes=production_completes,
        guide_to_remix_rate=round(guide_to_remix, 4),
        remix_to_production_rate=round(remix_to_production, 4),
        production_completion_rate=round(completion_rate, 4),
    )


@router.get("/creator/{creator_id}/history")
async def get_creator_history(
    creator_id: str,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 크리에이터의 활용 히스토리
    """
    result = await db.execute(
        select(CreatorBehaviorEvent)
        .where(CreatorBehaviorEvent.creator_id == UUID(creator_id))
        .order_by(CreatorBehaviorEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    
    return {
        "creator_id": creator_id,
        "total": len(events),
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type.value if hasattr(e.event_type, "value") else e.event_type,
                "node_id": str(e.node_id) if e.node_id else None,
                "payload": e.payload_json,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ]
    }
