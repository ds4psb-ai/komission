"""
Director Pack v1.0.2 Pydantic Schemas

Real-time coaching rules compiled from VDG v4.0.
Used by Gemini Live for 1-second interval coaching.

v1.0.2 Protocol Freeze Patches:
- metric_id uses domain.name.v1 format
- evidence_refs unified to List[str]
"""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


# ====================
# 1. SOURCE REFS
# ====================

class SourceRef(BaseModel):
    """VDG 원본 참조"""
    vdg_content_id: Optional[str] = None
    vdg_version: Optional[str] = None
    cluster_id: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)


# ====================
# 2. PACK METADATA
# ====================

class PackMeta(BaseModel):
    """Pack 메타데이터"""
    pack_id: str
    generated_at: str
    compiler_version: str
    source_refs: List[SourceRef] = Field(default_factory=list)
    # Phase 2: Operational debugging - log when fallback rules used
    compiler_warnings: List[str] = Field(default_factory=list)
    
    # H-Final-1: Version tracking for rollback and experiments
    prompt_version: str = "v1"  # VDG prompt version used
    model_version: str = "gemini-2.5-pro"  # AI model used for analysis
    parent_pack_id: Optional[str] = None  # Previous pack (for rollback lineage)
    experiment_id: Optional[str] = None  # A/B test flag (optional)


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
    persona_preset: Optional[str] = None
    persona_vector: Dict[str, Any] = Field(default_factory=dict)
    situation_constraints: Dict[str, Any] = Field(default_factory=dict)


# Blueprint Persona Presets (Phase 2)
PERSONA_PRESETS: Dict[str, Dict[str, Any]] = {
    "cynical_expert": {
        "display_name": "시니컬 전문가",
        "opening_tone": "시니컬",
        "reaction_intensity": "low",
        "camera_distance": "medium",
        "coach_lines": {
            "greeting": "억지로 웃지 마세요. 평소처럼 시니컬하게.",
            "energy": "과하게 움직이지 마세요. 차분하게.",
            "hook": "바로 본론으로 가세요. 인사 생략."
        }
    },
    "home_cook": {
        "display_name": "홈쿡 크리에이터",
        "opening_tone": "친근한",
        "reaction_intensity": "medium",
        "props": "주방용품",
        "setting": "집 주방",
        "coach_lines": {
            "prop": "프라이팬을 더 높이 드세요!",
            "angle": "요리가 잘 보이게 카메라 각도 조정!",
            "hook": "맛있는 냄새가 나는 것처럼 표정 지어보세요~"
        }
    },
    "energetic_host": {
        "display_name": "에너지 넘치는 MC",
        "opening_tone": "활기찬",
        "reaction_intensity": "high",
        "camera_distance": "close",
        "coach_lines": {
            "energy": "더 에너지 넘치게! 텐션 UP!",
            "hook": "와! 하고 크게 시작하세요!",
            "gesture": "제스처를 더 크게!"
        }
    },
    "serious_pro": {
        "display_name": "진지한 전문가",
        "opening_tone": "진지함",
        "reaction_intensity": "low",
        "camera_distance": "wide",
        "coach_lines": {
            "tone": "전문가답게 차분하게 설명하세요.",
            "hook": "핵심 포인트부터 말씀하세요.",
            "credibility": "자신감 있는 목소리로!"
        }
    },
    "friendly_neighbor": {
        "display_name": "친근한 이웃",
        "opening_tone": "친구같은",
        "reaction_intensity": "medium",
        "camera_distance": "medium",
        "coach_lines": {
            "tone": "친구한테 말하듯이 편하게!",
            "hook": "안녕~ 하고 자연스럽게 시작해요.",
            "energy": "너무 힘 빼지 말고 자연스럽게~"
        }
    }
}


def get_persona_config(preset_name: str) -> Optional[Dict[str, Any]]:
    """프리셋 이름으로 Persona 설정 가져오기"""
    return PERSONA_PRESETS.get(preset_name)


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
    """코칭 대사 템플릿"""
    strict: Optional[str] = None
    friendly: Optional[str] = None
    neutral: Optional[str] = None
    ko: Optional[Dict[str, str]] = None
    en: Optional[Dict[str, str]] = None


