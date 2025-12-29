"""
Analysis Planner (Bridge Logic)

Converts Semantic Pass Result → Visual Pass Analysis Plan

Key Responsibilities:
1. Extract analysis points from hook_genome.microbeats
2. Extract points from scene boundaries
3. Extract points from entity hints
4. [NEW] Extract points from mise_en_scene_signals (comment evidence)
5. Budget and prioritize points
"""
from typing import List, Dict, Any, Optional
import math
from app.schemas.vdg_v4 import (
    AnalysisPlan, 
    AnalysisPoint, 
    SemanticPassResult, 
    MetricRequest,
    SamplingPolicy,
    MiseEnSceneSignal
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
    """
    
    # Metric mappings for different analysis reasons
    METRIC_PRESETS = {
        "hook": [
            MetricRequest(metric_id="cmp.center_offset_xy.v1"),
            MetricRequest(metric_id="cmp.stability_score.v1"),
            MetricRequest(metric_id="lit.brightness_ratio.v1")
        ],
        "scene_boundary": [
            MetricRequest(metric_id="cmp.stability_score.v1"),
            MetricRequest(metric_id="cmp.composition_grid.v1")
        ],
        "entity": [
            MetricRequest(metric_id="ent.face_size_ratio.v1"),
            MetricRequest(metric_id="ent.expression_arouse.v1"),
            MetricRequest(metric_id="cmp.center_offset_xy.v1")
        ],
        "mise_en_scene": [
            MetricRequest(metric_id="cmp.composition_grid.v1"),
            MetricRequest(metric_id="vis.dominant_color.v1"),
            MetricRequest(metric_id="lit.brightness_ratio.v1")
        ],
        "default": [
            MetricRequest(metric_id="cmp.composition_grid.v1"),
            MetricRequest(metric_id="lit.brightness_ratio.v1")
        ]
    }
    
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
            
            # P0-1: Stable ID based on content (not execution order)
            # Format: ap_{reason}_{t_ms}_{hint}
            t_ms = int(t * 1000)
            hint_suffix = f"_{hint_key}" if hint_key else ""
            stable_id = f"ap_{reason}_{t_ms:06d}{hint_suffix}"
            
            # Select metrics based on reason
            if metrics is None:
                if "hook" in reason:
                    metrics = cls.METRIC_PRESETS["hook"]
                elif reason == "scene_boundary":
                    metrics = cls.METRIC_PRESETS["scene_boundary"]
                elif reason in ["comment_mise_en_scene", "comment_evidence"]:
                    metrics = cls.METRIC_PRESETS["mise_en_scene"]
                elif hint_key:
                    metrics = cls.METRIC_PRESETS["entity"]
                else:
                    metrics = cls.METRIC_PRESETS["default"]
            
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

        logger.info(f"📋 AnalysisPlan generated: {len(points)} points")
        
        return AnalysisPlan(
            max_points_total=max_points,
            sampling=SamplingPolicy(target_fps=target_fps),
            points=points
        )


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
