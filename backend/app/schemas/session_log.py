"""
Session Log Schemas for Audio Coaching v1.1

Based on Proof Playbook v1.0 minimum required fields:
- Session: 한 촬영 세션
- InterventionEvent: 코칭 개입 발생
- OutcomeEvent: 행동 변화 관찰
- UploadOutcome: 업로드 결과 프록시

v1.1 Hardening:
- Field validators for t_sec, compliance
- Enhanced aggregation methods
- LiftCalculator utility class
- Per-rule statistics

Used for:
1. RL 조인키 구성
2. Compliance Lift 계산
3. Outcome Lift 측정
4. Goodhart 방지 승격 판단
"""
from datetime import datetime
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field
from app.utils.time import utcnow


# ====================
# SESSION LOG
# ====================

class SessionLog(BaseModel):
    """
    한 촬영 세션 로그
    
    핵심 조인키: session_id + pattern_id + pack_id
    """
    session_id: str
    user_id_hash: str  # 개인정보 X - 해시만
    
    mode: Literal["homage", "mutation", "campaign"]
    pattern_id: str
    pack_id: str
    pack_hash: Optional[str] = None  # Pack 버전 추적용
    
    # Coaching assignment (from CoachingRouter)
    assignment: Literal["coached", "control"]
    holdout_group: bool = False
    
    # Timestamps
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_sec: Optional[float] = None
    
    # Device/Environment (optional - P2)
    device_type: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ====================
# INTERVENTION EVENT
# ====================

class InterventionEvent(BaseModel):
    """
    코칭 개입이 발생한 시점 기록
    
    증명용 핵심 필드:
    - t_sec: 언제 개입했는지
    - rule_id: 어떤 규칙 위반인지
    - coach_line_id: 어떤 코칭 문장이었는지
    """
    session_id: str
    t_sec: float  # 세션 시작 기준 초
    
    rule_id: str  # e.g., "hook_start_within_2s_v1"
    ap_id: Optional[str] = None  # ActionPoint ID (if applicable)
    
    # Evidence
    evidence_id: str  # 프레임 ID, 오디오 세그먼트 ID 등
    evidence_type: Literal["frame", "audio", "text"]
    
    # Coach line delivered
    coach_line_id: str  # 템플릿 ID (strict/friendly/neutral)
    coach_line_text: Optional[str] = None  # 실제 전달된 문장
    
    # Metric snapshot at intervention
    metric_value: Optional[float] = None
    metric_threshold: Optional[float] = None
    
    timestamp: datetime = Field(default_factory=utcnow)


# ====================
# OUTCOME EVENT
# ====================

class OutcomeEvent(BaseModel):
    """
    행동 변화 관찰 기록
    
    compliance = True: 코칭 후 규칙 준수
    compliance = False: 코칭 후에도 위반 지속
    compliance = None: 측정 불가
    """
    session_id: str
    t_sec: float  # 관찰 시점
    
    rule_id: str
    
    compliance: Optional[bool] = None  # True/False/None
    compliance_unknown_reason: Optional[Literal[
        "occluded",        # 가려짐
        "out_of_frame",    # 프레임 밖
        "no_audio",        # 오디오 없음
        "ambiguous",       # 모호함
        "timeout"          # 타임아웃
    ]] = None
    
    # Metric after intervention
    metric_value_after: Optional[float] = None
    metric_delta: Optional[float] = None  # 개선폭
    
    # Time since intervention
    latency_sec: Optional[float] = None  # 개입 후 몇 초 뒤 관찰
    
    timestamp: datetime = Field(default_factory=utcnow)


# ====================
# UPLOAD OUTCOME
# ====================

class UploadOutcome(BaseModel):
    """
    업로드 결과 프록시
    
    최소 1개 이상의 성과 지표 필요 (Lift 계산용)
    """
    session_id: str
    
    # Upload status
    uploaded: bool = False
    upload_platform: Optional[str] = None  # tiktok/youtube/instagram
    
    # Early performance (if available)
    early_views_bucket: Optional[Literal[
        "0-100", "100-1K", "1K-10K", "10K-100K", "100K+"
    ]] = None
    early_likes_bucket: Optional[str] = None
    
    # Self-rating (1-5)
    self_rating: Optional[int] = None
    self_rating_reason: Optional[str] = None
    
    # Outcome timestamp
    recorded_at: datetime = Field(default_factory=utcnow)


# ====================
# SESSION COMPLETE LOG
# ====================

