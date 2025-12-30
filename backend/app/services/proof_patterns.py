"""
Proof Patterns v1.0

TOP 3 증명용 패턴 - 오디오 코칭 효과 검증

Based on Proof Playbook criteria:
1. Observability: 저비용 측정 가능
2. Interventionability: 한 문장 코칭으로 행동 변화
3. Generalizability: 2+ 클러스터에서 재현

Patterns:
1. hook_start_within_2s_v1 - 2초 훅 스타트 (Semantic-only)
2. hook_center_anchor_v1 - 훅 중앙 앵커 (Visual cheap)
3. exposure_floor_v1 - 밝기 바닥선 (Visual cheapest)
"""
from typing import Dict, Any, List
from datetime import datetime

from app.schemas.director_pack import (
    DirectorPack, PackMeta, SourceRef, TargetSpec, RuntimeContract,
    Persona, Scoring, DNAInvariant, TimeScope, RuleSpec,
    CoachLineTemplates, MutationSlot, Checkpoint, Policy, LoggingSpec
)


# ====================
# PATTERN 1: 2초 훅 스타트
# ====================

HOOK_START_WITHIN_2S = DNAInvariant(
    rule_id="hook_start_within_2s_v1",
    domain="timing",
    priority="critical",
    tolerance="tight",
    weight=1.0,
    time_scope=TimeScope(
        t_window=[0.0, 2.0],
        relative_to="start"
    ),
    spec=RuleSpec(
        metric_id="tim.first_speech_start.v1",
        op="<=",
        target=2.0,
        unit="seconds",
        required_inputs=["audio"]
    ),
    check_hint="첫 발화/액션이 2초 내 시작되어야 함",
    coach_line_templates=CoachLineTemplates(
        strict="지금 바로 치고 들어가세요!",
        friendly="바로 시작해요~ 첫 마디 지금!",
        neutral="시작 후 2초 안에 말씀하세요.",
        ko={"default": "지금 바로 한 문장으로 치고 들어가요!"},
        en={"default": "Start speaking now! Punch in within 2 seconds."}
    ),
    evidence_refs=["proof_playbook_v1"],
    fallback="generic_tip"
)


# ====================
# PATTERN 2: 훅 중앙 앵커
# ====================

HOOK_CENTER_ANCHOR = DNAInvariant(
    rule_id="hook_center_anchor_v1",
    domain="composition",
    priority="critical",
    tolerance="normal",
    weight=1.0,
    time_scope=TimeScope(
        t_window=[0.0, 3.0],
        relative_to="start"
    ),
    spec=RuleSpec(
        metric_id="cmp.center_offset_xy.v1",
        op="<=",
        target=0.12,  # 12% max offset from center
        unit="ratio",
        aggregation="max",
        required_inputs=["video_1fps"]
    ),
    check_hint="훅 구간에서 주피사체 중앙 이탈 금지 (±12%)",
    coach_line_templates=CoachLineTemplates(
        strict="화면 중앙에 고정하세요!",
        friendly="중앙으로 와주세요~",
        neutral="피사체를 중앙에 유지하세요.",
        ko={"default": "중앙에 박아!"},
        en={"default": "Stay in the center!"}
    ),
    evidence_refs=["proof_playbook_v1"],
    fallback="generic_tip"
)


# ====================
# PATTERN 3: 밝기 바닥선
# ====================

EXPOSURE_FLOOR = DNAInvariant(
    rule_id="exposure_floor_v1",
    domain="composition",  # Using composition for lighting
    priority="critical",
    tolerance="tight",
    weight=0.9,
    time_scope=TimeScope(
        t_window=[0.0, 60.0],  # 전체 영상
        relative_to="start"
    ),
    spec=RuleSpec(
        metric_id="lit.brightness_ratio.v1",
        op=">=",
        target=0.55,  # 55% minimum brightness
        unit="ratio",
        aggregation="min",
        required_inputs=["video_1fps"]
    ),
    check_hint="밝기가 55% 이하로 내려가면 즉시 개입",
    coach_line_templates=CoachLineTemplates(
        strict="조명을 켜세요! 너무 어둡습니다.",
        friendly="조금 더 밝게 해주세요~",
        neutral="조명을 개선하세요.",
        ko={"default": "조명 켜요. 창문 쪽으로 30도만!"},
        en={"default": "Turn on the light! Move 30 degrees toward the window."}
    ),
    evidence_refs=["proof_playbook_v1"],
    fallback="generic_tip"
)


