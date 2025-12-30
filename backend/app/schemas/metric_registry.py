"""
Metric Registry (Single Source of Record)

H-1 Hardening: All metric definitions in ONE authoritative location.
Planner/VisualPass/DirectorCompiler MUST import from here.

Philosophy:
- "AI가 발전해도 metric 정의는 고정된다"
- metric_id = domain.name.v1 format
- Future: CV 모델 바꿔도 동일 계약 유지
"""
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


# ====================
# METRIC DEFINITIONS (Authoritative)
# ====================

class MetricDefinition(BaseModel):
    """Authoritative metric definition."""
    metric_id: str
    description: str
    description_ko: str
    unit: Literal["norm_0_1", "norm_-1_1", "deg", "ratio", "bool", "enum", "px", "sec"]
    domain: str
    aggregation_default: str = "median"
    expected_range: Optional[List[float]] = None


# Authoritative Registry (Single SoR)
METRIC_DEFINITIONS: Dict[str, MetricDefinition] = {
    # ===================
    # COMPOSITION (cmp)
    # ===================
    "cmp.center_offset_xy.v1": MetricDefinition(
        metric_id="cmp.center_offset_xy.v1",
        description="Distance of main subject from center (0=center, 1=edge)",
        description_ko="주피사체 중앙 이탈도",
        unit="norm_0_1",
        domain="composition",
        expected_range=[0.0, 1.0]
    ),
    "cmp.stability_score.v1": MetricDefinition(
        metric_id="cmp.stability_score.v1",
        description="Camera/subject stability (0=shaky, 1=stable)",
        description_ko="안정성 점수",
        unit="norm_0_1",
        domain="composition",
        expected_range=[0.0, 1.0]
    ),
    "cmp.composition_grid.v1": MetricDefinition(
        metric_id="cmp.composition_grid.v1",
        description="Rule of thirds grid alignment",
        description_ko="구도 그리드 준수",
        unit="enum",
        domain="composition"
    ),
    
    # ===================
    # LIGHTING (lit)
    # ===================
    "lit.brightness_ratio.v1": MetricDefinition(
        metric_id="lit.brightness_ratio.v1",
        description="Subject brightness relative to background",
        description_ko="밝기 비율",
        unit="ratio",
        domain="lighting",
        expected_range=[0.5, 2.0]
    ),
    "lit.contrast.v1": MetricDefinition(
        metric_id="lit.contrast.v1",
        description="Contrast level (0=flat, 1=high contrast)",
        description_ko="대비",
        unit="norm_0_1",
        domain="lighting"
    ),
    
    # ===================
    # ENTITY (ent)
    # ===================
    "ent.face_size_ratio.v1": MetricDefinition(
        metric_id="ent.face_size_ratio.v1",
        description="Face size relative to frame height",
        description_ko="얼굴 크기 비율",
        unit="ratio",
        domain="entity",
        expected_range=[0.05, 0.5]
    ),
    "ent.expression_arouse.v1": MetricDefinition(
        metric_id="ent.expression_arouse.v1",
        description="Expression arousal/energy level",
        description_ko="표정 각성도",
        unit="norm_0_1",
        domain="entity"
    ),
    "ent.eye_contact.v1": MetricDefinition(
        metric_id="ent.eye_contact.v1",
        description="Looking at camera",
        description_ko="아이컨택 여부",
        unit="bool",
        domain="entity"
    ),
    
    # ===================
    # VISUAL (vis)
    # ===================
    "vis.dominant_color.v1": MetricDefinition(
        metric_id="vis.dominant_color.v1",
        description="Dominant color in frame",
        description_ko="지배 색상",
        unit="enum",
        domain="visual"
    ),
    "vis.motion_intensity.v1": MetricDefinition(
        metric_id="vis.motion_intensity.v1",
        description="Motion/movement intensity",
        description_ko="움직임 강도",
        unit="norm_0_1",
        domain="visual"
    ),
    
    # ===================
    # TIMING (timing)
    # ===================
    "timing.hook_punch.v1": MetricDefinition(
        metric_id="timing.hook_punch.v1",
        description="Time to hook punch moment",
        description_ko="훅 펀치 타이밍",
        unit="sec",
        domain="timing",
        expected_range=[0.0, 3.0]
    ),
    
    # ===================
    # MISE-EN-SCENE (mise)
    # ===================
    "mise.lighting.v1": MetricDefinition(
        metric_id="mise.lighting.v1",
        description="Lighting style category",
        description_ko="조명 스타일",
        unit="enum",
        domain="mise_en_scene"
    ),
    "mise.props.v1": MetricDefinition(
        metric_id="mise.props.v1",
        description="Props/object category",
        description_ko="소품 유형",
        unit="enum",
        domain="mise_en_scene"
    ),
    "mise.wardrobe.v1": MetricDefinition(
        metric_id="mise.wardrobe.v1",
        description="Wardrobe/outfit category",
        description_ko="의상 유형",
        unit="enum",
        domain="mise_en_scene"
    ),
    "mise.background.v1": MetricDefinition(
        metric_id="mise.background.v1",
        description="Background/setting category",
        description_ko="배경 유형",
        unit="enum",
        domain="mise_en_scene"
    ),
}


