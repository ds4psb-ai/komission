"""
Proof Patterns v1.1

TOP 3 증명용 패턴 - 오디오 코칭 효과 검증

Based on Proof Playbook criteria:
1. Observability: 저비용 측정 가능
2. Interventionability: 한 문장 코칭으로 행동 변화
3. Generalizability: 2+ 클러스터에서 재현

Patterns:
1. hook_start_within_2s_v1 - 2초 훅 스타트 (Semantic-only)
2. hook_center_anchor_v1 - 훅 중앙 앵커 (Visual cheap)
3. exposure_floor_v1 - 밝기 바닥선 (Visual cheapest)

v1.1 Hardening:
- MetricEvaluator class for rule evaluation
- PatternValidator for input validation
- EvaluationResult dataclass with detailed status
- Comprehensive error handling
"""
from typing import Dict, Any, List, Optional, Literal, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.schemas.director_pack import (
    DirectorPack, PackMeta, SourceRef, TargetSpec, RuntimeContract,
    Persona, Scoring, DNAInvariant, TimeScope, RuleSpec,
    CoachLineTemplates, MutationSlot, Checkpoint, Policy, LoggingSpec
)

logger = logging.getLogger(__name__)


# ====================
# EVALUATION RESULT
# ====================

class EvaluationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class EvaluationResult:
    """메트릭 평가 결과"""
    rule_id: str
    status: EvaluationStatus
    
    # 측정값
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    
    # 위반 정보
    violated: bool = False
    violation_severity: Optional[float] = None  # 0~1, 위반 정도
    
    # 코칭
    coach_line: Optional[str] = None
    coach_tone: str = "friendly"
    
    # 메타
    t_sec: float = 0.0
    evaluated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    @property
    def needs_intervention(self) -> bool:
        """개입 필요 여부"""
        return self.violated and self.status == EvaluationStatus.FAIL


# ====================
# METRIC EVALUATOR
# ====================

class MetricEvaluator:
    """
    메트릭 기반 규칙 평가기
    
    Usage:
        evaluator = MetricEvaluator()
        result = evaluator.evaluate(
            pattern=HOOK_START_WITHIN_2S,
            metric_value=2.5,
            t_sec=2.5
        )
    """
    
    # 연산자별 평가 함수
    OPERATORS = {
        "<=": lambda v, t: v <= t,
        "<": lambda v, t: v < t,
        ">=": lambda v, t: v >= t,
        ">": lambda v, t: v > t,
        "equals": lambda v, t: v == t,
        "exists": lambda v, t: v is not None,
    }
    
    def __init__(self, default_tone: str = "friendly"):
        self.default_tone = default_tone
    
    def evaluate(
        self,
        pattern: DNAInvariant,
        metric_value: Optional[float],
        t_sec: float = 0.0,
        aggregation_values: Optional[List[float]] = None,
        tone: str = None,
        skip_time_check: bool = True  # v1.1: 기본적으로 메트릭 기반 평가만
    ) -> EvaluationResult:
        """
        패턴 규칙 평가
        
        Args:
            pattern: 평가할 DNAInvariant
            metric_value: 단일 측정값 (aggregation 없을 때)
            t_sec: 측정 시점
            aggregation_values: 집계용 값 리스트 (mean/max/min용)
            tone: 코칭 톤 (strict/friendly/neutral)
            skip_time_check: True면 time_window 체크 스킵 (메트릭만 평가)
            
        Returns:
            EvaluationResult with detailed status
        """
        tone = tone or self.default_tone
        spec = pattern.spec
        
        try:
            # 1. 시간 범위 체크 (옵셔널)
            if not skip_time_check and not self._in_time_window(t_sec, pattern.time_scope):
                return EvaluationResult(
                    rule_id=pattern.rule_id,
                    status=EvaluationStatus.SKIPPED,
                    t_sec=t_sec,
                    error_message="Outside time window"
                )
            
            # 2. 값 계산 (단일 or 집계)
            if aggregation_values and spec.aggregation:
                actual_value = self._aggregate(aggregation_values, spec.aggregation)
            else:
                actual_value = metric_value
            
            # 3. 값 없으면 UNKNOWN
            if actual_value is None:
                return EvaluationResult(
                    rule_id=pattern.rule_id,
                    status=EvaluationStatus.UNKNOWN,
                    t_sec=t_sec,
                    error_message="No metric value provided"
                )
            
            # 4. 규칙 평가
            target = spec.target
            op = spec.op
            
            if op == "between":
                range_ = spec.range or [0, 1]
                passed = range_[0] <= actual_value <= range_[1]
            elif op in self.OPERATORS:
                passed = self.OPERATORS[op](actual_value, target)
            else:
                return EvaluationResult(
                    rule_id=pattern.rule_id,
                    status=EvaluationStatus.ERROR,
                    t_sec=t_sec,
                    error_message=f"Unknown operator: {op}"
                )
            
            # 5. 위반 정도 계산
            violation_severity = None
            if not passed and target is not None:
                violation_severity = self._calculate_severity(actual_value, target, op)
            
            # 6. 결과 구성
            coach_line = self._get_coach_line(pattern, tone) if not passed else None
            
            return EvaluationResult(
                rule_id=pattern.rule_id,
                status=EvaluationStatus.PASS if passed else EvaluationStatus.FAIL,
                metric_value=actual_value,
                threshold=target,
                violated=not passed,
                violation_severity=violation_severity,
                coach_line=coach_line,
                coach_tone=tone,
                t_sec=t_sec
            )
            
        except Exception as e:
            logger.error(f"Evaluation error for {pattern.rule_id}: {e}")
            return EvaluationResult(
                rule_id=pattern.rule_id,
                status=EvaluationStatus.ERROR,
                t_sec=t_sec,
                error_message=str(e)
            )
    
    def _in_time_window(self, t_sec: float, scope: TimeScope) -> bool:
        """시간 범위 내인지 체크"""
        t_min, t_max = scope.t_window
        return t_min <= t_sec <= t_max
    
    def _aggregate(self, values: List[float], agg_type: str) -> Optional[float]:
        """값 집계"""
        if not values:
            return None
        
        if agg_type == "mean":
            return sum(values) / len(values)
        elif agg_type == "max":
            return max(values)
        elif agg_type == "min":
            return min(values)
        elif agg_type == "sum":
            return sum(values)
        elif agg_type == "first":
            return values[0]
        elif agg_type == "last":
            return values[-1]
        else:
            return sum(values) / len(values)  # default to mean
    
    def _calculate_severity(
        self, 
        actual: float, 
        target: float, 
        op: str
    ) -> float:
        """위반 심각도 계산 (0~1)"""
        if target == 0:
            return 1.0
        
        if op in ["<=", "<"]:
            # 초과량 / 기준값
            return min(1.0, (actual - target) / target)
        elif op in [">=", ">"]:
            # 부족량 / 기준값
            return min(1.0, (target - actual) / target) if actual < target else 0.0
        else:
            return 0.5  # default medium severity
    
    def _get_coach_line(self, pattern: DNAInvariant, tone: str) -> Optional[str]:
        """코칭 라인 가져오기"""
        templates = pattern.coach_line_templates
        if tone == "strict":
            return templates.strict
        elif tone == "friendly":
            return templates.friendly
        elif tone == "neutral":
            return templates.neutral
        else:
            return templates.ko.get("default") if templates.ko else templates.neutral