# ====================
# 8. RULE SPEC
# ====================

class TimeScope(BaseModel):
    """시간 범위"""
    t_window: List[float]
    relative_to: Optional[str] = None


class RuleSpec(BaseModel):
    """머신 체크 가능한 규칙 스펙"""
    metric_id: str  # domain.name.v1 형식
    op: Literal["<=", "<", ">=", ">", "between", "equals", "exists"]
    target: Optional[Any] = None
    range: Optional[List[float]] = None
    unit: Optional[str] = None
    aggregation: Optional[str] = None
    selector: Optional[str] = None
    required_inputs: List[Literal["audio", "video_1fps", "text"]] = Field(default_factory=list)


class DNAInvariant(BaseModel):
    """DNA 불변 규칙"""
    rule_id: str
    domain: Literal["composition", "timing", "audio", "performance", "text", "safety"]
    priority: Literal["critical", "high", "medium", "low"]
    tolerance: Optional[Literal["tight", "normal", "loose"]] = None
    weight: Optional[float] = None
    
    time_scope: TimeScope
    spec: RuleSpec
    check_hint: Optional[str] = None
    
    coach_line_templates: CoachLineTemplates = Field(default_factory=CoachLineTemplates)
    evidence_refs: List[str] = Field(default_factory=list)
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
    """금기"""
    mutation_id: str
    reason: str
    severity: Optional[Literal["critical", "high", "medium", "low"]] = None
    evidence_refs: List[str] = Field(default_factory=list)


# ====================
# 11. CHECKPOINTS
# ====================

class Checkpoint(BaseModel):
    """시간 기반 규칙 활성화"""
    checkpoint_id: str
    t_window: List[float]
    active_rules: List[str]
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
# 14. DIRECTOR PACK v1.0.2
# ====================

class DirectorPack(BaseModel):
    """Director Pack v1.0.2 - Protocol Freeze 완료"""
    pack_version: str = "1.0.2"
    pattern_id: str
    goal: Optional[str] = None
    
    pack_meta: PackMeta
    target: TargetSpec = Field(default_factory=TargetSpec)
    runtime_contract: RuntimeContract
    persona: Persona = Field(default_factory=Persona)
    scoring: Scoring = Field(default_factory=Scoring)
    
    dna_invariants: List[DNAInvariant]
    mutation_slots: List[MutationSlot] = Field(default_factory=list)
    forbidden_mutations: List[ForbiddenMutation] = Field(default_factory=list)
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    
    policy: Policy
    logging_spec: LoggingSpec = Field(default_factory=LoggingSpec)
    extensions: Dict[str, Any] = Field(default_factory=dict)


# ====================
# 15. EXAMPLE PACK
# ====================

EXAMPLE_DIRECTOR_PACK = {
    "pack_version": "1.0.2",
    "pattern_id": "hook_subversion_v1",
    "goal": "훅 펀치 순간 피사체 중앙 유지",
    "pack_meta": {
        "pack_id": "dp_20251229_001",
        "generated_at": "2025-12-29T11:10:00Z",
        "compiler_version": "1.0.2",
        "source_refs": [
            {"vdg_content_id": "vdg_xxx", "vdg_version": "4.0.2", "evidence_refs": ["ev_001"]}
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
                "metric_id": "cmp.stability_score.v1",  # domain.name.v1 형식
                "op": ">=",
                "target": 0.85,
                "aggregation": "mean",
                "required_inputs": ["video_1fps"]
            },
            "check_hint": "훅 펀치 구간 피사체 중앙 안정성 ≥ 0.85",
            "coach_line_templates": {
                "strict": "화면 중앙에 고정하세요!",
                "friendly": "피사체를 중앙에 잡아주세요~",
                "neutral": "중앙 배치를 유지하세요."
            },
            "evidence_refs": ["ev_001", "ev_002"]
        }
    ],
    "checkpoints": [
        {
            "checkpoint_id": "hook_punch",
            "t_window": [0.2, 0.8],
            "active_rules": ["hook_center_anchor"],
            "note": "훅 펀치 순간"
        }
    ],
    "policy": {
        "one_command_only": True,
        "cooldown_sec": 4,
        "uncertainty_policy": "ask_user"
    }
}
