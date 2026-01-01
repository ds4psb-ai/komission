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
from pydantic import BaseModel, Field, field_validator
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

# ====================
# 1.5 AI VIDEO TREND ANALYSIS (2026 Future-Proof)
# ====================

class SceneTransitionType(str, Enum):
    """컷 전환 유형"""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    ZOOM = "zoom"
    WHIP_PAN = "whip_pan"
    MATCH_CUT = "match_cut"
    JUMP_CUT = "jump_cut"


class SceneTransition(BaseModel):
    """컷 전환 분석 - AI 영상 퀄리티 핵심 지표 (Sora 2 / Veo 3 대비)"""
    from_scene_idx: int = Field(description="전환 전 씬 인덱스")
    to_scene_idx: int = Field(description="전환 후 씬 인덱스")
    t_transition: float = Field(description="전환 시점 (초)")
    transition_type: SceneTransitionType = Field(default=SceneTransitionType.CUT)
    continuity_score: float = Field(ge=0, le=1, description="캐릭터/배경 일관성 0-1")
    rhythm_match: bool = Field(default=True, description="리듬 연결 자연스러움")
    transition_quality: Literal["seamless", "acceptable", "jarring"] = "acceptable"


class CameraMovementType(str, Enum):
    """카메라 무빙 유형"""
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    DOLLY = "dolly"
    TRUCK = "truck"
    ZOOM = "zoom"
    HANDHELD = "handheld"
    DRONE = "drone"
    ORBIT = "orbit"
    WHIP_PAN = "whip_pan"


class CameraMetadata(BaseModel):
    """카메라 무빙 분석 - 3D 재구성 대비 (Gaussian Splatting)"""
    scene_id: str = Field(description="씬 ID")
    movement_type: CameraMovementType = Field(default=CameraMovementType.STATIC)
    movement_intensity: Literal["subtle", "moderate", "dynamic"] = "moderate"
    estimated_fov: Optional[float] = Field(default=None, description="추정 화각 (도)")
    spatial_consistency: float = Field(ge=0, le=1, default=0.8, description="3D 재구성 적합도")
    depth_variation: Literal["flat", "shallow", "deep"] = "shallow"
    steady_score: float = Field(ge=0, le=1, default=0.8, description="안정성 (0=흔들림, 1=완벽)")


class MultiShotAnalysis(BaseModel):
    """멀티샷 일관성 분석 - AI 영상 퀄리티 핵심 (Sora 2 Multi-Shot Consistency)"""
    character_persistence: float = Field(ge=0, le=1, description="캐릭터 동일성 0-1")
    location_consistency: float = Field(ge=0, le=1, description="장소 일관성 0-1")
    prop_tracking: float = Field(ge=0, le=1, description="소품 추적 일관성 0-1")
    lighting_consistency: float = Field(ge=0, le=1, description="조명 일관성 0-1")
    color_grading_consistency: float = Field(ge=0, le=1, description="색보정 일관성 0-1")
    overall_coherence: float = Field(ge=0, le=1, description="전체 스토리 흐름 0-1")
    ai_generation_likelihood: float = Field(ge=0, le=1, default=0.0, description="AI 생성 영상일 확률")
    notes: Optional[str] = Field(default=None, description="일관성 분석 메모")




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
    
    # 2026 AI Video Trend Analysis (Future-Proof)
    scene_transitions: List[SceneTransition] = Field(
        default_factory=list,
        description="씬 전환 분석 (Sora 2 / Veo 3 멀티샷 대비)"
    )
    camera_metadata: List[CameraMetadata] = Field(
        default_factory=list,
        description="카메라 무빙 분석 (Gaussian Splatting 3D 변환 대비)"
    )
    multi_shot_analysis: Optional[MultiShotAnalysis] = Field(
        default=None,
        description="멀티샷 일관성 분석 (AI 영상 퀄리티 핵심)"
    )
    
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
    
    # P0-1: Quality Gate Meta (added for proof_ready tracking)
    meta: Dict[str, Any] = Field(
        default_factory=lambda: {
            "proof_ready": False,
            "quality_issues": None,
            "prompt_version": None,
            "model_id": None,
            "schema_version": "4.0.2",
        }
    )


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