# ====================
# PATTERN VALIDATOR
# ====================

class PatternValidator:
    """패턴 및 입력 유효성 검증"""
    
    @staticmethod
    def validate_pattern(pattern: DNAInvariant) -> Tuple[bool, List[str]]:
        """
        패턴 유효성 검증
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # rule_id 체크
        if not pattern.rule_id:
            errors.append("rule_id is required")
        
        # spec 체크
        spec = pattern.spec
        if not spec.metric_id:
            errors.append("metric_id is required")
        if not spec.op:
            errors.append("operator is required")
        if spec.op not in ["<=", "<", ">=", ">", "between", "equals", "exists"]:
            errors.append(f"Invalid operator: {spec.op}")
        
        # time_scope 체크
        scope = pattern.time_scope
        if len(scope.t_window) != 2:
            errors.append("t_window must have exactly 2 values")
        elif scope.t_window[0] > scope.t_window[1]:
            errors.append("t_window[0] must be <= t_window[1]")
        
        # between 연산자는 range 필요
        if spec.op == "between" and not spec.range:
            errors.append("range is required for 'between' operator")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_metric_input(
        pattern: DNAInvariant,
        metric_value: Optional[float],
        t_sec: float
    ) -> Tuple[bool, Optional[str]]:
        """
        메트릭 입력 유효성 검증
        
        Returns:
            (is_valid, error_message)
        """
        # t_sec 음수 체크
        if t_sec < 0:
            return False, "t_sec cannot be negative"
        
        # 값 타입 체크
        if metric_value is not None and not isinstance(metric_value, (int, float)):
            return False, f"metric_value must be numeric, got {type(metric_value)}"
        
        return True, None


# 싱글톤 인스턴스
_evaluator: Optional[MetricEvaluator] = None


def get_metric_evaluator() -> MetricEvaluator:
    """싱글톤 MetricEvaluator 인스턴스"""
    global _evaluator
    if _evaluator is None:
        _evaluator = MetricEvaluator()
    return _evaluator



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

def get_pattern_by_id(pattern_id: str) -> Optional[DNAInvariant]:
    """Get a specific pattern by ID."""
    for p in TOP_3_PROOF_PATTERNS:
        if p.rule_id == pattern_id:
            return p
    return None


def get_coach_line(pattern_id: str, tone: str = "friendly") -> Optional[str]:
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
