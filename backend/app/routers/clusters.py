"""
Cluster API Router

P2 Roadmap: 클러스터 관리 API
- 클러스터 CRUD
- Kids 관리
- Distill 준비 상태 확인
- P2 진행률 조회

Endpoints:
- POST /clusters - 클러스터 생성
- POST /clusters/from-template - 템플릿에서 생성
- GET /clusters - 클러스터 목록
- GET /clusters/{id} - 클러스터 상세
- DELETE /clusters/{id} - 클러스터 삭제
- POST /clusters/{id}/kids - Kid 추가
- DELETE /clusters/{id}/kids/{kid_vdg_id} - Kid 제거
- GET /clusters/{id}/distill-readiness - Distill 준비 상태
- GET /clusters/p2-progress - P2 진행률
- GET /clusters/templates - 사용 가능한 템플릿
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.vdg_v4 import ContentCluster, ClusterKid, ClusterSignature
from app.services.cluster_service import get_cluster_service, P2_CLUSTER_TEMPLATES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clusters", tags=["clusters"])


# ====================
# REQUEST SCHEMAS
# ====================

class CreateClusterRequest(BaseModel):
    """Create cluster request."""
    cluster_name: str
    parent_vdg_id: str
    parent_content_id: str
    parent_tier: str = "A"
    parent_merger_quality: str = "gold"
    signature: Optional[ClusterSignature] = None


class CreateFromTemplateRequest(BaseModel):
    """Create cluster from template."""
    template_key: str
    parent_vdg_id: str
    parent_content_id: str
    parent_tier: str = "A"
    parent_merger_quality: str = "gold"


class AddKidRequest(BaseModel):
    """Add kid to cluster."""
    vdg_id: str
    content_id: str
    variation_type: str = "variation"
    success: bool = True
    similarity_score: float = 0.0


# ====================
# CLUSTER CRUD
# ====================

@router.post("", response_model=ContentCluster)
async def create_cluster(request: CreateClusterRequest):
    """Create a new cluster."""
    service = get_cluster_service()
    
    cluster = service.create_cluster(
        cluster_name=request.cluster_name,
        parent_vdg_id=request.parent_vdg_id,
        parent_content_id=request.parent_content_id,
        parent_tier=request.parent_tier,
        parent_merger_quality=request.parent_merger_quality,
        signature=request.signature
    )
    
    return cluster


@router.post("/from-template", response_model=ContentCluster)
async def create_from_template(request: CreateFromTemplateRequest):
    """Create a cluster from P2 template."""
    service = get_cluster_service()
    
    try:
        cluster = service.create_from_template(
            template_key=request.template_key,
            parent_vdg_id=request.parent_vdg_id,
            parent_content_id=request.parent_content_id,
            parent_tier=request.parent_tier,
            parent_merger_quality=request.parent_merger_quality
        )
        return cluster
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_clusters(distill_ready_only: bool = False):
    """List all clusters."""
    service = get_cluster_service()
    clusters = service.list_clusters(distill_ready_only=distill_ready_only)
    
    return {
        "total": len(clusters),
        "clusters": [c.model_dump() for c in clusters]
    }


@router.get("/templates")
async def list_templates():
    """List available P2 cluster templates."""
    return {
        "total": len(P2_CLUSTER_TEMPLATES),
        "templates": [
            {
                "key": key,
                "name": template["cluster_name"],
                "signature": template["signature"]
            }
            for key, template in P2_CLUSTER_TEMPLATES.items()
        ]
    }


@router.get("/p2-progress")
async def get_p2_progress():
    """Get P2 roadmap progress (10 clusters goal)."""
    service = get_cluster_service()
    return service.get_p2_progress()


@router.get("/{cluster_id}", response_model=ContentCluster)
async def get_cluster(cluster_id: str):
    """Get cluster by ID."""
    service = get_cluster_service()
    cluster = service.get_cluster(cluster_id)
    
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    return cluster


@router.delete("/{cluster_id}")
async def delete_cluster(cluster_id: str):
    """Delete a cluster."""
    service = get_cluster_service()
    
    if not service.delete_cluster(cluster_id):
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    return {"deleted": True, "cluster_id": cluster_id}


# ====================
# KIDS MANAGEMENT
# ====================

@router.post("/{cluster_id}/kids")
async def add_kid(cluster_id: str, request: AddKidRequest):
    """Add a kid to a cluster."""
    service = get_cluster_service()
    
    cluster = service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    kid = ClusterKid(
        vdg_id=request.vdg_id,
        content_id=request.content_id,
        variation_type=request.variation_type,
        success=request.success,
        similarity_score=request.similarity_score
    )
    
    if not service.add_kid(cluster_id, kid):
        raise HTTPException(status_code=400, detail="Failed to add kid (may already exist)")
    
    # Get updated cluster
    updated = service.get_cluster(cluster_id)
    return {
        "added": True,
        "kid_vdg_id": request.vdg_id,
        "cluster_id": cluster_id,
        "total_kids": len(updated.kids) if updated else 0,
        "distill_ready": updated.distill_ready if updated else False
    }


@router.delete("/{cluster_id}/kids/{kid_vdg_id}")
async def remove_kid(cluster_id: str, kid_vdg_id: str):
    """Remove a kid from a cluster."""
    service = get_cluster_service()
    
    if not service.remove_kid(cluster_id, kid_vdg_id):
        raise HTTPException(status_code=404, detail="Cluster or kid not found")
    
    updated = service.get_cluster(cluster_id)
    return {
        "removed": True,
        "kid_vdg_id": kid_vdg_id,
        "cluster_id": cluster_id,
        "total_kids": len(updated.kids) if updated else 0
    }


# ====================
# DISTILL READINESS
# ====================

@router.get("/{cluster_id}/distill-readiness")
async def get_distill_readiness(cluster_id: str):
    """Get detailed distill readiness report for a cluster."""
    service = get_cluster_service()
    
    report = service.get_distill_readiness_report(cluster_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    
    return report
