"""
Analysis Planner (Bridge Logic)

Converts Semantic Pass Result → Visual Pass Analysis Plan

Key Responsibilities:
1. Extract analysis points from hook_genome.microbeats
2. Extract points from scene boundaries
3. Extract points from entity hints
4. [NEW] Extract points from mise_en_scene_signals (comment evidence)
5. Budget and prioritize points

H-1 Hardening: Imports from centralized metric_registry.py (Single SoR)
"""
from typing import List, Dict, Any, Optional
import math
import hashlib
from app.schemas.vdg_v4 import (
    AnalysisPlan, 
    AnalysisPoint, 
    SemanticPassResult, 
    MetricRequest,
    SamplingPolicy,
    MiseEnSceneSignal
)
# H-1: Import from Single Source of Record
from app.schemas.metric_registry import (
    validate_metric_id,
    get_preset_metrics,
    METRIC_DEFINITIONS,
    METRIC_ALIASES
)
import logging

logger = logging.getLogger(__name__)


class AnalysisPlanner:
    """
    Bridge Logic: Semantic Pass Result -> Visual Pass Analysis Plan
    
    Generates targeted analysis points for Visual Pass based on:
    - Hook microbeats (critical)
    - Scene boundaries (high)
    - Entity hints (high)
    - Mise-en-scene signals from comments (medium/high) ← Core Evidence
    
    H-1 Hardening:
    - Imports metric definitions from centralized metric_registry.py
    - No local copies of registry (SSoT)
    """
    
    # Metric presets use the centralized registry
    @classmethod
    def _get_metrics_for_reason(cls, reason: str) -> List[MetricRequest]:
        """Get MetricRequests for a given analysis reason."""
        preset_ids = get_preset_metrics(reason)
        return [MetricRequest(metric_id=mid) for mid in preset_ids]
    
    @classmethod
    def _validate_metric_id(cls, metric_id: str) -> str:
        """Validate metric_id using centralized registry."""
        return validate_metric_id(metric_id)
    
    @classmethod
    def plan(
        cls,
        semantic: SemanticPassResult,
        mise_en_scene_signals: List[MiseEnSceneSignal] = None,
        max_points: int = 20,
        target_fps: float = 10.0
    ) -> AnalysisPlan:
        """
        Generate an AnalysisPlan based on semantic insights.
        
        Args:
            semantic: SemanticPassResult from Pass 1
            mise_en_scene_signals: Separate list of signals (from VDG root)
            max_points: Maximum analysis points budget
            target_fps: Target FPS for visual analysis
        
        Returns:
            AnalysisPlan with prioritized analysis points
        """
        points: List[AnalysisPoint] = []
        
        def add_point(
            t: float, 
            reason: str, 
            priority: str, 
            duration: float = 1.0, 
            hint_key: str = None,
            source_ref: str = "",
            metrics: List[MetricRequest] = None,
            measurement_method: str = "llm"
        ):
            # Clamp t to positive
            t = max(0.0, t)
            
            # H1 Hardening: SHA1-based deterministic ID for RL join key stability
            # Same input → same ID (재분석해도 동일한 ID 보장)
            t_ms = int(t * 1000)
            id_seed = f"{reason}|{source_ref}|{t_ms}|{hint_key or ''}"
            id_hash = hashlib.sha1(id_seed.encode()).hexdigest()[:8]
            stable_id = f"ap_{reason}_{t_ms:06d}_{id_hash}"
            
            # Select metrics based on reason
            if metrics is None:
                if "hook" in reason:
                    metrics = cls._get_metrics_for_reason("hook")
                elif reason == "scene_boundary":
                    metrics = cls._get_metrics_for_reason("scene_boundary")
                elif reason in ["comment_mise_en_scene", "comment_evidence"]:
                    metrics = cls._get_metrics_for_reason("mise_en_scene")
                elif hint_key:
                    metrics = cls._get_metrics_for_reason("entity")
                else:
                    metrics = cls._get_metrics_for_reason("default")
            
            p = AnalysisPoint(
                id=stable_id,  # P0-1: Stable ID
                t_center=t,
                t_window=[max(0.0, t - duration/2), t + duration/2],
                priority=priority,
                reason=reason,
                source_ref=source_ref,
                target_hint_key=hint_key,
                metrics_requested=metrics,
                measurement_method=measurement_method
            )
            points.append(p)

        # 1. Hook Analysis (Critical) - Highest Priority
        if semantic.hook_genome:
            for beat in semantic.hook_genome.microbeats:
                reason_map = {
                    "start": "hook_start",
                    "build": "hook_build", 
                    "punch": "hook_punch",
                    "end": "hook_end"
                }
                reason_val = reason_map.get(beat.role, "hook_build")
                priority = "critical" if beat.role == "punch" else "high"
                add_point(
                    t=beat.t, 
                    reason=reason_val, 
                    priority=priority, 
                    duration=0.5,
                    source_ref=f"microbeat_{beat.role}"
                )
            logger.info(f"   └─ Hook points: {len(semantic.hook_genome.microbeats)}")

        # 2. Scene Boundaries (High)
        scene_points = 0
        for scene in semantic.scenes:
            if scene.time_start > 3.0:  # Skip if covered by hook
                add_point(
                    t=scene.time_start, 
                    reason="scene_boundary", 
                    priority="high", 
                    duration=1.0,
                    source_ref=f"scene_{scene.scene_id}"
                )
                scene_points += 1
        if scene_points > 0:
            logger.info(f"   └─ Scene boundary points: {scene_points}")
        
        # 3. Entity Hints (High) - Main Speaker Tracking
        main_speaker = semantic.entity_hints.get("main_speaker")
        if main_speaker:
            mid_t = 5.0
            if semantic.scenes:
                mid_t = semantic.scenes[len(semantic.scenes)//2].time_start + 1.0
            
            add_point(
                t=mid_t, 
                reason="key_dialogue", 
                priority="high", 
                duration=1.0, 
                hint_key="main_speaker",
                source_ref="entity_hint_main_speaker"
            )
            logger.info(f"   └─ Entity point at t={mid_t:.1f}s")
        
        # 4. ★ COMMENT EVIDENCE - Mise-en-Scene Signals (Medium/High)
        # This is the CORE feature: best comments reveal viral moments
        signals = mise_en_scene_signals or []
        comment_points = 0
        
        for signal in signals:
            # Prioritize by likes and sentiment
            if signal.sentiment == "positive" and signal.likes > 100:
                priority = "high" if signal.likes > 500 else "medium"
                
                # Estimate timestamp (if not available, use middle of video)
                # TODO: In future, extract timestamp from comment text patterns
                t_estimate = 3.0  # Default to early-mid (where hooks happen)
                
                add_point(
                    t=t_estimate,
                    reason="comment_evidence",
                    priority=priority,
                    duration=2.0,  # Wider window for discovery
                    source_ref=f"comment_{signal.likes}_{signal.element}",
                    measurement_method="hybrid"  # LLM should audit CV measurements
                )
                comment_points += 1
            
            # Also capture negative signals as "what to avoid"
            elif signal.sentiment == "negative" and signal.likes > 200:
                add_point(
                    t=5.0,  # Mid video
                    reason="comment_mise_en_scene",
                    priority="medium",
                    duration=2.0,
                    source_ref=f"negative_comment_{signal.element}",
                    measurement_method="llm"
                )
                comment_points += 1
        
        if comment_points > 0:
            logger.info(f"   └─ Comment evidence points: {comment_points}")

        # H4 Hardening: Overlap Merge (same t_window → combine)
        points = cls._merge_overlapping_points(points, threshold_sec=0.5)
        logger.info(f"   └─ After overlap merge: {len(points)} points")

        # 5. Budget Enforcement
        if len(points) > max_points:
            prio_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            points = sorted(points, key=lambda x: prio_map.get(x.priority, 99))
            points = points[:max_points]
            logger.info(f"   └─ Trimmed to budget: {max_points}")
              
        # Sort by time for execution efficiency (ID remains stable)
        points.sort(key=lambda x: x.t_center)
        
        # P0-1: NO renumbering - IDs are content-based and stable
        # Execution order is just for efficiency, not identity

        # P0-3: Validate all metric_ids against registry
        for point in points:
            if point.metrics_requested:
                for metric in point.metrics_requested:
                    metric.metric_id = cls._validate_metric_id(metric.metric_id)

        logger.info(f"📋 AnalysisPlan generated: {len(points)} points")
        
        return AnalysisPlan(
            max_points_total=max_points,
            sampling=SamplingPolicy(target_fps=target_fps),
            points=points
        )
    
    @classmethod
    def _merge_overlapping_points(
        cls,
        points: List[AnalysisPoint],
        threshold_sec: float = 0.5
    ) -> List[AnalysisPoint]:
        """
        H4 Hardening: Merge overlapping analysis points.
        
        Points within threshold_sec of each other:
        - Metrics: union
        - Priority: max (critical > high > medium > low)
        - Source refs: combine
        """
        if not points:
            return points
        
        # Sort by t_center for merge
        sorted_pts = sorted(points, key=lambda x: x.t_center)
        merged: List[AnalysisPoint] = []
        current = sorted_pts[0]
        
        prio_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        for next_pt in sorted_pts[1:]:
            if abs(next_pt.t_center - current.t_center) <= threshold_sec:
                # Merge: combine metrics, take higher priority
                combined_metrics = list({m.metric_id: m for m in 
                    (current.metrics_requested or []) + (next_pt.metrics_requested or [])
                }.values())
                
                # Take higher priority
                curr_prio = prio_order.get(current.priority, 99)
                next_prio = prio_order.get(next_pt.priority, 99)
                best_priority = current.priority if curr_prio <= next_prio else next_pt.priority
                
                # Create merged point with new ID
                t_ms = int(current.t_center * 1000)
                merged_id = f"ap_merged_{t_ms:06d}_{hashlib.sha1(f'{current.id}|{next_pt.id}'.encode()).hexdigest()[:6]}"
                
                current = AnalysisPoint(
                    id=merged_id,
                    t_center=current.t_center,
                    t_window=[
                        min(current.t_window[0], next_pt.t_window[0]),
                        max(current.t_window[1], next_pt.t_window[1])
                    ],
                    priority=best_priority,
                    reason=f"{current.reason}+{next_pt.reason}",
                    source_ref=f"{current.source_ref}|{next_pt.source_ref}",
                    target_hint_key=current.target_hint_key or next_pt.target_hint_key,
                    metrics_requested=combined_metrics,
                    measurement_method=current.measurement_method
                )
            else:
                merged.append(current)
                current = next_pt
        
        merged.append(current)
        return merged


# Legacy function for backward compatibility
def generate_analysis_plan(
    semantic: SemanticPassResult,
    config: Dict[str, Any] = None
) -> AnalysisPlan:
    """
    Legacy wrapper for AnalysisPlanner.plan()
    """
    config = config or {}
    return AnalysisPlanner.plan(
        semantic=semantic,
        max_points=config.get("max_points", 20),
        target_fps=config.get("target_fps", 10.0)
    )
