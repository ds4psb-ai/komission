"""
Backward Compatibility Wrapper for VDG Pipeline

All new code should import from:
    from app.services.vdg_pipeline import GeminiPipeline, gemini_pipeline

This file is kept for backward compatibility with existing imports.
"""
# Re-export everything from new package
from app.services.vdg_pipeline import (
    GeminiPipeline,
    gemini_pipeline,
    VDG_PROMPT,
    get_analysis_depth_hints,
    build_enhanced_prompt,
    convert_unified_to_vdg_v4,
    sanitize_vdg_payload,
    populate_legacy_fields,
)

# Backward compatibility aliases (underscore prefix versions)
_get_analysis_depth_hints = get_analysis_depth_hints
_build_enhanced_prompt = build_enhanced_prompt
