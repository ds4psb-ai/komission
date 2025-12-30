"""
Coaching Session Repository v1.0

SQLAlchemy-backed repository for coaching session data persistence.

Usage:
    from app.services.coaching_repository import CoachingRepository
    
    async with AsyncSessionLocal() as db:
        repo = CoachingRepository(db)
        session = await repo.create_session(user_id_hash="abc", mode="homage", ...)
        await repo.add_intervention(session_id, intervention_data)
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import (
    CoachingSession, CoachingIntervention, CoachingOutcome, CoachingUploadOutcome,
    CoachingAssignment, CoachingMode, EvidenceType, ComplianceResult
)
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


class CoachingRepository:
    """
    Repository for coaching session persistence.
    
    Aggregation metrics are calculated on session end and stored
    denormalized for efficient querying.
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
        """Create a new coaching session."""
        session = CoachingSession(
            session_id=session_id,
            user_id_hash=user_id_hash,
            mode=CoachingMode(mode),
            pattern_id=pattern_id,
            pack_id=pack_id,
            assignment=CoachingAssignment(assignment),
            holdout_group=holdout_group,
            pack_hash=pack_hash,
            started_at=utcnow()
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info(f"Created coaching session: {session_id}")
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
    
    async def end_session(
        self,
        session_id: str,
        duration_sec: float
    ) -> Optional[CoachingSession]:
        """End session and calculate aggregated metrics."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
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
        
        total_outcomes = complied_count + violated_count + unknown_count
        compliance_rate = complied_count / (complied_count + violated_count) if (complied_count + violated_count) > 0 else None
        unknown_rate = unknown_count / total_outcomes if total_outcomes > 0 else None
        
        # Update session
        session.ended_at = utcnow()
        session.duration_sec = duration_sec
        session.intervention_count = intervention_count
        session.compliance_rate = compliance_rate
        session.unknown_rate = unknown_rate
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Ended session {session_id}: interventions={intervention_count}, compliance={compliance_rate}")
        return session
    
    async def list_sessions(
        self,
        user_id_hash: Optional[str] = None,
        pattern_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CoachingSession]:
        """List sessions with optional filters."""
        query = select(CoachingSession).order_by(CoachingSession.started_at.desc())
        
        if user_id_hash:
            query = query.where(CoachingSession.user_id_hash == user_id_hash)
        if pattern_id:
            query = query.where(CoachingSession.pattern_id == pattern_id)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
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
        """Record an intervention event."""
        intervention = CoachingIntervention(
            session_id=session_id,
            t_sec=t_sec,
            rule_id=rule_id,
            evidence_id=evidence_id,
            evidence_type=EvidenceType(evidence_type),
            coach_line_id=coach_line_id,
            coach_line_text=coach_line_text,
            metric_value=metric_value,
            metric_threshold=metric_threshold,
            ap_id=ap_id,
            created_at=utcnow()
        )
        self.db.add(intervention)
        await self.db.commit()
        await self.db.refresh(intervention)
        
        logger.debug(f"Added intervention: session={session_id}, rule={rule_id}, t={t_sec}s")
        return intervention
    
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
        """Record an outcome event."""
        outcome = CoachingOutcome(
            session_id=session_id,
            t_sec=t_sec,
            rule_id=rule_id,
            compliance=ComplianceResult(compliance),
            compliance_unknown_reason=compliance_unknown_reason,
            metric_value_after=metric_value_after,
            metric_delta=metric_delta,
            latency_sec=latency_sec,
            created_at=utcnow()
        )
        self.db.add(outcome)
        await self.db.commit()
        await self.db.refresh(outcome)
        
        logger.debug(f"Added outcome: session={session_id}, rule={rule_id}, compliance={compliance}")
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
        """Record upload outcome for session."""
        # Check if exists
        existing = await self.db.execute(
            select(CoachingUploadOutcome).where(
                CoachingUploadOutcome.session_id == session_id
            )
        )
        upload_outcome = existing.scalar_one_or_none()
        
        if upload_outcome:
            # Update
            upload_outcome.uploaded = uploaded
            upload_outcome.upload_platform = upload_platform
            upload_outcome.early_views_bucket = early_views_bucket
            upload_outcome.early_likes_bucket = early_likes_bucket
            upload_outcome.self_rating = self_rating
            upload_outcome.self_rating_reason = self_rating_reason
            upload_outcome.recorded_at = utcnow()
        else:
            # Create
            upload_outcome = CoachingUploadOutcome(
                session_id=session_id,
                uploaded=uploaded,
                upload_platform=upload_platform,
                early_views_bucket=early_views_bucket,
                early_likes_bucket=early_likes_bucket,
                self_rating=self_rating,
                self_rating_reason=self_rating_reason,
                recorded_at=utcnow()
            )
            self.db.add(upload_outcome)
        
        await self.db.commit()
        await self.db.refresh(upload_outcome)
        
        logger.info(f"Set upload outcome: session={session_id}, uploaded={uploaded}")
        return upload_outcome
    
    # ====================
    # STATISTICS
    # ====================
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get per-rule statistics for a session."""
        session = await self.get_session(session_id)
        if not session:
            return {}
        
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
                    "delta_sum": 0.0,
                    "delta_count": 0
                }
            stats[rule_id]["intervention_count"] += 1
        
        # Add outcomes
        for outcome in session.outcomes:
            rule_id = outcome.rule_id
            if rule_id not in stats:
                continue
            
            if outcome.compliance == ComplianceResult.COMPLIED.value:
                stats[rule_id]["complied_count"] += 1
            elif outcome.compliance == ComplianceResult.VIOLATED.value:
                stats[rule_id]["violated_count"] += 1
            else:
                stats[rule_id]["unknown_count"] += 1
            
            if outcome.latency_sec:
                stats[rule_id]["latency_sum"] += outcome.latency_sec
            if outcome.metric_delta:
                stats[rule_id]["delta_sum"] += outcome.metric_delta
                stats[rule_id]["delta_count"] += 1
        
        # Calculate rates
        result = {}
        for rule_id, raw in stats.items():
            known_count = raw["complied_count"] + raw["violated_count"]
            result[rule_id] = {
                "intervention_count": raw["intervention_count"],
                "compliance_rate": raw["complied_count"] / known_count if known_count > 0 else None,
                "mean_latency_sec": raw["latency_sum"] / known_count if known_count > 0 else None,
                "mean_delta": raw["delta_sum"] / raw["delta_count"] if raw["delta_count"] > 0 else None
            }
        
        return result
