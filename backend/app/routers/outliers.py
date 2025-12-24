"""
Outliers API Router - Evidence Loop Phase 1
Handles outlier source management and candidate crawling
"""
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models import (
    OutlierSource,
    OutlierItem,
    OutlierItemStatus,
    RemixNode,
    NodeLayer,
    NodePermission,
    NodeGovernance,
)
from app.routers.auth import require_curator, User
from app.services.remix_nodes import generate_remix_node_id
from app.schemas.evidence import (
    OutlierSourceCreate,
    OutlierSourceResponse,
    OutlierItemCreate,
    OutlierItemManualCreate,
    OutlierItemResponse,
    OutlierCandidatesResponse,
)

router = APIRouter(prefix="/outliers", tags=["Outliers"])


async def _get_or_create_source(db: AsyncSession, name: str) -> OutlierSource:
    result = await db.execute(select(OutlierSource).where(OutlierSource.name == name))
    source = result.scalar_one_or_none()
    if source:
        return source

    source = OutlierSource(
        name=name,
        base_url="manual://",
        auth_type="none",
        crawl_interval_hours=24,
    )
    db.add(source)
    await db.flush()
    return source


# ==================
# OUTLIER SOURCES
# ==================

@router.post("/sources", response_model=OutlierSourceResponse)
async def create_source(
    source: OutlierSourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """크롤링 소스 등록"""
    new_source = OutlierSource(
        name=source.name,
        base_url=source.base_url,
        auth_type=source.auth_type,
        auth_config=source.auth_config,
        crawl_interval_hours=source.crawl_interval_hours,
    )
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    return OutlierSourceResponse(
        id=str(new_source.id),
        name=new_source.name,
        base_url=new_source.base_url,
        auth_type=new_source.auth_type,
        last_crawled=new_source.last_crawled,
        is_active=new_source.is_active,
        created_at=new_source.created_at,
    )


@router.get("/sources", response_model=List[OutlierSourceResponse])
async def list_sources(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """등록된 소스 목록 조회"""
    query = select(OutlierSource)
    if active_only:
        query = query.where(OutlierSource.is_active == True)
    result = await db.execute(query)
    sources = result.scalars().all()
    return [
        OutlierSourceResponse(
            id=str(s.id),
            name=s.name,
            base_url=s.base_url,
            auth_type=s.auth_type,
            last_crawled=s.last_crawled,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in sources
    ]


# ==================
# OUTLIER ITEMS (CANDIDATES)
# ==================

@router.post("/items", response_model=OutlierItemResponse)
async def create_item(
    item: OutlierItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """아웃라이어 후보 수동 등록 (크롤러 또는 수동)"""
    new_item = OutlierItem(
        source_id=UUID(item.source_id),
        external_id=item.external_id,
        video_url=item.video_url,
        title=item.title,
        thumbnail_url=item.thumbnail_url,
        platform=item.platform,
        category=item.category,
        view_count=item.view_count,
        like_count=item.like_count,
        share_count=item.share_count,
        growth_rate=item.growth_rate,
        status=OutlierItemStatus.PENDING,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return _item_to_response(new_item)


@router.post("/items/manual", response_model=OutlierItemResponse)
async def create_item_manual(
    item: OutlierItemManualCreate,
    current_user: User = Depends(require_curator),
    db: AsyncSession = Depends(get_db)
):
    """관리자 수동 아웃라이어 등록 (링크 기반)"""
    external_id = f"manual_{hashlib.sha256(item.video_url.encode('utf-8')).hexdigest()}"
    existing = await db.execute(
        select(OutlierItem).where(OutlierItem.external_id == external_id)
    )
    existing_item = existing.scalar_one_or_none()
    if existing_item:
        return _item_to_response(existing_item)

    source_name = (item.source_name or "manual").strip() or "manual"
    source = await _get_or_create_source(db, source_name)

    new_item = OutlierItem(
        source_id=source.id,
        external_id=external_id,
        video_url=item.video_url,
        title=item.title,
        thumbnail_url=item.thumbnail_url,
        platform=item.platform,
        category=item.category,
        view_count=item.view_count,
        like_count=item.like_count,
        share_count=item.share_count,
        growth_rate=item.growth_rate,
        status=OutlierItemStatus.PENDING,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return _item_to_response(new_item)


@router.get("/candidates", response_model=OutlierCandidatesResponse)
async def list_candidates(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = Query(default="pending"),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """후보 아웃라이어 목록 조회 (선별 대상)"""
    query = select(OutlierItem).order_by(OutlierItem.view_count.desc())
    
    if category:
        query = query.where(OutlierItem.category == category)
    if platform:
        query = query.where(OutlierItem.platform == platform)
    if status:
        try:
            status_enum = OutlierItemStatus(status)
            query = query.where(OutlierItem.status == status_enum)
        except ValueError:
            pass
    
    query = query.limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return OutlierCandidatesResponse(
        total=len(items),
        candidates=[_item_to_response(i) for i in items],
    )


@router.patch("/items/{item_id}/status")
async def update_item_status(
    item_id: str,
    new_status: str,
    db: AsyncSession = Depends(get_db)
):
    """후보 상태 변경 (selected, rejected, promoted)"""
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == UUID(item_id))
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Outlier item not found")
    
    try:
        item.status = OutlierItemStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    
    await db.commit()
    return {"updated": True, "new_status": new_status}


@router.post("/items/{item_id}/promote")
async def promote_to_parent(
    item_id: str,
    current_user: User = Depends(require_curator),
    db: AsyncSession = Depends(get_db)
):
    """
    아웃라이어를 Parent RemixNode로 승격
    TODO: RemixNode 생성 로직 연결
    """
    result = await db.execute(
        select(OutlierItem).where(OutlierItem.id == UUID(item_id))
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Outlier item not found")
    
    if item.status == OutlierItemStatus.PROMOTED:
        raise HTTPException(status_code=400, detail="Already promoted")

    node_id = await generate_remix_node_id(db)
    node = RemixNode(
        node_id=node_id,
        title=item.title or "Untitled Outlier",
        source_video_url=item.video_url,
        platform=item.platform,
        layer=NodeLayer.MASTER,
        permission=NodePermission.READ_ONLY,
        governed_by=NodeGovernance.OPEN_COMMUNITY,
        view_count=item.view_count or 0,
        created_by=current_user.id,
        owner_type=current_user.role,
    )
    db.add(node)
    await db.flush()

    item.status = OutlierItemStatus.PROMOTED
    item.promoted_to_node_id = node.id
    await db.commit()
    await db.refresh(node)

    return {
        "promoted": True,
        "item_id": item_id,
        "node_id": node.node_id,
        "remix_id": str(node.id),
    }


def _item_to_response(item: OutlierItem) -> OutlierItemResponse:
    return OutlierItemResponse(
        id=str(item.id),
        source_id=str(item.source_id),
        external_id=item.external_id,
        video_url=item.video_url,
        title=item.title,
        thumbnail_url=item.thumbnail_url,
        platform=item.platform,
        category=item.category,
        view_count=item.view_count,
        like_count=item.like_count,
        growth_rate=item.growth_rate,
        status=item.status,
        promoted_to_node_id=str(item.promoted_to_node_id) if item.promoted_to_node_id else None,
        crawled_at=item.crawled_at,
    )