# ====================
# A→B MIGRATION (Signal → Invariant)
# ====================

# Promotion thresholds (configurable)
PROMOTION_THRESHOLDS = {
    "slot_to_candidate": {
        "min_sessions": 10,
        "min_success_rate": 0.7,
        "min_distinct_contents": 3
    },
    "candidate_to_dna": {
        "min_sessions": 50,
        "min_success_rate": 0.8,
        "requires_distill_validation": True
    }
}


class SignalPerformance(BaseModel):
    """
    Tracks mise_en_scene_signal performance over time.
    
    A→B Migration: As data accumulates, signals with high success_rate
    are automatically promoted to InvariantCandidate.
    
    Example signal_key: "outfit_color.yellow", "background.minimal"
    """
    signal_key: str  # domain.value format
    element: str  # outfit_color, background, lighting, props
    value: str  # yellow, minimal, bright, etc.
    sentiment: str = "positive"  # positive/negative
    
    # First seen
    first_seen_at: Optional[str] = None
    first_seen_content_id: Optional[str] = None
    
    # Tracking counters
    sessions_applied: int = 0  # How many sessions used this as slot
    success_count: int = 0  # User followed advice
    violation_count: int = 0  # User ignored or failed
    distinct_content_ids: List[str] = Field(default_factory=list)
    
    # Computed metrics
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.violation_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def confidence_tier(self) -> str:
        """low → medium → high based on data volume."""
        if self.sessions_applied < 10:
            return "low"
        elif self.sessions_applied < 50:
            return "medium"
        else:
            return "high"
    
    def should_promote_to_candidate(self) -> bool:
        """Check if signal meets promotion threshold."""
        thresholds = PROMOTION_THRESHOLDS["slot_to_candidate"]
        return (
            self.sessions_applied >= thresholds["min_sessions"] and
            self.success_rate >= thresholds["min_success_rate"] and
            len(self.distinct_content_ids) >= thresholds["min_distinct_contents"]
        )


class InvariantCandidate(BaseModel):
    """
    Intermediate state between MutationSlot and DNAInvariant.
    
    A→B Migration: Signals that pass promotion threshold become
    candidates. Candidates become DNA Invariants after:
    1. More data accumulation (50+ sessions)
    2. DistillRun validation (optional but recommended)
    
    Status flow: pending → approved → promoted (or rejected)
    """
    candidate_id: str
    source: str = "signal_promotion"  # signal_promotion, distill_run, manual
    
    # Original signal info
    signal_key: str
    element: str
    value: str
    sentiment: str = "positive"
    
    # Evidence
    evidence_refs: List[str] = Field(default_factory=list)
    source_content_ids: List[str] = Field(default_factory=list)
    performance_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # Proposed invariant
    proposed_rule_id: Optional[str] = None
    proposed_domain: str = "composition"
    proposed_priority: str = "medium"
    
    # Status
    status: str = "pending"  # pending, canary, approved, promoted, rejected, rolled_back
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Distill validation
    distill_validated: bool = False
    distill_run_id: Optional[str] = None
    
    # (B) Promotion Safety: Canary + Rollback + Cluster Diversity
    canary_enabled: bool = False  # Run in canary mode before full promotion
    canary_session_ratio: float = 0.1  # Apply to 10% of sessions only
    canary_started_at: Optional[str] = None
    canary_sessions_count: int = 0
    canary_success_rate: float = 0.0
    
    # Cluster diversity requirement (must reproduce across clusters)
    cluster_ids_verified: List[str] = Field(default_factory=list)  # Clusters where signal succeeded
    min_clusters_required: int = 2  # Require 2+ cluster verification before DNA
    
    # Rollback capability
    rollback_eligible: bool = True  # Can downgrade if performance drops
    promoted_at: Optional[str] = None
    rolled_back_at: Optional[str] = None
    rollback_reason: Optional[str] = None


# ====================
# PHASE 3: CLUSTER SoR (Parent-Kids)
# ====================

