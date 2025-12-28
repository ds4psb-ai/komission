"""
Notebook Library API Router
NotebookLM Pattern Engine 결과를 DB에 래핑하여 저장/조회 (PEGL v1.0)
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
    """NotebookLM Pattern Engine 결과 저장"""
    parent_id = None
    if payload.parent_node_id:
        try:
            parent_id = UUID(payload.parent_node_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent_node_id")

    source_pack_id = None
    if payload.source_pack_id:
        try:
            source_pack_id = UUID(payload.source_pack_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid source_pack_id")

    entry = NotebookLibraryEntry(
        source_url=payload.source_url,
        platform=payload.platform,
        category=payload.category,
        summary=payload.summary,
        cluster_id=payload.cluster_id,
        parent_node_id=parent_id,
        source_pack_id=source_pack_id,
        temporal_phase=payload.temporal_phase,
        variant_age_days=payload.variant_age_days,
        novelty_decay_score=payload.novelty_decay_score,
        burstiness_index=payload.burstiness_index,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return NotebookLibraryResponse.model_validate(entry)


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
    return [NotebookLibraryResponse.model_validate(e) for e in entries]


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
    return NotebookLibraryResponse.model_validate(entry)


# ==================
# Source Pack Management (Phase D)
# ==================

from app.models import NotebookSourcePack
from pydantic import BaseModel
from datetime import datetime


class SourcePackItem(BaseModel):
    id: str
    cluster_id: str
    temporal_phase: str
    pack_type: str
    drive_url: Optional[str] = None
    notebook_id: Optional[str] = None  # NotebookLM integration status
    output_targets: Optional[str] = None
    pack_mode: Optional[str] = None
    entry_count: int
    created_at: str


class SourcePackListResponse(BaseModel):
    total: int
    source_packs: list[SourcePackItem]


@router.get("/source-packs", response_model=SourcePackListResponse)
async def list_source_packs(
    cluster_id: Optional[str] = Query(default=None),
    has_notebook: Optional[bool] = Query(default=None, description="Filter by NotebookLM upload status"),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    List all Source Packs with their NotebookLM upload status.
    Use has_notebook=false to find pending uploads.
    """
    query = select(NotebookSourcePack).order_by(NotebookSourcePack.created_at.desc())
    
    if cluster_id:
        query = query.where(NotebookSourcePack.cluster_id == cluster_id)
    
    if has_notebook is not None:
        if has_notebook:
            query = query.where(NotebookSourcePack.notebook_id.isnot(None))
        else:
            query = query.where(NotebookSourcePack.notebook_id.is_(None))
    
    query = query.limit(limit)
    result = await db.execute(query)
    packs = result.scalars().all()
    
    items = []
    for p in packs:
        items.append(SourcePackItem(
            id=str(p.id),
            cluster_id=p.cluster_id,
            temporal_phase=p.temporal_phase,
            pack_type=p.pack_type,
            drive_url=p.drive_url,
            notebook_id=p.notebook_id,
            output_targets=p.output_targets,
            pack_mode=p.pack_mode,
            entry_count=p.entry_count,
            created_at=p.created_at.isoformat() if p.created_at else "",
        ))
    
    return SourcePackListResponse(total=len(items), source_packs=items)


@router.get("/source-packs/{pack_id}")
async def get_source_pack(
    pack_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific Source Pack by ID."""
    try:
        pack_uuid = UUID(pack_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pack ID")
    
    result = await db.execute(
        select(NotebookSourcePack).where(NotebookSourcePack.id == pack_uuid)
    )
    pack = result.scalar_one_or_none()
    
    if not pack:
        raise HTTPException(status_code=404, detail="Source pack not found")
    
    return {
        "id": str(pack.id),
        "cluster_id": pack.cluster_id,
        "temporal_phase": pack.temporal_phase,
        "pack_type": pack.pack_type,
        "drive_url": pack.drive_url,
        "drive_file_id": pack.drive_file_id,
        "notebook_id": pack.notebook_id,
        "output_targets": pack.output_targets,
        "pack_mode": pack.pack_mode,
        "schema_version": pack.schema_version,
        "entry_count": pack.entry_count,
        "inputs_hash": pack.inputs_hash,
        "created_at": pack.created_at.isoformat() if pack.created_at else "",
    }


class UploadToNotebookRequest(BaseModel):
    pack_id: str


class UploadToNotebookResponse(BaseModel):
    success: bool
    notebook_id: Optional[str] = None
    message: str


@router.post("/source-packs/upload-to-notebook", response_model=UploadToNotebookResponse)
async def upload_source_pack_to_notebook(
    request: UploadToNotebookRequest,
    current_user: User = Depends(require_curator),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a Source Pack to NotebookLM Enterprise.
    This triggers the Phase D automation: creates a notebook and adds the sheet as source.
    """
    try:
        pack_uuid = UUID(request.pack_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pack ID")
    
    # Get pack
    result = await db.execute(
        select(NotebookSourcePack).where(NotebookSourcePack.id == pack_uuid)
    )
    pack = result.scalar_one_or_none()
    
    if not pack:
        raise HTTPException(status_code=404, detail="Source pack not found")
    
    if pack.notebook_id:
        return UploadToNotebookResponse(
            success=True,
            notebook_id=pack.notebook_id,
            message="Already uploaded to NotebookLM"
        )
    
    if not pack.drive_url:
        raise HTTPException(status_code=400, detail="Source pack has no drive_url")
    
    # Import NotebookLM client
    try:
        from app.services.notebooklm_api import get_client
        client = get_client()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"NotebookLM client unavailable: {e}")
    
    try:
        # Create notebook
        title = f"[VDG] {pack.cluster_id} - {pack.temporal_phase}"
        notebook = await client.create_notebook(
            title=title,
            description=f"VDG Source Pack (entries: {pack.entry_count})",
            sources=[pack.drive_url]
        )
        
        # Extract notebook ID
        notebook_name = notebook.get("name", "")
        notebook_id = notebook_name.split("/")[-1]
        
        # Update pack
        pack.notebook_id = notebook_id
        db.add(pack)
        await db.commit()
        
        await client.close()
        
        return UploadToNotebookResponse(
            success=True,
            notebook_id=notebook_id,
            message=f"Created notebook: {title}"
        )
        
    except Exception as e:
        await client.close()
        raise HTTPException(status_code=500, detail=f"NotebookLM upload failed: {e}")

