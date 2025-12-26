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
from app.models import RemixNode, NodeLayer, NodePermission, NodeGovernance, O2OCampaign, O2OLocation
from app.routers.auth import get_current_user, require_admin, User
from app.services.gemini_pipeline import gemini_pipeline
from app.services.remix_nodes import generate_remix_node_id
from app.services.royalty_engine import RoyaltyEngine
from app.services.neo4j_graph import neo4j_graph

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



@router.get("", response_model=List[RemixNodeResponse])
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


@router.post("", response_model=RemixNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_remix_node(
    data: RemixNodeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new master remix node (Admin only)"""
    node_id = await generate_remix_node_id(db)
    
    node = RemixNode(
        node_id=node_id,
        title=data.title,
        source_video_url=data.source_video_url,
        platform=data.platform,
        layer=NodeLayer.MASTER,
        permission=NodePermission.READ_ONLY,
        governed_by=NodeGovernance.OPEN_COMMUNITY,
        created_by=current_user.id,
        owner_type="user"
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
    current_user: User = Depends(get_current_user),
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


# --- Quest Matching API (Expert Recommendation) ---

class MatchingRequest(BaseModel):
    category: Optional[str] = None  # fashion, beauty, food, lifestyle
    music_genre: Optional[str] = None  # k-pop, hip-hop, edm
    platform: Optional[str] = None  # tiktok, instagram


class QuestRecommendation(BaseModel):
    id: str
    brand: Optional[str]
    campaign_title: str
    category: Optional[str]
    reward_points: int
    reward_product: Optional[str]
    place_name: Optional[str]
    address: Optional[str]
    deadline: datetime
    campaign_type: str
    fulfillment_steps: Optional[List[str]] = None


@router.post("/{node_id}/matching")
async def get_quest_matching(
    node_id: str,
    data: MatchingRequest = MatchingRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recommended O2O quests based on node's content category.
    
    Matches node's inferred category/genre with active O2O campaigns.
    Used in Remix Detail Page to show "Recommended Quests" section.
    """
    # 1. Get the node to infer category if not provided
    result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Remix node not found")
    
    # 2. Infer category from node's Gemini analysis if not provided
    category = data.category
    if not category and node.gemini_analysis:
        # Try to extract category from AI analysis
        analysis = node.gemini_analysis
        if isinstance(analysis, dict):
            category = analysis.get("category") or analysis.get("content_type")
    
    # 3. Query active O2O location campaigns (visit)
    now = datetime.utcnow()
    location_query = select(O2OLocation).where(
        (O2OLocation.active_start <= now) &
        (O2OLocation.active_end >= now)
    )
    
    # Filter by category if available
    if category:
        location_query = location_query.where(O2OLocation.category == category)
    
    location_query = location_query.order_by(O2OLocation.reward_points.desc()).limit(5)
    location_result = await db.execute(location_query)
    locations = location_result.scalars().all()

    # 4. Query active O2O campaigns (instant/shipment)
    campaign_query = select(O2OCampaign).where(
        (O2OCampaign.active_start <= now) &
        (O2OCampaign.active_end >= now)
    )
    if category:
        campaign_query = campaign_query.where(O2OCampaign.category == category)
    campaign_query = campaign_query.order_by(O2OCampaign.reward_points.desc()).limit(5)
    campaign_result = await db.execute(campaign_query)
    campaigns = campaign_result.scalars().all()
    
    # 5. Format response
    recommendations: List[QuestRecommendation] = []

    for loc in locations:
        recommendations.append(
            QuestRecommendation(
                id=str(loc.id),
                brand=loc.brand,
                campaign_title=loc.campaign_title,
                category=loc.category,
                reward_points=loc.reward_points,
                reward_product=loc.reward_product,
                place_name=loc.place_name,
                address=loc.address,
                deadline=loc.active_end,
                campaign_type="visit",
                fulfillment_steps=["위치 인증", "촬영"],
            )
        )

    for camp in campaigns:
        steps = None
        if isinstance(camp.fulfillment_steps, dict):
            steps = camp.fulfillment_steps.get("steps")
        elif isinstance(camp.fulfillment_steps, list):
            steps = camp.fulfillment_steps

        recommendations.append(
            QuestRecommendation(
                id=str(camp.id),
                brand=camp.brand,
                campaign_title=camp.campaign_title,
                category=camp.category,
                reward_points=camp.reward_points,
                reward_product=camp.reward_product,
                place_name=None,
                address=None,
                deadline=camp.active_end,
                campaign_type=camp.campaign_type,
                fulfillment_steps=steps,
            )
        )

    recommendations.sort(key=lambda item: item.reward_points, reverse=True)
    
    return {
        "node_id": node_id,
        "inferred_category": category,
        "recommended_quests": [r.model_dump() for r in recommendations],
        "total_count": len(recommendations)
    }


# --- Mutation Strategy (Genealogy Graph) ---

class MutationStrategyResponse(BaseModel):
    mutation_strategy: dict
    expected_boost: str
    reference_views: Optional[int]
    confidence: float
    rationale: str


@router.get("/mutation-strategy/{node_id}", response_model=List[MutationStrategyResponse])
async def get_mutation_strategy(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    [Genealogy Graph] 이 노드에서 어떤 변주를 하면 터질까?
    
    과거 성공 사례 기반으로 추천 변주 전략 반환
    - Neo4j EVOLVED_TO 엣지에서 성공 패턴 추출
    - 데이터 없으면 Mock 데이터 반환
    """
    # 1. Verify node exists
    result = await db.execute(
        select(RemixNode).where(RemixNode.node_id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    # 2. Query Neo4j for mutation strategies
    strategies = await neo4j_graph.query_mutation_strategy(
        template_node_id=node_id
    )
    
    return strategies


@router.get("/genealogy/{node_id}")
async def get_genealogy_tree(
    node_id: str,
    depth: int = Query(default=3, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """
    [Genealogy Graph] 특정 노드의 가계도(Family Tree) 반환
    
    - root: 요청한 노드 ID
    - edges: 부모→자식 관계 목록
    - total_nodes: 전체 노드 수
    """
    # 1. Verify node exists
    result = await db.execute(
        select(RemixNode).where(RemixNode.node_id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    # 2. Query Neo4j for genealogy tree
    tree = await neo4j_graph.get_genealogy_tree(
        node_id=node_id,
        depth=depth
    )
    
    return tree


# --- Feedback Loop (Pattern Calibration) ---

from app.services.pattern_calibrator import pattern_calibrator

class PerformanceReport(BaseModel):
    node_id: str
    actual_retention: float = Field(..., ge=0.0, le=1.0)
    actual_views: int = 0
    source: str = "manual"  # "tiktok_api" | "youtube_api" | "manual"


@router.post("/calibrate")
async def calibrate_node_performance(
    report: PerformanceReport,
    db: AsyncSession = Depends(get_db)
):
    """
    [Feedback Loop] 실제 성과 데이터 보고 및 패턴 신뢰도 보정
    
    사용 시나리오:
    1. 사용자가 영상 업로드 후 24-48시간 뒤
    2. 실제 조회수/유지율 데이터 수집
    3. 이 API 호출 → 패턴 신뢰도 자동 보정
    """
    # 1. Verify node exists
    result = await db.execute(
        select(RemixNode).where(RemixNode.node_id == report.node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {report.node_id} not found")
    
    # 2. Record actual performance and calibrate
    calibration_result = await pattern_calibrator.record_actual_performance(
        db=db,
        node_id=report.node_id,
        actual_retention=report.actual_retention,
        actual_views=report.actual_views,
        source=report.source
    )
    
    return calibration_result


@router.get("/pattern-confidence/{pattern_code}")
async def get_pattern_confidence(
    pattern_code: str,
    pattern_type: str = Query(default="visual"),
    db: AsyncSession = Depends(get_db)
):
    """
    [Feedback Loop] 특정 패턴의 예측 신뢰도 조회
    
    - confidence_score: 높을수록 예측이 정확함 (0.0 ~ 1.0)
    - sample_count: 검증된 샘플 수 (많을수록 신뢰)
    """
    confidence = await pattern_calibrator.get_pattern_confidence(
        db=db,
        pattern_code=pattern_code,
        pattern_type=pattern_type
    )
    
    return confidence


@router.get("/pattern-confidence-ranking")
async def get_pattern_confidence_ranking(
    min_samples: int = Query(default=5, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    [Feedback Loop] 모든 패턴의 신뢰도 랭킹 조회
    
    - 신뢰도가 높은 패턴일수록 예측이 정확함
    - min_samples 이상 검증된 패턴만 반환
    """
    ranking = await pattern_calibrator.get_all_pattern_confidences(
        db=db,
        min_samples=min_samples
    )
    
    return {
        "total_patterns": len(ranking),
        "ranking": ranking
    }


# --- GA/RL Pattern Optimizer ---

from app.services.viral_pattern_optimizer import viral_pattern_ga

class OptimizeRequest(BaseModel):
    category: Optional[str] = None
    mood: Optional[str] = None
    sequence_length: int = Field(default=5, ge=3, le=10)
    generations: int = Field(default=30, ge=10, le=100)


@router.post("/optimize-pattern")
async def optimize_pattern_sequence(
    request: OptimizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    [GA/RL] 유전 알고리즘으로 최적 바이럴 패턴 시퀀스 탐색
    
    - PatternConfidence 데이터를 fitness function으로 활용
    - 데이터가 쌓일수록 추천 정확도 향상
    
    Returns:
        {
            "best_sequence": [...패턴 시퀀스...],
            "best_fitness": 0.85,
            "generations": 30,
            "improvement": 0.2
        }
    """
    # 1. 패턴 신뢰도 데이터 로드
    await viral_pattern_ga.load_pattern_confidences(db)
    
    # 2. GA 파라미터 설정
    viral_pattern_ga.sequence_length = request.sequence_length
    
    # 3. 최적화 실행
    result = viral_pattern_ga.suggest_pattern_sequence(
        category=request.category,
        target_mood=request.mood
    )
    
    return result


@router.get("/pattern-suggestions")
async def get_quick_pattern_suggestions(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    [GA/RL] 빠른 패턴 조합 추천 (간소화 버전)
    
    전체 GA 실행 없이 PatternConfidence 기반 상위 패턴 반환
    """
    from app.models import PatternConfidence
    
    # 상위 신뢰도 패턴 조회
    result = await db.execute(
        select(PatternConfidence)
        .where(PatternConfidence.sample_count >= 3)
        .order_by(PatternConfidence.confidence_score.desc())
        .limit(10)
    )
    top_patterns = result.scalars().all()
    
    if top_patterns:
        suggestions = [
            {
                "pattern": p.pattern_code,
                "type": p.pattern_type,
                "confidence": p.confidence_score,
                "samples": p.sample_count
            }
            for p in top_patterns
        ]
    else:
        # 데이터 없으면 기본 추천
        suggestions = [
            {"pattern": "VIS_ZOOM_TO_FACE", "type": "visual", "confidence": 0.7, "samples": 0},
            {"pattern": "AUD_BASS_DROP", "type": "audio", "confidence": 0.75, "samples": 0},
            {"pattern": "VIS_RAPID_CUT", "type": "visual", "confidence": 0.68, "samples": 0},
        ]
    
    return {
        "category": category,
        "suggestions": suggestions,
        "source": "pattern_confidence" if top_patterns else "default"
    }


# --- Evidence Loop (Phase 4) ---

from app.services.evidence_service import evidence_service
from app.schemas.evidence import EvidenceTableResponse, EvidenceSnapshotResponse


@router.get("/{node_id}/evidence")
async def get_node_evidence(
    node_id: str,
    period: str = Query(default="4w", regex="^(4w|12w|1y)$"),
    format: str = Query(default="json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    [Evidence Loop] Parent 노드의 VDG 증거 테이블 조회
    
    Depth 1/2 자식 노드들의 mutation 성과를 집계하여 반환
    - json: API 응답용
    - csv: NotebookLM/Sheets 업로드용 파일 다운로드 (text/csv)
    """
    # 1. Verify node exists
    result = await db.execute(
        select(RemixNode).where(RemixNode.node_id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    # 2. CSV Export (for NotebookLM)
    if format == "csv":
        csv_content = await evidence_service.generate_evidence_csv(
            db=db,
            parent_node_id=str(node.id),
            period=period
        )
        from fastapi.responses import Response
        return Response(content=csv_content, media_type="text/csv")
    
    # 3. JSON Response (for API)
    evidence_table = await evidence_service.generate_evidence_table(
        db=db,
        parent_node_id=str(node.id),
        period=period
    )
    
    return evidence_table


@router.post("/{node_id}/evidence/snapshot")
async def create_evidence_snapshot(
    node_id: str,
    period: str = Query(default="4w", regex="^(4w|12w|1y)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    [Evidence Loop] EvidenceSnapshot 생성 및 저장
    
    VDG 분석 결과를 스냅샷으로 저장 (시트 동기화 전 단계)
    """
    # 1. Verify node exists
    result = await db.execute(
        select(RemixNode).where(RemixNode.node_id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    # 2. Create snapshot
    snapshot = await evidence_service.create_evidence_snapshot(
        db=db,
        parent_node_id=str(node.id),
        period=period
    )
    
    return {
        "snapshot_id": str(snapshot.id),
        "parent_node_id": node_id,
        "period": snapshot.period,
        "sample_count": snapshot.sample_count,
        "top_mutation": f"{snapshot.top_mutation_type}:{snapshot.top_mutation_pattern}" if snapshot.top_mutation_type else None,
        "created_at": snapshot.created_at.isoformat()
    }


@router.get("/{node_id}/vdg-summary")
async def get_vdg_summary(
    node_id: str,
    period: str = Query(default="4w", regex="^(4w|12w|1y)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    [Evidence Loop] VDG 요약 (raw 데이터)
    
    Canvas Evidence Node에서 사용할 원시 VDG 데이터
    """
    # 1. Verify node exists
    result = await db.execute(
        select(RemixNode).where(RemixNode.node_id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    # 2. Calculate VDG summary
    summary = await evidence_service.calculate_vdg_summary(
        db=db,
        parent_node_id=str(node.id),
        period=period
    )
    
    return {
        "node_id": node_id,
        "period": period,
        **summary
    }


# --- VDG Export for NotebookLM ---

@router.get("/{node_id}/vdg-export")
async def export_vdg_for_notebooklm(
    node_id: str,
    format: str = Query(default="markdown", regex="^(markdown|json)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    [NotebookLM] VDG 분석 결과를 NotebookLM Source Pack 형식으로 Export
    
    - markdown: NotebookLM에 직접 업로드 가능한 Markdown 형식
    - json: 구조화된 JSON 형식
    
    Returns:
        markdown: text/markdown Content-Type 응답
        json: application/json 응답
    """
    # 1. Get node and VDG data
    result = await db.execute(
        select(RemixNode).where(RemixNode.node_id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    vdg = node.gemini_analysis
    if not vdg:
        raise HTTPException(status_code=404, detail="No VDG analysis found for this node")
    
    # 2. Extract VDG components (support both v2 and v3 schemas)
    title = vdg.get("title") or node.title or "Untitled Video"
    summary = vdg.get("summary", "")
    
    # Hook Genome (v3: hook_genome, v2: global_context)
    hook = vdg.get("hook_genome", {})
    if not hook:
        gc = vdg.get("global_context", {})
        hook = {
            "pattern": gc.get("hook_pattern", "unknown"),
            "strength": gc.get("hook_strength_score", 0),
            "hook_summary": gc.get("viral_hook_summary", "")
        }
    
    # Intent Layer (v3)
    intent = vdg.get("intent_layer", {})
    dopamine = intent.get("dopamine_radar", {})
    irony = intent.get("irony_analysis", {})
    
    # Capsule Brief (v3)
    capsule = vdg.get("capsule_brief", {})
    constraints = capsule.get("constraints", {})
    
    # 3. Format output
    if format == "json":
        return {
            "node_id": node_id,
            "title": title,
            "summary": summary,
            "hook_genome": hook,
            "dopamine_radar": dopamine,
            "irony_analysis": irony,
            "production_constraints": constraints,
            "export_format": "notebooklm_source_pack",
            "exported_at": datetime.utcnow().isoformat()
        }
    
    # Markdown format
    md_lines = [
        f"# Video Analysis: {title}",
        "",
        f"> {summary}" if summary else "",
        "",
        "## Hook Genome",
        f"- **Pattern**: {hook.get('pattern', 'N/A')}",
        f"- **Delivery**: {hook.get('delivery', 'N/A')}",
        f"- **Strength**: {hook.get('strength', 0):.0%}",
        "",
        f"### Hook Summary",
        hook.get('hook_summary', 'No summary available'),
        "",
    ]
    
    # Dopamine Radar
    if dopamine:
        md_lines.extend([
            "## Dopamine Radar",
            "",
            "| Axis | Score |",
            "|------|-------|",
            f"| 👁️ Visual | {dopamine.get('visual_spectacle', 0)}/10 |",
            f"| 🎵 Audio | {dopamine.get('audio_stimulation', 0)}/10 |",
            f"| 📖 Story | {dopamine.get('narrative_intrigue', 0)}/10 |",
            f"| ❤️ Emotion | {dopamine.get('emotional_resonance', 0)}/10 |",
            f"| 😂 Comedy | {dopamine.get('comedy_shock', 0)}/10 |",
            "",
        ])
    
    # Irony Gap
    if irony and irony.get("gap_type", "none") != "none":
        md_lines.extend([
            "## Irony Gap Analysis",
            f"**Gap Type**: {irony.get('gap_type', 'N/A')}",
            "",
            f"**Setup** (What viewer expects):",
            f"> {irony.get('setup', 'N/A')}",
            "",
            f"**Twist** (What actually happens):",
            f"> {irony.get('twist', 'N/A')}",
            "",
        ])
    
    # Production Constraints
    if constraints:
        props = constraints.get("props", [])
        locations = constraints.get("locations", [])
        
        md_lines.extend([
            "## Production Constraints",
            f"- **Difficulty**: {constraints.get('difficulty', 'N/A')}",
            f"- **Min Actors**: {constraints.get('min_actors', 1)}",
            f"- **Props**: {', '.join(props) if props else 'None'}",
            f"- **Locations**: {', '.join(locations) if locations else 'Any'}",
            "",
            "### Primary Challenge",
            constraints.get("primary_challenge", "No specific challenge noted"),
            "",
        ])
    
    # Footer
    md_lines.extend([
        "---",
        f"*Exported from Komission VDG v3.0 | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
    ])
    
    markdown_content = "\n".join(md_lines)
    
    from fastapi.responses import Response
    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=vdg_{node_id}.md"}
    )

