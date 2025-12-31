"""
Creator Events Router - Implicit Signal Logging

Tracks creator behavior for RL policy improvement:
- page_view: Video detail page viewed
- template_click: Template CTA clicked
- video_watch: Watched embedded video (with watch_seconds)
- camera_open: Opened camera for recording
- form_start/form_submit: Campaign application flow
- share: Shared content
"""
from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.time import utcnow

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user_optional

router = APIRouter(prefix="/events", tags=["Events"])


# ==================
# SCHEMAS
# ==================

class EventPayload(BaseModel):
    """Single event data."""
    event_type: str  # page_view, template_click, video_watch, etc.
    resource_type: Optional[str] = None  # video, template, campaign, node
    resource_id: Optional[str] = None
    metadata: Optional[dict] = None  # Additional data like watch_seconds
    timestamp: Optional[datetime] = None


class BatchEventRequest(BaseModel):
    """Batch of events (for buffered sending)."""
    events: List[EventPayload]
    session_id: Optional[str] = None


class EventResponse(BaseModel):
    """Response after logging events."""
    logged: int
    session_id: str


# ==================
# IN-MEMORY STORE (MVP)
# For production, use Redis or dedicated analytics DB
# ==================

_event_store: List[dict] = []
_MAX_STORE_SIZE = 10000


def _store_event(event: dict):
    """Store event in memory (MVP implementation)."""
    global _event_store
    _event_store.append(event)
    if len(_event_store) > _MAX_STORE_SIZE:
        _event_store = _event_store[-_MAX_STORE_SIZE:]


def _get_recent_events(limit: int = 100) -> List[dict]:
    """Get recent events."""
    return list(reversed(_event_store[-limit:]))


# ==================
# ENDPOINTS
# ==================

@router.post("/track", response_model=EventResponse)
async def track_events(
    request: BatchEventRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    크리에이터 행동 이벤트 로깅
    
    지원 이벤트 타입:
    - page_view: 페이지 조회
    - template_click: 템플릿 CTA 클릭
    - video_watch: 영상 시청 (metadata.watch_seconds)
    - camera_open: 카메라 오픈
    - form_start: 신청폼 시작
    - form_submit: 신청폼 제출
    - share: 공유 클릭
    - promote_click: Parent 승격 클릭
    """
    session_id = request.session_id or str(uuid4())
    user_id = str(current_user.id) if current_user else None
    logged = 0
    
    for event in request.events:
        event_data = {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "event_type": event.event_type,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "metadata": event.metadata or {},
            "timestamp": (event.timestamp or utcnow()).isoformat(),
            "logged_at": utcnow().isoformat(),
        }
        _store_event(event_data)
        logged += 1
    
    return EventResponse(logged=logged, session_id=session_id)


@router.get("/recent")
async def get_recent_tracked_events(
    limit: int = 100,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
):
    """
    최근 이벤트 조회 (분석/디버깅용)
    """
    events = _get_recent_events(limit * 2)  # Get more to filter
    
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    if resource_type:
        events = [e for e in events if e.get("resource_type") == resource_type]
    
    return {
        "events": events[:limit],
        "total_in_memory": len(_event_store),
    }


@router.get("/summary")
async def get_event_summary():
    """
    이벤트 요약 통계
    """
    if not _event_store:
        return {"total": 0, "by_type": {}, "by_resource": {}}
    
    by_type = {}
    by_resource = {}
    
    for event in _event_store:
        event_type = event.get("event_type", "unknown")
        resource_type = event.get("resource_type", "unknown")
        
        by_type[event_type] = by_type.get(event_type, 0) + 1
        by_resource[resource_type] = by_resource.get(resource_type, 0) + 1
    
    return {
        "total": len(_event_store),
        "by_type": by_type,
        "by_resource": by_resource,
    }


@router.get("/fingerprint/{user_id}")
async def get_creator_fingerprint(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    크리에이터 스타일 핑거프린트 산출 (PDR FR-010)
    
    암묵 신호 기반 스타일 추정:
    - 행동 로그 (template_view, video_watch 등)
    - Calibration 선택 결과
    - 변주 성과
    
    Returns:
        tone: humorous | informative | dramatic | neutral
        pacing: fast | medium | slow
        hook_preferences: List of preferred hook patterns
        visual_style: polished | raw | minimalist | neutral
        confidence: 0.0 - 1.0
    """
    from app.services.creator_fingerprint import fingerprint_service
    
    fingerprint = await fingerprint_service.calculate_fingerprint(user_id, db)
    return fingerprint.to_dict()
