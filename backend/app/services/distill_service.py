"""
DistillRun Service

P3 Roadmap: 주간 DistillRun 자동화
- 클러스터 선택 → NotebookLM 투입 → Pack 생성 → 승격 검증
- 3축 승격 기준: Compliance + Outcome + Robustness

워크플로우:
1. Cluster 선택 (가장 세션 많은 것)
2. DistillRun 생성 (VDG refs)
3. NotebookLM 프롬프트 생성
4. contract_candidates 추출
5. Pack 생성 (canary 10%)
6. 1주 후 성과 비교 → 승격/롤백
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import timedelta

from app.utils.time import iso_now, generate_short_id, utcnow
from app.schemas.vdg_v4 import ContentCluster, ClusterKid
from app.services.cluster_service import get_cluster_service

logger = logging.getLogger(__name__)


# ====================
# DISTILL TYPES
# ====================

class DistillStatus(str, Enum):
    """DistillRun status."""
    CREATED = "created"
    RUNNING = "running"
    CANDIDATES_EXTRACTED = "candidates_extracted"
    PACK_GENERATED = "pack_generated"
    CANARY_DEPLOYED = "canary_deployed"
    EVALUATING = "evaluating"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class PromotionDecision(str, Enum):
    """3-Axis promotion decision."""
    PROMOTE = "promote"
    ROLLBACK = "rollback"
    PENDING = "pending"
    NEEDS_MORE_DATA = "needs_more_data"


@dataclass
class ContractCandidates:
    """Extracted candidates from NotebookLM distillation."""
    dna_invariants: List[Dict[str, Any]] = field(default_factory=list)
    mutation_slots: List[Dict[str, Any]] = field(default_factory=list)
    forbidden_mutations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dna_invariants": self.dna_invariants,
            "mutation_slots": self.mutation_slots,
            "forbidden_mutations": self.forbidden_mutations
        }


@dataclass
class AxisMetrics:
    """3-Axis metrics for promotion evaluation."""
    # Axis 1: Compliance Lift
    compliance_lift: float = 0.0  # vs control (target: >= +0.15)
    compliance_sessions: int = 0
    
    # Axis 2: Outcome Lift
    outcome_lift: float = 0.0  # completion rate, upload rate improvement
    outcome_sessions: int = 0
    
    # Axis 3: Robustness (Diversity)
    cluster_count: int = 0  # target: >= 2
    persona_count: int = 0  # target: >= 2
    negative_evidence_rate: float = 0.0  # target: < 20%
    
    def is_promotion_ready(self) -> bool:
        """Check if all 3 axes pass thresholds."""
        return (
            self.compliance_lift >= 0.15 and
            self.compliance_sessions >= 50 and
            self.outcome_lift >= 0.0 and
            self.cluster_count >= 2 and
            self.persona_count >= 2 and
            self.negative_evidence_rate < 0.20
        )
    
    def get_failing_axes(self) -> List[str]:
        """Get list of failing axes."""
        failing = []
        if self.compliance_lift < 0.15:
            failing.append(f"compliance_lift: {self.compliance_lift:.2%} (need >=15%)")
        if self.compliance_sessions < 50:
            failing.append(f"compliance_sessions: {self.compliance_sessions} (need >=50)")
        if self.outcome_lift < 0.0:
            failing.append(f"outcome_lift: {self.outcome_lift:.2%} (need >=0%)")
        if self.cluster_count < 2:
            failing.append(f"cluster_count: {self.cluster_count} (need >=2)")
        if self.persona_count < 2:
            failing.append(f"persona_count: {self.persona_count} (need >=2)")
        if self.negative_evidence_rate >= 0.20:
            failing.append(f"negative_evidence_rate: {self.negative_evidence_rate:.2%} (need <20%)")
        return failing


@dataclass
class DistillRun:
    """Single distillation run for a cluster."""
    run_id: str
    cluster_id: str
    cluster_name: str
    
    # Source references
    parent_vdg_id: str
    kid_vdg_ids: List[str]
    source_refs: List[str]  # All VDG IDs
    
    # Status
    status: DistillStatus = DistillStatus.CREATED
    
    # Prompt
    prompt_version: str = "v1"
    distill_prompt: str = ""
    
    # Extracted candidates
    candidates: Optional[ContractCandidates] = None
    
    # Generated Pack
    pack_id: Optional[str] = None
    parent_pack_id: Optional[str] = None
    experiment_id: Optional[str] = None
    
    # Canary deployment
    canary_ratio: float = 0.10  # 10% canary
    canary_start: Optional[str] = None
    canary_end: Optional[str] = None
    
    # Evaluation
    axis_metrics: Optional[AxisMetrics] = None
    promotion_decision: PromotionDecision = PromotionDecision.PENDING
    rollback_count: int = 0  # 2회 연속 음수 → 롤백
    
    # Provenance
    created_at: str = ""
    updated_at: str = ""
    scheduled_evaluation_at: Optional[str] = None


# ====================
# NOTEBOOKLM PROMPT TEMPLATES
# ====================

DISTILL_PROMPT_V1 = """이 클러스터의 Parent와 Kids를 분석해서:

