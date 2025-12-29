"""
VDG (Video Data Graph) v4.0 Pydantic Schemas

2-Pass Pipeline Protocol:
- Pass 1: Semantic (의미/구조/의도)
- Pass 2: Visual (시각/객체/구도)

v4.0.1 Patches Applied:
1. Metric ID 통일 (MetricRequest + metric_id 참조)
2. Unit/Range 일관성 (norm_-1_1 추가)
3. stability_score 정의 명확화 (score = 1 - normalized_std)
4. target_entity_id → target_hint_key
5. aggregation per metric (MetricRequest로 이동)
6. MetricResult.samples Union 타입
7. evidence_refs → List[str] 통일
8. MeasurementProvenance 추가
"""
from typing import List, Literal, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ====================
# 0. EVIDENCE GRAPH (공용)
# ====================

class EvidenceType(str, Enum):
    FRAME = "frame"
    CLIP = "clip"
    AUDIO_SEGMENT = "audio_segment"
    ASR_SPAN = "asr_span"
    OCR_SPAN = "ocr_span"
    COMMENT = "comment"
    METRIC = "metric"


class EvidenceItem(BaseModel):
    """증거 아이템 (공용 규격)"""
    evidence_id: str
    type: EvidenceType
    t_range: Optional[List[float]] = None  # [start, end]
    uri: Optional[str] = None
    sha256: Optional[str] = None
    summary: Optional[str] = None


class EvidenceLink(BaseModel):
    """증거 연결 (모든 산출물에 첨부)"""
    evidence_refs: List[str] = Field(default_factory=list)  # Patch #7: str only
    confidence: float = 0.8
    method: Literal["llm", "cv", "asr", "ocr", "hybrid"] = "hybrid"
    model_info: Optional[Dict[str, Any]] = None


# ====================
# 1. METRIC REGISTRY
# ====================

# Patch #2: unit 확장 (norm_-1_1 추가)
MetricUnit = Literal[
    "norm_0_1",    # 0~1 정규화
    "norm_-1_1",   # -1~1 정규화 (signed)
    "deg",         # 각도
    "ratio",       # 비율
    "bool",        # 불리언
    "enum",        # 열거형
    "px"           # 픽셀
]


class MetricDefinition(BaseModel):
    """측정 지표 정의 (미래에도 명확하게 유지)"""
    metric_id: str
    description: str
    unit: MetricUnit
    coordinate_frame: Literal[
        "raw_frame",
        "safe_area_adjusted",
        "cropped_primary_subject"
    ] = "raw_frame"
    aggregation_allowed: List[Literal[
        "mean", "median", "trimmed_mean", "mode", "p10_p90", "variance", "max", "min"
    ]] = Field(default_factory=lambda: ["mean", "median"])
    expected_range: Optional[List[float]] = None
    
    # Patch #3: score 정의 명확화
    score_formula: Optional[str] = None  # e.g. "1 - normalized_std"
    notes: Optional[str] = None


# ====================
# 2. METRIC REQUEST (Patch #1, #5)
# ====================

class MetricRequest(BaseModel):
    """측정 요청 (metric_id 중심 통일)"""
    metric_id: str  # 반드시 MetricRegistry에 존재
    aggregation: Optional[Literal[
        "mean", "median", "max", "min", "mode", "variance", "trimmed_mean"
    ]] = None
    selector: Optional[str] = None  # vector2면 "x"/"y"/"l2"/"abs_x"
    params: Dict[str, Any] = Field(default_factory=dict)


# ====================
# 3. MEASUREMENT PROVENANCE (Patch #8)
# ====================

class MeasurementProvenance(BaseModel):
    """측정 방법/모델 버전 (과거 데이터 재현 가능성)"""
    method: Literal["cv", "llm", "hybrid"]
    detector: Optional[str] = None  # "YOLO-World", "Grounding-DINO"
    detector_version: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    params_sha256: Optional[str] = None


# ====================
# 4. ENTITY HINTS
# ====================

class EntityHint(BaseModel):
    """2차 추적을 위한 주인공 힌트 (구조화)"""
    hint_key: str  # "main_speaker"
    entity_type: Literal["person", "product", "text", "hand", "other"]
    label: str  # human-readable "yellow shirt woman"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    candidates: List[str] = Field(default_factory=list)
    confidence: float = 0.7
    evidence_refs: List[str] = Field(default_factory=list)  # Patch #7


