"""
STPF v3.1 Report Generator

최종 출력 규격 생성기.
모든 STPF 분석 결과를 표준화된 리포트로 변환.
"""
from typing import Dict, Any, List, Optional, Tuple, Literal
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.stpf.schemas import STPFResult
from app.services.stpf.kelly_criterion import KellyDecision, GradeInfo, kelly_engine
from app.services.stpf.simulation import ToTResult, MonteCarloResult
from app.services.stpf.bayesian_updater import BayesianPosterior


class VariableContribution(BaseModel):
    """변수 기여도"""
    variable: str
    score: float
    weight: float
    contribution: float
    interpretation: Optional[str] = None


class ActionItem(BaseModel):
    """행동 항목"""
    action: str
    impact: str
    priority: Literal["high", "medium", "low"]
    target_variable: Optional[str] = None


class STPFKernel(BaseModel):
    """STPF 핵심 출력"""
    raw_score: float
    score_1000: int
    go_nogo: str
    gate_passed: bool


class STPFVariablesFull(BaseModel):
    """전체 변수 테이블"""
    gates: Dict[str, float]
    numerator: Dict[str, float]
    denominator: Dict[str, float]
    multipliers: Dict[str, float]


class STPFProbabilityInfo(BaseModel):
    """확률 정보"""
    p_success: float
    confidence_interval: Tuple[float, float]
    sample_count: int
    confidence_level: str


class STPFScenarios(BaseModel):
    """시나리오 분석"""
    worst: Dict[str, Any]
    base: Dict[str, Any]
    best: Dict[str, Any]
    weighted_score: float
    recommendation: str


class STPFDiagnosis(BaseModel):
    """진단 (Why)"""
    top_contributors: List[VariableContribution]
    critical_friction: Optional[VariableContribution] = None
    gate_issues: List[str] = Field(default_factory=list)


class STPFActionPlan(BaseModel):
    """행동 계획 (How)"""
    numerator_actions: List[ActionItem]
    denominator_actions: List[ActionItem]
    gate_actions: List[ActionItem]
    timeline: Dict[str, List[str]] = Field(default_factory=dict)


class STPFVerdict(BaseModel):
    """최종 판결"""
    grade: str  # S/A/B/C
    grade_label: str
    grade_description: str
    recommended_action: str
    kelly_fraction: float
    recommended_effort_percent: float
    signal: str  # GO, MODERATE, CAUTION, NO_GO


class STPFReport(BaseModel):
    """STPF 표준 리포트
    
    전체 분석 결과를 하나의 구조화된 문서로 출력.
    """
    
    # A. Kernel
    kernel: STPFKernel
    
    # B. Variable Table
    variables: STPFVariablesFull
    variable_interpretations: Dict[str, str] = Field(default_factory=dict)
    
    # C. Probability (Bayesian)
    probability: Optional[STPFProbabilityInfo] = None
    
    # D. Scenarios (ToT)
    scenarios: Optional[STPFScenarios] = None
    
    # E. Diagnosis (Why)
    diagnosis: STPFDiagnosis
    
    # F. Action Plan (How)
    action_plan: STPFActionPlan
    
    # G. Verdict
    verdict: STPFVerdict
    
    # H. Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "kernel": {"score_1000": 850, "go_nogo": "GO"},
                "verdict": {"grade": "S", "signal": "GO"},
            }
        }