## Parent 영상 (바이럴 성공)
- VDG ID: {parent_vdg_id}
- Content ID: {parent_content_id}
- Tier: {parent_tier}

## Kids 영상 (변주)
{kids_list}

---

위 영상들을 분석해서 다음을 JSON으로 추출해주세요:

### 1. 불변 규칙 (DNA Invariants)
- 모든 성공 영상에서 유지된 요소
- 실패 영상에서 깨진 요소
- 형식: {{"rule_id": "string", "description": "string", "checkpoint": "hook_punch|mid_valley|final_punchline"}}

### 2. 가변 슬롯 (Mutation Slots)
- 성공 영상 간에도 다른 요소
- 창의성 발휘 가능 영역
- 형식: {{"slot_id": "string", "description": "string", "allowed_range": "string"}}

### 3. 금지 변형 (Forbidden Mutations)
- 실패 영상의 공통 실수
- 절대 하면 안 되는 것
- 형식: {{"forbidden_id": "string", "description": "string", "reason": "string"}}

JSON 형태로 출력:
```json
{{
  "dna_invariants": [...],
  "mutation_slots": [...],
  "forbidden_mutations": [...]
}}
```
"""


class DistillRunService:
    """
    P3 DistillRun management service.
    
    Usage:
        service = get_distill_service()
        
        # Create run from cluster
        run = service.create_from_cluster("cluster_xxx")
        
        # Generate NotebookLM prompt
        prompt = service.generate_distill_prompt(run.run_id)
        
        # After NotebookLM extraction, update candidates
        service.update_candidates(run.run_id, candidates_json)
        
        # Generate Pack from candidates
        pack_id = service.generate_pack(run.run_id)
        
        # Deploy canary and schedule evaluation
        service.deploy_canary(run.run_id)
        
        # After 1 week, evaluate and decide
        decision = service.evaluate_and_decide(run.run_id)
    """
    
    def __init__(self):
        """Initialize with in-memory storage (MVP)."""
        self._runs: Dict[str, DistillRun] = {}
        self._cluster_service = get_cluster_service()
    
    # ====================
    # CREATE / LIST
    # ====================
    
    def create_from_cluster(self, cluster_id: str) -> DistillRun:
        """Create DistillRun from a cluster."""
        cluster = self._cluster_service.get_cluster(cluster_id)
        if not cluster:
            raise ValueError(f"Cluster not found: {cluster_id}")
        
        if not cluster.is_distill_ready():
            raise ValueError(f"Cluster not distill-ready: {cluster_id}")
        
        run_id = f"distill_{generate_short_id()}"
        now = iso_now()
        
        # Collect all VDG IDs
        kid_vdg_ids = [k.vdg_id for k in cluster.kids]
        source_refs = [cluster.parent_vdg_id] + kid_vdg_ids
        
        run = DistillRun(
            run_id=run_id,
            cluster_id=cluster_id,
            cluster_name=cluster.cluster_name,
            parent_vdg_id=cluster.parent_vdg_id,
            kid_vdg_ids=kid_vdg_ids,
            source_refs=source_refs,
            created_at=now,
            updated_at=now
        )
        
        self._runs[run_id] = run
        
        # Link to cluster
        cluster.distill_run_ids.append(run_id)
        
        logger.info(f"Created DistillRun: {run_id} from cluster {cluster_id}")
        return run
    
    def get_run(self, run_id: str) -> Optional[DistillRun]:
        """Get DistillRun by ID."""
        return self._runs.get(run_id)
    
    def list_runs(self, status: Optional[DistillStatus] = None) -> List[DistillRun]:
        """List all DistillRuns, optionally filtered by status."""
        runs = list(self._runs.values())
        if status:
            runs = [r for r in runs if r.status == status]
        return runs
    
    # ====================
    # DISTILLATION STEPS
    # ====================
    
    def generate_distill_prompt(self, run_id: str) -> str:
        """Generate NotebookLM prompt for distillation."""
        run = self._runs.get(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        cluster = self._cluster_service.get_cluster(run.cluster_id)
        if not cluster:
            raise ValueError(f"Cluster not found: {run.cluster_id}")
        
        # Build kids list
        kids_list = ""
        for i, kid in enumerate(cluster.kids, 1):
            status = "✅ 성공" if kid.success else "❌ 실패"
            kids_list += f"- {i}. VDG: {kid.vdg_id} | Type: {kid.variation_type} | {status}\n"
        
        prompt = DISTILL_PROMPT_V1.format(
            parent_vdg_id=cluster.parent_vdg_id,
            parent_content_id=cluster.parent_content_id,
            parent_tier=cluster.parent_tier,
            kids_list=kids_list
        )
        
        run.distill_prompt = prompt
        run.status = DistillStatus.RUNNING
        run.updated_at = iso_now()
        
        return prompt
    
    def update_candidates(
        self,
        run_id: str,
        candidates_json: Dict[str, Any]
    ) -> ContractCandidates:
        """Update run with extracted candidates from NotebookLM."""
        run = self._runs.get(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        candidates = ContractCandidates(
            dna_invariants=candidates_json.get("dna_invariants", []),
            mutation_slots=candidates_json.get("mutation_slots", []),
            forbidden_mutations=candidates_json.get("forbidden_mutations", [])
        )
        
        run.candidates = candidates
        run.status = DistillStatus.CANDIDATES_EXTRACTED
        run.updated_at = iso_now()
        
        logger.info(
            f"Updated candidates for {run_id}: "
            f"{len(candidates.dna_invariants)} invariants, "
            f"{len(candidates.mutation_slots)} slots, "
            f"{len(candidates.forbidden_mutations)} forbidden"
        )
        
        return candidates
    
    def generate_pack(
        self,
        run_id: str,
        parent_pack_id: Optional[str] = None
    ) -> str:
        """Generate Pack from extracted candidates."""
        run = self._runs.get(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        if not run.candidates:
            raise ValueError(f"No candidates extracted for {run_id}")
        
        # Generate Pack ID and experiment ID
        pack_id = f"pack_{generate_short_id()}"
        experiment_id = f"exp_{generate_short_id()}"
        
        run.pack_id = pack_id
        run.parent_pack_id = parent_pack_id
        run.experiment_id = experiment_id
        run.status = DistillStatus.PACK_GENERATED
        run.updated_at = iso_now()
        
        # TODO: Actually create Pack using DirectorCompiler
        # For now, just track the intent
        
        logger.info(f"Generated Pack {pack_id} for run {run_id}")
        return pack_id
    
    def deploy_canary(self, run_id: str, duration_days: int = 7) -> Dict[str, Any]:
        """Deploy canary and schedule evaluation."""
        run = self._runs.get(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        if not run.pack_id:
            raise ValueError(f"No Pack generated for {run_id}")
        
        now = utcnow()
        canary_end = now + timedelta(days=duration_days)
        
        run.canary_start = iso_now()
        run.canary_end = canary_end.isoformat()
        run.scheduled_evaluation_at = canary_end.isoformat()
        run.status = DistillStatus.CANARY_DEPLOYED
        run.updated_at = iso_now()
        
        logger.info(f"Deployed canary for {run_id}, evaluation at {run.scheduled_evaluation_at}")
        
        return {
            "run_id": run_id,
            "pack_id": run.pack_id,
            "canary_ratio": run.canary_ratio,
            "canary_start": run.canary_start,
            "canary_end": run.canary_end,
            "scheduled_evaluation_at": run.scheduled_evaluation_at
        }
    
    # ====================
    # EVALUATION (3-Axis)
    # ====================
    
    def evaluate_and_decide(
        self,
        run_id: str,
        metrics: Optional[AxisMetrics] = None
    ) -> Dict[str, Any]:
        """
        Evaluate canary performance and make promotion decision.
        
        3-Axis Criteria:
        1. Compliance Lift >= +15% (vs control)
        2. Outcome Lift >= 0% (completion, upload)
        3. Robustness: 2+ clusters, 2+ personas, <20% negative evidence
        """
        run = self._runs.get(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        # Use provided metrics or fetch from log quality
        if metrics:
            run.axis_metrics = metrics
        else:
            # TODO: Fetch actual metrics from session logs
            run.axis_metrics = AxisMetrics()  # Empty for now
        
        run.status = DistillStatus.EVALUATING
        run.updated_at = iso_now()
        
        # Check if promotion ready
        if not run.axis_metrics:
            run.promotion_decision = PromotionDecision.NEEDS_MORE_DATA
            return {
                "run_id": run_id,
                "decision": run.promotion_decision.value,
                "reason": "No metrics available"
            }
        
        if run.axis_metrics.compliance_sessions < 10:
            run.promotion_decision = PromotionDecision.NEEDS_MORE_DATA
            return {
                "run_id": run_id,
                "decision": run.promotion_decision.value,
                "reason": f"Only {run.axis_metrics.compliance_sessions} sessions, need 10+"
            }
        
        # Check 3-Axis criteria
        if run.axis_metrics.is_promotion_ready():
            run.promotion_decision = PromotionDecision.PROMOTE
            run.status = DistillStatus.PROMOTED
            reason = "All 3 axes passed"
        else:
            # Check rollback condition: 2+ consecutive negative outcome_lift
            if run.axis_metrics.outcome_lift < 0:
                run.rollback_count += 1
            else:
                run.rollback_count = 0
            
            if run.rollback_count >= 2:
                run.promotion_decision = PromotionDecision.ROLLBACK
                run.status = DistillStatus.ROLLED_BACK
                reason = "2 consecutive negative outcome_lift"
            else:
                run.promotion_decision = PromotionDecision.PENDING
                reason = f"Failing: {run.axis_metrics.get_failing_axes()}"
        
        run.updated_at = iso_now()
        
        return {
            "run_id": run_id,
            "decision": run.promotion_decision.value,
            "status": run.status.value,
            "reason": reason,
            "metrics": {
                "compliance_lift": run.axis_metrics.compliance_lift,
                "outcome_lift": run.axis_metrics.outcome_lift,
                "cluster_count": run.axis_metrics.cluster_count,
                "persona_count": run.axis_metrics.persona_count,
                "negative_evidence_rate": run.axis_metrics.negative_evidence_rate
            },
            "failing_axes": run.axis_metrics.get_failing_axes()
        }
    
    # ====================
    # WEEKLY SCHEDULER
    # ====================
    
    def get_best_cluster_for_distill(self) -> Optional[str]:
        """Get best cluster for weekly distill (most session data)."""
        clusters = self._cluster_service.list_clusters(distill_ready_only=True)
        
        if not clusters:
            return None
        
        # For now, just return first distill-ready cluster
        # TODO: Sort by session count when session data is linked
        return clusters[0].cluster_id
    
    def run_weekly_distill(self) -> Dict[str, Any]:
        """
        Run weekly distillation workflow.
        
        Steps:
        1. Select best cluster
        2. Create DistillRun
        3. Generate prompt
        4. (Manual) Run NotebookLM
        5. (Manual) Update candidates
        6. Generate Pack
        7. Deploy canary
        8. Schedule evaluation
        """
        # Step 1: Select cluster
        cluster_id = self.get_best_cluster_for_distill()
        if not cluster_id:
            return {
                "success": False,
                "error": "No distill-ready clusters available"
            }
        
        try:
            # Step 2: Create run
            run = self.create_from_cluster(cluster_id)
            
            # Step 3: Generate prompt
            prompt = self.generate_distill_prompt(run.run_id)
            
            return {
                "success": True,
                "run_id": run.run_id,
                "cluster_id": cluster_id,
                "status": run.status.value,
                "next_step": "Run NotebookLM with generated prompt, then call update_candidates",
                "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt
            }
            
        except Exception as e:
            logger.error(f"Weekly distill failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ====================
    # STATS
    # ====================
    
    def get_distill_stats(self) -> Dict[str, Any]:
        """Get distillation statistics."""
        runs = list(self._runs.values())
        
        status_counts = {}
        for status in DistillStatus:
            status_counts[status.value] = sum(1 for r in runs if r.status == status)
        
        decision_counts = {}
        for decision in PromotionDecision:
            decision_counts[decision.value] = sum(1 for r in runs if r.promotion_decision == decision)
        
        return {
            "total_runs": len(runs),
            "by_status": status_counts,
            "by_decision": decision_counts,
            "promoted_count": decision_counts.get("promote", 0),
            "rollback_count": decision_counts.get("rollback", 0),
            "pending_evaluation": sum(1 for r in runs if r.status == DistillStatus.CANARY_DEPLOYED)
        }


# Singleton
_distill_service_instance = None


def get_distill_service() -> DistillRunService:
    """Get singleton DistillRunService instance."""
    global _distill_service_instance
    if _distill_service_instance is None:
        _distill_service_instance = DistillRunService()
    return _distill_service_instance
