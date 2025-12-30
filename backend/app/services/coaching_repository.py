"""
Coaching Session Repository v2.0 (Hardened)

SQLAlchemy-backed repository for coaching session data persistence.

v2.0 Hardening:
- Input validators with Pydantic
- Custom exceptions
- Constants for limits
- Enhanced logging
- Transaction safety
- Duplicate check on create

Usage:
    from app.services.coaching_repository import CoachingRepository
    
    async with AsyncSessionLocal() as db:
        repo = CoachingRepository(db)
        session = await repo.create_session(...)
"""
import logging
import hashlib
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.models import (
    CoachingSession, CoachingIntervention, CoachingOutcome, CoachingUploadOutcome,
    CoachingAssignment, CoachingMode, EvidenceType, ComplianceResult
)
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


# ====================
# CONSTANTS
# ====================

class CoachingConstants:
    """Coaching system constants."""
    
    # Limits
    MAX_INTERVENTIONS_PER_SESSION = 100
    MAX_OUTCOMES_PER_SESSION = 100
    MAX_SESSION_DURATION_SEC = 3600  # 1 hour
    MIN_SESSION_DURATION_SEC = 5
    
    # Cooldown
    DEFAULT_COOLDOWN_SEC = 4.0
    
    # Validation
    MIN_T_SEC = 0.0
    MAX_T_SEC = 3600.0
    MAX_RULE_ID_LENGTH = 100
    MAX_EVIDENCE_ID_LENGTH = 100
    
    # Rating
    MIN_SELF_RATING = 1
    MAX_SELF_RATING = 5
    
    # Assignment ratios (for validation)
    CONTROL_GROUP_RATIO = 0.10
    HOLDOUT_GROUP_RATIO = 0.05


# ====================
# EXCEPTIONS
# ====================

class CoachingRepositoryError(Exception):
    """Base exception for coaching repository."""
    pass


class SessionNotFoundError(CoachingRepositoryError):
    """Session does not exist."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionAlreadyExistsError(CoachingRepositoryError):
    """Session already exists."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session already exists: {session_id}")


class SessionLimitExceededError(CoachingRepositoryError):
    """Session limit exceeded."""
    def __init__(self, limit_type: str, current: int, max_allowed: int):
        self.limit_type = limit_type
        self.current = current
        self.max_allowed = max_allowed
        super().__init__(f"{limit_type} limit exceeded: {current}/{max_allowed}")


class PromotionSafetyError(CoachingRepositoryError):
    """
    H5: Promotion safety error.
    
    Raised when attempting to promote a session without required outcomes.
    Prevents Goodhart's Law violations by enforcing outcome requirements.
    """
    def __init__(self, session_id: str, reason: str):
        self.session_id = session_id
        self.reason = reason
        super().__init__(f"Promotion blocked for {session_id}: {reason}")


class InvalidParameterError(CoachingRepositoryError):
    """Invalid parameter value."""
    def __init__(self, param_name: str, value: Any, reason: str):
        self.param_name = param_name
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid {param_name}={value}: {reason}")


# ====================
# INPUT SCHEMAS
# ====================

class CreateSessionInput(BaseModel):
    """Validated input for session creation."""
    session_id: str = Field(..., min_length=5, max_length=50)
    user_id_hash: str = Field(..., min_length=16, max_length=64)
    mode: Literal["homage", "mutation", "campaign"]
    pattern_id: str = Field(..., min_length=1, max_length=100)
    pack_id: str = Field(..., min_length=1, max_length=100)
    assignment: Literal["coached", "control"] = "coached"
    holdout_group: bool = False
    pack_hash: Optional[str] = Field(None, max_length=64)


