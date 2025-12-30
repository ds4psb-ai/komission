"""
VDG (Video Data Graph) v4.0 Pydantic Schemas

2-Pass Pipeline Protocol:
- Pass 1: Semantic (의미/구조/의도)
- Pass 2: Visual (시각/객체/구도)

v4.0.2 Protocol Freeze Patches:
1. Metric ID versioning (domain.name.v1)
2. safe_area definition in media
5. EntityCandidate structured type
6. entity_fallback_policy in AnalysisPlan
7. OCRContentItem with first_appear_t
8. EvidenceItem.t for single frame
9. bbox_norm format documented
10. mise_en_scene_signals moved to semantic root
"""
from typing import List, Literal, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ====================
# 0. EVIDENCE GRAPH (Patch #10: t for single frame)
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
    t: Optional[float] = None  # Patch #10: 단일 프레임용 (type=FRAME)
    t_range: Optional[List[float]] = None  # CLIP/SEGMENT용
    uri: Optional[str] = None
    sha256: Optional[str] = None
    summary: Optional[str] = None


class EvidenceLink(BaseModel):
    """증거 연결 (모든 산출물에 첨부)"""
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: float = 0.8
    method: Literal["llm", "cv", "asr", "ocr", "hybrid"] = "hybrid"
    model_info: Optional[Dict[str, Any]] = None


# ====================
# 1. METRIC REGISTRY (Patch #1: domain.name.v1 versioning)
# ====================

MetricUnit = Literal[
    "norm_0_1",
    "norm_-1_1",
    "deg",
    "ratio",
    "bool",
    "enum",
    "px"
]


class MetricDefinition(BaseModel):
    """측정 지표 정의 (미래에도 명확하게 유지)"""
    metric_id: str  # Patch #1: domain.name.v1 형식 (e.g. cmp.center_offset_xy.v1)
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
    score_formula: Optional[str] = None
    notes: Optional[str] = None


# ====================
# 2. METRIC REQUEST
# ====================

class MetricRequest(BaseModel):
    """측정 요청 (metric_id 중심 통일)"""
    metric_id: str  # 반드시 domain.name.v1 형식
    aggregation: Optional[Literal[
        "mean", "median", "max", "min", "mode", "variance", "trimmed_mean"
    ]] = None
    selector: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


# ====================
# 3. MEASUREMENT PROVENANCE
# ====================

class MeasurementProvenance(BaseModel):
    """측정 방법/모델 버전"""
    method: Literal["cv", "llm", "hybrid"]
    detector: Optional[str] = None
    detector_version: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    params_sha256: Optional[str] = None


# ====================
# 4. ENTITY HINTS (Patch #7: EntityCandidate structured)
# ====================

class EntityCandidate(BaseModel):
    """Entity 후보 (구조화)"""
    label: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5


class EntityHint(BaseModel):
    """2차 추적을 위한 주인공 힌트"""
    hint_key: str
    entity_type: Literal["person", "product", "text", "hand", "other"]
    label: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    candidates: List[EntityCandidate] = Field(default_factory=list)  # Patch #7
    confidence: float = 0.7
    evidence_refs: List[str] = Field(default_factory=list)


class EntityResolution(BaseModel):
    """2차에서 Entity 검증 결과"""
    hint_key: str
    resolved_entity_id: Optional[str] = None
    resolution_method: Literal["direct", "fallback_largest", "fallback_speaker", "failed"]
    confidence: float
    provenance: Optional[MeasurementProvenance] = None


# ====================
# 5. SAFE AREA DEFINITION (Patch #5)
# ====================

class SafeAreaDefinition(BaseModel):
    """플랫폼별 Safe Area 정의"""
    platform: str  # "tiktok", "youtube_shorts", "instagram_reels"
    mask_norm: List[float]  # [x, y, width, height] normalized
    definition_version: str  # "tiktok_v1"
    notes: Optional[str] = None


# Patch #11: bbox_norm format 규약
BBOX_FORMAT = "xywh"  # [x, y, width, height] top-left + size, normalized 0~1


# ====================
# 6. ANALYSIS PLAN (Patch #8: entity_fallback_policy)
# ====================

class SamplingPolicy(BaseModel):
    """샘플링 정책"""
    target_fps: float = 10.0
    min_samples: int = 8
    max_samples: int = 24
    frame_stride: Optional[int] = None


