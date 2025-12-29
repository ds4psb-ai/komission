"""
Director Pack v1.0 Pydantic Schemas

Real-time coaching rules compiled from VDG v4.0.
Used by Gemini Live for 1-second interval coaching.

Features:
- DNA Invariants (불변 규칙)
- Mutation Slots (가변 영역)
- Forbidden Mutations (금기)
- Checkpoints (시간 기반 규칙 활성화)
- Policy (코칭 정책)
"""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ====================
# 1. SOURCE REFS
# ====================

class SourceRef(BaseModel):
    """VDG 원본 참조"""
    vdg_content_id: Optional[str] = None
    vdg_version: Optional[str] = None
    cluster_id: Optional[str] = None
    evidence_refs: List[Dict[str, Any]] = Field(default_factory=list)


# ====================
# 2. PACK METADATA
# ====================

class PackMeta(BaseModel):
    """Pack 메타데이터"""
    pack_id: str
    generated_at: str
    compiler_version: str
    source_refs: List[SourceRef] = Field(default_factory=list)


# ====================
# 3. TARGET SPEC
# ====================

class TargetSpec(BaseModel):
    """촬영 타겟 스펙"""
    platform: Optional[str] = None
    orientation: Optional[Literal["portrait", "landscape", "square"]] = None
    duration_target_sec: Optional[float] = None
    language: Optional[str] = None


# ====================
# 4. RUNTIME CONTRACT
# ====================

class RuntimeContract(BaseModel):
    """실시간 검증 계약"""
    input_modalities_expected: List[Literal["audio", "video_1fps", "text"]]
    verification_granularity: Literal["frame", "window"]
    max_instruction_words: Optional[int] = None
    cooldown_sec_default: Optional[float] = None


# ====================
# 5. PERSONA
# ====================

class Persona(BaseModel):
    """사용자 페르소나"""
    persona_preset: Optional[str] = None  # "cynical_expert", "friendly_neighbor"
    persona_vector: Dict[str, Any] = Field(default_factory=dict)
    situation_constraints: Dict[str, Any] = Field(default_factory=dict)


# ====================
# 6. SCORING
# ====================

class Scoring(BaseModel):
    """점수 가중치"""
    dna_weights: Dict[str, float] = Field(default_factory=dict)
    persona_weights: Dict[str, float] = Field(default_factory=dict)
    risk_penalty_rules: List[Dict[str, Any]] = Field(default_factory=list)


# ====================
# 7. COACH LINE TEMPLATES
# ====================

class CoachLineTemplates(BaseModel):
    """코칭 대사 템플릿 (톤별)"""
    strict: Optional[str] = None
    friendly: Optional[str] = None
    neutral: Optional[str] = None
    ko: Optional[Dict[str, str]] = None  # 한국어 버전
    en: Optional[Dict[str, str]] = None  # 영어 버전


# ====================
# 8. RULE SPEC
# ====================

class TimeScope(BaseModel):
    """시간 범위"""
    t_window: List[float]  # [start, end]
    relative_to: Optional[str] = None  # "start", "hook_start", "scene_id"


class RuleSpec(BaseModel):
    """머신 체크 가능한 규칙 스펙"""
    metric: str  # "center_offset", "hook_timing"
    op: Literal["<=", "<", ">=", ">", "between", "equals", "exists"]
    target: Optional[Any] = None
    range: Optional[List[float]] = None  # for "between"
    unit: Optional[str] = None
    required_inputs: List[Literal["audio", "video_1fps", "text"]] = Field(default_factory=list)


class DNAInvariant(BaseModel):
    """DNA 불변 규칙 (절대 타협 불가)"""
    rule_id: str
    domain: Literal["composition", "timing", "audio", "performance", "text", "safety"]
    priority: Literal["critical", "high", "medium", "low"]
    tolerance: Optional[Literal["tight", "normal", "loose"]] = None
    weight: Optional[float] = None
    
    time_scope: TimeScope
    spec: RuleSpec
    check_hint: Optional[str] = None
    
    coach_line_templates: CoachLineTemplates = Field(default_factory=CoachLineTemplates)
    evidence_refs: List[Dict[str, Any]] = Field(default_factory=list)
    fallback: Optional[Literal["ask_user", "do_nothing", "generic_tip"]] = None


# ====================
# 9. MUTATION SLOTS
# ====================

class MutationSlot(BaseModel):
    """변주 가능 영역"""
    slot_id: str
    slot_type: Literal[
        "persona_tone", "setting", "props", "script_style",
        "reaction_intensity", "camera_distance", "wardrobe", "other"
    ]
    guide: Optional[str] = None
    allowed_options: Optional[List[str]] = None
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    coach_line_templates: Dict[str, str] = Field(default_factory=dict)