class ClusterSignature(BaseModel):
    """Cluster signature for similarity matching."""
    hook_pattern: str = ""  # e.g., "question_hook", "visual_punch"
    primary_intent: str = ""  # e.g., "tutorial", "review", "vlog"
    audio_style: str = ""  # e.g., "voiceover", "direct_address"
    avg_duration_sec: float = 0.0
    key_elements: List[str] = Field(default_factory=list)


class ClusterKid(BaseModel):
    """Single kid in a cluster with success/failure metadata."""
    vdg_id: str
    content_id: str
    variation_type: str = "variation"  # "homage", "variation", "adaptation"
    success: bool = True  # For success/failure contrast
    similarity_score: float = 0.0  # 0-1, cluster_signature matching
    created_at: Optional[str] = None


class ContentCluster(BaseModel):
    """
    Phase 3 + P2 Roadmap: Content Cluster for Parent-Kids relationships.
    
    Enables NotebookLM-integrated pipeline:
    - DistillRun operates on clusters, not single videos
    - Pack quality improves with cluster-validated rules
    
    P2 Requirements:
    - Parent: Tier S/A, merger_quality=gold, kids>=3
    - Kids: similarity>=70%, success+failure included
    
    Hardening (v1.1):
    - Deterministic cluster_id generation
    - Signature hash normalization
    - Kids dedup+sort via validator
    """
    cluster_id: str
    cluster_name: str  # Human readable
    
    # Parent info (with selection criteria)
    parent_vdg_id: str
    parent_content_id: str
    parent_tier: str = "A"  # S, A, B (S/A required for distill)
    parent_merger_quality: str = "gold"  # gold, silver, bronze
    
    # Kids structure (P2 enhanced)
    kids: List[ClusterKid] = Field(default_factory=list)
    
    # Legacy fields (for backward compat) - auto-deduped and sorted
    kid_vdg_ids: List[str] = Field(default_factory=list)
    kid_content_ids: List[str] = Field(default_factory=list)
    
    # Cluster signature
    signature: ClusterSignature = Field(default_factory=ClusterSignature)
    signature_hash: Optional[str] = None  # v1.1: Deterministic hash
    
    # P2 Selection criteria
    min_kids_required: int = 6  # Consultant: 6~8이 현실적
    min_similarity_threshold: float = 0.70  # 70% match required
    requires_success_failure_contrast: bool = True
    
    # Distill status
    distill_ready: bool = False  # Set True when criteria met
    distill_run_ids: List[str] = Field(default_factory=list)  # Linked DistillRuns
    
    # Provenance
    created_by: str = "manual"  # manual, auto_similarity, auto_time
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @field_validator('kid_vdg_ids', mode='before')
    @classmethod
    def dedupe_sort_kid_vdg_ids(cls, v: List[str]) -> List[str]:
        """Ensure kid_vdg_ids are deduplicated and sorted."""
        if v:
            return sorted(set(v))
        return v
    
    @field_validator('kid_content_ids', mode='before')
    @classmethod
    def dedupe_sort_kid_content_ids(cls, v: List[str]) -> List[str]:
        """Ensure kid_content_ids are deduplicated and sorted."""
        if v:
            return sorted(set(v))
        return v
    
    def compute_signature_hash(self) -> str:
        """Compute deterministic hash from signature."""
        import hashlib
        import json
        
        sig_dict = self.signature.model_dump()
        # Normalize: sort keys, round floats
        def normalize(obj):
            if isinstance(obj, dict):
                return {k: normalize(v) for k, v in sorted(obj.items())}
            if isinstance(obj, float):
                return round(obj, 6)
            if isinstance(obj, list):
                return [normalize(x) for x in obj]
            return obj
        
        normalized = normalize(sig_dict)
        json_str = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
        hash_digest = hashlib.sha256(json_str.encode()).hexdigest()[:12]
        return f"sig.{hash_digest}"
    
    def update_signature_hash(self) -> None:
        """Update the signature_hash field."""
        self.signature_hash = self.compute_signature_hash()
    
    def is_distill_ready(self) -> bool:
        """Check if cluster meets P2 distill criteria."""
        if len(self.kids) < self.min_kids_required:
            return False
        if self.parent_tier not in ["S", "A"]:
            return False
        if self.parent_merger_quality != "gold":
            return False
        if self.requires_success_failure_contrast:
            has_success = any(k.success for k in self.kids)
            has_failure = any(not k.success for k in self.kids)
            if not (has_success and has_failure):
                return False
        return True


