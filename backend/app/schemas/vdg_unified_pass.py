# backend/app/schemas/vdg_unified_pass.py
"""
VDG Unified Pass Schema (LLM 1회 호출 출력 계약)

설계 원칙:
- Pass 1 (LLM): 의미/인과/측정설계(Plan)만 생성
- Pass 2 (CV): 수치/좌표/결정론 측정만 수행

정합성 규칙:
- ID 생성 금지 (ap_id, evidence_id는 코드에서 생성)
- Metric Registry 밖 metric_id 금지
- Plan은 Seed로만 받음 (정규화는 코드에서)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


# -------------------------
# Shared small types
# -------------------------

class TimeWindowMs(BaseModel):
    """밀리초 단위 시간 윈도우"""
    # model_config removed for Gemini compatibility

    start_ms: int = Field(..., ge=0, description="inclusive")
    end_ms: int = Field(..., ge=0, description="exclusive")

    @model_validator(mode="after")
    def _validate_order(self):
        if self.end_ms <= self.start_ms:
            raise ValueError("end_ms must be > start_ms")
        return self


# -------------------------
# Hook / Story
# -------------------------

MicrobeatRole = Literal[
    "start", "setup", "hook", "punch", "reveal", "demo", "payoff", "cta", "loop"
]


class MicrobeatLLM(BaseModel):
    """마이크로비트 (훅 내부 리듬 단위)"""
    # model_config removed for Gemini compatibility

    t_ms: int = Field(..., ge=0, description="timestamp in ms")
    role: MicrobeatRole
    description: str = Field(..., min_length=1, max_length=500)
    evidence: Optional[str] = Field(None, max_length=500, description="짧은 근거 (대사/텍스트/행동 등)")


class HookGenomeLLM(BaseModel):
    """훅 유전체 (바이럴 DNA 핵심)"""
    # model_config removed for Gemini compatibility

    # NEW: pattern and delivery fields for proper hook classification
    pattern: Literal[
        "question_hook", "shock_reveal", "countdown", "pov", "before_after",
        "curiosity_gap", "challenge", "tutorial_tease", "story_hook", "visual_punch",
        "confession", "list_format", "myth_bust", "social_proof", "pain_point"
    ] = "curiosity_gap"
    
    delivery: Literal[
        "visual_gag", "storytelling", "reaction", "tutorial", "reveal",
        "montage", "talking_head", "challenge", "transformation", "comparison"
    ] = "visual_gag"
    
    hook_summary: str = Field(default="", max_length=200, description="훅의 핵심 요약 (한국어)")
    
    strength: float = Field(..., ge=0.0, le=1.0)
    hook_start_ms: int = Field(..., ge=0)
    hook_end_ms: int = Field(..., ge=0)
    microbeats: List[MicrobeatLLM] = Field(default_factory=list, max_length=12)

    spoken_hook: Optional[str] = Field(None, max_length=140)
    on_screen_text: Optional[str] = Field(None, max_length=140)

    @model_validator(mode="after")
    def _validate_hook_range(self):
        if self.hook_end_ms < self.hook_start_ms:
            raise ValueError("hook_end_ms must be >= hook_start_ms")
        return self


class SceneLLM(BaseModel):
    """씬 정보"""
    # model_config removed for Gemini compatibility

    idx: int = Field(..., ge=0)
    window: TimeWindowMs
    label: str = Field(..., min_length=1, max_length=100, description="예: setup/demo/reveal/payoff")
    summary: str = Field(..., min_length=1, max_length=500)


class CapsuleBriefLLM(BaseModel):
    """Capsule Brief - 촬영 가이드 (LLM 출력용)"""
    # model_config removed for Gemini compatibility

    shotlist: List[str] = Field(
        default_factory=list, max_length=6,
        description="3-6개 샷 설명 (예: '클로즈업으로 제품 강조')"
    )
    do_not: List[str] = Field(
        default_factory=list, max_length=4,
        description="2-4개 피해야 할 것 (예: '흔들리는 카메라', '너무 긴 인트로')"
    )
    hook_script: str = Field(
        default="",
        max_length=200,
        description="훅 스크립트 (1-2문장)"
    )


# -------------------------
# Mise-en-scène / Intent
# -------------------------

MiseType = Literal[
    "composition", "lighting", "color", "wardrobe", "prop", "setting",
    "camera", "editing", "audio", "text"
]


class MiseEnSceneSignalLLM(BaseModel):
    """미장센 신호"""
    # model_config removed for Gemini compatibility

    type: MiseType
    description: str = Field(..., min_length=1, max_length=500)
    why_it_matters: str = Field(..., min_length=1, max_length=500)
    anchor_ms: Optional[int] = Field(None, ge=0, description="대표 타임스탬프(없으면 None)")


class IntentLayerLLM(BaseModel):
    """크리에이터 의도 레이어"""
    # model_config removed for Gemini compatibility

    creator_intent: str = Field(..., min_length=1, max_length=500)
    audience_trigger: List[str] = Field(default_factory=list, max_length=12, description="감정/욕구 트리거")
    novelty: str = Field(..., min_length=1, max_length=500)
    clarity: str = Field(..., min_length=1, max_length=500)


# -------------------------
# Entity hints for CV
# -------------------------

EntityType = Literal["person", "face", "hand", "product", "text", "environment", "other"]


class EntityHintLLM(BaseModel):
    """CV에게 전달할 엔티티 힌트"""
    # model_config removed for Gemini compatibility

    key: str = Field(..., min_length=1, max_length=40, description="entity hint key (e.g. 'main_subject')")
    entity_type: EntityType
    description: str = Field(..., min_length=1, max_length=200)
    appears_windows: List[TimeWindowMs] = Field(default_factory=list, max_length=6)
    cv_priority: Literal["primary", "secondary", "optional"] = "secondary"


# -------------------------
# Causal reasoning (why viral)
# -------------------------

class CausalReasoningLLM(BaseModel):
    """인과 추론 (왜 바이럴인가)"""
    # model_config removed for Gemini compatibility

    why_viral_one_liner: str = Field(
        default="",
        max_length=300,
        alias="why_viral",
        validation_alias="why_viral",
        description="왜 바이럴인지 한 줄 요약"
    )
    causal_chain: List[str] = Field(default_factory=list, max_length=8, description="원인→결과 체인")
    replication_recipe: List[str] = Field(default_factory=list, max_length=8, description="따라하기 레시피(크리에이터 언어)")
    risks_or_unknowns: List[str] = Field(default_factory=list, max_length=6, description="불확실성/가정")


# -------------------------
# Evidence Anchors (P0 Hardening)
# -------------------------

CommentSignalType = Literal[
    "hook", "twist", "relatability", "aesthetic", "instruction",
    "shock", "product", "editing", "music", "humor", "other"
]


class CommentEvidenceLLM(BaseModel):
    """
    댓글 증거 (Top 5)
    
    중요: LLM은 새 ID를 생성하지 않고, 입력된 comment_rank만 참조
    """
    # model_config removed for Gemini compatibility

    comment_rank: int = Field(..., ge=1, le=20, description="top_comments의 순위 (1-20)")
    quote: str = Field(..., min_length=1, max_length=500, description="댓글 핵심 구절")
    signal_type: CommentSignalType
    why_it_matters: str = Field(..., min_length=1, max_length=500, description="이 댓글이 왜 바이럴 신호인지")
    anchor_ms: Optional[int] = Field(None, ge=0, description="이 댓글이 가리키는 영상 구간 (특정 가능시)")


KeyframeRole = Literal["start", "peak", "end"]


class KeyframeLLM(BaseModel):
    """
    키프레임 증거 (START/PEAK/END)
    
    각 바이럴 킥당 정확히 3장 필수
    """
    t_ms: int = Field(..., ge=0, description="정확한 타임스탬프 (밀리초)")
    role: KeyframeRole
    what_to_see: str = Field(..., min_length=1, max_length=100, description="이 프레임의 바이럴 포인트")


class ViralKickLLM(BaseModel):
    """
    바이럴 킥 구간 (3~5개)
    
    댓글 증거 + 영상 증거 cue + 키프레임 3장을 반드시 포함
    """
    # model_config removed for Gemini compatibility

    kick_index: int = Field(..., ge=0, le=8)  # Allow 0-based from LLM
    window: TimeWindowMs
    title: str = Field(..., min_length=1, max_length=200, description="킥 제목 (예: '2.3초 표정 반전')")
    mechanism: str = Field(..., min_length=1, max_length=500, description="왜 먹히는지 인과 설명")
    
    # 증거 연결 (MUST)
    evidence_comment_ranks: List[int] = Field(
        ..., min_length=1, max_length=5,
        description="comment_evidence_top5에서 참조하는 rank 목록 (최소 1개)"
    )
    evidence_cues: List[str] = Field(
        ..., min_length=1, max_length=6,
        description="영상 증거: 대사/온스크린텍스트/행동 (최소 1개)"
    )
    
    # 키프레임 증거 (P0 Hardening - MUST)
    keyframes: List[KeyframeLLM] = Field(
        default_factory=list, max_length=5,
        description="START/PEAK/END 3장 (프롬프트에서 강제, 전처리로 기본값 생성)"
    )
    
    # 코칭용
    creator_instruction: str = Field(
        ..., min_length=1, max_length=500,
        description="크리에이터 언어로 된 실행 지시문 (1~2문장)"
    )
    scene_index: Optional[int] = Field(None, ge=0, description="scenes[] 인덱스 (해당시)")
    
    # P0-2: Proof-Grade Evidence Anchoring
    confidence: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="킥 신뢰도 점수 (high-conf >= 0.6)"
    )
    missing_reason: Optional[str] = Field(
        None, max_length=50,
        description="증거 부족 사유: 'no_evidence' | 'out_of_range' | 'low_confidence'"
    )
    comment_evidence_refs: List[str] = Field(
        default_factory=list, max_length=5,
        description="댓글 증거 ID 리스트 (ev.comment.xxx 형식)"
    )
    frame_evidence_refs: List[str] = Field(
        default_factory=list, max_length=5,
        description="프레임 증거 ID 리스트 (ev.frame.xxx 형식)"
    )


# -------------------------
# Analysis plan seeds (for CV)
# -------------------------

Aggregation = Literal["mean", "median", "max", "min", "first", "last", "p95"]
ROI = Literal["full_frame", "face", "main_subject", "product", "text_overlay"]


class MeasurementSpecLLM(BaseModel):
    """CV 측정 명세"""
    # model_config removed for Gemini compatibility

    metric_id: str = Field(..., min_length=1, max_length=80, description="MUST be from METRIC_DEFINITIONS keys")
    aggregation: Aggregation = "mean"
    roi: ROI = "full_frame"
    notes: Optional[str] = Field(None, max_length=120)


PlanPriority = Literal["critical", "high", "medium", "low"]


class AnalysisPointSeedLLM(BaseModel):
    """
    CV 측정 지점 제안
    
    중요: ID(ap_id) 생성 금지, 수치 생성 금지
    """
    # model_config removed for Gemini compatibility

    t_center_ms: int = Field(..., ge=0)
    t_window_ms: int = Field(..., ge=200, le=15000, description="CV 측정 윈도우 폭 (200~15000ms 권장)")
    kick_index: Optional[int] = Field(None, ge=0, le=8, description="연결된 viral_kick.kick_index (해당시, 0=none)")
    priority: PlanPriority
    reason: str = Field(..., min_length=1, max_length=200)

    # CV에게 "무엇을 숫자로 뽑아야 하는지"
    measurements: List[MeasurementSpecLLM] = Field(default_factory=list, max_length=8)

    # CV에게 "무엇을 대상으로 봐야 하는지"
    target_entity_keys: List[str] = Field(default_factory=list, max_length=4, description="entity_hints keys")

    evidence_note: Optional[str] = Field(None, max_length=200, description="왜 이 타임스탬프가 중요한지 짧게")

    @model_validator(mode="after")
    def _validate_measurements(self):
        if len(self.measurements) == 0:
            raise ValueError("analysis point must include at least 1 measurement")
        return self


class AnalysisPlanSeedLLM(BaseModel):
    """CV 측정 계획 Seed"""
    # model_config removed for Gemini compatibility

    points: List[AnalysisPointSeedLLM] = Field(default_factory=list, max_length=12)


# -------------------------
# Top-level LLM output
# -------------------------

class UnifiedPassLLMOutput(BaseModel):
    """
    LLM의 1회 호출 결과 (의미+인과+Plan Seed)
    
    중요:
    - IDs (ap_id/evidence_id)는 포함하지 않음 (코드에서 생성)
    - 수치 측정값 포함 금지 (CV Pass가 담당)
    
    Evidence Anchors (P0):
    - comment_evidence_top5: 반드시 5개 댓글 증거
    - viral_kicks: 3~5개 바이럴 킥 구간 (댓글+영상 증거 필수)
    """
    # model_config removed for Gemini compatibility

    schema_version: str = Field(..., description="e.g. 'unified_pass_llm.v2'")
    language: str = Field("ko", description="output language for text fields")
    duration_ms: int = Field(..., ge=0)

    # Meaning
    hook_genome: HookGenomeLLM
    scenes: List[SceneLLM] = Field(default_factory=list, max_length=12)
    intent_layer: IntentLayerLLM
    mise_en_scene_signals: List[MiseEnSceneSignalLLM] = Field(default_factory=list, max_length=16)

    # Evidence Anchors (P0 신규)
    comment_evidence_top5: List[CommentEvidenceLLM] = Field(
        ..., min_length=1, max_length=10,
        description="1~10개 댓글 증거 (숏폼은 댓글이 적을 수 있음)"
    )
    viral_kicks: List[ViralKickLLM] = Field(
        ..., min_length=3, max_length=6,
        description="3~5개 바이럴 킥 구간 (각각 댓글+영상 증거 필수)"
    )

    # CV guidance
    entity_hints: List[EntityHintLLM] = Field(default_factory=list, max_length=10)
    analysis_plan: AnalysisPlanSeedLLM = Field(default_factory=AnalysisPlanSeedLLM)

    # Why viral
    causal_reasoning: CausalReasoningLLM

    # Director guidance (신규)
    capsule_brief: CapsuleBriefLLM = Field(default_factory=CapsuleBriefLLM)

    @model_validator(mode="after")
    def _validate_kick_coverage(self):
        """각 viral_kick이 analysis_plan.points에 의해 커버되는지 검증"""
        if not self.analysis_plan.points:
            return self
        
        for kick in self.viral_kicks:
            kick_start = kick.window.start_ms
            kick_end = kick.window.end_ms
            
            # 적어도 하나의 point가 kick window와 겹치는지 확인
            covered = False
            for point in self.analysis_plan.points:
                point_start = point.t_center_ms - point.t_window_ms // 2
                point_end = point.t_center_ms + point.t_window_ms // 2
                
                # 겹침 검사
                if point_start < kick_end and point_end > kick_start:
                    covered = True
                    break
            
            if not covered:
                raise ValueError(
                    f"viral_kick {kick.kick_index} ({kick_start}-{kick_end}ms) "
                    f"is not covered by any analysis_plan.point"
                )
        
        return self

