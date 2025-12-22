"""
Remix Node Router - CRUD + Analysis
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import RemixNode, NodeLayer, NodePermission, NodeGovernance
from app.routers.auth import get_current_user, require_admin, User
from app.services.gemini_pipeline import gemini_pipeline
from app.services.royalty_engine import RoyaltyEngine

router = APIRouter()


# --- Schemas ---

class RemixNodeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    source_video_url: str
    platform: Optional[str] = "tiktok"


class RemixNodeResponse(BaseModel):
    id: str
    node_id: str
    title: str
    layer: str
    permission: str
    governed_by: str
    genealogy_depth: int
    source_video_url: Optional[str]
    platform: Optional[str]
    is_published: bool
    view_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class RemixNodeDetail(RemixNodeResponse):
    gemini_analysis: Optional[dict]
    claude_brief: Optional[dict]
    storyboard_images: Optional[dict]
    audio_guide_path: Optional[str]
    mutation_profile: Optional[dict]
    performance_delta: Optional[str]


class AnalyzeRequest(BaseModel):
    video_url: str


class ForkRequest(BaseModel):
    mutations: Optional[dict] = None  # {"audio": {"before": "A", "after": "B"}}
    device_fingerprint: Optional[str] = None  # Browser fingerprint for anti-abuse


# --- Endpoints ---

@router.get("/my/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated statistics for current user's nodes"""
    # Get total views and fork counts for user's nodes
    result = await db.execute(
        select(
            func.coalesce(func.sum(RemixNode.view_count), 0).label("total_views"),
            func.coalesce(func.sum(RemixNode.total_fork_count), 0).label("total_forks"),
            func.count(RemixNode.id).label("node_count")
        ).where(RemixNode.created_by == current_user.id)
    )
    stats = result.one()
    
    return {
        "total_views": int(stats.total_views),
        "total_forks": int(stats.total_forks),
        "node_count": int(stats.node_count),
        "k_points": current_user.k_points,
        "total_royalty_received": current_user.total_royalty_received,
        "pending_royalty": current_user.pending_royalty
    }


