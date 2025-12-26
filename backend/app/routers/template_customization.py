"""
Template Customization Logging Router

Tracks creator customizations of template fields for RL-lite learning.
Based on Phase 3 #5: 템플릿 커스터마이징 로그 수집

Events flow:
1. Creator modifies template field on Canvas
2. Frontend sends customization event
3. Backend stores for pattern analysis
4. BatchPolicyUpdater uses this data for RL updates
"""
from typing import Optional, List, Any, Dict
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, TemplateVersion
from app.routers.auth import get_current_user_optional
from app.constants import CUSTOMIZATION_STORE_MAX_SIZE
from app.utils.time import iso_now


router = APIRouter(prefix="/templates", tags=["Templates"])


# ==================
# SCHEMAS
# ==================

class TemplateCustomizationEvent(BaseModel):
    """Single template customization event."""
    template_id: str = Field(..., description="Template or node ID")
    field_changed: str = Field(..., description="Field name: hook, audio, timing, etc.")
    old_value: Optional[Any] = None
    new_value: Any
    node_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class BatchCustomizationRequest(BaseModel):
    """Batch customization events for buffered sending."""
    customizations: List[TemplateCustomizationEvent]
    session_id: Optional[str] = None


class CustomizationResponse(BaseModel):
    """Response after logging customizations."""
    logged: int
    session_id: str


class CustomizationStats(BaseModel):
    """Aggregated customization statistics."""
    template_id: str
    total_customizations: int
    by_field: Dict[str, int]
    recent_changes: List[Dict[str, Any]]


# ==================
# IN-MEMORY STORE (MVP)
# For production, persist to TemplateVersion or dedicated table
# ==================

_customization_store: List[Dict[str, Any]] = []


def _store_customization(event: Dict[str, Any]):
    """Store customization in memory."""
    global _customization_store
    _customization_store.append(event)
    if len(_customization_store) > CUSTOMIZATION_STORE_MAX_SIZE:
        _customization_store = _customization_store[-CUSTOMIZATION_STORE_MAX_SIZE:]


# ==================
# ENDPOINTS
# ==================

@router.post("/customize", response_model=CustomizationResponse)
async def log_customizations(
    request: BatchCustomizationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    템플릿 커스터마이징 이벤트 로깅
    
    Canvas에서 Creator가 템플릿 필드를 수정할 때 호출됩니다.
    수집된 데이터는 RL-lite 정책 업데이트에 활용됩니다.
    
    지원 필드:
    - hook: 훅 패턴/타이밍 변경
    - audio: 오디오/음악 변경
    - timing: 장면 타이밍 변경
    - visual: 시각적 스타일 변경
    - subtitle: 자막 스타일/밀도 변경
    - shotlist: 샷 리스트 순서/내용 변경
    """
    session_id = request.session_id or str(uuid4())
    user_id = str(current_user.id) if current_user else None
    logged = 0
    
    for event in request.customizations:
        customization_data = {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "template_id": event.template_id,
            "field_changed": event.field_changed,
            "old_value": event.old_value,
            "new_value": event.new_value,
            "node_id": event.node_id,
            "context": event.context or {},
            "timestamp": iso_now(),
        }
        _store_customization(customization_data)
        logged += 1
    
    return CustomizationResponse(logged=logged, session_id=session_id)


@router.get("/customizations/{template_id}", response_model=CustomizationStats)
async def get_customizations(
    template_id: str,
    limit: int = 50,
):
    """
    특정 템플릿의 커스터마이징 이력 조회
    
    RL-lite 정책 분석 및 템플릿 개선에 활용됩니다.
    """
    # Filter by template_id
    template_customizations = [
        c for c in _customization_store
        if c.get("template_id") == template_id
    ]
    
    # Aggregate by field
    by_field: Dict[str, int] = {}
    for c in template_customizations:
        field = c.get("field_changed", "unknown")
        by_field[field] = by_field.get(field, 0) + 1
    
    # Recent changes (sorted by timestamp, newest first)
    sorted_customizations = sorted(
        template_customizations,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )
    recent = sorted_customizations[:limit]
    
    return CustomizationStats(
        template_id=template_id,
        total_customizations=len(template_customizations),
        by_field=by_field,
        recent_changes=[
            {
                "field": c.get("field_changed"),
                "old_value": c.get("old_value"),
                "new_value": c.get("new_value"),
                "timestamp": c.get("timestamp"),
                "user_id": c.get("user_id"),
            }
            for c in recent
        ],
    )


@router.get("/customizations/summary/all")
async def get_all_customization_summary():
    """
    전체 커스터마이징 요약 통계
    
    어떤 필드가 가장 많이 수정되는지 분석합니다.
    RL-lite 학습 우선순위 결정에 활용됩니다.
    """
    if not _customization_store:
        return {
            "total": 0,
            "by_field": {},
            "by_template": {},
            "top_modified_fields": [],
        }
    
    by_field: Dict[str, int] = {}
    by_template: Dict[str, int] = {}
    
    for c in _customization_store:
        field = c.get("field_changed", "unknown")
        template = c.get("template_id", "unknown")
        
        by_field[field] = by_field.get(field, 0) + 1
        by_template[template] = by_template.get(template, 0) + 1
    
    # Sort fields by count
    top_fields = sorted(by_field.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "total": len(_customization_store),
        "by_field": by_field,
        "by_template": by_template,
        "top_modified_fields": [
            {"field": f, "count": c} for f, c in top_fields[:10]
        ],
    }


# ==================
# HELPER FUNCTIONS FOR RL-LITE
# ==================

def get_customization_patterns() -> Dict[str, Any]:
    """
    Get customization patterns for RL-lite policy updates.
    Called by BatchPolicyUpdater.
    
    Returns patterns like:
    {
        "hook": {"most_common_change": "duration", "avg_delta": 2.5},
        "audio": {"preferred_genres": ["kpop", "hiphop"]},
    }
    """
    if not _customization_store:
        return {}
    
    patterns: Dict[str, List[Any]] = {}
    
    for c in _customization_store:
        field = c.get("field_changed")
        if field:
            if field not in patterns:
                patterns[field] = []
            patterns[field].append({
                "old": c.get("old_value"),
                "new": c.get("new_value"),
            })
    
    # Aggregate patterns
    result = {}
    for field, changes in patterns.items():
        result[field] = {
            "change_count": len(changes),
            "sample_changes": changes[:5],  # First 5 as examples
        }
    
    return result
