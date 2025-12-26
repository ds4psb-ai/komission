"""
Depth Experiments Service

Manages the flow from Depth1 → Decision → Depth2 experiments.
Based on Phase 4 #3: Decision 반영 후 Depth2 시작

Flow:
1. Parent is created from OutlierItem promotion
2. Depth1 experiments run (manual or auto mutations)
3. Evidence collected and Decision generated
4. Depth2 starts based on winning Depth1 patterns
"""
from typing import Dict, List, Optional, Any
from uuid import uuid4
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RemixNode, EvidenceSnapshot, TemplateSeed
from app.constants import (
    CONFIDENCE_LOW, EXPERIMENT_MIN_DAYS, EXPERIMENT_FIRST_REVIEW_DAYS,
    DEPTH2_VARIANTS_COUNT, DEPTH2_TRACKING_DAYS
)
from app.utils.time import utcnow, days_between, iso_now

logger = logging.getLogger(__name__)


class DepthExperimentService:
    """
    Manages depth experiment lifecycle.
    
    Depth1: Initial mutation experiments from Parent
    Depth2: Refined experiments based on Depth1 winners
    """
    
    async def get_experiment_status(
        self,
        db: AsyncSession,
        parent_id: str,
    ) -> Dict[str, Any]:
        """
        Get current experiment status for a Parent node.
        
        Returns:
            {
                "parent_id": str,
                "current_depth": 1 or 2,
                "variants_count": int,
                "days_tracked": int,
                "ready_for_depth2": bool,
                "decision": Optional[Dict],
            }
        """
        # Get parent node
        parent = await db.execute(
            select(RemixNode).where(RemixNode.node_id == parent_id)
        )
        parent_node = parent.scalar_one_or_none()
        
        if not parent_node:
            return {"error": "Parent not found", "parent_id": parent_id}
        
        # Count children (variants)
        children = await db.execute(
            select(func.count(RemixNode.id))
            .where(RemixNode.parent_node_id == parent_node.id)
        )
        variants_count = children.scalar() or 0
        
        # Get latest evidence snapshot
        evidence = await db.execute(
            select(EvidenceSnapshot)
            .where(EvidenceSnapshot.parent_node_id == parent_node.id)
            .order_by(EvidenceSnapshot.created_at.desc())
            .limit(1)
        )
        latest_evidence = evidence.scalar_one_or_none()
        
        # Calculate days tracked
        days_tracked = 0
        if parent_node.created_at:
            days_tracked = days_between(parent_node.created_at)
        
        # Check if ready for Depth2 (defined in constants)
        ready_for_depth2 = (
            days_tracked >= EXPERIMENT_MIN_DAYS and 
            latest_evidence is not None and 
            latest_evidence.confidence >= CONFIDENCE_LOW
        )
        
        # Build decision from evidence
        decision = None
        if latest_evidence:
            decision = {
                "top_mutation_type": latest_evidence.top_mutation_type,
                "top_mutation_pattern": latest_evidence.top_mutation_pattern,
                "top_mutation_rate": latest_evidence.top_mutation_rate,
                "confidence": latest_evidence.confidence,
                "sample_count": latest_evidence.sample_count,
            }
        
        return {
            "parent_id": parent_id,
            "parent_title": parent_node.title,
            "current_depth": 2 if ready_for_depth2 else 1,
            "variants_count": variants_count,
            "days_tracked": days_tracked,
            "ready_for_depth2": ready_for_depth2,
            "decision": decision,
            "recommendation": self._get_recommendation(
                days_tracked, variants_count, latest_evidence
            ),
        }
    
    def _get_recommendation(
        self,
        days_tracked: int,
        variants_count: int,
        evidence: Optional[EvidenceSnapshot],
    ) -> str:
        """Generate actionable recommendation."""
        
        if days_tracked < EXPERIMENT_FIRST_REVIEW_DAYS:
            return f"계속 추적 중 - {EXPERIMENT_FIRST_REVIEW_DAYS}일 후 첫 번째 분석 가능"
        
        if variants_count < DEPTH2_VARIANTS_COUNT:
            return f"더 많은 변주 필요 - 최소 {DEPTH2_VARIANTS_COUNT}개 이상 권장"
        
        if evidence is None:
            return "Evidence 생성 대기 중 - 크롤러/수동 입력으로 데이터 수집"
        
        if evidence.confidence < 0.5:
            return "신뢰도 낮음 - 더 많은 데이터 필요"
        
        if evidence.confidence < 0.7:
            return "패턴 분석 중 - 곧 Depth2 시작 가능"
        
        if evidence.top_mutation_pattern:
            return f"Depth2 권장: '{evidence.top_mutation_pattern}' 패턴을 기반으로 심화 실험"
        
        return "분석 완료 - Depth2 시작 가능"
    
    async def start_depth2_experiment(
        self,
        db: AsyncSession,
        parent_id: str,
        decision_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start Depth2 experiment based on Depth1 decision.
        
        This creates refined variants focusing on the winning patterns.
        
        Returns:
            {
                "experiment_id": str,
                "base_pattern": str,
                "variants_created": int,
            }
        """
        # Get parent status
        status = await self.get_experiment_status(db, parent_id)
        
        if status.get("error"):
            return status
        
        if not status.get("ready_for_depth2"):
            return {
                "error": "Not ready for Depth2",
                "days_tracked": status.get("days_tracked"),
                "recommendation": status.get("recommendation"),
            }
        
        decision = status.get("decision")
        if not decision:
            return {"error": "No decision available for Depth2"}
        
        # Generate experiment ID
        experiment_id = f"depth2_{parent_id[:8]}_{str(uuid4())[:8]}"
        
        # In production, this would create actual RemixNode children
        # For now, return the experiment plan
        depth2_plan = {
            "experiment_id": experiment_id,
            "parent_id": parent_id,
            "base_pattern": decision.get("top_mutation_pattern"),
            "mutation_type": decision.get("top_mutation_type"),
            "refinement_axes": self._generate_refinement_axes(decision),
            "variants_to_create": DEPTH2_VARIANTS_COUNT,
            "tracking_days": DEPTH2_TRACKING_DAYS,
            "started_at": iso_now(),
        }
        
        logger.info(f"Depth2 experiment started: {experiment_id}")
        
        return depth2_plan
    
    def _generate_refinement_axes(self, decision: Dict[str, Any]) -> List[str]:
        """
        Generate refinement axes for Depth2 based on winning pattern.
        
        Depth2 focuses on fine-tuning the winning pattern in specific dimensions.
        """
        mutation_type = decision.get("top_mutation_type", "")
        
        axes = {
            "audio": ["tempo_variation", "music_genre", "audio_mixing"],
            "visual": ["color_grade", "transition_style", "shot_duration"],
            "semantic": ["hook_variation", "cta_placement", "subtitle_density"],
        }
        
        return axes.get(mutation_type, ["timing", "intensity", "style"])
    
    async def get_active_experiments(
        self,
        db: AsyncSession,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get all active depth experiments.
        """
        # Get Parents with children (active experiments)
        parents = await db.execute(
            select(RemixNode)
            .where(RemixNode.parent_node_id.is_(None))  # Only Parents
            .order_by(RemixNode.created_at.desc())
            .limit(limit)
        )
        parent_nodes = parents.scalars().all()
        
        experiments = []
        for parent in parent_nodes:
            status = await self.get_experiment_status(db, parent.node_id)
            if status.get("variants_count", 0) > 0:
                experiments.append(status)
        
        return experiments


# Singleton instance
depth_experiment_service = DepthExperimentService()
