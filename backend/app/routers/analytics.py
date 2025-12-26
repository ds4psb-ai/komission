"""
Analytics and KPI Dashboard Router
backend/app/routers/analytics.py

Provides endpoints for:
- Weekly performance aggregation
- Pattern Lift calculations
- Experiment tracking dashboard
- KPI reports

Based on Phase 4 requirements from 03_IMPLEMENTATION_ROADMAP.md
"""
from datetime import timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    RemixNode, EvidenceSnapshot, NotebookLibraryEntry,
    OutlierItem, PatternCluster
)
from app.routers.auth import require_curator, User
from app.constants import (
    CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, EXPERIMENT_MIN_DAYS,
    PATTERN_MIN_SAMPLES, PATTERN_LIFT_LIMIT
)
from app.utils.time import utcnow, days_ago, iso_now

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ==================
# Response Models
# ==================

class PatternLiftResult(BaseModel):
    pattern: str
    mutation_type: str
    baseline_rate: float
    current_rate: float
    lift: float  # (current - baseline) / baseline
    sample_count: int
    confidence: float

class WeeklyKPI(BaseModel):
    week_start: str
    week_end: str
    total_analyses: int
    successful_patterns: int
    avg_confidence: float
    top_patterns: List[PatternLiftResult]
    cluster_growth: int
    outliers_promoted: int

class ExperimentStatus(BaseModel):
    parent_id: str
    parent_title: str
    current_depth: int
    days_tracked: int
    variants_count: int
    top_variant: Optional[str]
    top_variant_rate: Optional[float]
    status: str  # "tracking" | "complete" | "needs_decision"

class DashboardSummary(BaseModel):
    total_parents: int
    total_clusters: int
    total_library_entries: int
    active_experiments: int
    avg_pattern_lift: float
    weekly_kpi: WeeklyKPI


# ==================
# Endpoints
# ==================

@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _curator = Depends(require_curator)
):
    """
    Get high-level dashboard summary for Admin/Curator.
    """
    # Count Parents (layer = 'master')
    parents = await db.execute(
        select(func.count(RemixNode.id))
        .where(RemixNode.layer == "master")
    )
    total_parents = parents.scalar() or 0
    
    # Count Clusters
    clusters = await db.execute(select(func.count(PatternCluster.id)))
    total_clusters = clusters.scalar() or 0
    
    # Count Library Entries
    entries = await db.execute(select(func.count(NotebookLibraryEntry.id)))
    total_library_entries = entries.scalar() or 0
    
    # Active Experiments (evidence snapshots in last 14 days)
    active = await db.execute(
        select(func.count(EvidenceSnapshot.id))
        .where(EvidenceSnapshot.created_at >= days_ago(EXPERIMENT_MIN_DAYS))
    )
    active_experiments = active.scalar() or 0
    
    # Get weekly KPI
    weekly_kpi = await _calculate_weekly_kpi(db)
    
    # Calculate average pattern lift
    avg_lift = 0.0
    if weekly_kpi.top_patterns:
        lifts = [p.lift for p in weekly_kpi.top_patterns if p.lift > 0]
        if lifts:
            avg_lift = sum(lifts) / len(lifts)
    
    return DashboardSummary(
        total_parents=total_parents,
        total_clusters=total_clusters,
        total_library_entries=total_library_entries,
        active_experiments=active_experiments,
        avg_pattern_lift=avg_lift,
        weekly_kpi=weekly_kpi
    )


@router.get("/weekly-kpi", response_model=WeeklyKPI)
async def get_weekly_kpi(
    weeks_ago: int = Query(0, ge=0, le=12),
    db: AsyncSession = Depends(get_db),
    _curator = Depends(require_curator)
):
    """
    Get KPI metrics for a specific week.
    weeks_ago=0 means current week.
    """
    return await _calculate_weekly_kpi(db, weeks_ago)