class AnalysisPoint(BaseModel):
    """2차에서 분석할 지점"""
    id: str
    t_center: float
    t_window: List[float]
    priority: Literal["critical", "high", "medium", "low"]
    reason: Literal[
        "hook_punch", "hook_start", "hook_build", "hook_end",
        "scene_boundary", "sentiment_shift",
        "product_mention", "key_dialogue", "text_appear",
        "comment_mise_en_scene", "comment_evidence"  # Patch #13: 댓글 증거 기반
    ]
    source_ref: str
    target_hint_key: Optional[str] = None
    metrics_requested: List[MetricRequest] = Field(default_factory=list)
    window_policy: Literal["clamp", "split"] = "clamp"
    instruction: Optional[str] = None
    
    # Patch #14: CV-First, LLM-Auditor 지원
    measurement_method: Literal["llm", "cv_geometry", "cv_tracking", "hybrid"] = "llm"


class AnalysisPlan(BaseModel):
    """분석 계획"""
    plan_version: str = "1.0"
    max_points_total: int = 25
    budget_by_priority: Dict[str, int] = Field(default_factory=lambda: {
        "critical": 8, "high": 10, "medium": 7, "low": 0
    })
    merge_overlap_threshold: float = 0.6
    clamp_to_scene_boundaries: bool = True
    sampling: SamplingPolicy = Field(default_factory=SamplingPolicy)
    
    # Patch #8: entity fallback policy
    entity_fallback_policy: List[Literal[
        "largest_face_bbox",
        "most_speech_overlap",
        "center_screen_priority",
        "most_motion"
    ]] = Field(default_factory=lambda: ["largest_face_bbox", "center_screen_priority"])
    
    points: List[AnalysisPoint] = Field(default_factory=list)


# ====================
# 7. SEMANTIC PASS (Patch #9, #12)
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


# Patch #9: OCRContentItem 구조화
class OCRContentItem(BaseModel):
    """1차 OCR 내용 (시간 정보 포함)"""
    text: str
    first_appear_t: Optional[float] = None
    lang: Optional[str] = None
    confidence: Optional[float] = None
    evidence_refs: List[str] = Field(default_factory=list)


# Patch #12: MiseEnSceneSignal을 semantic root로 이동
class MiseEnSceneSignal(BaseModel):
    """댓글 기반 미장센 신호 (semantic root에 위치)"""
    element: Literal["outfit_color", "background", "lighting", "props", "makeup", "setting"]
    value: str
    sentiment: Literal["positive", "negative", "neutral"]
    source_comment: str
    likes: int
    evidence_refs: List[str] = Field(default_factory=list)


class AudienceReaction(BaseModel):
    """시청자 반응 분석 (댓글/반응만)"""
    analysis: str = ""
    best_comments: List[Dict[str, Any]] = Field(default_factory=list)
    common_reactions: List[str] = Field(default_factory=list)
    overall_sentiment: str = "positive"
    viral_signal: str = ""
    # Patch #12: mise_en_scene_signals 제거 (semantic root로 이동)


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
    """1차 분석 결과"""
    scenes: List[Scene] = Field(default_factory=list)
    hook_genome: HookGenome = Field(default_factory=HookGenome)
    intent_layer: IntentLayer = Field(default_factory=IntentLayer)
    asr_transcript: Dict[str, Any] = Field(default_factory=dict)
    ocr_content: List[OCRContentItem] = Field(default_factory=list)  # Patch #9
    audience_reaction: AudienceReaction = Field(default_factory=AudienceReaction)
    capsule_brief: CapsuleBrief = Field(default_factory=CapsuleBrief)
    commerce: Dict[str, Any] = Field(default_factory=dict)
    entity_hints: Dict[str, EntityHint] = Field(default_factory=dict)
    # H5 SSoT: mise_en_scene_signals is CANONICAL here (comment-based visual signals)
    mise_en_scene_signals: List[MiseEnSceneSignal] = Field(default_factory=list)
    summary: str = ""
    provenance: SemanticPassProvenance = Field(default_factory=SemanticPassProvenance)


# ====================
# 8. VISUAL PASS
# ====================

SampleValue = Union[float, int, bool, str, List[float]]


class MetricSample(BaseModel):
    """개별 측정 샘플"""
    t: float
    value: SampleValue
    frame_ref: Optional[str] = None
    confidence: Optional[float] = None


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
    """벡터2 측정 통계 (성분별)"""
    x: Optional[ScalarStats] = None
    y: Optional[ScalarStats] = None
    l2_norm: Optional[ScalarStats] = None


class EnumStats(BaseModel):
    """열거형 측정 통계"""
    mode: Optional[str] = None
    distribution: Dict[str, int] = Field(default_factory=dict)


class StabilityResult(BaseModel):
    """안정성 결과"""
    score: float
    raw_std: float
    normalized_std: float
    formula: str = "1 - normalized_std"


