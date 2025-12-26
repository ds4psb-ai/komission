"""
Notebook Library API Router
NotebookLM 요약 결과를 DB에 래핑하여 저장/조회
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import NotebookLibraryEntry
from app.routers.auth import require_curator, User
from app.schemas.notebook_library import NotebookLibraryCreate, NotebookLibraryResponse

router = APIRouter(prefix="/notebook-library", tags=["NotebookLibrary"])


@router.post("/entries", response_model=NotebookLibraryResponse)
async def create_entry(
    payload: NotebookLibraryCreate,
    current_user: User = Depends(require_curator),
    db: AsyncSession = Depends(get_db),
):
    parent_id = None
    if payload.parent_node_id:
        try:
            parent_id = UUID(payload.parent_node_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent_node_id")

    entry = NotebookLibraryEntry(
        source_url=payload.source_url,
        platform=payload.platform,
        category=payload.category,
        summary=payload.summary,
        cluster_id=payload.cluster_id,
        parent_node_id=parent_id,
        temporal_phase=payload.temporal_phase,
        variant_age_days=payload.variant_age_days,
        novelty_decay_score=payload.novelty_decay_score,
        burstiness_index=payload.burstiness_index,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return NotebookLibraryResponse.from_orm(entry)


@router.get("/entries", response_model=List[NotebookLibraryResponse])
async def list_entries(
    cluster_id: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(NotebookLibraryEntry).order_by(NotebookLibraryEntry.created_at.desc())
    if cluster_id:
        query = query.where(NotebookLibraryEntry.cluster_id == cluster_id)
    if platform:
        query = query.where(NotebookLibraryEntry.platform == platform)
    if category:
        query = query.where(NotebookLibraryEntry.category == category)
    query = query.limit(limit)
    result = await db.execute(query)
    entries = result.scalars().all()
    return [NotebookLibraryResponse.from_orm(e) for e in entries]


@router.get("/entries/{entry_id}", response_model=NotebookLibraryResponse)
async def get_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        entry_uuid = UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entry ID")

    result = await db.execute(
        select(NotebookLibraryEntry).where(NotebookLibraryEntry.id == entry_uuid)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Notebook entry not found")
    return NotebookLibraryResponse.from_orm(entry)