class EntityResolution(BaseModel):
    """2차에서 Entity 검증 결과"""
    hint_key: str
    resolved_entity_id: Optional[str] = None
    resolution_method: Literal["direct", "fallback_largest", "fallback_speaker", "failed"]
    confidence: float
    provenance: Optional[MeasurementProvenance] = None  # Patch #8


# ====================
# 5. ANALYSIS PLAN
# ====================

class SamplingPolicy(BaseModel):
    """샘플링 정책"""
    target_fps: float = 12.0
    min_samples: int = 8
    max_samples: int = 24
    frame_stride: Optional[int] = None


class AnalysisPoint(BaseModel):
    """2차에서 분석할 지점 (지령서)"""
    id: str
    t_center: float
    t_window: List[float]  # [start, end]
    priority: Literal["critical", "high", "medium", "low"]
    reason: Literal[
        "hook_punch", "hook_start", "hook_build", "hook_end",
        "scene_boundary", "sentiment_shift",
        "product_mention", "key_dialogue", "text_appear",
        "comment_mise_en_scene"
    ]
    source_ref: str
    
    # Patch #4: target_entity_id → target_hint_key
    target_hint_key: Optional[str] = None  # semantic.entity_hints key
    
    # Patch #1, #5: metrics_requested → List[MetricRequest]
    metrics_requested: List[MetricRequest] = Field(default_factory=list)
    
    # 씬 경계 처리
    window_policy: Literal["clamp", "split"] = "clamp"
    
    # 구체적 지시
    instruction: Optional[str] = None


class AnalysisPlan(BaseModel):
    """분석 계획 (예산/병합/클램프)"""
    plan_version: str = "1.0"
    max_points_total: int = 25
    budget_by_priority: Dict[str, int] = Field(default_factory=lambda: {
        "critical": 8, "high": 10, "medium": 7, "low": 0
    })
    merge_overlap_threshold: float = 0.6
    clamp_to_scene_boundaries: bool = True
    sampling: SamplingPolicy = Field(default_factory=SamplingPolicy)
    points: List[AnalysisPoint] = Field(default_factory=list)


# ====================
# 6. SEMANTIC PASS (1차)
# ====================

class Microbeat(BaseModel):
    """Hook 내 세부 비트"""
    t: float
    role: Literal["start", "build", "punch", "end"] = "start"
    cue: Literal["visual", "audio", "text", "action"] = "visual"
    note: str = ""


class HookGenome(BaseModel):
    """훅 분석"""
    start_sec: float = 0.0
    end_sec: float = 3.0
    pattern: str = "other"
    delivery: str = "visual_gag"
    strength: float = Field(0.5, ge=0.0, le=1.0)
    hook_summary: str = ""
    microbeats: List[Microbeat] = Field(default_factory=list)


class Scene(BaseModel):
    """씬 정보"""
    scene_id: str
    time_start: float
    time_end: float
    duration_sec: float
    narrative_role: str = ""
    summary: str = ""


class IntentLayer(BaseModel):
    """심리적 의도"""
    hook_trigger: str = "curiosity_gap"
    hook_trigger_reason: str = ""
    retention_strategy: str = ""
    dopamine_radar: Dict[str, int] = Field(default_factory=dict)


class MiseEnSceneSignal(BaseModel):
    """댓글 기반 미장센 신호"""
    element: Literal["outfit_color", "background", "lighting", "props", "makeup", "setting"]
    value: str
    sentiment: Literal["positive", "negative", "neutral"]
    source_comment: str
    likes: int
    evidence_refs: List[str] = Field(default_factory=list)  # Patch #7


class AudienceReaction(BaseModel):
    """시청자 반응 분석"""
    analysis: str = ""
    best_comments: List[Dict[str, Any]] = Field(default_factory=list)
    common_reactions: List[str] = Field(default_factory=list)
    overall_sentiment: str = "positive"
    viral_signal: str = ""
    mise_en_scene_signals: List[MiseEnSceneSignal] = Field(default_factory=list)


class CapsuleBrief(BaseModel):
    """실행 가이드"""
    hook_script: str = ""
    shotlist: List[Dict[str, Any]] = Field(default_factory=list)
    do_not: List[str] = Field(default_factory=list)


class SemanticPassProvenance(BaseModel):
    """1차 패스 출처 정보"""
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    run_at: Optional[str] = None