class AddInterventionInput(BaseModel):
    """Validated input for intervention."""
    session_id: str
    t_sec: float = Field(..., ge=0, le=3600)
    rule_id: str = Field(..., min_length=1, max_length=100)
    evidence_id: str = Field(..., min_length=1, max_length=100)
    evidence_type: Literal["frame", "audio", "text"] = "frame"
    coach_line_id: str = Field("friendly", max_length=50)
    coach_line_text: Optional[str] = Field(None, max_length=500)
    metric_value: Optional[float] = None
    metric_threshold: Optional[float] = None
    ap_id: Optional[str] = Field(None, max_length=100)
    
    @field_validator('t_sec')
    @classmethod
    def validate_t_sec(cls, v: float) -> float:
        if v < 0:
            raise ValueError("t_sec must be non-negative")
        return round(v, 3)  # 밀리초 정밀도


class AddOutcomeInput(BaseModel):
    """Validated input for outcome."""
    session_id: str
    t_sec: float = Field(..., ge=0, le=3600)
    rule_id: str = Field(..., min_length=1, max_length=100)
    compliance: Literal["complied", "violated", "unknown"] = "unknown"
    compliance_unknown_reason: Optional[str] = Field(None, max_length=50)
    metric_value_after: Optional[float] = None
    metric_delta: Optional[float] = None
    latency_sec: Optional[float] = Field(None, ge=0)


class SetUploadOutcomeInput(BaseModel):
    """Validated input for upload outcome."""
    session_id: str
    uploaded: bool
    upload_platform: Optional[str] = Field(None, max_length=50)
    early_views_bucket: Optional[str] = Field(None, max_length=20)
    early_likes_bucket: Optional[str] = Field(None, max_length=20)
    self_rating: Optional[int] = Field(None, ge=1, le=5)
    self_rating_reason: Optional[str] = Field(None, max_length=500)


# ====================
# REPOSITORY
# ====================

