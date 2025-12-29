"""
Visual Pass (VDG v4.0 Pass 2)

P0-2: Uses Metric Registry for authoritative measurement contracts
P0-4: Uses robust_generate_content for retry/fallback/JSON repair
"""
from typing import Dict, Any, List
import json
import logging
from datetime import datetime
import google.generativeai as genai
from google.generativeai import types
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
    - Metric Registry injected into prompt
    - Measurement contracts are authoritative
    
    P0-4 Hardening:
    - Retry with exponential backoff
    - Async fallback to sync
    - JSON repair loop
    """
    
    def __init__(self, client=None):
        self.client = client
        if not self.client and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use config or default to 1.5 Pro
        self.model_name = getattr(settings, "GEMINI_MODEL_PRO", "gemini-1.5-pro-latest")

    async def analyze(
        self,
        video_bytes: bytes,
        plan: AnalysisPlan,
        entity_hints: Dict[str, EntityHint],
        semantic_summary: str
    ) -> VisualPassResult:
        """
        Execute visual analysis pass based on the plan.
        
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
        
        # 3. Prepare Video Part
        video_part = types.Part(
            inline_data=types.Blob(
                data=video_bytes,
                mime_type="video/mp4"
            )
        )
        
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
        
        logger.info(f"🎥 Starting Visual Pass (Model: {self.model_name}) with {len(plan.points)} points")
        logger.info(f"   └─ Metrics requested: {len(requested_metrics)}")
        
        # P0-4: Use robust generation with retry/fallback/repair
        result = await robust_generate_content(
            model=model,
            contents=[video_part, user_prompt],
            result_schema=VisualPassResult,
            max_retries=3,
            initial_backoff=2.0  # Visual pass is heavier, longer initial backoff
        )
        
        # 5. Add provenance
        end_time = datetime.utcnow()
        elapsed_sec = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Visual Pass completed in {elapsed_sec:.1f}s")
        logger.info(f"   └─ Entity Resolutions: {len(result.entity_resolutions)}")
        logger.info(f"   └─ Analysis Results: {len(result.analysis_results)}")
        
        return result
