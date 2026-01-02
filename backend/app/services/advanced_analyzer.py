"""
Phase 5+: Advanced Session Analyzer

고급 자동학습 시스템:
- CoachingIntervention/CoachingOutcome 기록
- metric_before/after 비교
- AxisMetrics 계산 (3-Axis 평가)
- Canary 그룹 분류
- Negative Evidence 탐지
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.utils.time import iso_now, utcnow
from app.schemas.vdg_v4 import (
    CoachingIntervention,
    CoachingOutcome,
    SignalPerformance,
    InvariantCandidate,
    PROMOTION_THRESHOLDS,
)
from app.schemas.director_pack import DirectorPack, DNAInvariant
from app.services.evidence_updater import get_signal_tracker, SignalTracker

logger = logging.getLogger(__name__)


# ====================
# ENHANCED SIGNAL WITH METRICS
# ====================

@dataclass
class WeightedSignal:
    """
    메트릭 기반 가중 신호 (Phase 5+)
    
    기본 SignalPerformance 확장:
    - metric 개선율 추적
    - 시간 가중치 (최근 데이터 우선)
    - 클러스터/페르소나 다양성
    """
    signal_key: str
    element: str
    value: str
    
    # Metric improvements
    metric_improvements: List[float] = field(default_factory=list)
    metric_ids: List[str] = field(default_factory=list)
    
    # Time-weighted success
    outcomes: List[Tuple[bool, float, str]] = field(default_factory=list)  # (success, timestamp_weight, timestamp)
    
    # Diversity tracking
    cluster_ids: set = field(default_factory=set)
    persona_ids: set = field(default_factory=set)
    content_ids: set = field(default_factory=set)
    
    # Compliance vs Control
    coached_sessions: int = 0
    coached_complied: int = 0
    control_sessions: int = 0
    control_complied: int = 0
    
    # Negative evidence
    negative_count: int = 0
    negative_reasons: List[str] = field(default_factory=list)
    
    @property
    def weighted_success_rate(self) -> float:
        """시간 가중 성공률 (최근 데이터 2x 가중)"""
        if not self.outcomes:
            return 0.0
        
        total_weight = 0.0
        success_weight = 0.0
        
        for success, weight, _ in self.outcomes:
            total_weight += weight
            if success:
                success_weight += weight
        
        return success_weight / total_weight if total_weight > 0 else 0.0
    
    @property
    def avg_metric_improvement(self) -> float:
        """평균 메트릭 개선율"""
        if not self.metric_improvements:
            return 0.0
        return sum(self.metric_improvements) / len(self.metric_improvements)
    
    @property
    def compliance_lift(self) -> float:
        """Compliance Lift: (coached - control) / control"""
        coached_rate = self.coached_complied / self.coached_sessions if self.coached_sessions > 0 else 0
        control_rate = self.control_complied / self.control_sessions if self.control_sessions > 0 else 0
        
        if control_rate == 0:
            return coached_rate  # No control baseline
        return (coached_rate - control_rate) / control_rate
    
    @property
    def negative_evidence_rate(self) -> float:
        """Negative evidence 비율"""
        total = len(self.outcomes)
        return self.negative_count / total if total > 0 else 0.0
    
    def meets_promotion_criteria(self) -> bool:
        """3-Axis 승격 기준 충족 여부"""
        return (
            len(self.outcomes) >= 50 and  # 충분한 데이터
            self.compliance_lift >= 0.15 and  # Axis 1: +15%
            self.avg_metric_improvement >= 0 and  # Axis 2: 개선
            len(self.cluster_ids) >= 2 and  # Axis 3: 클러스터 다양성
            len(self.persona_ids) >= 2 and  # Axis 3: 페르소나 다양성
            self.negative_evidence_rate < 0.20  # Axis 3: 부정 증거 < 20%
        )


# ====================
# AXIS METRICS CALCULATOR
# ====================

@dataclass
class LiveAxisMetrics:
    """실시간 3-Axis 메트릭 계산"""
    
    # Axis 1: Compliance Lift
    compliance_lift: float = 0.0
    compliance_coached_sessions: int = 0
    compliance_control_sessions: int = 0
    
    # Axis 2: Outcome/Metric Lift
    outcome_lift: float = 0.0
    avg_metric_improvement: float = 0.0
    total_outcomes: int = 0
    
    # Axis 3: Robustness
    cluster_count: int = 0
    persona_count: int = 0
    negative_evidence_rate: float = 0.0
    negative_count: int = 0
    
    # Status
    is_promotion_ready: bool = False
    failing_axes: List[str] = field(default_factory=list)
    
    def calculate_readiness(self):
        """승격 준비 상태 계산"""
        self.failing_axes = []
        
        if self.compliance_lift < 0.15:
            self.failing_axes.append(f"compliance_lift: {self.compliance_lift:.1%} (need ≥15%)")
        if self.compliance_coached_sessions < 50:
            self.failing_axes.append(f"sessions: {self.compliance_coached_sessions} (need ≥50)")
        if self.outcome_lift < 0:
            self.failing_axes.append(f"outcome_lift: {self.outcome_lift:.1%} (need ≥0%)")
        if self.cluster_count < 2:
            self.failing_axes.append(f"clusters: {self.cluster_count} (need ≥2)")
        if self.persona_count < 2:
            self.failing_axes.append(f"personas: {self.persona_count} (need ≥2)")
        if self.negative_evidence_rate >= 0.20:
            self.failing_axes.append(f"negative_rate: {self.negative_evidence_rate:.1%} (need <20%)")
        
        self.is_promotion_ready = len(self.failing_axes) == 0


# ====================
# ADVANCED SESSION ANALYZER
# ====================

class AdvancedSessionAnalyzer:
    """
    Phase 5+: 고급 세션 분석기
    
    기능:
    1. CoachingIntervention 기록
    2. CoachingOutcome (metric_before/after) 기록
    3. WeightedSignal 업데이트
    4. AxisMetrics 계산
    5. Canary 그룹 분류
    6. Negative Evidence 탐지
    """
    
    TIME_DECAY_DAYS = 30  # 30일 이후 데이터는 가중치 감소
    
    def __init__(self):
        self._signals: Dict[str, WeightedSignal] = {}
        self._interventions: List[CoachingIntervention] = []
        self._outcomes: List[CoachingOutcome] = []
        self._base_tracker = get_signal_tracker()
    
    # ====================
    # INTERVENTION RECORDING
    # ====================
    
    def record_intervention(
        self,
        session_id: str,
        rule_id: str,
        domain: str,
        priority: str,
        message: str,
        t_sec: float,
        metric_id: Optional[str] = None,
        metric_before: Optional[float] = None,
        assignment: str = "coached",  # coached | control
        persona: str = "chill_guide",
    ) -> CoachingIntervention:
        """
        코칭 개입 기록
        """
        intervention_id = f"int_{session_id}_{int(t_sec * 1000)}"
        
        intervention = CoachingIntervention(
            intervention_id=intervention_id,
            session_id=session_id,
            rule_id=rule_id,
            domain=domain,
            priority=priority,
            coach_line=message,
            t_sec=t_sec,
            metric_id=metric_id,
            metric_before=metric_before,
            persona_preset=persona,
            assignment=assignment,
        )
        
        self._interventions.append(intervention)
        logger.debug(f"📝 Intervention recorded: {intervention_id}")
        
        return intervention
    
    # ====================
    # OUTCOME RECORDING
    # ====================
    
    def record_outcome(
        self,
        intervention_id: str,
        user_response: str,  # complied, ignored, questioned, retake
        compliance_detected: bool,
        metric_after: Optional[float] = None,
        metric_before: Optional[float] = None,
        is_negative_evidence: bool = False,
        negative_reason: Optional[str] = None,
        cluster_id: Optional[str] = None,
        persona: str = "chill_guide",
    ) -> CoachingOutcome:
        """
        코칭 결과 기록 (metric_before/after 비교)
        """
        # Calculate improvement
        improvement = None
        if metric_before is not None and metric_after is not None:
            if metric_before != 0:
                improvement = (metric_after - metric_before) / abs(metric_before)
            else:
                improvement = metric_after
        
        outcome = CoachingOutcome(
            intervention_id=intervention_id,
            user_response=user_response,
            compliance_detected=compliance_detected,
            metric_before=metric_before,
            metric_after=metric_after,
            improvement=improvement,
            is_negative_evidence=is_negative_evidence,
            negative_reason=negative_reason,
            observed_at=iso_now(),
        )
        
        self._outcomes.append(outcome)
        
        # Update weighted signal
        intervention = self._get_intervention(intervention_id)
        if intervention:
            self._update_weighted_signal(
                intervention=intervention,
                outcome=outcome,
                cluster_id=cluster_id,
                persona=persona,
            )
        
        logger.debug(f"📊 Outcome recorded: {intervention_id}, compliance={compliance_detected}, improvement={improvement}")
        
        return outcome
    
    def _get_intervention(self, intervention_id: str) -> Optional[CoachingIntervention]:
        """Get intervention by ID"""
        for inv in self._interventions:
            if inv.intervention_id == intervention_id:
                return inv
        return None
    
    # ====================
    # WEIGHTED SIGNAL UPDATE
    # ====================
    
    def _update_weighted_signal(
        self,
        intervention: CoachingIntervention,
        outcome: CoachingOutcome,
        cluster_id: Optional[str],
        persona: str,
    ):
        """WeightedSignal 업데이트"""
        signal_key = f"{intervention.domain}.{intervention.rule_id}"
        
        if signal_key not in self._signals:
            self._signals[signal_key] = WeightedSignal(
                signal_key=signal_key,
                element=intervention.domain,
                value=intervention.rule_id,
            )
        
        signal = self._signals[signal_key]
        
        # Time weight calculation (최근 데이터 더 높은 가중치)
        now = utcnow()
        weight = 1.0  # 최근 데이터는 가중치 1.0
        
        # Add outcome with weight
        signal.outcomes.append((
            outcome.compliance_detected,
            weight,
            iso_now(),
        ))
        
        # Metric improvement
        if outcome.improvement is not None:
            signal.metric_improvements.append(outcome.improvement)
            if intervention.metric_id:
                signal.metric_ids.append(intervention.metric_id)
        
        # Diversity
        if cluster_id:
            signal.cluster_ids.add(cluster_id)
        signal.persona_ids.add(persona)
        
        # Coached vs Control
        if intervention.assignment == "coached":
            signal.coached_sessions += 1
            if outcome.compliance_detected:
                signal.coached_complied += 1
        else:
            signal.control_sessions += 1
            if outcome.compliance_detected:
                signal.control_complied += 1
        
        # Negative evidence
        if outcome.is_negative_evidence:
            signal.negative_count += 1
            if outcome.negative_reason:
                signal.negative_reasons.append(outcome.negative_reason)
        
        # Also update base tracker for compatibility
        self._base_tracker.track_outcome(
            element=intervention.domain,
            value=intervention.rule_id,
            success=outcome.compliance_detected,
            content_id=intervention.session_id,
        )
    
    # ====================
    # AXIS METRICS CALCULATION
    # ====================
    
    def calculate_axis_metrics(self, signal_key: Optional[str] = None) -> LiveAxisMetrics:
        """
        실시간 3-Axis 메트릭 계산
        
        Args:
            signal_key: 특정 시그널만 계산 (없으면 전체)
        """
        metrics = LiveAxisMetrics()
        
        signals_to_check = [self._signals[signal_key]] if signal_key else list(self._signals.values())
        
        if not signals_to_check:
            return metrics
        
        # Aggregate across signals
        total_coached = 0
        total_coached_complied = 0
        total_control = 0
        total_control_complied = 0
        total_improvements = []
        all_clusters = set()
        all_personas = set()
        total_outcomes = 0
        total_negative = 0
        
        for signal in signals_to_check:
            total_coached += signal.coached_sessions
            total_coached_complied += signal.coached_complied
            total_control += signal.control_sessions
            total_control_complied += signal.control_complied
            total_improvements.extend(signal.metric_improvements)
            all_clusters.update(signal.cluster_ids)
            all_personas.update(signal.persona_ids)
            total_outcomes += len(signal.outcomes)
            total_negative += signal.negative_count
        
        # Calculate metrics
        coached_rate = total_coached_complied / total_coached if total_coached > 0 else 0
        control_rate = total_control_complied / total_control if total_control > 0 else 0
        
        metrics.compliance_coached_sessions = total_coached
        metrics.compliance_control_sessions = total_control
        metrics.compliance_lift = (coached_rate - control_rate) / control_rate if control_rate > 0 else coached_rate
        
        metrics.avg_metric_improvement = sum(total_improvements) / len(total_improvements) if total_improvements else 0
        metrics.outcome_lift = metrics.avg_metric_improvement
        metrics.total_outcomes = total_outcomes
        
        metrics.cluster_count = len(all_clusters)
        metrics.persona_count = len(all_personas)
        metrics.negative_count = total_negative
        metrics.negative_evidence_rate = total_negative / total_outcomes if total_outcomes > 0 else 0
        
        metrics.calculate_readiness()
        
        return metrics
    
    # ====================
    # CANARY MANAGEMENT
    # ====================
    
    def should_assign_canary(self, session_id: str) -> bool:
        """
        세션을 Canary 그룹에 할당할지 결정 (10%)
        """
        # Simple hash-based assignment
        hash_value = hash(session_id) % 100
        return hash_value < 10  # 10% canary
    
    def get_assignment(self, session_id: str) -> str:
        """
        세션 할당 결정: coached | control
        
        Control 그룹은 Goodhart 방지를 위해 10% 유지
        """
        hash_value = hash(session_id) % 100
        if hash_value < 10:
            return "control"
        return "coached"
    
    # ====================
    # PROMOTION CANDIDATES
    # ====================
    
    def check_promotions(self) -> List[Tuple[str, LiveAxisMetrics]]:
        """
        승격 가능 시그널 확인
        
        Returns:
            List of (signal_key, axis_metrics) for signals ready for promotion
        """
        ready = []
        
        for signal_key, signal in self._signals.items():
            if signal.meets_promotion_criteria():
                metrics = self.calculate_axis_metrics(signal_key)
                ready.append((signal_key, metrics))
                logger.info(f"🎉 Signal ready for promotion: {signal_key}")
        
        return ready
    
    # ====================
    # STATS / EXPORT
    # ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            "signals_tracked": len(self._signals),
            "interventions_recorded": len(self._interventions),
            "outcomes_recorded": len(self._outcomes),
            "promotion_ready": len(self.check_promotions()),
            "global_metrics": self.calculate_axis_metrics().__dict__,
        }
    
    def get_signal(self, signal_key: str) -> Optional[WeightedSignal]:
        """Get specific signal"""
        return self._signals.get(signal_key)
    
    def get_all_signals(self) -> Dict[str, WeightedSignal]:
        """Get all signals"""
        return self._signals.copy()


# ====================
# SINGLETON
# ====================

_advanced_analyzer: Optional[AdvancedSessionAnalyzer] = None


def get_advanced_analyzer() -> AdvancedSessionAnalyzer:
    """Get singleton AdvancedSessionAnalyzer instance"""
    global _advanced_analyzer
    if _advanced_analyzer is None:
        _advanced_analyzer = AdvancedSessionAnalyzer()
    return _advanced_analyzer
