"""
Visual Pass (VDG v4.0 Pass 2)

P0-2: Uses Plan-based frame extraction (not full mp4)
P0-4: Uses robust_generate_content for retry/fallback/JSON repair
"""
from typing import Dict, Any, List
import json
import logging
from datetime import datetime
from google.genai.types import Part
from app.schemas.vdg_v4 import (
    VisualPassResult, 
    AnalysisPlan, 
    EntityHint, 
    MetricResult
)
from app.services.vdg_2pass.prompts.visual_prompt import (
    VISUAL_SYSTEM_PROMPT, 
    VISUAL_USER_PROMPT,
    get_metric_registry_json
)
from app.services.vdg_2pass.gemini_utils import robust_generate_content
from app.services.vdg_2pass.frame_extractor import FrameExtractor
from app.services.genai_client import get_genai_client, DEFAULT_MODEL_PRO
from app.config import settings

logger = logging.getLogger(__name__)


class VisualPass:
    """
    VDG v4.0 Pass 2: Visual Analysis
    
    Uses Gemini Pro to execute AnalysisPlan:
    - High-precision frame analysis
    - Entity Resolution (Hint -> ID)
    - Metric Extraction (with Registry definitions)
    
    P0-2 Hardening:
    - Plan-based frame extraction (not full mp4)
    - Cost reduction: ~1/5 of full video tokens
    - Falls back to full video if ffmpeg unavailable
    
    P0-4 Hardening:
    - Retry with exponential backoff
    - Async fallback to sync
    - JSON repair loop
    """
    
    def __init__(self, client=None):
        self.client = client or get_genai_client()
        
        # Use config or default to Pro
        self.model_name = getattr(settings, "GEMINI_MODEL_PRO", DEFAULT_MODEL_PRO)
        
        # P0-2: Check if frame extraction is available
        self._use_frames = FrameExtractor.is_available()
        if self._use_frames:
            logger.info("📷 P0-2: Frame extraction enabled (ffmpeg available)")
        else:
            logger.warning("⚠️ P0-2: Frame extraction disabled, using full video fallback")

    async def analyze(
        self,
        video_bytes: bytes,
        plan: AnalysisPlan,
        entity_hints: Dict[str, EntityHint],
        semantic_summary: str
    ) -> VisualPassResult:
        """
        Execute visual analysis pass based on the plan.
        
        P0-2: Uses plan-based frame extraction instead of full mp4.
        Falls back to full video if ffmpeg not available.
        
        Args:
            video_bytes: Raw video data
            plan: AnalysisPlan with specific points and metrics
            entity_hints: Semantic hints to guide entity tracking
            semantic_summary: High-level summary from Pass 1
            
        Returns:
            VisualPassResult object containing metrics and resolutions
        """
        start_time = datetime.utcnow()
        
        # 1. Prepare Inputs
        plan_json = plan.model_dump_json(indent=2)
        hints_json = json.dumps(
            {k: v.model_dump() for k, v in entity_hints.items()}, 
            indent=2
        )
        
        # P0-2: Extract requested metric IDs and get registry definitions
        requested_metrics = set()
        for point in plan.points:
            for mr in point.metrics_requested:
                requested_metrics.add(mr.metric_id)
        metric_registry_json = get_metric_registry_json(list(requested_metrics))
        
        # 2. Build Prompt (with Metric Registry injection)
        system_prompt = VISUAL_SYSTEM_PROMPT
        user_prompt = VISUAL_USER_PROMPT.format(
            semantic_summary=semantic_summary,
            entity_hints_json=hints_json,
            metric_registry_json=metric_registry_json,  # P0-2
            analysis_plan_json=plan_json
        )
        
        # 3. P0-2: Prepare Video Input (frames or full video)
        if self._use_frames and len(plan.points) > 0:
            # Extract frames from plan t_windows
            frames = FrameExtractor.extract_for_plan(
                video_bytes, 
                plan, 
                target_fps=plan.sampling.target_fps if plan.sampling else 2.0
            )
            
            if frames:
                # Use frames as input
                video_parts = FrameExtractor.to_model_parts(frames)
                input_mode = f"frames ({len(frames)} extracted)"
            else:
                # Fallback to full video if extraction failed
                video_parts = [types.Part(
                    inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")
                )]
                input_mode = "full_video (frame extraction failed)"
        else:
            # Fallback: Use full video
            video_parts = [types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")
            )]
            input_mode = "full_video (fallback)"
        
        # 4. Generate Content with P0-4 hardening
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            generation_config=types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=VisualPassResult,
                temperature=0.0,  # Zero temp for precise measurement
                max_output_tokens=8192
            )
        )
        
        logger.info(f"🎥 Starting Visual Pass (Model: {self.model_name})")
        logger.info(f"   └─ Input mode: {input_mode}")
        logger.info(f"   └─ Plan points: {len(plan.points)}")
        logger.info(f"   └─ Metrics requested: {len(requested_metrics)}")
        
        # P0-4: Use robust generation with retry/fallback/repair
        result = await robust_generate_content(
            model=model,
            contents=video_parts + [user_prompt],
            result_schema=VisualPassResult,
            max_retries=3,
            initial_backoff=2.0  # Visual pass is heavier, longer initial backoff
        )
        
        # Phase 2: Validate metric_ids in results against registry
        result = self._validate_result_metrics(result)
        
        # 5. Add provenance
        end_time = datetime.utcnow()
        elapsed_sec = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Visual Pass completed in {elapsed_sec:.1f}s")
        logger.info(f"   └─ Entity Resolutions: {len(result.entity_resolutions)}")
        logger.info(f"   └─ Analysis Results: {len(result.analysis_results)}")
        
        return result
    
    def _validate_result_metrics(self, result: VisualPassResult) -> VisualPassResult:
        """
        Phase 2 Flywheel: Validate metric_ids in VisualPass results.
        
        - Normalizes aliases to canonical IDs
        - Marks unknown metrics with missing_reason
        - Prevents metric drift (same ID = same meaning over time)
        """
        from app.schemas.metric_registry import validate_metric_id, METRIC_DEFINITIONS
        
        validated_count = 0
        unknown_count = 0
        
        if result.analysis_results:
            for ap_id, ap_result in result.analysis_results.items():
                if hasattr(ap_result, 'metrics') and ap_result.metrics:
                    for metric_id, metric_result in list(ap_result.metrics.items()):
                        # Validate and normalize
                        canonical = validate_metric_id(metric_id)
                        
                        # If alias, update the key
                        if canonical != metric_id:
                            ap_result.metrics[canonical] = metric_result
                            del ap_result.metrics[metric_id]
                            metric_result.original_metric_id = metric_id
                            metric_id = canonical
                        
                        # If unknown (not in registry after alias resolution)
                        if canonical not in METRIC_DEFINITIONS:
                            if hasattr(metric_result, 'missing_reason'):
                                metric_result.missing_reason = "unknown_metric_id"
                            unknown_count += 1
                        else:
                            validated_count += 1
        
        if unknown_count > 0:
            logger.warning(f"⚠️ VisualPass: {unknown_count} unknown metric_ids (marked)")
        
        logger.info(f"   └─ Metrics validated: {validated_count}, unknown: {unknown_count}")
        return result
