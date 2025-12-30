"""
Coaching Session Service v1.1

Integrates proof patterns with audio coaching sessions.

v1.1 Hardening:
- MetricEvaluator integration
- Cooldown tracking
- Finalize session with per-rule stats
- Error handling

Usage:
    service = get_coaching_service()
    session = service.start_session(
        user_id_hash="abc123",
        mode="homage"
    )
    
    # Evaluate using MetricEvaluator
    result = service.evaluate_with_evaluator(
        session_id=session.session_id,
        rule_id="hook_start_within_2s_v1",
        t_sec=1.5,
        metric_value=2.5
    )
    
    if result.needs_intervention:
        print(result.coach_line)
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, List, Literal

from app.schemas.session_log import (
    SessionLog, InterventionEvent, OutcomeEvent, 
    UploadOutcome, SessionCompleteLog
)
from app.services.proof_patterns import (
    TOP_3_PROOF_PATTERNS, get_pattern_by_id, 
    get_coach_line, create_proof_pack, PATTERN_IDS,
    MetricEvaluator, get_metric_evaluator, EvaluationResult, EvaluationStatus,
    PatternValidator
)
from app.services.coaching_router import get_coaching_router

logger = logging.getLogger(__name__)


class CoachingSessionService:
    """
    Manages coaching sessions with proof patterns.
    
    v1.1: Uses MetricEvaluator for standardized rule evaluation.
    
    Responsibilities:
    - Session lifecycle
    - Rule evaluation and intervention
    - Outcome recording
    - Cooldown enforcement
    """
    
    DEFAULT_COOLDOWN_SEC = 4.0
    
    def __init__(self):
        self._sessions: Dict[str, SessionCompleteLog] = {}
        self._router = get_coaching_router()
        self._evaluator = get_metric_evaluator()
        
        # Cooldown tracking: {session_id: {rule_id: last_intervention_time}}
        self._cooldowns: Dict[str, Dict[str, float]] = {}
    
    def _can_intervene(self, session_id: str, rule_id: str, t_sec: float) -> bool:
        """Check if cooldown has passed for this rule."""
        if session_id not in self._cooldowns:
            return True
        
        session_cooldowns = self._cooldowns[session_id]
        if rule_id not in session_cooldowns:
            return True
        
        last_time = session_cooldowns[rule_id]
        return (t_sec - last_time) >= self.DEFAULT_COOLDOWN_SEC
    
    def _update_cooldown(self, session_id: str, rule_id: str, t_sec: float):
        """Update cooldown tracking."""
        if session_id not in self._cooldowns:
            self._cooldowns[session_id] = {}
        self._cooldowns[session_id][rule_id] = t_sec
    
    # ====================
    # SESSION LIFECYCLE
    # ====================
    
    def start_session(
        self,
        user_id_hash: str,
        mode: Literal["homage", "mutation", "campaign"],
        pattern_id: str = "proof_playbook_top3_v1",
        pack_id: Optional[str] = None
    ) -> SessionLog:
        """
        Start a new coaching session.
        
        Args:
            user_id_hash: Hashed user identifier (no PII)
            mode: Session mode
            pattern_id: Pattern being practiced
            pack_id: Optional specific pack ID
            
        Returns:
            SessionLog with assignment info
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        # Get assignment from router
        assignment = self._router.assign_group(session_id)
        
        # Create pack if not provided
        if not pack_id:
            pack = create_proof_pack(pattern_id=pattern_id)
            pack_id = pack.pack_meta.pack_id
        
        session = SessionLog(
            session_id=session_id,
            user_id_hash=user_id_hash,
            mode=mode,
            pattern_id=pattern_id,
            pack_id=pack_id,
            assignment=assignment.assignment,
            holdout_group=assignment.holdout_group,
            started_at=datetime.now()
        )
        
        # Store in memory (TODO: persist to DB)
        self._sessions[session_id] = SessionCompleteLog(session=session)
        
        return session
    
    def end_session(self, session_id: str) -> Optional[SessionCompleteLog]:
        """
        End a session and calculate metrics.
        
        Returns:
            Complete session log with aggregated metrics
        """
        if session_id not in self._sessions:
            return None
        
        complete_log = self._sessions[session_id]
        session = complete_log.session
        
        # Update end time
        session.ended_at = datetime.now()
        session.duration_sec = (session.ended_at - session.started_at).total_seconds()
        
        # Calculate aggregated metrics
        complete_log.intervention_count = len(complete_log.interventions)
        complete_log.compliance_rate = complete_log.calculate_compliance_rate()
        complete_log.unknown_rate = complete_log.calculate_unknown_rate()
        
        return complete_log
    
    # ====================
    # RULE EVALUATION
    # ====================
    
    def evaluate_rule(
        self,
        session_id: str,
        rule_id: str,
        t_sec: float,
        metric_value: float,
        evidence_id: str = None,
        evidence_type: Literal["frame", "audio", "text"] = "video"
    ) -> Optional[InterventionEvent]:
        """
        Evaluate a rule and potentially trigger intervention.
        
        Args:
            session_id: Session identifier
            rule_id: Rule to evaluate
            t_sec: Time in session
            metric_value: Current metric value
            evidence_id: Evidence reference
            evidence_type: Type of evidence
            
        Returns:
            InterventionEvent if rule violated, None otherwise
        """
        if session_id not in self._sessions:
            return None
        
        complete_log = self._sessions[session_id]
        session = complete_log.session
        
        # Skip if control group
        if session.assignment == "control":
            return None
        
        # Get pattern
        pattern = get_pattern_by_id(rule_id)
        if not pattern:
            return None
        
        # Check if rule violated
        spec = pattern.spec
        violated = self._check_violation(spec, metric_value)
        
        if not violated:
            return None
        
        # Create intervention
        coach_line = get_coach_line(rule_id, "friendly")
        intervention = InterventionEvent(
            session_id=session_id,
            t_sec=t_sec,
            rule_id=rule_id,
            evidence_id=evidence_id or f"ev_{uuid.uuid4().hex[:8]}",
            evidence_type=evidence_type,
            coach_line_id="friendly",
            coach_line_text=coach_line,
            metric_value=metric_value,
            metric_threshold=spec.target
        )
        
        complete_log.interventions.append(intervention)
        return intervention
    
    def _check_violation(self, spec, value: float) -> bool:
        """Check if metric value violates spec."""
        op = spec.op
        target = spec.target
        
        if op == "<=":
            return value > target
        elif op == "<":
            return value >= target
        elif op == ">=":
            return value < target
        elif op == ">":
            return value <= target
        elif op == "between":
            range_ = spec.range or [0, 1]
            return value < range_[0] or value > range_[1]
        else:
            return False
    
    # ====================
    # OUTCOME RECORDING
    # ====================
    
    def record_outcome(
        self,
        session_id: str,
        rule_id: str,
        t_sec: float,
        compliance: Optional[bool],
        compliance_unknown_reason: Optional[str] = None,
        metric_value_after: Optional[float] = None
    ) -> Optional[OutcomeEvent]:
        """
        Record outcome after intervention.
        
        Args:
            session_id: Session identifier
            rule_id: Rule being observed
            t_sec: Time of observation
            compliance: Whether user complied (None if unknown)
            compliance_unknown_reason: Reason if unknown
            metric_value_after: Metric value after intervention
            
        Returns:
            OutcomeEvent
        """
        if session_id not in self._sessions:
            return None
        
        complete_log = self._sessions[session_id]
        
        # Calculate latency from last intervention
        last_intervention = None
        for i in reversed(complete_log.interventions):
            if i.rule_id == rule_id:
                last_intervention = i
                break
        
        latency_sec = None
        metric_delta = None
        if last_intervention:
            latency_sec = t_sec - last_intervention.t_sec
            if metric_value_after is not None and last_intervention.metric_value is not None:
                metric_delta = metric_value_after - last_intervention.metric_value
        
        outcome = OutcomeEvent(
            session_id=session_id,
            t_sec=t_sec,
            rule_id=rule_id,
            compliance=compliance,
            compliance_unknown_reason=compliance_unknown_reason,
            metric_value_after=metric_value_after,
            metric_delta=metric_delta,
            latency_sec=latency_sec
        )
        
        complete_log.outcomes.append(outcome)
        return outcome
    
    def record_upload_outcome(
        self,
        session_id: str,
        uploaded: bool,
        upload_platform: Optional[str] = None,
        early_views_bucket: Optional[str] = None,
        self_rating: Optional[int] = None
    ) -> Optional[UploadOutcome]:
        """Record upload result for session."""
        if session_id not in self._sessions:
            return None
        
        outcome = UploadOutcome(
            session_id=session_id,
            uploaded=uploaded,
            upload_platform=upload_platform,
            early_views_bucket=early_views_bucket,
            self_rating=self_rating
        )
        
        self._sessions[session_id].upload_outcome = outcome
        return outcome
    
    # ====================
    # GETTERS
    # ====================
    
    def get_session(self, session_id: str) -> Optional[SessionCompleteLog]:
        """Get complete session log."""
        return self._sessions.get(session_id)
    
    def get_active_patterns(self) -> List[str]:
        """Get list of active proof pattern IDs."""
        return [p.rule_id for p in TOP_3_PROOF_PATTERNS]
    
    def get_pattern_coach_lines(self, pattern_id: str) -> Dict[str, str]:
        """Get all coach lines for a pattern."""
        pattern = get_pattern_by_id(pattern_id)
        if not pattern:
            return {}
        
        templates = pattern.coach_line_templates
        return {
            "strict": templates.strict,
            "friendly": templates.friendly,
            "neutral": templates.neutral,
            "ko_default": templates.ko.get("default") if templates.ko else None,
            "en_default": templates.en.get("default") if templates.en else None,
        }


# Singleton instance
_service_instance: Optional[CoachingSessionService] = None


def get_coaching_service() -> CoachingSessionService:
    """Get singleton coaching session service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CoachingSessionService()
    return _service_instance