class MetricResult(BaseModel):
    """개별 측정 결과"""
    metric_id: str  # domain.name.v1 형식
    value_type: Literal["scalar", "vector2", "ratio", "bool", "enum"]
    aggregated_value: Optional[SampleValue] = None
    
    # 개선된 샘플 저장
    samples: List[MetricSample] = Field(default_factory=list)
    sample_count: int = 0
    
    # 타입별 통계
    scalar_stats: Optional[ScalarStats] = None
    vector2_stats: Optional[Vector2Stats] = None
    enum_stats: Optional[EnumStats] = None
    stability: Optional[StabilityResult] = None
    
    missing_reason: Optional[str] = None
    confidence: float = 0.8
    provenance: Optional[MeasurementProvenance] = None


class AnalysisPointResult(BaseModel):
    """지령 이행 결과"""
    ap_id: str
    resolved_entity_id: Optional[str] = None
    metrics: Dict[str, MetricResult] = Field(default_factory=dict)
    best_frame_sample: Optional[Dict[str, Any]] = None
    semantic_visual_alignment: float = 0.8
    
    # Patch #14: LLM Auditor 결과
    auditor_verdict: Literal["pass", "warn", "fail"] = "pass"
    audit_reason: Optional[str] = None
    
    # Patch #15: 댓글 증거 연결
    comment_evidence_refs: List[str] = Field(default_factory=list)


class EntityTrack(BaseModel):
    """객체 추적"""
    track_id: str
    entity_id: str
    samples: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Optional[MeasurementProvenance] = None


class TextGeometry(BaseModel):
    """텍스트 위치/기하학"""
    text: str
    t_window: Optional[List[float]] = None
    bbox_norm: Optional[List[float]] = None  # Patch #11: [x, y, w, h] format
    bbox_format: str = "xywh"  # Patch #11: 명시적 규약
    role: Optional[str] = None
    lang: Optional[str] = None


class VisualPassResult(BaseModel):
    """2차 분석 결과"""
    entity_catalog: List[Dict[str, Any]] = Field(default_factory=list)
    entity_resolutions: Dict[str, EntityResolution] = Field(default_factory=dict)
    entity_tracks: List[EntityTrack] = Field(default_factory=list)
    text_geometries: List[TextGeometry] = Field(default_factory=list)
    analysis_results: Dict[str, AnalysisPointResult] = Field(default_factory=dict)


# ====================
# 9. MERGER
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
# 10. VDG v4.0 FULL (Patch #5: safe_area in media, Patch #12: mise_en_scene_signals at root)
# ====================

class MediaSpec(BaseModel):
    """미디어 스펙 (Patch #5: safe_area 포함)"""
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    aspect_ratio: Optional[str] = None
    orientation: Optional[Literal["portrait", "landscape", "square"]] = None
    safe_area: Optional[SafeAreaDefinition] = None  # Patch #5
    bbox_format: str = "xywh"  # Patch #11


class VDGv4(BaseModel):
    """VDG (Video Data Graph) v4.0.2 - Protocol Freeze 완료"""
    vdg_version: str = "4.0.2"
    
    # Identity
    content_id: str
    platform: str = "youtube"
    title: str = ""
    duration_sec: float = 0.0
    upload_date: Optional[str] = None
    
    # Media Spec (Patch #5)
    media: MediaSpec = Field(default_factory=MediaSpec)
    
    # Provenance
    provenance: Dict[str, Any] = Field(default_factory=dict)
    
    # Metric Registry
    metric_registry_version: str = "1.0"
    metric_definitions: Dict[str, MetricDefinition] = Field(default_factory=dict)
    
    # Evidence Graph
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    
    # Pass 1: Semantic
    semantic: SemanticPassResult = Field(default_factory=SemanticPassResult)
    
    # Patch #12: Mise-en-Scene Signals at root (separate layer)
    mise_en_scene_signals: List[MiseEnSceneSignal] = Field(default_factory=list)
    
    # Bridge: Analysis Plan
    analysis_plan: AnalysisPlan = Field(default_factory=AnalysisPlan)
    
    # Pass 2: Visual
    visual: VisualPassResult = Field(default_factory=VisualPassResult)
    
    # Merger Quality
    merger_quality: Optional[MergerQuality] = None
    
    # Contract Candidates
    contract_candidates: ContractCandidates = Field(default_factory=ContractCandidates)
    
    # Flywheel: NotebookLM Distill Runs (Phase 3)
    distill_runs: List["DistillRun"] = Field(default_factory=list)
    
    # Feature Vectors
    feature_store_version: str = "0.1"
    feature_vectors: Dict[str, Any] = Field(default_factory=dict)
    
    # v3.3 Compatibility
    legacy_flat_view: Optional[Dict[str, Any]] = None


# ====================
# NOTEBOOKLM DISTILL (Flywheel Phase 3)
# ====================

