"""
Royalty Router - Creator Royalty System API
Provides endpoints for viewing and managing creator royalties.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models import User, RemixNode, NodeRoyalty, RoyaltyReason
from app.routers.auth import get_current_user
from app.services.royalty_engine import RoyaltyEngine


router = APIRouter(prefix="/royalty", tags=["Royalty"])


# --- Schemas ---

class RoyaltyTransactionResponse(BaseModel):
    id: str
    points_earned: int
    reason: str
    source_node_id: str
    forked_node_id: Optional[str]
    forker_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MyRoyaltySummary(BaseModel):
    user_id: str
    total_earned: int
    pending: int
    k_points: int
    recent_transactions: List[dict]


class NodeEarningsSummary(BaseModel):
    node_id: str
    title: str
    total_fork_count: int
    total_royalty_earned: int
    view_count: int
    transactions: List[dict]


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    user_name: Optional[str]
    total_royalty: int
    node_count: int


# --- Endpoints ---

@router.get("/my", response_model=MyRoyaltySummary)
async def get_my_royalty(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's royalty summary.
    Includes total earned, pending settlement, and recent transactions.
    """
    engine = RoyaltyEngine(db)
    summary = await engine.get_user_royalty_summary(current_user.id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return summary


@router.get("/node/{node_id}/earnings", response_model=NodeEarningsSummary)
async def get_node_earnings(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get earnings summary for a specific node.
    Shows fork count, total royalty generated, and transaction history.
    """
    engine = RoyaltyEngine(db)
    summary = await engine.get_node_earnings(node_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    return summary


@router.get("/my/nodes")
async def get_my_earning_nodes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get all nodes owned by current user with their earnings.
    Sorted by total royalty earned.
    """
    result = await db.execute(
        select(RemixNode)
        .where(RemixNode.created_by == current_user.id)
        .order_by(desc(RemixNode.total_royalty_earned))
        .offset(skip)
        .limit(limit)
    )
    nodes = result.scalars().all()
    
    return [
        {
            "node_id": node.node_id,
            "title": node.title,
            "total_fork_count": node.total_fork_count,
            "total_royalty_earned": node.total_royalty_earned,
            "view_count": node.view_count,
            "is_published": node.is_published,
            "layer": node.layer.value if hasattr(node.layer, 'value') else node.layer,
            "created_at": node.created_at.isoformat()
        }
        for node in nodes
    ]


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_creator_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top creators by total royalty earned.
    """
    # Query for users with most royalties
    result = await db.execute(
        select(
            User.id,
            User.name,
            User.total_royalty_received,
            func.count(RemixNode.id).label("node_count")
        )
        .outerjoin(RemixNode, RemixNode.created_by == User.id)
        .group_by(User.id)
        .order_by(desc(User.total_royalty_received))
        .limit(limit)
    )
    rows = result.all()
    
    return [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=str(row[0]),
            user_name=row[1],
            total_royalty=row[2],
            node_count=row[3]
        )
        for idx, row in enumerate(rows)
    ]


@router.get("/history")
async def get_royalty_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    reason: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get detailed royalty transaction history for current user.
    Can filter by reason (fork, view_milestone, k_success, genealogy_bonus).
    """
    query = select(NodeRoyalty).where(NodeRoyalty.creator_id == current_user.id)
    
    # Filter by reason if provided
    if reason:
        try:
            reason_enum = RoyaltyReason(reason)
            query = query.where(NodeRoyalty.reason == reason_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid reason. Must be one of: {[r.value for r in RoyaltyReason]}"
            )
    
    query = query.order_by(desc(NodeRoyalty.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    royalties = result.scalars().all()
    
    return [
        {
            "id": str(r.id),
            "points_earned": r.points_earned,
            "reason": r.reason.value if hasattr(r.reason, 'value') else r.reason,
            "source_node_id": str(r.source_node_id),
            "forked_node_id": str(r.forked_node_id) if r.forked_node_id else None,
            "forker_id": str(r.forker_id) if r.forker_id else None,
            "is_settled": r.is_settled,
            "created_at": r.created_at.isoformat()
        }
        for r in royalties
    ]


@router.get("/stats")
async def get_platform_royalty_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get platform-wide royalty statistics.
    """
    # Total royalties distributed
    total_result = await db.execute(
        select(func.sum(NodeRoyalty.points_earned))
    )
    total_distributed = total_result.scalar() or 0
    
    # Total transactions
    count_result = await db.execute(
        select(func.count(NodeRoyalty.id))
    )
    total_transactions = count_result.scalar() or 0
    
    # Breakdown by reason
    breakdown_result = await db.execute(
        select(
            NodeRoyalty.reason,
            func.count(NodeRoyalty.id),
            func.sum(NodeRoyalty.points_earned)
        )
        .group_by(NodeRoyalty.reason)
    )
    breakdown = breakdown_result.all()
    
    # Top earning nodes
    top_nodes_result = await db.execute(
        select(RemixNode.node_id, RemixNode.title, RemixNode.total_royalty_earned)
        .order_by(desc(RemixNode.total_royalty_earned))
        .limit(5)
    )
    top_nodes = top_nodes_result.all()
    
    return {
        "total_distributed": total_distributed,
        "total_transactions": total_transactions,
        "breakdown_by_reason": {
            row[0].value if hasattr(row[0], 'value') else row[0]: {
                "count": row[1],
                "total_points": row[2] or 0
            }
            for row in breakdown
        },
        "top_earning_nodes": [
            {"node_id": row[0], "title": row[1], "royalty": row[2]}
            for row in top_nodes
        ]
    }
