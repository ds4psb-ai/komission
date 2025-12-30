"""
Session Events Schema

3종 이벤트 스키마:
1. RuleEvaluatedEvent - 규칙 평가 결과 (개입 없는 구간 포함)
2. InterventionEvent - 코칭 개입 전달
3. OutcomeEvent - 결과 관측

P1 Roadmap: 세션 로깅 인프라
"""
from datetime import datetime
from typing import Optional, Any, Dict, List, Literal
from pydantic import BaseModel, Field
import uuid


# ====================
# BASE EVENT
# ====================

class SessionEvent(BaseModel):
    """Base class for all session events."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    session_id: str
    event_type: str  # "rule_evaluated" | "intervention" | "outcome"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Linking keys (for RL join)
    rule_id: Optional[str] = None
    ap_id: Optional[str] = None
    evidence_id: Optional[str] = None


# ====================
# 1. RULE EVALUATED EVENT
# ====================

class RuleEvaluatedEvent(SessionEvent):
    """
    규칙 평가 이벤트 (개입 없는 구간 포함).
    
    핵심: intervention 없이도 이 이벤트는 기록되어야 함.
    "왜 개입하지 않았는지"도 학습에 필요.
    """
    event_type: str = "rule_evaluated"
    
    # What was evaluated
    checkpoint_id: str
    t_video: float = 0.0  # Video timestamp
    
    # Result
    result: Literal["passed", "violated", "unknown"] = "unknown"
    result_reason: Optional[str] = None  # Why unknown: "occluded", "out_of_frame"
    
    # Metric measurement (if applicable)
    metric_id: Optional[str] = None
    metric_value: Optional[float] = None
    
    # Decision
    intervention_triggered: bool = False  # Did this lead to coaching?


# ====================
# 2. INTERVENTION EVENT
# ====================

class InterventionEvent(SessionEvent):
    """
    코칭 개입 전달 이벤트.
    
    Links to CoachingIntervention schema.
    """
    event_type: str = "intervention"
    
    # Intervention details
    intervention_id: str
    checkpoint_id: str
    t_video: float = 0.0
    
    # What was delivered
    command_text: str = ""
    coach_channel: str = "audio"  # "audio" | "text" | "none"
    persona_preset: str = "neutral"
    
    # Control group (Goodhart prevention)
    assignment: str = "coached"  # "coached" | "control"
    holdout_group: bool = False


# ====================
# 3. OUTCOME EVENT
# ====================

class OutcomeEvent(SessionEvent):
    """
    결과 관측 이벤트.
    
    Two-stage:
    - Stage 1: Immediate (compliance)
    - Stage 2: Delayed (upload outcome)
    """
    event_type: str = "outcome"
    
    # Link to intervention
    intervention_id: str
    
    # Stage 1: Immediate
    compliance_detected: bool = False
    compliance_unknown_reason: Optional[str] = None
    user_response: str = "unknown"  # "complied", "ignored", "questioned", "retake"
    
    # Metric change
    metric_id: Optional[str] = None
    metric_before: Optional[float] = None
    metric_after: Optional[float] = None
    improvement: Optional[float] = None
    
    # Stage 2: Upload (delayed, may be updated later)
    upload_outcome_proxy: Optional[str] = None
    reported_views: Optional[int] = None
    reported_likes: Optional[int] = None
    reported_saves: Optional[int] = None
    outcome_unknown_reason: Optional[str] = None
    
    # Negative Evidence (Goodhart prevention)
    is_negative_evidence: bool = False
    negative_reason: Optional[str] = None


# ====================
# SESSION SUMMARY
# ====================

class SessionEventSummary(BaseModel):
    """Summary of all events in a session."""
    session_id: str
    pack_id: str
    assignment: str
    holdout_group: bool
    
    # Counts
    total_events: int = 0
    rules_evaluated: int = 0
    interventions_delivered: int = 0
    outcomes_observed: int = 0
    
    # Quality metrics
    intervention_outcome_join_rate: float = 0.0  # Should be 100%
    compliance_unknown_rate: float = 0.0  # Should be < 15%
    negative_evidence_rate: float = 0.0
    
    # Events
    events: List[SessionEvent] = Field(default_factory=list)