# ====================
# ALL TOP 3 PATTERNS
# ====================

TOP_3_PROOF_PATTERNS: List[DNAInvariant] = [
    HOOK_START_WITHIN_2S,
    HOOK_CENTER_ANCHOR,
    EXPOSURE_FLOOR,
]


# ====================
# PROOF PACK FACTORY
# ====================

def create_proof_pack(
    pattern_id: str = "proof_playbook_top3_v1",
    goal: str = "오디오 코칭 효과 증명용 3패턴",
    include_all: bool = True,
    select_patterns: List[str] = None
) -> DirectorPack:
    """
    Create a DirectorPack with TOP 3 proof patterns.
    
    Args:
        pattern_id: Pack identifier
        goal: Goal description
        include_all: Include all 3 patterns
        select_patterns: List of specific pattern IDs to include
        
    Returns:
        DirectorPack with selected proof patterns
    """
    # Select patterns
    if include_all:
        patterns = TOP_3_PROOF_PATTERNS.copy()
    else:
        pattern_map = {p.rule_id: p for p in TOP_3_PROOF_PATTERNS}
        patterns = [pattern_map[pid] for pid in (select_patterns or []) if pid in pattern_map]
    
    # Create checkpoints for each pattern
    checkpoints = []
    for p in patterns:
        checkpoints.append(Checkpoint(
            checkpoint_id=f"cp_{p.rule_id}",
            t_window=p.time_scope.t_window,
            active_rules=[p.rule_id],
            note=p.check_hint
        ))
    
    # Build pack
    pack = DirectorPack(
        pack_version="1.0.2",
        pattern_id=pattern_id,
        goal=goal,
        pack_meta=PackMeta(
            pack_id=f"proof_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            compiler_version="proof_patterns_v1",
            source_refs=[
                SourceRef(evidence_refs=["proof_playbook_v1"])
            ],
            prompt_version="v1",
            model_version="gemini-2.5-flash-native-audio"
        ),
        target=TargetSpec(
            platform="shorts",
            orientation="portrait",
            duration_target_sec=60.0,
            language="ko"
        ),
        runtime_contract=RuntimeContract(
            input_modalities_expected=["audio", "video_1fps"],
            verification_granularity="window",
            max_instruction_words=10,
            cooldown_sec_default=4.0
        ),
        persona=Persona(
            persona_preset="friendly_neighbor",
            persona_vector={},
            situation_constraints={}
        ),
        scoring=Scoring(
            dna_weights={p.rule_id: p.weight or 1.0 for p in patterns},
            persona_weights={},
            risk_penalty_rules=[]
        ),
        dna_invariants=patterns,
        mutation_slots=[],
        forbidden_mutations=[],
        checkpoints=checkpoints,
        policy=Policy(
            one_command_only=True,
            cooldown_sec=4.0,
            barge_in_handling="stop_and_ack",
            uncertainty_policy="generic_tip"
        ),
        logging_spec=LoggingSpec(
            log_level="standard",
            events=[
                "rule_evaluated",
                "intervention_triggered",
                "compliance_observed",
                "session_end"
            ]
        ),
        extensions={
            "proof_playbook_version": "1.0",
            "goodhart_prevention": True,
            "control_ratio": 0.10,
            "holdout_ratio": 0.05
        }
    )
    
    return pack


# ====================
# CONVENIENCE GETTERS
# ====================

def get_pattern_by_id(pattern_id: str) -> DNAInvariant | None:
    """Get a specific pattern by ID."""
    for p in TOP_3_PROOF_PATTERNS:
        if p.rule_id == pattern_id:
            return p
    return None


def get_coach_line(pattern_id: str, tone: str = "friendly") -> str | None:
    """Get coaching line for a pattern with specific tone."""
    pattern = get_pattern_by_id(pattern_id)
    if not pattern:
        return None
    
    templates = pattern.coach_line_templates
    if tone == "strict":
        return templates.strict
    elif tone == "friendly":
        return templates.friendly
    elif tone == "neutral":
        return templates.neutral
    else:
        # Use Korean default
        return templates.ko.get("default") if templates.ko else templates.neutral


# ====================
# PATTERN IDS
# ====================

PATTERN_IDS = {
    "HOOK_START": "hook_start_within_2s_v1",
    "CENTER_ANCHOR": "hook_center_anchor_v1", 
    "EXPOSURE_FLOOR": "exposure_floor_v1",
}