# ====================
# PHASE 5: LIVE LOG SCHEMA (RL Data Quality)
# ====================

class SessionContext(BaseModel):
    """
    Context for personalization learning.
    
    Captured per coaching session for RL to understand
    "why did this work/not work for this user?"
    """
    session_id: str
    
    # Persona
    persona_preset: str = "neutral"  # cynical_expert, home_cook, etc.
    
    # Environment
    environment: str = "unknown"  # home, outdoor, studio, store
    device_setup: str = "unknown"  # tripod, handheld, gimbal
    
    # Conditions (estimated)
    lighting_quality: str = "unknown"  # good, fair, poor
    noise_level: str = "unknown"  # quiet, moderate, noisy
    
    # User state
    experience_level: str = "unknown"  # beginner, intermediate, advanced


class CoachingIntervention(BaseModel):
    """
    Single coaching action delivered to user.
    
    RL join key: (session_id, rule_id, ap_id, evidence_id)
    
    Goodhart Prevention:
    - assignment: 'coached' vs 'control' (10% holdout for true A/B)
    - coach_channel: 'audio' vs 'text' vs 'none'
    """
    intervention_id: str
    session_id: str
    pack_id: str
    
    # What was delivered
    rule_id: str
    ap_id: Optional[str] = None  # Analysis point that triggered this
    checkpoint_id: Optional[str] = None
    evidence_id: Optional[str] = None
    
    # Timing
    delivered_at: str
    t_video: float = 0.0  # Video timestamp
    
    # Content
    command_text: str = ""
    persona_preset: str = "neutral"
    
    # Goodhart Prevention: Control Group (10% should be 'control')
    assignment: str = "coached"  # "coached" | "control" - CRITICAL for causal inference
    coach_channel: str = "audio"  # "audio" | "text" | "none"
    
    # Holdout flag (separate from canary - for promotion verification)
    holdout_group: bool = False  # If True, exclude from promotion calculations


class CoachingOutcome(BaseModel):
    """
    Observed result after intervention.
    
    Two-stage outcome for causal data:
    - Stage 1: Session outcome (compliance, metrics)
    - Stage 2: Upload outcome (viral performance proxy)
    
    Joins with CoachingIntervention via intervention_id.
    """
    intervention_id: str  # FK to intervention
    
    # Stage 1: Immediate (within 5s of coaching)
    user_response: str = "unknown"  # complied, ignored, questioned, retake
    compliance_detected: bool = False
    compliance_unknown_reason: Optional[str] = None  # "occluded", "out_of_frame", "no_audio", "ambiguous"
    
    # Measurement (if applicable)
    metric_id: Optional[str] = None
    metric_before: Optional[float] = None
    metric_after: Optional[float] = None
    improvement: Optional[float] = None
    
    # Session level
    retake_count: int = 0
    session_completed: bool = True
    observed_at: Optional[str] = None
    
    # Stage 2: Upload outcome (user-reported or scraped)
    # Critical for causal inference: "compliance → viral success"
    upload_outcome_proxy: Optional[str] = None  # "uploaded", "good_response", "no_upload", "unknown"
    reported_views: Optional[int] = None  # User self-report or scrape
    reported_likes: Optional[int] = None
    reported_saves: Optional[int] = None
    reported_comments: Optional[int] = None
    upload_url: Optional[str] = None  # For verification (optional)
    outcome_reported_at: Optional[str] = None
    
    # Goodhart Prevention: Outcome quality tracking
    outcome_unknown_reason: Optional[str] = None  # "api_blocked", "user_declined", "timeout", "scrape_failed"
    
    # Negative Evidence: Track failures for learning
    is_negative_evidence: bool = False  # True if this rule application led to failure
    negative_reason: Optional[str] = None  # "compliance_but_poor_outcome", "rule_caused_harm"


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
