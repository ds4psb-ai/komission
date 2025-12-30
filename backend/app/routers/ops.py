"""
Ops Console API (PEGL v1.0 P0-7)

운영자 콘솔 엔드포인트

기능:
- Run 상태 조회
- 실패 재시도
- 파이프라인 상태 대시보드
- EvidenceEvent 상태 조회
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.routers.auth import get_current_user, require_admin, User
from app.models import (
    Run, RunStatus, RunType, Artifact,
    EvidenceEvent, EvidenceEventStatus, DecisionObject,
    VDGEdge, VDGEdgeStatus,
    PatternCluster, NotebookSourcePack,
)
from app.utils.time import utcnow

router = APIRouter(prefix="/ops", tags=["Ops Console"])


# --- Schemas ---

class RunSummary(BaseModel):
    id: str
    run_type: str
    status: str
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_sec: Optional[float]
    result_summary: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class PipelineStatus(BaseModel):
    """파이프라인 전체 상태"""
    total_runs: int
    running: int
    completed: int
    failed: int
    
    total_evidence_events: int
    evidence_pending: int
    evidence_measured: int
    evidence_failed: int
    
    total_vdg_edges: int
    edges_candidate: int
    edges_confirmed: int
    
    total_clusters: int
    total_source_packs: int


class SessionHUD(BaseModel):
    """세션 HUD (운영자 헤드업 디스플레이)"""
    current_action: Optional[str]
    pending_items: int
    failed_items: int
    next_cta: Optional[str]
    last_run: Optional[RunSummary]


# --- Endpoints ---

@router.get("/status", response_model=PipelineStatus)
async def get_pipeline_status(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    파이프라인 전체 상태 조회 (Admin only)
    """
    # Run 통계
    run_stats = await db.execute(
        select(
            Run.status,
            func.count(Run.id).label("count")
        ).group_by(Run.status)
    )
    run_counts = {row.status.value: row.count for row in run_stats}
    
    total_runs = sum(run_counts.values())
    running = run_counts.get("RUNNING", 0)
    completed = run_counts.get("COMPLETED", 0)
    failed = run_counts.get("FAILED", 0)
    
    # EvidenceEvent 통계
    evidence_stats = await db.execute(
        select(
            EvidenceEvent.status,
            func.count(EvidenceEvent.id).label("count")
        ).group_by(EvidenceEvent.status)
    )
    evidence_counts = {row.status.value: row.count for row in evidence_stats}
    
    total_evidence = sum(evidence_counts.values())
    evidence_pending = evidence_counts.get("QUEUED", 0) + evidence_counts.get("RUNNING", 0)
    evidence_measured = evidence_counts.get("MEASURED", 0)
    evidence_failed = evidence_counts.get("FAILED", 0)
    
    # VDGEdge 통계
    edge_stats = await db.execute(
        select(
            VDGEdge.edge_status,
            func.count(VDGEdge.id).label("count")
        ).group_by(VDGEdge.edge_status)
    )
    edge_counts = {row.edge_status.value: row.count for row in edge_stats}
    
    total_edges = sum(edge_counts.values())
    edges_candidate = edge_counts.get("CANDIDATE", 0)
    edges_confirmed = edge_counts.get("CONFIRMED", 0)
    
    # 클러스터 및 Source Pack
    cluster_count = await db.scalar(select(func.count(PatternCluster.id)))
    pack_count = await db.scalar(select(func.count(NotebookSourcePack.id)))
    
    return PipelineStatus(
        total_runs=total_runs,
        running=running,
        completed=completed,
        failed=failed,
        total_evidence_events=total_evidence,
        evidence_pending=evidence_pending,
        evidence_measured=evidence_measured,
        evidence_failed=evidence_failed,
        total_vdg_edges=total_edges,
        edges_candidate=edges_candidate,
        edges_confirmed=edges_confirmed,
        total_clusters=cluster_count or 0,
        total_source_packs=pack_count or 0,
    )