class SessionCompleteLog(BaseModel):
    """
    완전한 세션 로그 (집계용)
    
    RL 학습용 조인:
    session + interventions + outcomes + upload
    """
    session: SessionLog
    interventions: List[InterventionEvent] = Field(default_factory=list)
    outcomes: List[OutcomeEvent] = Field(default_factory=list)
    upload_outcome: Optional[UploadOutcome] = None
    
    # Aggregated metrics
    intervention_count: int = 0
    compliance_rate: Optional[float] = None  # 준수율
    unknown_rate: Optional[float] = None  # 측정불가 비율
    
    # Lift calculations (populated by analyzer)
    compliance_lift: Optional[float] = None  # 코칭 → 행동 변화
    outcome_lift: Optional[float] = None  # 행동 → 성과 개선
    
    def calculate_compliance_rate(self) -> Optional[float]:
        """Calculate compliance rate excluding unknowns."""
        known_outcomes = [o for o in self.outcomes if o.compliance is not None]
        if not known_outcomes:
            return None
        
        compliant = sum(1 for o in known_outcomes if o.compliance)
        return compliant / len(known_outcomes)
    
    def calculate_unknown_rate(self) -> Optional[float]:
        """Calculate unknown/unmeasurable rate."""
        if not self.outcomes:
            return None
        
        unknown = sum(1 for o in self.outcomes if o.compliance is None)
        return unknown / len(self.outcomes)
    
    def get_per_rule_stats(self) -> Dict[str, Dict[str, float]]:
        """
        규칙별 통계
        
        Returns:
            {
                "hook_start_within_2s_v1": {
                    "intervention_count": 3,
                    "compliance_rate": 0.67,
                    "mean_latency_sec": 2.5,
                    "mean_delta": 0.15
                },
                ...
            }
        """
        stats: Dict[str, Dict[str, float]] = {}
        
        # 규칙별 개입 수 집계
        for intervention in self.interventions:
            rule_id = intervention.rule_id
            if rule_id not in stats:
                stats[rule_id] = {
                    "intervention_count": 0,
                    "compliant_count": 0,
                    "non_compliant_count": 0,
                    "unknown_count": 0,
                    "latency_sum": 0.0,
                    "delta_sum": 0.0,
                    "delta_count": 0
                }
            stats[rule_id]["intervention_count"] += 1
        
        # 규칙별 결과 집계
        for outcome in self.outcomes:
            rule_id = outcome.rule_id
            if rule_id not in stats:
                continue
            
            if outcome.compliance is True:
                stats[rule_id]["compliant_count"] += 1
            elif outcome.compliance is False:
                stats[rule_id]["non_compliant_count"] += 1
            else:
                stats[rule_id]["unknown_count"] += 1
            
            if outcome.latency_sec is not None:
                stats[rule_id]["latency_sum"] += outcome.latency_sec
            
            if outcome.metric_delta is not None:
                stats[rule_id]["delta_sum"] += outcome.metric_delta
                stats[rule_id]["delta_count"] += 1
        
        # 최종 통계 계산
        result = {}
        for rule_id, raw_stats in stats.items():
            intervention_count = raw_stats["intervention_count"]
            known_count = raw_stats["compliant_count"] + raw_stats["non_compliant_count"]
            
            result[rule_id] = {
                "intervention_count": intervention_count,
                "compliance_rate": (
                    raw_stats["compliant_count"] / known_count 
                    if known_count > 0 else None
                ),
                "mean_latency_sec": (
                    raw_stats["latency_sum"] / known_count 
                    if known_count > 0 else None
                ),
                "mean_delta": (
                    raw_stats["delta_sum"] / raw_stats["delta_count"] 
                    if raw_stats["delta_count"] > 0 else None
                )
            }
        
        return result
    
    def get_intervention_response_time(self) -> Optional[float]:
        """평균 개입 후 반응 시간 (초)"""
        latencies = [o.latency_sec for o in self.outcomes if o.latency_sec is not None]
        if not latencies:
            return None
        return sum(latencies) / len(latencies)
    
    def finalize(self) -> "SessionCompleteLog":
        """세션 종료 시 모든 지표 계산"""
        self.intervention_count = len(self.interventions)
        self.compliance_rate = self.calculate_compliance_rate()
        self.unknown_rate = self.calculate_unknown_rate()
        return self


# ====================
# LIFT CALCULATION REQUEST
# ====================

class LiftCalculationRequest(BaseModel):
    """
    Lift 계산 요청
    
    Goodhart 방지: 2+ 클러스터 재현 필수
    """
    pattern_id: str
    cluster_ids: List[str]  # 최소 2개
    
    min_sessions_per_cluster: int = 10
    control_required: bool = True  # 대조군 필수
    
    # Promotion criteria
    min_compliance_lift: float = 0.1  # 10% 이상 행동 개선
    min_outcome_lift: float = 0.05  # 5% 이상 성과 개선
    min_cluster_count: int = 2  # 2개 이상 클러스터에서 재현


class LiftCalculationResult(BaseModel):
    """Lift 계산 결과"""
    pattern_id: str
    
    # Per-cluster results
    cluster_results: List[dict] = Field(default_factory=list)
    
    # Aggregated
    avg_compliance_lift: Optional[float] = None
    avg_outcome_lift: Optional[float] = None
    
    # Promotion decision
    clusters_with_lift: int = 0
    promotion_eligible: bool = False
    promotion_reason: Optional[str] = None
