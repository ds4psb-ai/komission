"""
Evidence Boards Router - Experiment Grouping with KPI
Virlo Phase B: Collections → Evidence Boards
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    EvidenceBoard, EvidenceBoardItem, EvidenceBoardStatus,
    OutlierItem, RemixNode, User
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/boards", tags=["Evidence Boards"])


# ==================
# SCHEMAS
# ==================

class BoardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    kpi_target: Optional[str] = None


class BoardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    kpi_target: Optional[str] = None
    status: Optional[str] = None


class BoardItemAdd(BaseModel):
    outlier_item_id: Optional[UUID] = None
    remix_node_id: Optional[UUID] = None
    notes: Optional[str] = None


class ConclusionUpdate(BaseModel):
    conclusion: str
    winner_item_id: Optional[UUID] = None


class BoardItemResponse(BaseModel):
    id: UUID
    outlier_item_id: Optional[UUID]
    remix_node_id: Optional[UUID]
    notes: Optional[str]
    added_at: datetime
    
    # Inline data
    item_title: Optional[str] = None
    item_platform: Optional[str] = None
    item_thumbnail: Optional[str] = None

    class Config:
        from_attributes = True


class BoardResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    kpi_target: Optional[str]
    conclusion: Optional[str]
    winner_item_id: Optional[UUID]
    status: str
    item_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BoardDetailResponse(BoardResponse):
    items: List[BoardItemResponse]


# ==================
# ENDPOINTS
# ==================

@router.get("", response_model=List[BoardResponse])
async def list_boards(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's evidence boards
    """
    query = select(EvidenceBoard).where(
        EvidenceBoard.owner_id == current_user.id
    )
    
    if status:
        query = query.where(EvidenceBoard.status == status)
    
    query = query.order_by(EvidenceBoard.updated_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    boards = result.scalars().all()
    
    # Get item counts
    responses = []
    for board in boards:
        count_result = await db.execute(
            select(func.count(EvidenceBoardItem.id)).where(
                EvidenceBoardItem.board_id == board.id
            )
        )
        item_count = count_result.scalar() or 0
        
        responses.append(BoardResponse(
            id=board.id,
            title=board.title,
            description=board.description,
            kpi_target=board.kpi_target,
            conclusion=board.conclusion,
            winner_item_id=board.winner_item_id,
            status=board.status.value if hasattr(board.status, 'value') else board.status,
            item_count=item_count,
            created_at=board.created_at,
            updated_at=board.updated_at,
        ))
    
    return responses


@router.post("", response_model=BoardResponse)
async def create_board(
    data: BoardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new evidence board
    """
    board = EvidenceBoard(
        title=data.title,
        description=data.description,
        kpi_target=data.kpi_target,
        owner_id=current_user.id,
        status=EvidenceBoardStatus.DRAFT,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    
    return BoardResponse(
        id=board.id,
        title=board.title,
        description=board.description,
        kpi_target=board.kpi_target,
        conclusion=board.conclusion,
        winner_item_id=board.winner_item_id,
        status=board.status.value,
        item_count=0,
        created_at=board.created_at,
        updated_at=board.updated_at,
    )


@router.get("/{board_id}", response_model=BoardDetailResponse)
async def get_board(
    board_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get board with all items
    """
    result = await db.execute(
        select(EvidenceBoard)
        .where(EvidenceBoard.id == board_id)
        .options(selectinload(EvidenceBoard.items))
    )
    board = result.scalar_one_or_none()
    
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your board")
    
    # Build item responses with inline data
    item_responses = []
    for item in board.items:
        item_title = None
        item_platform = None
        item_thumbnail = None
        
        if item.outlier_item_id:
            outlier = await db.execute(
                select(OutlierItem).where(OutlierItem.id == item.outlier_item_id)
            )
            outlier = outlier.scalar_one_or_none()
            if outlier:
                item_title = outlier.title
                item_platform = outlier.platform
                item_thumbnail = outlier.thumbnail_url
        
        if item.remix_node_id:
            node = await db.execute(
                select(RemixNode).where(RemixNode.id == item.remix_node_id)
            )
            node = node.scalar_one_or_none()
            if node:
                item_title = node.title
                item_platform = node.platform
        
        item_responses.append(BoardItemResponse(
            id=item.id,
            outlier_item_id=item.outlier_item_id,
            remix_node_id=item.remix_node_id,
            notes=item.notes,
            added_at=item.added_at,
            item_title=item_title,
            item_platform=item_platform,
            item_thumbnail=item_thumbnail,
        ))
    
    return BoardDetailResponse(
        id=board.id,
        title=board.title,
        description=board.description,
        kpi_target=board.kpi_target,
        conclusion=board.conclusion,
        winner_item_id=board.winner_item_id,
        status=board.status.value if hasattr(board.status, 'value') else board.status,
        item_count=len(item_responses),
        created_at=board.created_at,
        updated_at=board.updated_at,
        items=item_responses,
    )


@router.post("/{board_id}/items", response_model=BoardItemResponse)
async def add_item_to_board(
    board_id: UUID,
    data: BoardItemAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add an item (outlier or remix node) to a board
    """
    # Verify board ownership
    result = await db.execute(
        select(EvidenceBoard).where(EvidenceBoard.id == board_id)
    )
    board = result.scalar_one_or_none()
    
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your board")
    
    if not data.outlier_item_id and not data.remix_node_id:
        raise HTTPException(status_code=400, detail="Must provide outlier_item_id or remix_node_id")
    
    # Create item
    item = EvidenceBoardItem(
        board_id=board_id,
        outlier_item_id=data.outlier_item_id,
        remix_node_id=data.remix_node_id,
        notes=data.notes,
    )
    db.add(item)
    
    # Update board timestamp and status
    board.updated_at = datetime.utcnow()
    if board.status == EvidenceBoardStatus.DRAFT:
        board.status = EvidenceBoardStatus.ACTIVE
    
    await db.commit()
    await db.refresh(item)
    
    return BoardItemResponse(
        id=item.id,
        outlier_item_id=item.outlier_item_id,
        remix_node_id=item.remix_node_id,
        notes=item.notes,
        added_at=item.added_at,
    )


@router.patch("/{board_id}/conclusion")
async def set_conclusion(
    board_id: UUID,
    data: ConclusionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set the conclusion for a board (marks as concluded)
    """
    result = await db.execute(
        select(EvidenceBoard).where(EvidenceBoard.id == board_id)
    )
    board = result.scalar_one_or_none()
    
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your board")
    
    board.conclusion = data.conclusion
    board.winner_item_id = data.winner_item_id
    board.status = EvidenceBoardStatus.CONCLUDED
    board.concluded_at = datetime.utcnow()
    board.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "status": "concluded",
        "conclusion": board.conclusion,
        "winner_item_id": str(board.winner_item_id) if board.winner_item_id else None,
    }


@router.delete("/{board_id}/items/{item_id}")
async def remove_item_from_board(
    board_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an item from a board
    """
    # Verify board ownership
    result = await db.execute(
        select(EvidenceBoard).where(EvidenceBoard.id == board_id)
    )
    board = result.scalar_one_or_none()
    
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your board")
    
    # Find and delete item
    item_result = await db.execute(
        select(EvidenceBoardItem).where(
            EvidenceBoardItem.id == item_id,
            EvidenceBoardItem.board_id == board_id
        )
    )
    item = item_result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(item)
    await db.commit()
    
    return {"status": "removed", "item_id": str(item_id)}
