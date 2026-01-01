"""
VDG Format Converter (Unified → VDGv4)

UnifiedResult를 VDGv4 포맷으로 변환하는 로직
"""
import logging
from typing import Dict, Any

from app.schemas.vdg_v4 import (
    VDGv4, HookGenome, Scene, Microbeat,
    IntentLayer, MiseEnSceneSignal, AudienceReaction,
    SemanticPassResult, SemanticPassProvenance, CapsuleBrief,
    VisualPassResult, AnalysisPlan, AnalysisPoint,
    MediaSpec, MetricResult,
    # 2026 AI Video Trend Analysis
    SceneTransition, SceneTransitionType,
    CameraMetadata, CameraMovementType,
    MultiShotAnalysis,
)

logger = logging.getLogger(__name__)


def convert_unified_to_vdg_v4(
    unified_result,
    content_id: str,
    video_url: str,
    platform: str,
    duration_sec: float,
) -> VDGv4:
    """UnifiedResult를 VDGv4 포맷으로 변환"""
    
    llm = unified_result.llm_output
    cv = unified_result.cv_result
    
    # Role mapping from UnifiedPass to VDGv4
    role_map = {
        'start': 'start', 'setup': 'start', 'hook': 'start',
        'punch': 'punch', 'reveal': 'punch', 'twist': 'punch',
        'build': 'build', 'demo': 'build',
        'end': 'end', 'cta': 'end', 'loop': 'end', 'payoff': 'end',
    }
    
    # Hook genome 변환
    microbeats = []
    for m in (llm.hook_genome.microbeats or []):
        mb_role = role_map.get(m.role, 'start')
        microbeats.append(Microbeat(
            t=m.t_ms / 1000.0,  # ms → seconds
            role=mb_role,
            cue='visual',
            note=m.description[:50] if m.description else '',
        ))
    
    hook = HookGenome(
        start_sec=llm.hook_genome.hook_start_ms / 1000.0,  # ms → seconds
        end_sec=llm.hook_genome.hook_end_ms / 1000.0,      # ms → seconds
        pattern=llm.hook_genome.pattern,          # NEW: from LLM schema
        delivery=llm.hook_genome.delivery,        # NEW: from LLM schema
        hook_summary=llm.hook_genome.hook_summary or "",  # NEW: from LLM schema
        strength=llm.hook_genome.strength,
        microbeats=microbeats,
    )
    
    # Scenes 변환
    scenes = [
        Scene(
            scene_id=f"S{s.idx:02d}",
            time_start=s.window.start_ms / 1000.0,  # ms → seconds
            time_end=s.window.end_ms / 1000.0,      # ms → seconds
            duration_sec=(s.window.end_ms - s.window.start_ms) / 1000.0,
            narrative_role=s.label,
            summary=s.summary,
        )
        for s in llm.scenes
    ]
    
    # Intent layer 변환
    intent = IntentLayer(
        creator_intent=llm.intent_layer.creator_intent,
        audience_trigger=llm.intent_layer.audience_trigger,
        novelty=llm.intent_layer.novelty,
        clarity=llm.intent_layer.clarity,
    )
    
    # Mise-en-scene signals 변환
    # Element mapping from UnifiedPass to VDGv4
    element_map = {
        'prop': 'props', 'composition': 'setting', 'color': 'outfit_color',
        'wardrobe': 'outfit_color', 'camera': 'setting', 'editing': 'setting',
        'audio': 'setting', 'text': 'setting',
    }
    valid_elements = {'outfit_color', 'background', 'lighting', 'props', 'makeup', 'setting'}
    
    mise_signals = []
    for m in llm.mise_en_scene_signals:
        element = element_map.get(m.type, m.type)
        if element not in valid_elements:
            element = 'setting'  # default fallback
        mise_signals.append(MiseEnSceneSignal(
            element=element,
            value=m.description[:50],
            sentiment="positive",
            source_comment="",
            likes=0,
        ))
    
    # Comment evidence를 audience_reaction으로 변환
    best_comments = [
        {
            "rank": c.comment_rank,
            "text": c.quote,
            "signal_type": c.signal_type,
            "why_it_matters": c.why_it_matters,
            "anchor_ms": getattr(c, 'anchor_ms', None),
        }
        for c in llm.comment_evidence_top5
    ]
    
    # Viral kicks 변환
    viral_kicks = [
        {
            "kick_index": k.kick_index,
            "t_start_ms": k.window.start_ms,
            "t_end_ms": k.window.end_ms,
            "title": k.title,
            "mechanism": k.mechanism,
            "creator_instruction": k.creator_instruction,
            "evidence_comment_ranks": k.evidence_comment_ranks,
            "evidence_cues": k.evidence_cues,
        }
        for k in llm.viral_kicks
    ]
    
    audience = AudienceReaction(
        best_comments=best_comments,
        sentiment_distribution={},
        top_themes=[],
    )
    
    # Semantic pass result
    semantic_provenance = SemanticPassProvenance(
        model_id=unified_result.llm_provenance.model_id,
        prompt_version=unified_result.llm_provenance.prompt_version,
        run_at=unified_result.llm_provenance.run_at,
    )
    
    # Capsule brief 변환
    capsule_brief = CapsuleBrief(
        hook_script=llm.capsule_brief.hook_script if llm.capsule_brief else "",
        shotlist=[{"description": s} for s in (llm.capsule_brief.shotlist if llm.capsule_brief else [])],
        do_not=llm.capsule_brief.do_not if llm.capsule_brief else [],
    )
    
    semantic = SemanticPassResult(
        scenes=scenes,
        hook_genome=hook,
        intent_layer=intent,
        audience_reaction=audience,
        mise_en_scene_signals=mise_signals,
        capsule_brief=capsule_brief,
        summary=llm.causal_reasoning.why_viral_one_liner if llm.causal_reasoning else "",
        provenance=semantic_provenance,
    )
    
    # Analysis plan 변환
    analysis_points = []
    if llm.analysis_plan and llm.analysis_plan.points:
        # Reason mapping from UnifiedPass to VDGv4
        reason_map = {
            'critical': 'hook_punch', 'high': 'key_dialogue',
            'medium': 'scene_boundary', 'low': 'text_appear',
        }
        valid_reasons = {
            'hook_punch', 'hook_start', 'hook_build', 'hook_end',
            'scene_boundary', 'sentiment_shift', 'product_mention',
            'key_dialogue', 'text_appear', 'comment_mise_en_scene', 'comment_evidence'
        }
        for i, p in enumerate(llm.analysis_plan.points):
            # Map reason to valid enum or use priority-based mapping
            llm_reason = getattr(p, 'reason', '')
            if llm_reason in valid_reasons:
                mapped_reason = llm_reason
            else:
                mapped_reason = reason_map.get(p.priority, 'key_dialogue')
            
            t_start = (p.t_center_ms - p.t_window_ms // 2) / 1000.0
            t_end = (p.t_center_ms + p.t_window_ms // 2) / 1000.0
            
            point = AnalysisPoint(
                id=f"AP_{i:02d}",
                t_center=p.t_center_ms / 1000.0,
                t_window=[t_start, t_end],
                priority=p.priority,
                reason=mapped_reason,
                source_ref=f"llm_plan_{i}",
            )
            analysis_points.append(point)
    
    analysis_plan = AnalysisPlan(
        points=analysis_points,
    )
    
    # Visual pass result (CV measurements)
    visual = VisualPassResult()
    if unified_result.analysis_points:
        from app.schemas.vdg_v4 import AnalysisPointResult
        analysis_results = []
        for ap in unified_result.analysis_points:
            metrics_dict = {}
            for mid, mr in ap.metrics.items():
                # Infer value_type from value
                val = mr.value
                if isinstance(val, bool):
                    value_type = "bool"
                elif isinstance(val, (list, tuple)):
                    value_type = "vector2"
                elif isinstance(val, float):
                    value_type = "scalar"
                else:
                    value_type = "scalar"
                
                metrics_dict[mid] = MetricResult(
                    metric_id=mid,
                    value_type=value_type,
                    confidence=mr.confidence,
                )
            
            analysis_results.append(AnalysisPointResult(
                ap_id=ap.ap_id,
                t_center_ms=ap.t_center_ms,
                t_window_ms=ap.t_window_ms,
                metrics=metrics_dict,
            ))
        visual.analysis_results = analysis_results
    
    # Media spec
    media = MediaSpec(
        duration_ms=int(duration_sec * 1000),
    )
    
    # 2026 AI Video Trend Analysis - Parse from LLM output if available
    scene_transitions = []
    raw_transitions = getattr(llm, 'scene_transitions', None) or []
    for t in raw_transitions:
        try:
            scene_transitions.append(SceneTransition(
                from_scene_idx=t.get('from_scene_idx', 0),
                to_scene_idx=t.get('to_scene_idx', 1),
                t_transition=t.get('t_transition', 0.0),
                transition_type=t.get('transition_type', 'cut'),
                continuity_score=t.get('continuity_score', 0.8),
                rhythm_match=t.get('rhythm_match', True),
                transition_quality=t.get('transition_quality', 'acceptable'),
            ))
        except Exception as e:
            logger.warning(f"Failed to parse scene transition: {e}")
    
    camera_metadata_list = []
    raw_camera = getattr(llm, 'camera_metadata', None) or []
    for c in raw_camera:
        try:
            camera_metadata_list.append(CameraMetadata(
                scene_id=c.get('scene_id', 'S01'),
                movement_type=c.get('movement_type', 'static'),
                movement_intensity=c.get('movement_intensity', 'moderate'),
                estimated_fov=c.get('estimated_fov'),
                spatial_consistency=c.get('spatial_consistency', 0.8),
                depth_variation=c.get('depth_variation', 'shallow'),
                steady_score=c.get('steady_score', 0.8),
            ))
        except Exception as e:
            logger.warning(f"Failed to parse camera metadata: {e}")
    
    multi_shot = None
    raw_multi_shot = getattr(llm, 'multi_shot_analysis', None)
    if raw_multi_shot:
        try:
            multi_shot = MultiShotAnalysis(
                character_persistence=raw_multi_shot.get('character_persistence', 0.8),
                location_consistency=raw_multi_shot.get('location_consistency', 0.8),
                prop_tracking=raw_multi_shot.get('prop_tracking', 0.8),
                lighting_consistency=raw_multi_shot.get('lighting_consistency', 0.8),
                color_grading_consistency=raw_multi_shot.get('color_grading_consistency', 0.8),
                overall_coherence=raw_multi_shot.get('overall_coherence', 0.8),
                ai_generation_likelihood=raw_multi_shot.get('ai_generation_likelihood', 0.0),
                notes=raw_multi_shot.get('notes'),
            )
        except Exception as e:
            logger.warning(f"Failed to parse multi-shot analysis: {e}")
    
    return VDGv4(
        content_id=content_id,
        platform=platform,
        duration_sec=duration_sec,
        media=media,
        semantic=semantic,
        analysis_plan=analysis_plan,
        visual=visual,
        mise_en_scene_signals=mise_signals,
        # 2026 AI Video Trend Analysis
        scene_transitions=scene_transitions,
        camera_metadata=camera_metadata_list,
        multi_shot_analysis=multi_shot,
        provenance={
            "pipeline_version": "v5.0_unified",
            "pass1_model": unified_result.llm_provenance.model_id,
            "pass2_version": unified_result.cv_provenance.version if cv else None,
            "viral_kicks": viral_kicks,
            "causal_reasoning": {
                "why_viral_one_liner": llm.causal_reasoning.why_viral_one_liner,
                "causal_chain": llm.causal_reasoning.causal_chain,
                "replication_recipe": llm.causal_reasoning.replication_recipe,
            } if llm.causal_reasoning else {},
        },
    )


# Backward compatibility alias
_convert_unified_to_vdg_v4 = convert_unified_to_vdg_v4