class SemanticPassResult(BaseModel):
    """1차 분석 결과: 텍스트/오디오/구조 중심"""
    scenes: List[Scene] = Field(default_factory=list)
    hook_genome: HookGenome = Field(default_factory=HookGenome)
    intent_layer: IntentLayer = Field(default_factory=IntentLayer)
    asr_transcript: Dict[str, Any] = Field(default_factory=dict)
    ocr_content: List[str] = Field(default_factory=list)
    audience_reaction: AudienceReaction = Field(default_factory=AudienceReaction)
    capsule_brief: CapsuleBrief = Field(default_factory=CapsuleBrief)
    commerce: Dict[str, Any] = Field(default_factory=dict)
    entity_hints: Dict[str, EntityHint] = Field(default_factory=dict)
    summary: str = ""
    provenance: SemanticPassProvenance = Field(default_factory=SemanticPassProvenance)  # Patch #8


# ====================
# 7. VISUAL PASS (2차)
# ====================

# Patch #6: Union 타입 샘플 값
SampleValue = Union[float, int, bool, str, List[float]]


class ScalarStats(BaseModel):
    """스칼라 측정 통계"""
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    p10: Optional[float] = None
    p90: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None


class Vector2Stats(BaseModel):
    """벡터2 측정 통계"""
    mean_x: Optional[float] = None
    mean_y: Optional[float] = None
    l2_norm_mean: Optional[float] = None
    std_x: Optional[float] = None
    std_y: Optional[float] = None


class EnumStats(BaseModel):
    """열거형 측정 통계"""
    mode: Optional[str] = None
    distribution: Dict[str, int] = Field(default_factory=dict)


# Patch #3: stability_score는 score로 저장 (1 - normalized_std)
class StabilityResult(BaseModel):
    """안정성 결과 (분산 기반)"""
    score: float  # 0~1, 높을수록 안정적
    raw_std: float
    normalized_std: float
    formula: str = "1 - normalized_std"


class MetricResult(BaseModel):
    """개별 측정 결과"""
    metric_id: str  # Patch #1: registry 참조
    value_type: Literal["scalar", "vector2", "ratio", "bool", "enum"]
    aggregated_value: Optional[SampleValue] = None
    
    # Patch #6: Union 타입 샘플
    samples: List[SampleValue] = Field(default_factory=list)
    sample_count: int = 0
    
    # 타입별 통계
    scalar_stats: Optional[ScalarStats] = None
    vector2_stats: Optional[Vector2Stats] = None
    enum_stats: Optional[EnumStats] = None
    stability: Optional[StabilityResult] = None
    
    missing_reason: Optional[str] = None
    confidence: float = 0.8
    
    # Patch #8: 측정 출처
    provenance: Optional[MeasurementProvenance] = None


class AnalysisPointResult(BaseModel):
    """지령 이행 결과"""
    ap_id: str
    
    # Patch #4: resolved entity ID 별도 필드
    resolved_entity_id: Optional[str] = None
    
    metrics: Dict[str, MetricResult] = Field(default_factory=dict)
    best_frame_sample: Optional[Dict[str, Any]] = None
    semantic_visual_alignment: float = Field(
        default=0.8,
        description="1차 의도와 시각적 강도의 일치도"
    )


class EntityTrack(BaseModel):
    """객체 추적"""
    track_id: str
    entity_id: str
    samples: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Optional[MeasurementProvenance] = None  # Patch #8


class TextGeometry(BaseModel):
    """텍스트 위치/기하학"""
    text: str
    t_window: Optional[List[float]] = None
    bbox_norm: Optional[List[float]] = None
    role: Optional[str] = None
    lang: Optional[str] = None


class VisualPassResult(BaseModel):
    """2차 분석 결과: 시각/객체/구도 중심"""
    entity_catalog: List[Dict[str, Any]] = Field(default_factory=list)
    entity_resolutions: Dict[str, EntityResolution] = Field(default_factory=dict)
    entity_tracks: List[EntityTrack] = Field(default_factory=list)
    text_geometries: List[TextGeometry] = Field(default_factory=list)
    analysis_results: Dict[str, AnalysisPointResult] = Field(default_factory=dict)


# ====================
# 8. MERGER
# ====================

class MergerQuality(BaseModel):
    """병합 품질 지표"""
    overall_alignment: float
    mismatch_flags: List[str] = Field(default_factory=list)
    data_quality_tier: Literal["gold", "silver", "bronze", "reject"]