class DistillRun(BaseModel):
    """
    NotebookLM Distill Run record.
    
    Stores results from parent-kids cluster distillation.
    Enables "NotebookLM-integrated" pipeline when distill job runs.
    
    Philosophy:
    - 지금: NotebookLM-ready (스키마 준비)
    - 다음: NotebookLM-integrated (잡 자동화)
    """
    distill_id: str  # Unique run ID
    cluster_id: str  # Parent-kids cluster
    source_refs: List[str] = Field(default_factory=list)  # VDG IDs
    prompt_version: str = "v1"
    run_at: Optional[str] = None
    
    # Output candidates
    dna_invariants_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    mutation_slots_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    forbidden_mutations_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    weights_candidates: Dict[str, float] = Field(default_factory=dict)
    
    # Provenance
    evidence_refs: List[str] = Field(default_factory=list)
    model_id: Optional[str] = None


# Forward reference resolution
VDGv4.model_rebuild()


# ====================
# 11. STANDARD METRICS (Patch #1: domain.name.v1 형식)
# ====================

STANDARD_METRIC_DEFINITIONS = {
    "cmp.center_offset_xy.v1": MetricDefinition(
        metric_id="cmp.center_offset_xy.v1",
        description="주 피사체의 화면 중앙 대비 오프셋 (signed vector2)",
        unit="norm_-1_1",
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["median", "mean"],
        expected_range=[-1.0, 1.0]
    ),
    "cmp.center_offset_x.v1": MetricDefinition(
        metric_id="cmp.center_offset_x.v1",
        description="X축 중앙 대비 오프셋",
        unit="norm_-1_1",
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["median", "mean"],
        expected_range=[-1.0, 1.0]
    ),
    "cmp.center_offset_y.v1": MetricDefinition(
        metric_id="cmp.center_offset_y.v1",
        description="Y축 중앙 대비 오프셋",
        unit="norm_-1_1",
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["median", "mean"],
        expected_range=[-1.0, 1.0]
    ),
    "cmp.headroom_ratio.v1": MetricDefinition(
        metric_id="cmp.headroom_ratio.v1",
        description="피사체 위 여백 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean", "median"],
        expected_range=[0.0, 1.0]
    ),
    "cmp.subject_area_ratio.v1": MetricDefinition(
        metric_id="cmp.subject_area_ratio.v1",
        description="피사체가 화면에서 차지하는 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean", "median"],
        expected_range=[0.0, 1.0]
    ),
    "cmp.stability_score.v1": MetricDefinition(
        metric_id="cmp.stability_score.v1",
        description="구간 내 측정값 안정성 (1.0=부동)",
        unit="norm_0_1",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean"],
        expected_range=[0.0, 1.0],
        score_formula="1 - (std / expected_range_span)"
    ),
    "vis.visibility_ratio.v1": MetricDefinition(
        metric_id="vis.visibility_ratio.v1",
        description="객체 가시성 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["max", "mean"],
        expected_range=[0.0, 1.0]
    ),
    "vis.dominant_color.v1": MetricDefinition(
        metric_id="vis.dominant_color.v1",
        description="주요 색상 (HEX or name)",
        unit="enum",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mode"]
    ),
    "vis.brightness_ratio.v1": MetricDefinition(
        metric_id="vis.brightness_ratio.v1",
        description="평균 밝기 비율",
        unit="ratio",
        coordinate_frame="raw_frame",
        aggregation_allowed=["mean"],
        expected_range=[0.0, 1.0]
    ),
    "txt.text_safe_area_clear.v1": MetricDefinition(
        metric_id="txt.text_safe_area_clear.v1",
        description="텍스트 안전영역 침범 여부",
        unit="bool",
        coordinate_frame="safe_area_adjusted",
        aggregation_allowed=["mode"]
    )
}


# ====================
# 12. PLATFORM SAFE AREAS (Patch #5)
# ====================

PLATFORM_SAFE_AREAS = {
    "tiktok": SafeAreaDefinition(
        platform="tiktok",
        mask_norm=[0.0, 0.08, 1.0, 0.84],  # top 8%, bottom 8% excluded
        definition_version="tiktok_v1",
        notes="Excludes top status bar and bottom UI controls"
    ),
    "youtube_shorts": SafeAreaDefinition(
        platform="youtube_shorts",
        mask_norm=[0.0, 0.05, 1.0, 0.90],
        definition_version="youtube_shorts_v1",
        notes="Excludes top bar and bottom subscribe button area"
    ),
    "instagram_reels": SafeAreaDefinition(
        platform="instagram_reels",
        mask_norm=[0.0, 0.06, 1.0, 0.88],
        definition_version="instagram_reels_v1",
        notes="Excludes top bar and bottom action buttons"
    )
}