# ====================
# 10. FORBIDDEN MUTATIONS
# ====================

class ForbiddenMutation(BaseModel):
    """금기 (하지 말 것)"""
    mutation_id: str
    reason: str
    severity: Optional[Literal["critical", "high", "medium", "low"]] = None
    evidence_refs: List[Dict[str, Any]] = Field(default_factory=list)


# ====================
# 11. CHECKPOINTS
# ====================

class Checkpoint(BaseModel):
    """시간 기반 규칙 활성화"""
    checkpoint_id: str
    t_window: List[float]  # [start, end]
    active_rules: List[str]  # rule_id 목록
    note: Optional[str] = None


# ====================
# 12. POLICY
# ====================

class Policy(BaseModel):
    """코칭 정책"""
    one_command_only: bool = True
    cooldown_sec: float = 4.0
    barge_in_handling: Optional[Literal["stop_and_ack", "restart", "ignore"]] = None
    uncertainty_policy: Literal["ask_user", "do_nothing", "generic_tip"] = "ask_user"


# ====================
# 13. LOGGING SPEC
# ====================

class LoggingSpec(BaseModel):
    """로깅 설정"""
    log_level: Optional[Literal["minimal", "standard", "debug"]] = None
    events: List[str] = Field(default_factory=list)


# ====================
# 14. DIRECTOR PACK v1.0
# ====================

class DirectorPack(BaseModel):
    """Director Pack v1.0 - 실시간 코칭 지령서"""
    pack_version: str = "1.0.0"
    pattern_id: str
    goal: Optional[str] = None
    
    # Metadata
    pack_meta: PackMeta
    
    # Target
    target: TargetSpec = Field(default_factory=TargetSpec)
    
    # Runtime Contract
    runtime_contract: RuntimeContract
    
    # Persona
    persona: Persona = Field(default_factory=Persona)
    
    # Scoring
    scoring: Scoring = Field(default_factory=Scoring)
    
    # Rules
    dna_invariants: List[DNAInvariant]
    mutation_slots: List[MutationSlot] = Field(default_factory=list)
    forbidden_mutations: List[ForbiddenMutation] = Field(default_factory=list)
    
    # Checkpoints
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    
    # Policy
    policy: Policy
    
    # Logging
    logging_spec: LoggingSpec = Field(default_factory=LoggingSpec)
    
    # Extensions
    extensions: Dict[str, Any] = Field(default_factory=dict)


# ====================
# 15. EXAMPLE PACK
# ====================

EXAMPLE_DIRECTOR_PACK = {
    "pack_version": "1.0.0",
    "pattern_id": "hook_subversion_v1",
    "goal": "훅 펀치 순간 피사체 중앙 유지",
    "pack_meta": {
        "pack_id": "dp_20251229_001",
        "generated_at": "2025-12-29T10:45:00Z",
        "compiler_version": "1.0.0",
        "source_refs": [
            {"vdg_content_id": "vdg_xxx", "vdg_version": "4.0.0"}
        ]
    },
    "runtime_contract": {
        "input_modalities_expected": ["video_1fps"],
        "verification_granularity": "window",
        "max_instruction_words": 10,
        "cooldown_sec_default": 4
    },
    "dna_invariants": [
        {
            "rule_id": "hook_center_anchor",
            "domain": "composition",
            "priority": "critical",
            "time_scope": {
                "t_window": [0.2, 0.8],
                "relative_to": "start"
            },
            "spec": {
                "metric": "center_offset_stability",
                "op": ">=",
                "target": 0.85,
                "required_inputs": ["video_1fps"]
            },
            "check_hint": "훅 펀치 구간 피사체 중앙 안정성 ≥ 0.85",
            "coach_line_templates": {
                "strict": "화면 중앙에 고정하세요!",
                "friendly": "피사체를 중앙에 잡아주세요~",
                "neutral": "중앙 배치를 유지하세요."
            },
            "evidence_refs": [
                {"source": "composition_metrics.ap_001", "value": 0.92}
            ]
        }
    ],
    "checkpoints": [
        {
            "checkpoint_id": "hook_punch",
            "t_window": [0.2, 0.8],
            "active_rules": ["hook_center_anchor"],
            "note": "훅 펀치 순간 - 중앙 배치 검증"
        }
    ],
    "policy": {
        "one_command_only": True,
        "cooldown_sec": 4,
        "uncertainty_policy": "ask_user"
    }
}