@router.get("/outliers", response_model=List[RemixNodeResponse])
async def list_outliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    layer: Optional[str] = None,
    published_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Alias for listing remix nodes (Outliers)"""
    return await list_remix_nodes(skip, limit, layer, published_only, db)



@router.get("/", response_model=List[RemixNodeResponse])
async def list_remix_nodes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    layer: Optional[str] = None,
    published_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all published remix nodes with pagination"""
    query = select(RemixNode)
    
    if published_only:
        query = query.where(RemixNode.is_published == True)
    if layer:
        query = query.where(RemixNode.layer == layer)
    
    query = query.order_by(RemixNode.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    nodes = result.scalars().all()
    
    return [RemixNodeResponse(
        id=str(n.id),
        node_id=n.node_id,
        title=n.title,
        layer=n.layer.value if isinstance(n.layer, NodeLayer) else n.layer,
        permission=n.permission.value if isinstance(n.permission, NodePermission) else n.permission,
        governed_by=n.governed_by.value if isinstance(n.governed_by, NodeGovernance) else n.governed_by,
        genealogy_depth=n.genealogy_depth,
        source_video_url=n.source_video_url,
        platform=n.platform,
        is_published=n.is_published,
        view_count=n.view_count,
        created_at=n.created_at
    ) for n in nodes]


@router.get("/{node_id}", response_model=RemixNodeDetail)
async def get_remix_node(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single remix node by node_id"""
    result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Remix node not found")
    
    # Increment view count
    node.view_count += 1
    await db.commit()
    
    return RemixNodeDetail(
        id=str(node.id),
        node_id=node.node_id,
        title=node.title,
        layer=node.layer.value if isinstance(node.layer, NodeLayer) else node.layer,
        permission=node.permission.value if isinstance(node.permission, NodePermission) else node.permission,
        governed_by=node.governed_by.value if isinstance(node.governed_by, NodeGovernance) else node.governed_by,
        genealogy_depth=node.genealogy_depth,
        source_video_url=node.source_video_url,
        platform=node.platform,
        is_published=node.is_published,
        view_count=node.view_count,
        created_at=node.created_at,
        gemini_analysis=node.gemini_analysis,
        claude_brief=node.claude_brief,
        storyboard_images=node.storyboard_images,
        audio_guide_path=node.audio_guide_path,
        mutation_profile=node.mutation_profile,
        performance_delta=node.performance_delta
    )


@router.post("/", response_model=RemixNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_remix_node(
    data: RemixNodeCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new master remix node (Admin only)"""
    # Generate unique node_id
    date_str = datetime.now().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(RemixNode.node_id.like(f"remix_{date_str}%"))
    )
    count = count_result.scalar() or 0
    node_id = f"remix_{date_str}_{count + 1:03d}"
    
    node = RemixNode(
        node_id=node_id,
        title=data.title,
        source_video_url=data.source_video_url,
        platform=data.platform,
        layer=NodeLayer.MASTER,
        permission=NodePermission.READ_ONLY,
        governed_by=NodeGovernance.OPEN_COMMUNITY,
        created_by=current_user.id,
        owner_type="admin"
    )
    
    db.add(node)
    await db.commit()
    await db.refresh(node)
    
    return RemixNodeResponse(
        id=str(node.id),
        node_id=node.node_id,
        title=node.title,
        layer=node.layer.value,
        permission=node.permission.value,
        governed_by=node.governed_by.value,
        genealogy_depth=node.genealogy_depth,
        source_video_url=node.source_video_url,
        platform=node.platform,
        is_published=node.is_published,
        view_count=node.view_count,
        created_at=node.created_at
    )


@router.post("/{node_id}/analyze")
async def analyze_node_video(
    node_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Run Gemini analysis + Claude Planning on a node's source video (Admin only)"""
    result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Remix node not found")
    
    if not node.source_video_url:
        raise HTTPException(status_code=400, detail="No source video URL")
    
    # Run AI Pipeline
    try:
        # 1. Gemini Analysis
        analysis = await gemini_pipeline.analyze_video(node.source_video_url, node_id)
        node.gemini_analysis = analysis.model_dump()
        
        # 2. Claude Korean Planning
        # Use analysis result to generate scenario
        from app.services.claude_korean import claude_planner
        plan = await claude_planner.generate_scenario(node.gemini_analysis)
        node.claude_brief = plan
        
        await db.commit()
        
        return {
            "status": "success", 
            "gemini": analysis.model_dump(),
            "claude": plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@router.post("/{node_id}/view")
async def increment_view_count(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Increment view count for a node.
    Triggers impact verification for royalty payout when threshold is reached.
    """
    from sqlalchemy import update
    
    result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    old_view_count = node.view_count
    new_view_count = old_view_count + 1
    
    # Update view count
    await db.execute(
        update(RemixNode)
        .where(RemixNode.id == node.id)
        .values(view_count=new_view_count)
    )
    await db.commit()
    
    # 🛡️ Check if this triggers impact verification (100 views threshold)
    impact_verified = False
    if old_view_count < 100 <= new_view_count:
        try:
            royalty_engine = RoyaltyEngine(db)
            impact_verified = await royalty_engine.verify_impact(node.id)
            if impact_verified:
                print(f"✅ Impact verified for node {node_id}, royalties released!")
        except Exception as e:
            print(f"⚠️ Impact verification failed: {e}")
    
    return {
        "node_id": node_id,
        "view_count": new_view_count,
        "impact_verified": impact_verified
    }


@router.post("/{node_id}/fork", response_model=RemixNodeResponse)
async def fork_remix_node(
    node_id: str,
    data: ForkRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fork (copy) a remix node for personal customization"""
    
    # 🛡️ Get client IP for anti-abuse
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()  # First IP in chain
    
    result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(status_code=404, detail="Parent node not found")
    
    # Check genealogy depth limit
    if parent.genealogy_depth >= 3:
        raise HTTPException(status_code=400, detail="Maximum genealogy depth (3) reached")
    
    # Determine new layer
    new_layer = NodeLayer.FORK_OF_FORK if parent.layer == NodeLayer.FORK else NodeLayer.FORK
    
    # Generate fork node_id
    fork_node_id = f"fork_{uuid4().hex[:8]}"
    
    fork = RemixNode(
        node_id=fork_node_id,
        title=f"[Fork] {parent.title}",
        source_video_url=parent.source_video_url,
        platform=parent.platform,
        layer=new_layer,
        permission=NodePermission.FULL_EDIT,
        governed_by=NodeGovernance.OPEN_COMMUNITY,
        genealogy_depth=parent.genealogy_depth + 1,
        parent_node_id=parent.id,
        mutation_profile=data.mutations,
        gemini_analysis=parent.gemini_analysis,
        claude_brief=parent.claude_brief,
        storyboard_images=parent.storyboard_images,
        audio_guide_path=parent.audio_guide_path,
        created_by=current_user.id,
        owner_type="user"
    )
    
    db.add(fork)
    await db.commit()
    await db.refresh(fork)
    
    # Award royalty to parent node creator (with anti-abuse tracking)
    try:
        royalty_engine = RoyaltyEngine(db)
        await royalty_engine.on_fork(
            parent, 
            fork, 
            current_user,
            ip_address=client_ip,
            device_fingerprint=data.device_fingerprint
        )
    except Exception as e:
        # Log error but don't fail the fork operation
        print(f"⚠️ Royalty distribution failed: {e}")
    
    return RemixNodeResponse(
        id=str(fork.id),
        node_id=fork.node_id,
        title=fork.title,
        layer=fork.layer.value,
        permission=fork.permission.value,
        governed_by=fork.governed_by.value,
        genealogy_depth=fork.genealogy_depth,
        source_video_url=fork.source_video_url,
        platform=fork.platform,
        is_published=fork.is_published,
        view_count=fork.view_count,
        created_at=fork.created_at
    )


@router.patch("/{node_id}/publish")
async def publish_node(
    node_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Publish a remix node (Admin only)"""
    result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Remix node not found")
    
    node.is_published = True
    await db.commit()
    
    return {"status": "published", "node_id": node_id}
    return {"status": "published", "node_id": node_id}


@router.get("/{node_id}/genealogy")
async def get_node_genealogy(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the viral genealogy graph for a remix node (Neo4j)"""
    # 1. Check if node exists in Postgres
    result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Remix node not found")
        
    # 2. Fetch Graph Data
    try:
        from app.services.graph_db import graph_db
        graph_data = await graph_db.get_genealogy(node_id)
        
        if not graph_data:
            # Fallback if not in graph (e.g. sync failed)
            return {
                "current": {"id": node.node_id, "title": node.title},
                "ancestors": [],
                "children": [],
                "source": "postgres_fallback"
            }
            
        return graph_data
    except Exception as e:
        # Graceful degradation
        print(f"⚠️ Graph query failed: {e}")
        return {
            "current": {"id": node.node_id, "title": node.title},
            "ancestors": [],
            "children": [],
            "error": "Graph service unavailable"
        }