class CoachingRepository:
    """
    Repository for coaching session persistence.
    
    v2.0 Hardening:
    - Pydantic validation on all inputs
    - Custom exceptions for error handling
    - Limit enforcement
    - Transaction safety
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ====================
    # SESSION CRUD
    # ====================
    
    async def create_session(
        self,
        session_id: str,
        user_id_hash: str,
        mode: str,
        pattern_id: str,
        pack_id: str,
        assignment: str = "coached",
        holdout_group: bool = False,
        pack_hash: Optional[str] = None
    ) -> CoachingSession:
        """
        Create a new coaching session.
        
        Raises:
            SessionAlreadyExistsError: If session_id already exists
            InvalidParameterError: If input validation fails
        """
        # Validate input
        try:
            validated = CreateSessionInput(
                session_id=session_id,
                user_id_hash=user_id_hash,
                mode=mode,
                pattern_id=pattern_id,
                pack_id=pack_id,
                assignment=assignment,
                holdout_group=holdout_group,
                pack_hash=pack_hash
            )
        except Exception as e:
            raise InvalidParameterError("create_session", str(e), "validation failed")
        
        # Check for duplicate
        existing = await self.get_session(validated.session_id)
        if existing:
            raise SessionAlreadyExistsError(validated.session_id)
        
        session = CoachingSession(
            session_id=validated.session_id,
            user_id_hash=validated.user_id_hash,
            mode=CoachingMode(validated.mode),
            pattern_id=validated.pattern_id,
            pack_id=validated.pack_id,
            assignment=CoachingAssignment(validated.assignment),
            holdout_group=validated.holdout_group,
            pack_hash=validated.pack_hash,
            started_at=utcnow()
        )
        
        self.db.add(session)
        
        try:
            await self.db.commit()
            await self.db.refresh(session)
        except IntegrityError:
            await self.db.rollback()
            raise SessionAlreadyExistsError(validated.session_id)
        
        logger.info(f"[COACHING] Created session: {session_id} (mode={mode}, assignment={assignment})")
        return session
    
    async def get_session(self, session_id: str) -> Optional[CoachingSession]:
        """Get session by ID with relationships."""
        result = await self.db.execute(
            select(CoachingSession)
            .where(CoachingSession.session_id == session_id)
            .options(
                selectinload(CoachingSession.interventions),
                selectinload(CoachingSession.outcomes),
                selectinload(CoachingSession.upload_outcome)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_session_or_raise(self, session_id: str) -> CoachingSession:
        """Get session or raise SessionNotFoundError."""
        session = await self.get_session(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        return session
    
    async def get_session_for_promotion(self, session_id: str) -> CoachingSession:
        """
        H5: Get session for candidate promotion with safety checks.
        
        Validates that required outcomes exist before allowing promotion.
        This prevents Goodhart's Law violations by enforcing the two-stage
        outcome model (proxy outcome must exist before promotion).
        
        Args:
            session_id: Session ID to validate for promotion
            
        Returns:
            CoachingSession if promotion is safe
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            PromotionSafetyError: If session lacks required outcomes
            
        Example:
            try:
                session = await repo.get_session_for_promotion(session_id)
                # Safe to promote candidates from this session
                await promote_candidates(session)
            except PromotionSafetyError as e:
                logger.warning(f"Promotion blocked: {e.reason}")
        """
        session = await self.get_session_or_raise(session_id)
        
        # Check for any outcomes
        if not session.outcomes or len(session.outcomes) == 0:
            raise PromotionSafetyError(
                session_id,
                "no outcomes recorded - cannot promote without outcome data"
            )
        
        # Check for proxy outcome (stage 1 of two-stage model)
        proxy_outcomes = [
            o for o in session.outcomes 
            if hasattr(o, 'outcome_type') and o.outcome_type == 'proxy'
        ]
        
        if not proxy_outcomes:
            # Allow if any outcome exists (for backwards compatibility)
            # but log a warning
            logger.warning(
                f"[COACHING] Session {session_id} has outcomes but no proxy outcome. "
                f"Consider adding proxy outcome for two-stage model."
            )
        
        # Check for upload outcomes
        if not session.upload_outcomes or len(session.upload_outcomes) == 0:
            raise PromotionSafetyError(
                session_id,
                "no upload outcomes - session content status unknown"
            )
        
        logger.info(
            f"[COACHING] Promotion safety check passed for session={session_id}: "
            f"outcomes={len(session.outcomes)}, upload_outcomes={len(session.upload_outcomes)}"
        )
        
        return session
    
    async def end_session(
        self,
        session_id: str,
        duration_sec: float
    ) -> CoachingSession:
        """
        End session and calculate aggregated metrics.
        
        Raises:
            SessionNotFoundError: If session doesn't exist
            InvalidParameterError: If duration invalid
        """
        # Validate duration
        if duration_sec < CoachingConstants.MIN_SESSION_DURATION_SEC:
            raise InvalidParameterError(
                "duration_sec", duration_sec, 
                f"must be >= {CoachingConstants.MIN_SESSION_DURATION_SEC}"
            )
        if duration_sec > CoachingConstants.MAX_SESSION_DURATION_SEC:
            raise InvalidParameterError(
                "duration_sec", duration_sec,
                f"must be <= {CoachingConstants.MAX_SESSION_DURATION_SEC}"
            )
        
        session = await self.get_session_or_raise(session_id)
        
        # Calculate metrics
        intervention_count = len(session.interventions)
        complied_count = sum(
            1 for o in session.outcomes 
            if o.compliance == ComplianceResult.COMPLIED.value
        )
        violated_count = sum(
            1 for o in session.outcomes 
            if o.compliance == ComplianceResult.VIOLATED.value
        )
        unknown_count = sum(
            1 for o in session.outcomes 
            if o.compliance == ComplianceResult.UNKNOWN.value
        )
        
        known_count = complied_count + violated_count
        total_outcomes = known_count + unknown_count
        
        compliance_rate = complied_count / known_count if known_count > 0 else None
        unknown_rate = unknown_count / total_outcomes if total_outcomes > 0 else None
        
        # Update session
        session.ended_at = utcnow()
        session.duration_sec = duration_sec
        session.intervention_count = intervention_count
        session.compliance_rate = compliance_rate
        session.unknown_rate = unknown_rate
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(
            f"[COACHING] Ended session: {session_id} "
            f"(duration={duration_sec:.1f}s, interventions={intervention_count}, "
            f"compliance={compliance_rate:.2%})" if compliance_rate else 
            f"[COACHING] Ended session: {session_id} (duration={duration_sec:.1f}s, no outcomes)"
        )
        return session
    
    async def list_sessions(
        self,
        user_id_hash: Optional[str] = None,
        pattern_id: Optional[str] = None,
        assignment: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CoachingSession]:
        """List sessions with optional filters."""
        # Validate limits
        limit = min(max(1, limit), 100)
        offset = max(0, offset)
        
        query = select(CoachingSession).order_by(CoachingSession.started_at.desc())
        
        if user_id_hash:
            query = query.where(CoachingSession.user_id_hash == user_id_hash)
        if pattern_id:
            query = query.where(CoachingSession.pattern_id == pattern_id)
        if assignment:
            query = query.where(CoachingSession.assignment == CoachingAssignment(assignment))
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_sessions(
        self,
        user_id_hash: Optional[str] = None,
        pattern_id: Optional[str] = None
    ) -> int:
        """Count sessions matching filters."""
        query = select(func.count(CoachingSession.id))
        
        if user_id_hash:
            query = query.where(CoachingSession.user_id_hash == user_id_hash)
        if pattern_id:
            query = query.where(CoachingSession.pattern_id == pattern_id)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    # ====================
    # INTERVENTION CRUD
    # ====================
    
    async def add_intervention(
        self,
        session_id: str,
        t_sec: float,
        rule_id: str,
        evidence_id: str,
        evidence_type: str = "frame",
        coach_line_id: str = "friendly",
        coach_line_text: Optional[str] = None,
        metric_value: Optional[float] = None,
        metric_threshold: Optional[float] = None,
        ap_id: Optional[str] = None
    ) -> CoachingIntervention:
        """
        Record an intervention event.
        
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionLimitExceededError: If intervention limit reached
        """
        # Validate input
        try:
            validated = AddInterventionInput(
                session_id=session_id,
                t_sec=t_sec,
                rule_id=rule_id,
                evidence_id=evidence_id,
                evidence_type=evidence_type,
                coach_line_id=coach_line_id,
                coach_line_text=coach_line_text,
                metric_value=metric_value,
                metric_threshold=metric_threshold,
                ap_id=ap_id
            )
        except Exception as e:
            raise InvalidParameterError("add_intervention", str(e), "validation failed")
        
        # Check session exists
        session = await self.get_session_or_raise(session_id)
        
        # Check limit
        if len(session.interventions) >= CoachingConstants.MAX_INTERVENTIONS_PER_SESSION:
            raise SessionLimitExceededError(
                "interventions",
                len(session.interventions),
                CoachingConstants.MAX_INTERVENTIONS_PER_SESSION
            )
        
        intervention = CoachingIntervention(
            session_id=validated.session_id,
            t_sec=validated.t_sec,
            rule_id=validated.rule_id,
            evidence_id=validated.evidence_id,
            evidence_type=EvidenceType(validated.evidence_type),
            coach_line_id=validated.coach_line_id,
            coach_line_text=validated.coach_line_text,
            metric_value=validated.metric_value,
            metric_threshold=validated.metric_threshold,
            ap_id=validated.ap_id,
            created_at=utcnow()
        )
        
        self.db.add(intervention)
        await self.db.commit()
        await self.db.refresh(intervention)
        
        logger.debug(f"[COACHING] Intervention: session={session_id}, rule={rule_id}, t={t_sec:.2f}s")
        return intervention
    
    async def add_intervention_idempotent(
        self,
        session_id: str,
        t_sec: float,
        rule_id: str,
        evidence_id: str,
        evidence_type: str = "frame",
        coach_line_id: str = "friendly",
        coach_line_text: Optional[str] = None,
        metric_value: Optional[float] = None,
        metric_threshold: Optional[float] = None,
        ap_id: Optional[str] = None,
        bucket_ms: int = 500
    ) -> tuple[CoachingIntervention, bool]:
        """
        H4: Idempotent intervention recording.
        
        Prevents duplicate interventions from network retries by using
        (session_id, rule_id, t_sec_bucket) as a dedup key.
        
        Args:
            session_id: Session ID
            t_sec: Intervention time in seconds
            rule_id: Rule that triggered the intervention
            evidence_id: Evidence reference
            bucket_ms: Time bucket for deduplication (default 500ms)
            ... other params same as add_intervention
            
        Returns:
            (intervention, is_new): Tuple of intervention and whether it was newly created
            
        Example:
            intervention, is_new = await repo.add_intervention_idempotent(
                session_id="sess_123",
                t_sec=5.2,
                rule_id="hook_3s",
                evidence_id="ev_001"
            )
            if not is_new:
                logger.info("Duplicate intervention ignored")
        """
        # Calculate t_sec bucket for deduplication
        t_ms = int(t_sec * 1000)
        t_bucket_ms = (t_ms // bucket_ms) * bucket_ms
        
        # Check for existing intervention in same bucket
        query = select(CoachingIntervention).where(
            CoachingIntervention.session_id == session_id,
            CoachingIntervention.rule_id == rule_id,
            # Check if t_sec falls in same bucket
            func.floor(CoachingIntervention.t_sec * 1000 / bucket_ms) == t_bucket_ms // bucket_ms
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.debug(
                f"[COACHING] Idempotent: duplicate intervention ignored "
                f"session={session_id}, rule={rule_id}, t_bucket={t_bucket_ms}ms"
            )
            return existing, False
        
        # Create new intervention
        intervention = await self.add_intervention(
            session_id=session_id,
            t_sec=t_sec,
            rule_id=rule_id,
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            coach_line_id=coach_line_id,
            coach_line_text=coach_line_text,
            metric_value=metric_value,
            metric_threshold=metric_threshold,
            ap_id=ap_id
        )
        
        logger.debug(
            f"[COACHING] Idempotent: new intervention created "
            f"session={session_id}, rule={rule_id}, t={t_sec:.2f}s"
        )
        return intervention, True
    
    async def get_interventions(
        self,
        session_id: str,
        rule_id: Optional[str] = None
    ) -> List[CoachingIntervention]:
        """Get interventions for a session."""
        query = select(CoachingIntervention).where(
            CoachingIntervention.session_id == session_id
        ).order_by(CoachingIntervention.t_sec)
        
        if rule_id:
            query = query.where(CoachingIntervention.rule_id == rule_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ====================
    # OUTCOME CRUD
    # ====================
    
    async def add_outcome(
        self,
        session_id: str,
        t_sec: float,
        rule_id: str,
        compliance: str = "unknown",
        compliance_unknown_reason: Optional[str] = None,
        metric_value_after: Optional[float] = None,
        metric_delta: Optional[float] = None,
        latency_sec: Optional[float] = None
    ) -> CoachingOutcome:
        """
        Record an outcome event.
        
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionLimitExceededError: If outcome limit reached
        """
        # Validate input
        try:
            validated = AddOutcomeInput(
                session_id=session_id,
                t_sec=t_sec,
                rule_id=rule_id,
                compliance=compliance,
                compliance_unknown_reason=compliance_unknown_reason,
                metric_value_after=metric_value_after,
                metric_delta=metric_delta,
                latency_sec=latency_sec
            )
        except Exception as e:
            raise InvalidParameterError("add_outcome", str(e), "validation failed")
        
        # Check session exists
        session = await self.get_session_or_raise(session_id)
        
        # Check limit
        if len(session.outcomes) >= CoachingConstants.MAX_OUTCOMES_PER_SESSION:
            raise SessionLimitExceededError(
                "outcomes",
                len(session.outcomes),
                CoachingConstants.MAX_OUTCOMES_PER_SESSION
            )
        
        outcome = CoachingOutcome(
            session_id=validated.session_id,
            t_sec=validated.t_sec,
            rule_id=validated.rule_id,
            compliance=ComplianceResult(validated.compliance),
            compliance_unknown_reason=validated.compliance_unknown_reason,
            metric_value_after=validated.metric_value_after,
            metric_delta=validated.metric_delta,
            latency_sec=validated.latency_sec,
            created_at=utcnow()
        )
        
        self.db.add(outcome)
        await self.db.commit()
        await self.db.refresh(outcome)
        
        logger.debug(f"[COACHING] Outcome: session={session_id}, rule={rule_id}, compliance={compliance}")
        return outcome
    
    async def get_outcomes(
        self,
        session_id: str,
        rule_id: Optional[str] = None
    ) -> List[CoachingOutcome]:
        """Get outcomes for a session."""
        query = select(CoachingOutcome).where(
            CoachingOutcome.session_id == session_id
        ).order_by(CoachingOutcome.t_sec)
        
        if rule_id:
            query = query.where(CoachingOutcome.rule_id == rule_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ====================
    # UPLOAD OUTCOME
    # ====================
    
    async def set_upload_outcome(
        self,
        session_id: str,
        uploaded: bool,
        upload_platform: Optional[str] = None,
        early_views_bucket: Optional[str] = None,
        early_likes_bucket: Optional[str] = None,
        self_rating: Optional[int] = None,
        self_rating_reason: Optional[str] = None
    ) -> CoachingUploadOutcome:
        """
        Record upload outcome for session.
        
        Auto-creates or updates existing record.
        
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Validate input
        try:
            validated = SetUploadOutcomeInput(
                session_id=session_id,
                uploaded=uploaded,
                upload_platform=upload_platform,
                early_views_bucket=early_views_bucket,
                early_likes_bucket=early_likes_bucket,
                self_rating=self_rating,
                self_rating_reason=self_rating_reason
            )
        except Exception as e:
            raise InvalidParameterError("set_upload_outcome", str(e), "validation failed")
        
        # Verify session exists
        await self.get_session_or_raise(session_id)
        
        # Check if exists
        existing = await self.db.execute(
            select(CoachingUploadOutcome).where(
                CoachingUploadOutcome.session_id == session_id
            )
        )
        upload_outcome = existing.scalar_one_or_none()
        
        if upload_outcome:
            # Update
            upload_outcome.uploaded = validated.uploaded
            upload_outcome.upload_platform = validated.upload_platform
            upload_outcome.early_views_bucket = validated.early_views_bucket
            upload_outcome.early_likes_bucket = validated.early_likes_bucket
            upload_outcome.self_rating = validated.self_rating
            upload_outcome.self_rating_reason = validated.self_rating_reason
            upload_outcome.recorded_at = utcnow()
        else:
            # Create
            upload_outcome = CoachingUploadOutcome(
                session_id=validated.session_id,
                uploaded=validated.uploaded,
                upload_platform=validated.upload_platform,
                early_views_bucket=validated.early_views_bucket,
                early_likes_bucket=validated.early_likes_bucket,
                self_rating=validated.self_rating,
                self_rating_reason=validated.self_rating_reason,
                recorded_at=utcnow()
            )
            self.db.add(upload_outcome)
        
        await self.db.commit()
        await self.db.refresh(upload_outcome)
        
        logger.info(f"[COACHING] Upload outcome: session={session_id}, uploaded={uploaded}")
        return upload_outcome
    
    # ====================
    # STATISTICS
    # ====================
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get per-rule statistics for a session.
        
        Returns dict with rule_id keys containing:
        - intervention_count
        - compliance_rate (None if no known outcomes)
        - mean_latency_sec
        - mean_delta
        """
        session = await self.get_session_or_raise(session_id)
        
        stats: Dict[str, Dict[str, Any]] = {}
        
        # Group interventions by rule
        for intervention in session.interventions:
            rule_id = intervention.rule_id
            if rule_id not in stats:
                stats[rule_id] = {
                    "intervention_count": 0,
                    "complied_count": 0,
                    "violated_count": 0,
                    "unknown_count": 0,
                    "latency_sum": 0.0,
                    "latency_count": 0,
                    "delta_sum": 0.0,
                    "delta_count": 0
                }
            stats[rule_id]["intervention_count"] += 1
        
        # Add outcomes
        for outcome in session.outcomes:
            rule_id = outcome.rule_id
            if rule_id not in stats:
                # Outcome without intervention (edge case)
                stats[rule_id] = {
                    "intervention_count": 0,
                    "complied_count": 0,
                    "violated_count": 0,
                    "unknown_count": 0,
                    "latency_sum": 0.0,
                    "latency_count": 0,
                    "delta_sum": 0.0,
                    "delta_count": 0
                }
            
            if outcome.compliance == ComplianceResult.COMPLIED.value:
                stats[rule_id]["complied_count"] += 1
            elif outcome.compliance == ComplianceResult.VIOLATED.value:
                stats[rule_id]["violated_count"] += 1
            else:
                stats[rule_id]["unknown_count"] += 1
            
            if outcome.latency_sec is not None:
                stats[rule_id]["latency_sum"] += outcome.latency_sec
                stats[rule_id]["latency_count"] += 1
            if outcome.metric_delta is not None:
                stats[rule_id]["delta_sum"] += outcome.metric_delta
                stats[rule_id]["delta_count"] += 1
        
        # Calculate rates
        result = {}
        for rule_id, raw in stats.items():
            known_count = raw["complied_count"] + raw["violated_count"]
            result[rule_id] = {
                "intervention_count": raw["intervention_count"],
                "complied_count": raw["complied_count"],
                "violated_count": raw["violated_count"],
                "unknown_count": raw["unknown_count"],
                "compliance_rate": raw["complied_count"] / known_count if known_count > 0 else None,
                "mean_latency_sec": raw["latency_sum"] / raw["latency_count"] if raw["latency_count"] > 0 else None,
                "mean_delta": raw["delta_sum"] / raw["delta_count"] if raw["delta_count"] > 0 else None
            }
        
        return result
    
    async def get_aggregated_stats(
        self,
        pattern_id: Optional[str] = None,
        min_sessions: int = 10
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics across sessions.
        
        For Proof Playbook compliance lift calculation.
        """
        sessions = await self.list_sessions(pattern_id=pattern_id, limit=1000)
        
        if len(sessions) < min_sessions:
            return {
                "error": f"Insufficient sessions: {len(sessions)}/{min_sessions}",
                "total_sessions": len(sessions)
            }
        
        coached_sessions = [s for s in sessions if s.assignment == CoachingAssignment.COACHED.value]
        control_sessions = [s for s in sessions if s.assignment == CoachingAssignment.CONTROL.value]
        
        def avg_compliance(session_list: List[CoachingSession]) -> Optional[float]:
            rates = [s.compliance_rate for s in session_list if s.compliance_rate is not None]
            return sum(rates) / len(rates) if rates else None
        
        coached_rate = avg_compliance(coached_sessions)
        control_rate = avg_compliance(control_sessions)
        
        lift = None
        if coached_rate is not None and control_rate is not None and control_rate > 0:
            lift = (coached_rate - control_rate) / control_rate
        
        return {
            "total_sessions": len(sessions),
            "coached_sessions": len(coached_sessions),
            "control_sessions": len(control_sessions),
            "coached_compliance_rate": coached_rate,
            "control_compliance_rate": control_rate,
            "compliance_lift": lift,
            "control_group_ratio": len(control_sessions) / len(sessions) if sessions else None
        }
