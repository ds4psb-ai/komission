"""
Session Logger

3종 이벤트 로깅 서비스:
1. rule_evaluated - 규칙 평가 (개입 없는 구간 포함)
2. intervention - 코칭 개입
3. outcome - 결과 관측

MVP: In-memory 저장 → 추후 DB 마이그레이션

P1 Roadmap: 세션 로깅 인프라
"""
import logging
from typing import Dict, List, Optional
from collections import defaultdict

from app.utils.time import iso_now
from app.schemas.session_events import (
    SessionEvent,
    RuleEvaluatedEvent,
    InterventionEvent,
    OutcomeEvent,
    SessionEventSummary,
)
from app.schemas.vdg_v4 import CoachingIntervention, CoachingOutcome

logger = logging.getLogger(__name__)


class SessionLogger:
    """
    Logs session events for RL and promotion calculations.
    
    Usage:
        session_logger = SessionLogger()
        
        # Log rule evaluation (even without intervention)
        session_logger.log_rule_evaluated(
            session_id="sess_123",
            rule_id="hook_center",
            ap_id="ap_hook_001",
            checkpoint_id="hook_punch",
            result="passed"
        )
        
        # Log intervention
        session_logger.log_intervention(intervention)
        
        # Log outcome
        session_logger.log_outcome(outcome)
    """
    
    def __init__(self):
        """Initialize in-memory event store."""
        # session_id -> List[SessionEvent]
        self._events: Dict[str, List[SessionEvent]] = defaultdict(list)
        
        # session_id -> metadata
        self._sessions: Dict[str, dict] = {}
        
        # intervention_id -> session_id (for outcome linking)
        self._intervention_map: Dict[str, str] = {}
    
    # ====================
    # SESSION MANAGEMENT
    # ====================
    
    def start_session(
        self,
        session_id: str,
        pack_id: str,
        assignment: str = "coached",
        holdout_group: bool = False
    ) -> dict:
        """Register a new session."""
        self._sessions[session_id] = {
            "session_id": session_id,
            "pack_id": pack_id,
            "assignment": assignment,
            "holdout_group": holdout_group,
            "started_at": iso_now(),
        }
        logger.info(f"📊 Session started: {session_id} (assignment={assignment}, holdout={holdout_group})")
        return self._sessions[session_id]
    
    # ====================
    # EVENT LOGGING
    # ====================
    
    def log_rule_evaluated(
        self,
        session_id: str,
        rule_id: str,
        ap_id: str,
        checkpoint_id: str,
        result: str = "unknown",
        result_reason: Optional[str] = None,
        t_video: float = 0.0,
        metric_id: Optional[str] = None,
        metric_value: Optional[float] = None,
        evidence_id: Optional[str] = None,
        intervention_triggered: bool = False,
    ) -> RuleEvaluatedEvent:
        """
        Log rule evaluation event.
        
        CRITICAL: This should be logged even when NO intervention is triggered.
        """
        event = RuleEvaluatedEvent(
            session_id=session_id,
            rule_id=rule_id,
            ap_id=ap_id,
            checkpoint_id=checkpoint_id,
            result=result,
            result_reason=result_reason,
            t_video=t_video,
            metric_id=metric_id,
            metric_value=metric_value,
            evidence_id=evidence_id,
            intervention_triggered=intervention_triggered,
        )
        
        self._events[session_id].append(event)
        logger.debug(f"📋 Rule evaluated: {rule_id} = {result} (intervention={intervention_triggered})")
        return event
    
    def log_intervention(
        self,
        intervention: CoachingIntervention,
    ) -> InterventionEvent:
        """Log coaching intervention event."""
        event = InterventionEvent(
            session_id=intervention.session_id,
            intervention_id=intervention.intervention_id,
            rule_id=intervention.rule_id,
            ap_id=intervention.ap_id,
            checkpoint_id=intervention.checkpoint_id or "",
            t_video=intervention.t_video,
            command_text=intervention.command_text,
            coach_channel=intervention.coach_channel,
            persona_preset=intervention.persona_preset,
            assignment=intervention.assignment,
            holdout_group=intervention.holdout_group,
            evidence_id=intervention.evidence_id,
        )
        
        self._events[intervention.session_id].append(event)
        self._intervention_map[intervention.intervention_id] = intervention.session_id
        
        logger.debug(f"🎙️ Intervention: {intervention.rule_id} (assignment={intervention.assignment})")
        return event
    
    def log_outcome(
        self,
        outcome: CoachingOutcome,
    ) -> OutcomeEvent:
        """Log outcome event with automatic negative evidence detection."""
        # Find session from intervention
        session_id = self._intervention_map.get(outcome.intervention_id, "unknown")
        
        # Auto-detect negative evidence
        is_negative = self._detect_negative_evidence(outcome)
        negative_reason = None
        if is_negative:
            negative_reason = self._classify_negative_reason(outcome)
        
        event = OutcomeEvent(
            session_id=session_id,
            intervention_id=outcome.intervention_id,
            rule_id=outcome.metric_id,  # Link to rule via metric
            compliance_detected=outcome.compliance_detected,
            compliance_unknown_reason=outcome.compliance_unknown_reason,
            user_response=outcome.user_response,
            metric_id=outcome.metric_id,
            metric_before=outcome.metric_before,
            metric_after=outcome.metric_after,
            improvement=outcome.improvement,
            upload_outcome_proxy=outcome.upload_outcome_proxy,
            reported_views=outcome.reported_views,
            reported_likes=outcome.reported_likes,
            reported_saves=outcome.reported_saves,
            outcome_unknown_reason=outcome.outcome_unknown_reason,
            is_negative_evidence=is_negative,
            negative_reason=negative_reason,
        )
        
        self._events[session_id].append(event)
        
        log_level = "⚠️" if is_negative else "✅"
        logger.debug(f"{log_level} Outcome: compliance={outcome.compliance_detected}, negative={is_negative}")
        return event
    
    # ====================
    # NEGATIVE EVIDENCE DETECTION
    # ====================
    
    def _detect_negative_evidence(self, outcome: CoachingOutcome) -> bool:
        """
        Auto-detect if this outcome should be flagged as negative evidence.
        
        Negative evidence = compliance achieved but outcome was poor.
        This is critical for Goodhart prevention.
        """
        # Case 1: Complied but poor upload outcome
        if outcome.compliance_detected and outcome.upload_outcome_proxy == "no_upload":
            return True
        
        # Case 2: Complied but negative improvement
        if outcome.compliance_detected and outcome.improvement is not None:
            if outcome.improvement < 0:
                return True
        
        # Case 3: Explicit negative markers
        if outcome.is_negative_evidence:
            return True
        
        return False
    
    def _classify_negative_reason(self, outcome: CoachingOutcome) -> str:
        """Classify the reason for negative evidence."""
        if outcome.compliance_detected and outcome.upload_outcome_proxy == "no_upload":
            return "compliance_but_no_upload"
        
        if outcome.compliance_detected and outcome.improvement is not None and outcome.improvement < 0:
            return "compliance_but_metric_degraded"
        
        return "compliance_but_poor_outcome"
    
    # ====================
    # RETRIEVAL
    # ====================
    
    def get_session_events(self, session_id: str) -> List[SessionEvent]:
        """Get all events for a session."""
        return self._events.get(session_id, [])
    
    def get_session_summary(self, session_id: str) -> Optional[SessionEventSummary]:
        """Get summary statistics for a session."""
        if session_id not in self._sessions:
            return None
        
        events = self._events.get(session_id, [])
        session_meta = self._sessions[session_id]
        
        # Count by type
        rules_evaluated = sum(1 for e in events if e.event_type == "rule_evaluated")
        interventions = sum(1 for e in events if e.event_type == "intervention")
        outcomes = sum(1 for e in events if e.event_type == "outcome")
        
        # Quality metrics
        intervention_outcome_join_rate = outcomes / interventions if interventions > 0 else 0
        
        unknown_count = sum(
            1 for e in events 
            if e.event_type == "outcome" and e.compliance_unknown_reason is not None
        )
        compliance_unknown_rate = unknown_count / outcomes if outcomes > 0 else 0
        
        negative_count = sum(
            1 for e in events 
            if e.event_type == "outcome" and getattr(e, 'is_negative_evidence', False)
        )
        negative_evidence_rate = negative_count / outcomes if outcomes > 0 else 0
        
        return SessionEventSummary(
            session_id=session_id,
            pack_id=session_meta.get("pack_id", ""),
            assignment=session_meta.get("assignment", "coached"),
            holdout_group=session_meta.get("holdout_group", False),
            total_events=len(events),
            rules_evaluated=rules_evaluated,
            interventions_delivered=interventions,
            outcomes_observed=outcomes,
            intervention_outcome_join_rate=intervention_outcome_join_rate,
            compliance_unknown_rate=compliance_unknown_rate,
            negative_evidence_rate=negative_evidence_rate,
            events=events,
        )
    
    def get_all_sessions_summary(self) -> dict:
        """Get summary of all sessions for P1 verification."""
        summaries = []
        for session_id in self._sessions:
            summary = self.get_session_summary(session_id)
            if summary:
                summaries.append(summary)
        
        # Aggregate stats
        total_sessions = len(summaries)
        control_sessions = sum(1 for s in summaries if s.assignment == "control")
        holdout_sessions = sum(1 for s in summaries if s.holdout_group)
        
        return {
            "total_sessions": total_sessions,
            "control_sessions": control_sessions,
            "control_ratio": control_sessions / total_sessions if total_sessions > 0 else 0,
            "holdout_sessions": holdout_sessions,
            "avg_intervention_outcome_join_rate": (
                sum(s.intervention_outcome_join_rate for s in summaries) / total_sessions
                if total_sessions > 0 else 0
            ),
            "avg_compliance_unknown_rate": (
                sum(s.compliance_unknown_rate for s in summaries) / total_sessions
                if total_sessions > 0 else 0
            ),
        }


# Singleton instance
_logger_instance = None


def get_session_logger() -> SessionLogger:
    """Get singleton SessionLogger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SessionLogger()
    return _logger_instance