# ====================
# ALIASES (Deprecated → Canonical)
# ====================

METRIC_ALIASES: Dict[str, str] = {
    "lit.brightness_lux.v1": "lit.brightness_ratio.v1",  # lux → ratio (no sensor data)
    "cmp.rule_of_thirds.v1": "cmp.composition_grid.v1",
    "cmp.center_offset.v1": "cmp.center_offset_xy.v1",  # Short name → full name
}


# ====================
# VALIDATION FUNCTIONS
# ====================

def validate_metric_id(metric_id: str) -> str:
    """
    Validate and normalize metric_id against registry.
    
    Returns canonical metric_id or logs warning for unknown.
    """
    # Check aliases first
    if metric_id in METRIC_ALIASES:
        canonical = METRIC_ALIASES[metric_id]
        logger.debug(f"Metric alias: {metric_id} → {canonical}")
        return canonical
    
    # Check registry
    if metric_id in METRIC_DEFINITIONS:
        return metric_id
    
    # Unknown metric - log warning and return as-is (soft fail)
    logger.warning(f"⚠️ Unknown metric_id: {metric_id} (not in registry)")
    return metric_id


def get_metric_definition(metric_id: str) -> Optional[MetricDefinition]:
    """Get metric definition by ID (resolves aliases)."""
    canonical = validate_metric_id(metric_id)
    return METRIC_DEFINITIONS.get(canonical)


def get_all_metric_ids() -> List[str]:
    """Get all valid metric IDs."""
    return list(METRIC_DEFINITIONS.keys())


def to_prompt_json(metric_ids: List[str] = None) -> str:
    """
    Generate JSON for prompt injection (for LLM to understand metrics).
    
    Args:
        metric_ids: Subset of metrics to include (None = all)
        
    Returns:
        JSON string for prompt
    """
    import json
    
    metrics_to_include = metric_ids or list(METRIC_DEFINITIONS.keys())
    
    result = {}
    for mid in metrics_to_include:
        canonical = validate_metric_id(mid)
        defn = METRIC_DEFINITIONS.get(canonical)
        if defn:
            result[canonical] = {
                "description": defn.description,
                "unit": defn.unit,
                "expected_range": defn.expected_range
            }
    
    return json.dumps(result, indent=2)


# ====================
# DOMAIN HELPERS
# ====================

def get_metrics_by_domain(domain: str) -> List[str]:
    """Get all metric IDs for a domain."""
    return [
        mid for mid, defn in METRIC_DEFINITIONS.items()
        if defn.domain == domain
    ]


# ====================
# PRESETS FOR PLANNER
# ====================

METRIC_PRESETS = {
    "hook": ["cmp.center_offset_xy.v1", "cmp.stability_score.v1", "lit.brightness_ratio.v1"],
    "scene_boundary": ["cmp.stability_score.v1", "cmp.composition_grid.v1"],
    "entity": ["ent.face_size_ratio.v1", "ent.expression_arouse.v1", "cmp.center_offset_xy.v1"],
    "mise_en_scene": ["cmp.composition_grid.v1", "vis.dominant_color.v1", "lit.brightness_ratio.v1"],
    "default": ["cmp.composition_grid.v1", "lit.brightness_ratio.v1"],
}


def get_preset_metrics(preset_name: str) -> List[str]:
    """Get metric IDs for a named preset."""
    return METRIC_PRESETS.get(preset_name, METRIC_PRESETS["default"])