@router.get("/pattern-lifts", response_model=List[PatternLiftResult])
async def get_pattern_lifts(
    limit: int = Query(20, ge=1, le=100),
    min_samples: int = Query(3, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pattern lift calculations for top-performing mutations.
    Pattern Lift = (current_rate - baseline_rate) / baseline_rate
    """
    # Get recent evidence snapshots
    result = await db.execute(
        select(EvidenceSnapshot)
        .where(EvidenceSnapshot.confidence >= 0.5)
        .order_by(desc(EvidenceSnapshot.created_at))
        .limit(200)
    )
    snapshots = result.scalars().all()
    
    # Aggregate pattern stats
    pattern_stats: Dict[str, Dict[str, Any]] = {}
    
    for snap in snapshots:
        if not snap.depth1_summary:
            continue
            
        for mutation_type, patterns in snap.depth1_summary.items():
            for pattern, stats in patterns.items():
                key = f"{mutation_type}:{pattern}"
                if key not in pattern_stats:
                    pattern_stats[key] = {
                        "pattern": pattern,
                        "mutation_type": mutation_type,
                        "rates": [],
                        "confidences": [],
                        "samples": 0
                    }
                
                rate = stats.get("success_rate", 0)
                conf = stats.get("confidence", 0.5)
                count = stats.get("sample_count", 1)
                
                pattern_stats[key]["rates"].append(rate)
                pattern_stats[key]["confidences"].append(conf)
                pattern_stats[key]["samples"] += count
    
    # Calculate lifts (baseline = 0.5 = random success)
    BASELINE = 0.5
    lifts = []
    
    for key, data in pattern_stats.items():
        if data["samples"] < min_samples:
            continue
            
        avg_rate = sum(data["rates"]) / len(data["rates"]) if data["rates"] else 0
        avg_conf = sum(data["confidences"]) / len(data["confidences"]) if data["confidences"] else 0
        
        lift = (avg_rate - BASELINE) / BASELINE if BASELINE > 0 else 0
        
        lifts.append(PatternLiftResult(
            pattern=data["pattern"],
            mutation_type=data["mutation_type"],
            baseline_rate=BASELINE,
            current_rate=avg_rate,
            lift=lift,
            sample_count=data["samples"],
            confidence=avg_conf
        ))
    
    # Sort by lift
    lifts.sort(key=lambda x: x.lift, reverse=True)
    return lifts[:limit]


@router.get("/experiments", response_model=List[ExperimentStatus])
async def get_experiments_list(
    status: Optional[str] = Query(None, regex="^(tracking|complete|needs_decision)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _curator = Depends(require_curator)
):
    """
    Get status of active depth experiments.
    
    Delegates to DepthExperimentService for consistent logic.
    """
    from app.services.depth_experiments import depth_experiment_service
    
    # Get all active experiments from service
    all_experiments = await depth_experiment_service.get_active_experiments(db, limit * 2)
    
    # Transform to response model and filter by status
    experiments = []
    for exp in all_experiments:
        # Map service status to API status
        exp_status = "tracking"
        days = exp.get("days_tracked", 0)
        confidence = exp.get("decision", {}).get("confidence", 0) if exp.get("decision") else 0
        
        if days >= EXPERIMENT_MIN_DAYS:
            exp_status = "complete" if confidence >= CONFIDENCE_HIGH else "needs_decision"
        
        # Apply status filter
        if status and exp_status != status:
            continue
        
        experiments.append(ExperimentStatus(
            parent_id=exp.get("parent_id", ""),
            parent_title=exp.get("parent_title", ""),
            current_depth=exp.get("current_depth", 1),
            days_tracked=days,
            variants_count=exp.get("variants_count", 0),
            top_variant=exp.get("decision", {}).get("top_mutation_pattern") if exp.get("decision") else None,
            top_variant_rate=confidence,
            status=exp_status
        ))
        
        if len(experiments) >= limit:
            break
    
    return experiments


@router.post("/rl-update")
async def trigger_rl_policy_update(
    db: AsyncSession = Depends(get_db),
    _curator = Depends(require_curator),
):
    """
    RL-lite 정책 배치 업데이트 트리거 (Phase 4 #7)
    
    This endpoint:
    1. Aggregates customization patterns from template usage
    2. Updates TemplateSeed defaults based on evidence
    3. Returns winning patterns and update report
    
    Usually called weekly, but can be triggered manually.
    """
    from app.services.bandit_policy import batch_updater
    
    # Run batch policy update (internally fetches customization patterns)
    policy_result = await batch_updater.update_template_defaults(db)
    
    return {
        "status": "completed",
        "timestamp": iso_now(),
        "policy_update": policy_result,
        "message": "RL-lite policy batch update completed successfully",
    }


@router.get("/depth-experiments/{parent_id}")
async def get_depth_experiment_status(
    parent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    특정 Parent의 Depth 실험 상태 조회 (Phase 4 #3)
    
    Returns:
        - current_depth: 현재 실험 깊이 (1 or 2)
        - variants_count: 생성된 변주 수
        - ready_for_depth2: Depth2 시작 가능 여부
        - decision: 최신 Decision 정보
        - recommendation: 다음 단계 권장 사항
    """
    from app.services.depth_experiments import depth_experiment_service
    
    return await depth_experiment_service.get_experiment_status(db, parent_id)


@router.post("/depth-experiments/{parent_id}/depth2")
async def start_depth2(
    parent_id: str,
    db: AsyncSession = Depends(get_db),
    _curator = Depends(require_curator),
):
    """
    Depth2 실험 시작 (Phase 4 #3)
    
    Depth1 Decision을 기반으로 심화 실험을 시작합니다.
    - 최소 14일 추적 후
    - Confidence 0.6 이상
    - Winning pattern 확인 후 실행 가능
    """
    from app.services.depth_experiments import depth_experiment_service
    
    return await depth_experiment_service.start_depth2_experiment(db, parent_id)


@router.get("/depth-experiments")
async def list_active_experiments(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _curator = Depends(require_curator),
):
    """
    활성 Depth 실험 목록 조회
    """
    from app.services.depth_experiments import depth_experiment_service
    
    experiments = await depth_experiment_service.get_active_experiments(db, limit)
    return {"experiments": experiments, "total": len(experiments)}


# ==================
# Helper Functions
# ==================

async def _calculate_weekly_kpi(
    db: AsyncSession,
    weeks_ago: int = 0
) -> WeeklyKPI:
    """Calculate KPI for a specific week."""
    
    # Calculate week boundaries
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday() + 7 * weeks_ago)
    week_end = week_start + timedelta(days=6)
    
    start_dt = datetime.combine(week_start, datetime.min.time())
    end_dt = datetime.combine(week_end, datetime.max.time())
    
    # Total analyses this week
    analyses = await db.execute(
        select(func.count(EvidenceSnapshot.id))
        .where(and_(
            EvidenceSnapshot.created_at >= start_dt,
            EvidenceSnapshot.created_at <= end_dt
        ))
    )
    total_analyses = analyses.scalar() or 0
    
    # Successful patterns (confidence > 0.7)
    successful = await db.execute(
        select(func.count(EvidenceSnapshot.id))
        .where(and_(
            EvidenceSnapshot.created_at >= start_dt,
            EvidenceSnapshot.created_at <= end_dt,
            EvidenceSnapshot.confidence >= 0.7
        ))
    )
    successful_patterns = successful.scalar() or 0
    
    # Average confidence
    avg_conf = await db.execute(
        select(func.avg(EvidenceSnapshot.confidence))
        .where(and_(
            EvidenceSnapshot.created_at >= start_dt,
            EvidenceSnapshot.created_at <= end_dt
        ))
    )
    avg_confidence = avg_conf.scalar() or 0.0
    
    # Cluster growth
    new_clusters = await db.execute(
        select(func.count(PatternCluster.id))
        .where(and_(
            PatternCluster.created_at >= start_dt,
            PatternCluster.created_at <= end_dt
        ))
    )
    cluster_growth = new_clusters.scalar() or 0
    
    # Outliers promoted
    promoted = await db.execute(
        select(func.count(OutlierItem.id))
        .where(and_(
            OutlierItem.status == "promoted",
            OutlierItem.crawled_at >= start_dt,
            OutlierItem.crawled_at <= end_dt
        ))
    )
    outliers_promoted = promoted.scalar() or 0
    
    # Top patterns (simplified - use pattern_lifts endpoint for full data)
    top_patterns = []
    
    return WeeklyKPI(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        total_analyses=total_analyses,
        successful_patterns=successful_patterns,
        avg_confidence=float(avg_confidence),
        top_patterns=top_patterns,
        cluster_growth=cluster_growth,
        outliers_promoted=outliers_promoted
    )
