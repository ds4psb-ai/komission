
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.services.curation_service import learn_curation_rules_from_decisions
from app.models import CurationRule

router = APIRouter(
    prefix="/curation",
    tags=["curation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/learn", status_code=202)
async def trigger_learning(
    min_samples: int = 10,
    min_support_ratio: float = 0.6,
    db: Session = Depends(get_db)
):
    """
    Trigger the rule learning engine.
    Scans recent decisions and updates rule library.
    """
    result = await learn_curation_rules_from_decisions(
        db,
        min_samples=min_samples,
        min_support_ratio=min_support_ratio
    )
    
    count = result["created"] + result["updated"]
    
    return {
        "status": "success",
        "message": f"Learning complete. Created {result['created']}, Updated {result['updated']} rules.",
        "details": result,
        "new_rules_count": count
    }

@router.get("/rules")
async def list_rules(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all curation rules"""
    query = select(CurationRule)
    if active_only:
        query = query.where(CurationRule.is_active == True)
        
    result = await db.execute(query.order_by(CurationRule.accuracy.desc()))
    rules = result.scalars().all()
    return rules
