"""
Curation Learning Router (Admin-only)
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import require_admin, User
from app.services.curation_service import learn_curation_rules_from_decisions
from app.models import CurationRule


# =====================================
# Schemas
# =====================================

class CurationRuleOut(BaseModel):
    """Pydantic schema for CurationRule response"""
    id: UUID
    rule_name: str
    rule_type: str
    conditions: dict
    source: Optional[str] = None
    priority: int = 0
    sample_size: int = 0
    accuracy: Optional[float] = None
    match_count: int = 0
    follow_count: int = 0
    is_active: bool = True
    description: Optional[str] = None

    class Config:
        from_attributes = True


class LearnResult(BaseModel):
    """Response schema for learning trigger"""
    status: str
    message: str
    total_decisions: int
    created: int
    updated: int
    skipped: int


# =====================================
# Router (Admin-only)
# =====================================

router = APIRouter(
    prefix="/ops/curation",  # Under /ops for admin access
    tags=["Curation (Admin)"],
    responses={404: {"description": "Not found"}},
)


@router.post("/learn", response_model=LearnResult, status_code=202)
async def trigger_learning(
    min_samples: int = Query(10, ge=1, description="Minimum samples for rule generation"),
    min_support_ratio: float = Query(0.6, gt=0, le=1, description="Minimum support ratio"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the rule learning engine (Admin-only).
    Scans recent decisions and updates rule library.
    """
    result = await learn_curation_rules_from_decisions(
        db,
        min_samples=min_samples,
        min_support_ratio=min_support_ratio
    )
    
    return LearnResult(
        status="success",
        message=f"Learning complete. Created {result['created']}, Updated {result['updated']} rules.",
        total_decisions=result["total_decisions"],
        created=result["created"],
        updated=result["updated"],
        skipped=result["skipped"],
    )


@router.get("/rules", response_model=List[CurationRuleOut])
async def list_rules(
    active_only: bool = Query(True, description="Only return active rules"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all curation rules (Admin-only)"""
    query = select(CurationRule)
    if active_only:
        query = query.where(CurationRule.is_active == True)
        
    result = await db.execute(query.order_by(CurationRule.priority.desc()))
    rules = result.scalars().all()
    return [CurationRuleOut.model_validate(r) for r in rules]