class ContractCandidates(BaseModel):
    """Pack 컴파일을 위한 규칙 후보"""
    dna_invariants_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    mutation_slots_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    forbidden_mutations_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    weights_candidates: Dict[str, float] = Field(default_factory=dict)
    tolerances_candidates: Dict[str, float] = Field(default_factory=dict)


# ====================
# 9. VDG v4.0 FULL
# ====================

class VDGv4(BaseModel):
    """VDG (Video Data Graph) v4.0.1 - 패치 적용된 최종 스키마"""
    vdg_version: str = "4.0.1"
    
    # Identity
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    upload_date: Optional[str] = None
    
    # Media Spec
    media: Dict[str, Any] = Field(default_factory=dict)
    
    # Provenance
    provenance: Dict[str, Any] = Field(default_factory=dict)
    
    # Metric Registry
    metric_registry_version: str = "1.0"
    metric_definitions: Dict[str, MetricDefinition] = Field(default_factory=dict)
    
    # Evidence Graph (shared)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    
    # Pass 1: Semantic
    semantic: SemanticPassResult = Field(default_factory=SemanticPassResult)
    
    # Bridge: Analysis Plan
    analysis_plan: AnalysisPlan = Field(default_factory=AnalysisPlan)
    
    # Pass 2: Visual
    visual: VisualPassResult = Field(default_factory=VisualPassResult)
    
    # Merger Quality
    merger_quality: Optional[MergerQuality] = None
    
    # Contract Candidates (for Pack Compiler)
    contract_candidates: ContractCandidates = Field(default_factory=ContractCandidates)
    
    # Feature Vectors (for ML/Clustering)
    feature_store_version: str = "0.1"
    feature_vectors: Dict[str, Any] = Field(default_factory=dict)
    
    # v3.3 Compatibility
    legacy_flat_view: Optional[Dict[str, Any]] = None


# ====================
# 10. STANDARD METRICS (Patch #2, #3 반영)
# ====================

STANDARD_METRIC_DEFINITIONS = {
    "center_offset_xy": MetricDefinition(
        metric_id="center_offset_xy",
        description="주 피사체의 화면 중앙 대비 오프셋 (signed)",
        unit="norm_-1_1",  # Patch #2
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["median", "mean"],
        expected_range=[-1.0, 1.0]
    ),
    "center_offset_x": MetricDefinition(
        metric_id="center_offset_x",
        description="X축 중앙 대비 오프셋",
        unit="norm_-1_1",
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["median", "mean"],
        expected_range=[-1.0, 1.0]
    ),
    "center_offset_y": MetricDefinition(
        metric_id="center_offset_y",
        description="Y축 중앙 대비 오프셋",
        unit="norm_-1_1",
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["median", "mean"],
        expected_range=[-1.0, 1.0]
    ),
    "headroom_ratio": MetricDefinition(
        metric_id="headroom_ratio",
        description="피사체 위 여백 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean", "median"],
        expected_range=[0.0, 1.0]
    ),
    "subject_area_ratio": MetricDefinition(
        metric_id="subject_area_ratio",
        description="피사체가 화면에서 차지하는 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean", "median"],
        expected_range=[0.0, 1.0]
    ),
    "stability_score": MetricDefinition(
        metric_id="stability_score",
        description="구간 내 측정값 안정성 (1.0=부동)",
        unit="norm_0_1",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean"],  # Patch #3: score 자체는 mean
        expected_range=[0.0, 1.0],
        score_formula="1 - (std / expected_range_span)"  # Patch #3
    ),
    "visibility_ratio": MetricDefinition(
        metric_id="visibility_ratio",
        description="객체 가시성 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["max", "mean"],
        expected_range=[0.0, 1.0]
    ),
    "dominant_color": MetricDefinition(
        metric_id="dominant_color",
        description="주요 색상 (HEX or name)",
        unit="enum",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mode"]
    ),
    "brightness_ratio": MetricDefinition(
        metric_id="brightness_ratio",
        description="평균 밝기 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean"],
        expected_range=[0.0, 1.0]
    ),
    "text_safe_area_clear": MetricDefinition(
        metric_id="text_safe_area_clear",
        description="텍스트 안전영역 침범 여부",
        unit="bool",
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["mode"]
    )
}
