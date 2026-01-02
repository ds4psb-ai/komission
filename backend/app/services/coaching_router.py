"""
Coaching Router

Control Group 할당 + Holdout 분리 로직.

Goodhart Prevention:
- 10% control (코칭 없음) - 인과 증명용
- 5% holdout (승격 판단 제외) - 검증용

P1 Roadmap: 세션 로깅 인프라
"""
import random
import hashlib
from typing import Tuple
from dataclasses import dataclass


@dataclass
class AssignmentResult:
    """Assignment decision result."""
    assignment: str  # "coached" | "control"
    holdout_group: bool
    reason: str


class CoachingRouter:
    """
    Routes sessions to coached/control groups.
    
    Usage:
        router = CoachingRouter()
        result = router.assign_group(session_id)
        
        if result.assignment == "control":
            # Don't deliver coaching, but still log rule_evaluated events
        
        if result.holdout_group:
            # Exclude from promotion calculations
    """
    
    # Configurable ratios
    CONTROL_RATIO: float = 0.10  # 10% control group
    HOLDOUT_RATIO: float = 0.05  # 5% holdout (subset of coached)
    
    # Seed for reproducibility (optional)
    SEED: int = 42
    
    def __init__(self, control_ratio: float = None, holdout_ratio: float = None):
        """Initialize router with optional custom ratios."""
        if control_ratio is not None:
            self.CONTROL_RATIO = control_ratio
        if holdout_ratio is not None:
            self.HOLDOUT_RATIO = holdout_ratio
    
    def assign_group(self, session_id: str) -> AssignmentResult:
        """
        Assign session to control/coached group.
        
        Uses deterministic hash-based assignment for reproducibility.
        Same session_id always gets same assignment.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            AssignmentResult with assignment and holdout_group
        """
        import os
        # DEV MODE: Always return coached for testing
        if os.getenv("ENV", "development") == "development":
            return AssignmentResult(
                assignment="coached",
                holdout_group=False,
                reason="dev_mode_always_coached"
            )
        
        # Deterministic random based on session_id
        hash_value = self._session_hash(session_id)
        
        # Control group: first 10%
        if hash_value < self.CONTROL_RATIO:
            return AssignmentResult(
                assignment="control",
                holdout_group=False,
                reason="control_group_for_causal_inference"
            )
        
        # Holdout: next 5% of coached (so 10-15% range)
        holdout_threshold = self.CONTROL_RATIO + self.HOLDOUT_RATIO
        if hash_value < holdout_threshold:
            return AssignmentResult(
                assignment="coached",
                holdout_group=True,
                reason="holdout_for_promotion_verification"
            )
        
        # Normal coached: remaining 85%
        return AssignmentResult(
            assignment="coached",
            holdout_group=False,
            reason="normal_coached_session"
        )
    
    def _session_hash(self, session_id: str) -> float:
        """
        Generate deterministic hash value [0, 1) from session_id.
        
        Same session_id always produces same hash.
        """
        hash_bytes = hashlib.sha256(
            f"{session_id}:{self.SEED}".encode()
        ).digest()
        
        # Convert first 8 bytes to float [0, 1)
        hash_int = int.from_bytes(hash_bytes[:8], 'big')
        return hash_int / (2 ** 64)
    
    def get_group_stats(self, session_ids: list) -> dict:
        """
        Calculate group distribution for a list of sessions.
        
        Useful for verifying 10% control ratio is maintained.
        """
        control_count = 0
        holdout_count = 0
        coached_count = 0
        
        for sid in session_ids:
            result = self.assign_group(sid)
            if result.assignment == "control":
                control_count += 1
            elif result.holdout_group:
                holdout_count += 1
            else:
                coached_count += 1
        
        total = len(session_ids)
        return {
            "total": total,
            "control": control_count,
            "control_ratio": control_count / total if total > 0 else 0,
            "holdout": holdout_count,
            "holdout_ratio": holdout_count / total if total > 0 else 0,
            "coached": coached_count,
            "coached_ratio": coached_count / total if total > 0 else 0,
        }


# Singleton instance
_router_instance = None


def get_coaching_router() -> CoachingRouter:
    """Get singleton CoachingRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = CoachingRouter()
    return _router_instance
