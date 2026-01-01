"""
VDG Pipeline Package - Video Data Graph Analysis

Usage:
    from app.services.vdg_pipeline import GeminiPipeline, gemini_pipeline
    
    # Analyze video (v5 unified pipeline)
    vdg = await gemini_pipeline.analyze_video_v4(video_url, node_id, comments)
    
    # Legacy v3 analysis
    vdg = await gemini_pipeline.analyze_video(video_url, node_id, comments)
"""
from .analyzer import GeminiPipeline, gemini_pipeline
from .constants import VDG_PROMPT
from .prompt_builder import get_analysis_depth_hints, build_enhanced_prompt
from .converter import convert_unified_to_vdg_v4
from .sanitizer import sanitize_vdg_payload, populate_legacy_fields

__all__ = [
    # Main exports
    "GeminiPipeline",
    "gemini_pipeline",
    
    # Constants
    "VDG_PROMPT",
    
    # Functions
    "get_analysis_depth_hints",
    "build_enhanced_prompt",
    "convert_unified_to_vdg_v4",
    "sanitize_vdg_payload",
    "populate_legacy_fields",
]
