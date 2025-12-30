"""
DistillRun API Router

P3 Roadmap: 주간 DistillRun 자동화 API
- DistillRun CRUD
- NotebookLM 프롬프트 생성
- Candidates 업데이트
- Pack 생성
- Canary 배포
- 3-Axis 평가

Endpoints:
- POST /distill/weekly - 주간 DistillRun 실행
- POST /distill/runs - DistillRun 생성
- GET /distill/runs - DistillRun 목록
- GET /distill/runs/{id} - DistillRun 상세
- GET /distill/runs/{id}/prompt - NotebookLM 프롬프트
- POST /distill/runs/{id}/candidates - Candidates 업데이트
- POST /distill/runs/{id}/generate-pack - Pack 생성
- POST /distill/runs/{id}/deploy-canary - Canary 배포
- POST /distill/runs/{id}/evaluate - 3-Axis 평가
- GET /distill/stats - 통계
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.distill_service import (
    get_distill_service,
    DistillStatus,
    PromotionDecision,
    AxisMetrics
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/distill", tags=["distill"])


# ====================
# REQUEST SCHEMAS
# ====================

class CreateDistillRunRequest(BaseModel):
    """Create DistillRun from cluster."""
    cluster_id: str


class UpdateCandidatesRequest(BaseModel):
    """Update candidates from NotebookLM output."""
    dna_invariants: List[Dict[str, Any]] = Field(default_factory=list)
    mutation_slots: List[Dict[str, Any]] = Field(default_factory=list)
    forbidden_mutations: List[Dict[str, Any]] = Field(default_factory=list)


class GeneratePackRequest(BaseModel):
    """Generate Pack from candidates."""
    parent_pack_id: Optional[str] = None


class DeployCanaryRequest(BaseModel):
    """Deploy canary."""
    duration_days: int = 7


class EvaluateRequest(BaseModel):
    """Evaluate with metrics."""
    compliance_lift: float = 0.0
    compliance_sessions: int = 0
    outcome_lift: float = 0.0
    outcome_sessions: int = 0
    cluster_count: int = 0
    persona_count: int = 0
    negative_evidence_rate: float = 0.0


# ====================
# WEEKLY AUTOMATION
# ====================

@router.post("/weekly")
async def run_weekly_distill():
    """
    P3: 주간 DistillRun 자동 실행
    
    Steps:
    1. 가장 좋은 distill-ready 클러스터 선택
    2. DistillRun 생성
    3. NotebookLM 프롬프트 생성
    
    Returns:
        run_id, prompt, next step instructions
    """
    service = get_distill_service()
    result = service.run_weekly_distill()
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed"))
    
    return result


# ====================
# DISTILLRUN CRUD
# ====================

@router.post("/runs")
async def create_distill_run(request: CreateDistillRunRequest):
    """Create DistillRun from a cluster."""
    service = get_distill_service()
    
    try:
        run = service.create_from_cluster(request.cluster_id)
        return {
            "run_id": run.run_id,
            "cluster_id": run.cluster_id,
            "status": run.status.value,
            "source_refs": run.source_refs,
            "created_at": run.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs")
async def list_distill_runs(status: Optional[str] = None):
    """List all DistillRuns."""
    service = get_distill_service()
    
    status_enum = DistillStatus(status) if status else None
    runs = service.list_runs(status=status_enum)
    
    return {
        "total": len(runs),
        "runs": [
            {
                "run_id": r.run_id,
                "cluster_id": r.cluster_id,
                "cluster_name": r.cluster_name,
                "status": r.status.value,
                "pack_id": r.pack_id,
                "promotion_decision": r.promotion_decision.value,
                "created_at": r.created_at
            }
            for r in runs
        ]
    }


@router.get("/runs/{run_id}")
async def get_distill_run(run_id: str):
    """Get DistillRun details."""
    service = get_distill_service()
    run = service.get_run(run_id)
    
    if not run:
        raise HTTPException(status_code=404, detail="DistillRun not found")
    
    return {
        "run_id": run.run_id,
        "cluster_id": run.cluster_id,
        "cluster_name": run.cluster_name,
        "status": run.status.value,
        "parent_vdg_id": run.parent_vdg_id,
        "kid_vdg_ids": run.kid_vdg_ids,
        "source_refs": run.source_refs,
        "prompt_version": run.prompt_version,
        "candidates": run.candidates.to_dict() if run.candidates else None,
        "pack_id": run.pack_id,
        "parent_pack_id": run.parent_pack_id,
        "experiment_id": run.experiment_id,
        "canary_ratio": run.canary_ratio,
        "canary_start": run.canary_start,
        "canary_end": run.canary_end,
        "scheduled_evaluation_at": run.scheduled_evaluation_at,
        "promotion_decision": run.promotion_decision.value,
        "rollback_count": run.rollback_count,
        "created_at": run.created_at,
        "updated_at": run.updated_at
    }


# ====================
# DISTILLATION WORKFLOW
# ====================

@router.get("/runs/{run_id}/prompt")
async def get_distill_prompt(run_id: str):
    """Get/generate NotebookLM prompt for distillation."""
    service = get_distill_service()
    
    try:
        prompt = service.generate_distill_prompt(run_id)
        run = service.get_run(run_id)
        
        return {
            "run_id": run_id,
            "prompt_version": run.prompt_version if run else "v1",
            "prompt": prompt,
            "instructions": [
                "1. Copy this prompt to NotebookLM",
                "2. Add the VDG documents as sources",
                "3. Run distillation",
                "4. Extract JSON output",
                "5. Call POST /distill/runs/{run_id}/candidates"
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/candidates")
async def update_candidates(run_id: str, request: UpdateCandidatesRequest):
    """Update extracted candidates from NotebookLM."""
    service = get_distill_service()
    
    try:
        candidates = service.update_candidates(run_id, request.model_dump())
        
        return {
            "run_id": run_id,
            "updated": True,
            "candidates": {
                "dna_invariants_count": len(candidates.dna_invariants),
                "mutation_slots_count": len(candidates.mutation_slots),
                "forbidden_mutations_count": len(candidates.forbidden_mutations)
            },
            "next_step": "Call POST /distill/runs/{run_id}/generate-pack"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/generate-pack")
async def generate_pack(run_id: str, request: GeneratePackRequest):
    """Generate Pack from extracted candidates."""
    service = get_distill_service()
    
    try:
        pack_id = service.generate_pack(run_id, parent_pack_id=request.parent_pack_id)
        run = service.get_run(run_id)
        
        return {
            "run_id": run_id,
            "pack_id": pack_id,
            "parent_pack_id": run.parent_pack_id if run else None,
            "experiment_id": run.experiment_id if run else None,
            "next_step": "Call POST /distill/runs/{run_id}/deploy-canary"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/deploy-canary")
async def deploy_canary(run_id: str, request: DeployCanaryRequest):
    """Deploy canary and schedule evaluation."""
    service = get_distill_service()
    
    try:
        result = service.deploy_canary(run_id, duration_days=request.duration_days)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/evaluate")
async def evaluate_distill_run(run_id: str, request: EvaluateRequest):
    """
    Evaluate canary with 3-Axis metrics.
    
    3-Axis Criteria:
    1. Compliance Lift >= +15% (vs control)
    2. Outcome Lift >= 0% (completion, upload)
    3. Robustness: 2+ clusters, 2+ personas, <20% negative evidence
    """
    service = get_distill_service()
    
    metrics = AxisMetrics(
        compliance_lift=request.compliance_lift,
        compliance_sessions=request.compliance_sessions,
        outcome_lift=request.outcome_lift,
        outcome_sessions=request.outcome_sessions,
        cluster_count=request.cluster_count,
        persona_count=request.persona_count,
        negative_evidence_rate=request.negative_evidence_rate
    )
    
    try:
        result = service.evaluate_and_decide(run_id, metrics=metrics)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ====================
# STATS
# ====================

@router.get("/stats")
async def get_distill_stats():
    """Get distillation statistics."""
    service = get_distill_service()
    return service.get_distill_stats()