class STPFReportGenerator:
    """STPF 리포트 생성기"""
    
    VERSION = "1.0"
    
    def __init__(self):
        from app.services.stpf.anchors import VDGAnchorLookup
        self.anchor_lookup = VDGAnchorLookup()
    
    def generate(
        self,
        result: STPFResult,
        gates: Dict[str, float],
        numerator: Dict[str, float],
        denominator: Dict[str, float],
        multipliers: Dict[str, float],
        bayesian: Optional[BayesianPosterior] = None,
        tot_result: Optional[ToTResult] = None,
        monte_carlo: Optional[MonteCarloResult] = None,
        content_id: Optional[str] = None,
    ) -> STPFReport:
        """전체 리포트 생성"""
        
        # A. Kernel
        kernel = STPFKernel(
            raw_score=result.raw_score,
            score_1000=result.score_1000,
            go_nogo=result.go_nogo,
            gate_passed=result.gate_passed,
        )
        
        # B. Variables
        variables = STPFVariablesFull(
            gates=gates,
            numerator=numerator,
            denominator=denominator,
            multipliers=multipliers,
        )
        
        # 앵커 해석
        interpretations = {}
        for var, score in {**numerator, **multipliers}.items():
            interp = self.anchor_lookup.get_anchor(var, int(score))
            if interp:
                interpretations[var] = interp
        
        # C. Probability
        probability = None
        if bayesian:
            probability = STPFProbabilityInfo(
                p_success=bayesian.p_success,
                confidence_interval=bayesian.confidence_interval,
                sample_count=bayesian.sample_count,
                confidence_level=bayesian.get_confidence_level(),
            )
        
        # D. Scenarios
        scenarios = None
        if tot_result:
            scenarios = STPFScenarios(
                worst={"score": tot_result.worst.score_1000, "go_nogo": tot_result.worst.go_nogo},
                base={"score": tot_result.base.score_1000, "go_nogo": tot_result.base.go_nogo},
                best={"score": tot_result.best.score_1000, "go_nogo": tot_result.best.go_nogo},
                weighted_score=tot_result.weighted_score,
                recommendation=tot_result.recommendation,
            )
        
        # E. Diagnosis
        diagnosis = self._generate_diagnosis(result, gates, numerator, denominator, multipliers)
        
        # F. Action Plan
        action_plan = self._generate_action_plan(result, diagnosis)
        
        # G. Verdict
        kelly = kelly_engine.calculate_from_stpf(result.score_1000)
        grade = kelly_engine.get_grade_info(result.score_1000)
        
        verdict = STPFVerdict(
            grade=grade.grade,
            grade_label=grade.label,
            grade_description=grade.description,
            recommended_action=grade.action,
            kelly_fraction=kelly.safe_kelly_fraction,
            recommended_effort_percent=kelly.recommended_effort_percent,
            signal=kelly.signal,
        )
        
        # H. Metadata
        metadata = {
            "report_version": self.VERSION,
            "generated_at": datetime.now().isoformat(),
            "content_id": content_id,
            "stpf_version": "3.1",
        }
        
        if monte_carlo:
            metadata["monte_carlo"] = {
                "mean": monte_carlo.mean,
                "std": monte_carlo.std,
                "p_go": monte_carlo.go_probability,
            }
        
        return STPFReport(
            kernel=kernel,
            variables=variables,
            variable_interpretations=interpretations,
            probability=probability,
            scenarios=scenarios,
            diagnosis=diagnosis,
            action_plan=action_plan,
            verdict=verdict,
            metadata=metadata,
        )
    
    def _generate_diagnosis(
        self,
        result: STPFResult,
        gates: Dict[str, float],
        numerator: Dict[str, float],
        denominator: Dict[str, float],
        multipliers: Dict[str, float],
    ) -> STPFDiagnosis:
        """진단 생성 (Why)"""
        
        # 변수 기여도 계산 (단순화: 가중치 * 점수)
        contributions = []
        
        # 분자 기여도
        num_weights = {"essence": 2.0, "capability": 1.2, "novelty": 1.1, "connection": 1.0, "proof": 1.3}
        for var, score in numerator.items():
            weight = num_weights.get(var, 1.0)
            contrib = score * weight
            contributions.append(VariableContribution(
                variable=var,
                score=score,
                weight=weight,
                contribution=contrib,
                interpretation=self.anchor_lookup.get_anchor(var, int(score)),
            ))
        
        # 분모 기여도 (음수)
        for var, score in denominator.items():
            contrib = -score * 0.5  # 분모는 감점
            contributions.append(VariableContribution(
                variable=var,
                score=score,
                weight=0.5,
                contribution=contrib,
            ))
        
        # 상위 3개 양의 기여자
        positive = sorted([c for c in contributions if c.contribution > 0], 
                         key=lambda x: x.contribution, reverse=True)[:3]
        
        # 최대 마찰 요인
        negative = sorted([c for c in contributions if c.contribution < 0],
                         key=lambda x: x.contribution)
        critical_friction = negative[0] if negative else None
        
        # Gate 이슈
        gate_issues = []
        for gate, score in gates.items():
            if score < 4:
                gate_issues.append(f"{gate} = {score} (Kill Switch)")
            elif score < 6:
                gate_issues.append(f"{gate} = {score} (경고)")
        
        return STPFDiagnosis(
            top_contributors=positive,
            critical_friction=critical_friction,
            gate_issues=gate_issues,
        )
    
    def _generate_action_plan(
        self,
        result: STPFResult,
        diagnosis: STPFDiagnosis,
    ) -> STPFActionPlan:
        """행동 계획 생성 (How)"""
        
        # result.how에서 추출
        how_list = result.how or []
        
        # 분자 올리기
        numerator_actions = []
        for action in how_list[:3]:
            numerator_actions.append(ActionItem(
                action=action,
                impact="점수 +50~100",
                priority="high",
            ))
        
        # 분모 줄이기
        denominator_actions = []
        if diagnosis.critical_friction:
            denominator_actions.append(ActionItem(
                action=f"{diagnosis.critical_friction.variable} 개선",
                impact="마찰 -20%",
                priority="high",
                target_variable=diagnosis.critical_friction.variable,
            ))
        
        # Gate 조치
        gate_actions = []
        for issue in diagnosis.gate_issues:
            gate_actions.append(ActionItem(
                action=f"Gate 해결: {issue.split('=')[0].strip()}",
                impact="Gate 통과 필수",
                priority="high" if "Kill" in issue else "medium",
            ))
        
        # 타임라인
        timeline = {
            "7일": [a.action for a in numerator_actions[:1]],
            "30일": [a.action for a in numerator_actions[1:]] + [a.action for a in denominator_actions],
            "90일": ["지속적 모니터링 및 최적화"],
        }
        
        return STPFActionPlan(
            numerator_actions=numerator_actions,
            denominator_actions=denominator_actions,
            gate_actions=gate_actions,
            timeline=timeline,
        )


# Singleton instance
report_generator = STPFReportGenerator()