@router.get("/runs", response_model=List[RunSummary])
async def list_runs(
    status: Optional[str] = Query(None, description="Filter by status"),
    run_type: Optional[str] = Query(None, description="Filter by run type"),
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Run 목록 조회 (Admin only)
    """
    query = select(Run).order_by(Run.started_at.desc()).limit(limit)
    
    if status:
        try:
            status_enum = RunStatus(status.upper())
            query = query.where(Run.status == status_enum)
        except ValueError:
            pass
    
    if run_type:
        try:
            type_enum = RunType(run_type.upper())
            query = query.where(Run.run_type == type_enum)
        except ValueError:
            pass
    
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return [
        RunSummary(
            id=str(r.id),
            run_type=r.run_type.value,
            status=r.status.value,
            started_at=r.started_at.isoformat() if r.started_at else None,
            ended_at=r.ended_at.isoformat() if r.ended_at else None,
            duration_sec=(r.ended_at - r.started_at).total_seconds() if r.started_at and r.ended_at else None,
            result_summary=r.result_summary,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}")
async def get_run_detail(
    run_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Run 상세 조회 (Admin only)
    """
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # 연결된 Artifact 조회
    artifacts_result = await db.execute(
        select(Artifact).where(Artifact.run_id == run_id)
    )
    artifacts = artifacts_result.scalars().all()
    
    return {
        "run": {
            "id": str(run.id),
            "run_type": run.run_type.value,
            "status": run.status.value,
            "idempotency_key": run.idempotency_key,
            "inputs_hash": run.inputs_hash,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "ended_at": run.ended_at.isoformat() if run.ended_at else None,
            "error_message": run.error_message,
            "result_summary": run.result_summary,
            "triggered_by": run.triggered_by,
        },
        "artifacts": [
            {
                "id": str(a.id),
                "artifact_type": a.artifact_type.value,
                "file_path": a.file_path,
                "metadata": a.metadata,
            }
            for a in artifacts
        ]
    }


@router.post("/runs/{run_id}/retry")
async def retry_failed_run(
    run_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    실패한 Run 재시도 (Admin only)
    
    Note: 실제 재시도는 별도 스케줄러/워커가 처리합니다.
    이 엔드포인트는 상태를 PENDING으로 변경합니다.
    """
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status != RunStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed runs can be retried")
    
    # 상태 변경
    run.status = RunStatus.PENDING
    run.error_message = None
    run.ended_at = None
    
    await db.commit()
    
    return {
        "message": "Run marked for retry",
        "run_id": str(run_id),
        "new_status": "PENDING"
    }


@router.get("/hud", response_model=SessionHUD)
async def get_session_hud(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    세션 HUD (운영자 헤드업 디스플레이)
    
    현재 진행 상태, 대기 항목, 다음 액션을 요약합니다.
    """
    # 가장 최근 Run
    last_run_result = await db.execute(
        select(Run).order_by(Run.started_at.desc()).limit(1)
    )
    last_run = last_run_result.scalar_one_or_none()
    
    # 실행 중인 Run
    running_count = await db.scalar(
        select(func.count(Run.id)).where(Run.status == RunStatus.RUNNING)
    )
    
    # 대기 중인 항목 (PENDING runs + QUEUED evidence)
    pending_runs = await db.scalar(
        select(func.count(Run.id)).where(Run.status == RunStatus.PENDING)
    )
    pending_evidence = await db.scalar(
        select(func.count(EvidenceEvent.id)).where(EvidenceEvent.status == EvidenceEventStatus.QUEUED)
    )
    pending_items = (pending_runs or 0) + (pending_evidence or 0)
    
    # 실패 항목
    failed_runs = await db.scalar(
        select(func.count(Run.id)).where(Run.status == RunStatus.FAILED)
    )
    failed_evidence = await db.scalar(
        select(func.count(EvidenceEvent.id)).where(EvidenceEvent.status == EvidenceEventStatus.FAILED)
    )
    failed_items = (failed_runs or 0) + (failed_evidence or 0)
    
    # 현재 액션 결정
    current_action = None
    if running_count and running_count > 0:
        current_action = f"Running {running_count} job(s)"
    elif pending_items > 0:
        current_action = "Waiting for execution"
    elif failed_items > 0:
        current_action = "Attention: Failed items need review"
    else:
        current_action = "Idle"
    
    # 다음 CTA 결정
    next_cta = None
    if failed_items > 0:
        next_cta = "Review failed items"
    elif pending_items > 0:
        next_cta = "Start pending jobs"
    else:
        next_cta = "Schedule new crawl"
    
    last_run_summary = None
    if last_run:
        last_run_summary = RunSummary(
            id=str(last_run.id),
            run_type=last_run.run_type.value,
            status=last_run.status.value,
            started_at=last_run.started_at.isoformat() if last_run.started_at else None,
            ended_at=last_run.ended_at.isoformat() if last_run.ended_at else None,
            duration_sec=(last_run.ended_at - last_run.started_at).total_seconds() if last_run.started_at and last_run.ended_at else None,
            result_summary=last_run.result_summary,
        )
    
    return SessionHUD(
        current_action=current_action,
        pending_items=pending_items,
        failed_items=failed_items,
        next_cta=next_cta,
        last_run=last_run_summary,
    )


@router.get("/evidence-events")
async def list_evidence_events(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    EvidenceEvent 목록 조회 (Admin only)
    """
    query = select(EvidenceEvent).order_by(EvidenceEvent.created_at.desc()).limit(limit)
    
    if status:
        try:
            status_enum = EvidenceEventStatus(status.upper())
            query = query.where(EvidenceEvent.status == status_enum)
        except ValueError:
            pass
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return [
        {
            "id": str(e.id),
            "event_id": e.event_id,
            "status": e.status.value,
            "parent_node_id": str(e.parent_node_id) if e.parent_node_id else None,
            "snapshot_id": str(e.snapshot_id) if e.snapshot_id else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        }
        for e in events
    ]


@router.get("/vdg-edges")
async def list_vdg_edges(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    VDGEdge 목록 조회 (Admin only)
    """
    query = select(VDGEdge).order_by(VDGEdge.created_at.desc()).limit(limit)
    
    if status:
        try:
            status_enum = VDGEdgeStatus(status.upper())
            query = query.where(VDGEdge.edge_status == status_enum)
        except ValueError:
            pass
    
    result = await db.execute(query)
    edges = result.scalars().all()
    
    return [
        {
            "id": str(e.id),
            "parent_node_id": str(e.parent_node_id),
            "child_node_id": str(e.child_node_id),
            "edge_type": e.edge_type.value,
            "status": e.status.value,
            "confidence": e.confidence,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in edges
    ]


@router.post("/vdg-edges/{edge_id}/confirm")
async def confirm_edge(
    edge_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    VDGEdge 수동 확정 (Admin only)
    """
    from app.services.vdg_edge_service import VDGEdgeService
    
    service = VDGEdgeService(db)
    edge = await service.confirm_edge(
        edge_id=edge_id,
        confirmed_by=current_user.id,
        confirmation_source="admin_console"
    )
    
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    return {
        "message": "Edge confirmed",
        "edge_id": str(edge_id),
        "new_status": edge.status.value
    }
