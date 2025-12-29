"""
VDG Merger (VDG v4.0)

P0-5: Real quality gate (no more gold-fixed)
P0-6: VDG structure is nested (semantic/visual/plan separate)
"""
from typing import List, Set
from app.schemas.vdg_v4 import (
    VDGv4, 
    SemanticPassResult, 
    VisualPassResult, 
    AnalysisPlan,
    MergerQuality,
    ContractCandidates
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VDGMerger:
    """
    Merger Logic: Combine Semantic & Visual Results into Final VDGv4
    
    P0-5 Hardening:
    - Real quality gate based on coverage metrics
    - No more gold-fixed tier
    - Mismatch flags for debugging
    
    P0-6 Hardening:
    - VDG structure is nested (semantic/visual/plan are separate)
    """
    
    @classmethod
    def merge(
        cls,
        semantic: SemanticPassResult,
        visual: VisualPassResult,
        plan: AnalysisPlan,
        content_id: str,
        video_url: str,
        duration_sec: float = None
    ) -> VDGv4:
        """
        Merge Pass 1 and Pass 2 results with quality validation.
        
        Args:
            semantic: Pass 1 result
            visual: Pass 2 result
            plan: Analysis plan that was executed
            content_id: Unique content identifier
            video_url: Source video URL
            duration_sec: Video duration (optional, for validation)
            
        Returns:
            VDGv4 with quality tier based on actual coverage
        """
        logger.info(f"🔄 Merging VDG for {content_id}")
        
        # 1. P0-5: Calculate Quality Metrics
        quality = cls._calculate_quality(semantic, visual, plan, duration_sec)
        
        # 2. Build VDG with nested structure (P0-6)
        # H2 Hardening Note: Root-level copies are DEPRECATED (backward compat only)
        # Future: Remove root copies, use vdg.semantic.* only
        # Views should use get_flat_view() for API serving
        vdg = VDGv4(
            vdg_version="4.0.4",  # Bump version for H2 hardening
            content_id=content_id,
            video_url=video_url,
            duration_sec=duration_sec or 0.0,
            # [DEPRECATED] Semantic Layer at root - for backward compat only
            # TODO: Remove in v4.1, use vdg.semantic.* instead
            scenes=semantic.scenes,
            hook_genome=semantic.hook_genome,
            intent_layer=semantic.intent_layer,
            audience_reaction=semantic.audience_reaction,
            capsule_brief=semantic.capsule_brief,
            ocr_content=semantic.ocr_content,
            asr_transcript=semantic.asr_transcript,
            mise_en_scene_signals=semantic.mise_en_scene_signals,
            entity_hints=semantic.entity_hints,
            summary=semantic.summary or "",
            # [CANONICAL] Nested references - SoR (Source of Record)
            semantic=semantic,  # P0-6: Full semantic object (CANONICAL)
            visual=visual,      # P0-6: Full visual object (CANONICAL)
            analysis_plan=plan, # P0-6: Plan reference (CANONICAL)
            # Quality
            merger_quality=quality,
            # Provenance
            provenance__semantic=semantic.provenance
        )
        
        # 3. Generate Contract Candidates for DirectorCompiler
        vdg.contract_candidates = cls._generate_contract_candidates(semantic, visual, plan)
        
        logger.info(f"   └─ Quality Tier: {quality.data_quality_tier}")
        logger.info(f"   └─ Alignment: {quality.overall_alignment:.2f}")
        if quality.mismatch_flags:
            logger.warning(f"   └─ Mismatches: {quality.mismatch_flags}")
        
        return vdg
    
    @classmethod
    def _calculate_quality(
        cls,
        semantic: SemanticPassResult,
        visual: VisualPassResult,
        plan: AnalysisPlan,
        duration_sec: float = None
    ) -> MergerQuality:
        """
        P0-5: Calculate real quality metrics.
        
        Checks:
        1. Point coverage: How many plan points have results?
        2. Entity resolution rate: How many hints were resolved?
        3. Metric coverage: How many requested metrics have values?
        4. Time sanity: Are all timestamps valid?
        """
        mismatch_flags: List[str] = []
        
        # 1. Point Coverage
        plan_point_ids: Set[str] = {p.id for p in plan.points}
        result_point_ids: Set[str] = set(visual.analysis_results.keys()) if visual.analysis_results else set()
        missing_points = plan_point_ids - result_point_ids
        point_coverage = len(result_point_ids) / max(len(plan_point_ids), 1)
        
        if missing_points:
            mismatch_flags.append(f"missing_points:{len(missing_points)}/{len(plan_point_ids)}")
        
        # 2. Entity Resolution Rate
        hint_count = len(semantic.entity_hints) if semantic.entity_hints else 0
        resolved_count = len(visual.entity_resolutions) if visual.entity_resolutions else 0
        entity_resolution_rate = resolved_count / max(hint_count, 1) if hint_count > 0 else 1.0
        
        if hint_count > 0 and entity_resolution_rate < 0.5:
            mismatch_flags.append(f"low_entity_resolution:{resolved_count}/{hint_count}")
        
        # 3. Metric Coverage
        total_requested = sum(len(p.metrics_requested) for p in plan.points)
        total_present = 0
        if visual.analysis_results:
            for ap_result in visual.analysis_results.values():
                if hasattr(ap_result, 'metrics') and ap_result.metrics:
                    total_present += len(ap_result.metrics)
        metric_coverage = total_present / max(total_requested, 1)
        
        if metric_coverage < 0.5:
            mismatch_flags.append(f"low_metric_coverage:{total_present}/{total_requested}")
        
        # 4. Time Sanity (if duration provided)
        if duration_sec and duration_sec > 0:
            for point in plan.points:
                if point.t_center < 0 or point.t_center > duration_sec + 1:
                    mismatch_flags.append(f"invalid_time:{point.id}:{point.t_center}")
                if point.t_window[0] >= point.t_window[1]:
                    mismatch_flags.append(f"invalid_window:{point.id}")
        
        # 5. Hook sanity
        if not semantic.hook_genome or semantic.hook_genome.strength < 0.1:
            mismatch_flags.append("weak_or_missing_hook")
        
        # Calculate Overall Alignment
        # Weighted average: point coverage (40%), entity (30%), metric (30%)
        overall_alignment = (
            point_coverage * 0.4 +
            entity_resolution_rate * 0.3 +
            metric_coverage * 0.3
        )
        
        # Determine Tier
        if not mismatch_flags and overall_alignment >= 0.9:
            tier = "gold"
        elif len(mismatch_flags) <= 2 and overall_alignment >= 0.7:
            tier = "silver"
        elif overall_alignment >= 0.5:
            tier = "bronze"
        else:
            tier = "reject"
        
        return MergerQuality(
            overall_alignment=round(overall_alignment, 3),
            mismatch_flags=mismatch_flags,
            data_quality_tier=tier
        )
    
    @classmethod
    def _generate_contract_candidates(
        cls,
        semantic: SemanticPassResult,
        visual: VisualPassResult,
        plan: AnalysisPlan
    ) -> ContractCandidates:
        """
        Generate contract candidates for DirectorCompiler.
        
        Extracts potential DNA invariants from:
        - Hook microbeats (timing rules)
        - Strong metric measurements (composition rules)
        - Mise-en-scene signals (evidence-backed rules)
        """
        candidates = ContractCandidates()
        
        # 1. From Hook Microbeats → Timing Rules
        if semantic.hook_genome and semantic.hook_genome.microbeats:
            for beat in semantic.hook_genome.microbeats:
                if beat.role in ["punch", "start"]:
                    candidates.dna_invariants_candidates.append({
                        "rule_id": f"hook_{beat.role}_timing",
                        "domain": "timing",
                        "priority": "critical",
                        "t_window": [max(0, beat.t - 0.5), beat.t + 0.5],
                        "spec": {
                            "metric_id": f"timing.{beat.role}.v1",
                            "op": "<=",
                            "target": beat.t + 0.5
                        },
                        "check_hint": f"Hook {beat.role} at {beat.t}s",
                        "source_ref": f"microbeat_{beat.role}"
                    })
                    candidates.weights_candidates[f"hook_{beat.role}_timing"] = 0.9
        
        # 2. From Visual Results → Composition Rules
        if visual.analysis_results:
            for ap_id, result in visual.analysis_results.items():
                if hasattr(result, 'metrics') and result.metrics:
                    for metric_id, metric_result in result.metrics.items():
                        # High stability → create rule
                        if "stability" in metric_id:
                            if hasattr(metric_result, 'aggregated_value') and metric_result.aggregated_value:
                                if metric_result.aggregated_value > 0.8:
                                    candidates.dna_invariants_candidates.append({
                                        "rule_id": f"stability_{ap_id}",
                                        "domain": "composition",
                                        "priority": "high",
                                        "spec": {
                                            "metric_id": metric_id,
                                            "op": ">=",
                                            "target": metric_result.aggregated_value * 0.9
                                        },
                                        "check_hint": f"Maintain stability level from {ap_id}"
                                    })
        
        # 3. From Mise-en-scene Signals → Evidence-backed Rules
        if semantic.mise_en_scene_signals:
            for signal in semantic.mise_en_scene_signals:
                if signal.sentiment == "positive" and signal.likes > 200:
                    candidates.dna_invariants_candidates.append({
                        "rule_id": f"mise_{signal.element}",
                        "domain": "composition",
                        "priority": "medium",
                        "spec": {
                            "metric_id": f"mise.{signal.element}.v1",
                            "op": "exists"
                        },
                        "check_hint": f"Keep {signal.element}: {signal.value}",
                        "evidence_refs": [f"comment_{signal.likes}"]
                    })
                    candidates.weights_candidates[f"mise_{signal.element}"] = min(signal.likes / 1000, 0.8)
        
        return candidates
