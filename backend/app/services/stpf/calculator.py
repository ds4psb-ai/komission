"""
STPF v3.1 통합 점수 계산기

수학적 안전장치가 적용된 STPF 점수 계산기.

Formula:
    Score = G_total × (V / F^ω) × M_boost × EntropyBoost

v3.1 Safe Math:
- 분자: Raw Score 1-10 (Vanishing Gradient 방지)
- 분모: 1 + normalized × weight (Division by Zero 방지)
- Gate: < 4 = Kill Switch (즉시 0점)
"""
import math
import logging
from typing import Optional

from app.services.stpf.schemas import (
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
    STPFResult,
)
from app.services.stpf.invariant_rules import STPFInvariantRules

logger = logging.getLogger(__name__)


class STPFCalculator:
    """STPF v3.1 통합 점수 계산기 (수학적 안전장치 적용)"""
    
    VERSION = "3.1"
    
    def __init__(
        self,
        omega: float = 0.8,          # 분모 완화 지수
        gamma: float = 0.6,          # 엔트로피 보너스 계수
        reference_score: float = 500  # v3.1: 리스케일 기준값 (Unicorn ~5000 → 900+)
    ):
        self.omega = omega
        self.gamma = gamma
        self.reference_score = reference_score
        self.rules = STPFInvariantRules()
    
    def calculate(
        self,
        gates: STPFGates,
        numerator: STPFNumerator,
        denominator: STPFDenominator,
        multipliers: STPFMultipliers,
        expected_score: Optional[float] = None,
        actual_score: Optional[float] = None,
    ) -> STPFResult:
        """v3.1: 수학적 안정성이 보장된 통합 점수 계산
        
        Args:
            gates: Gate 변수 (Trust, Legality, Hygiene)
            numerator: 가치 변수 (Essence, Capability, Novelty, Connection, Proof)
            denominator: 저항 변수 (Cost, Risk, Threat, Pressure, Time Lag, Uncertainty)
            multipliers: 승수 변수 (Scarcity, Network, Leverage)
            expected_score: 기대 점수 (엔트로피 계산용)
            actual_score: 실제 점수 (엔트로피 계산용)
        
        Returns:
            STPFResult: 계산 결과
        """
        
        # 1. Gate 검증 (Kill Switch) - Rule 1
        gates_raw = [gates.trust_gate, gates.legality_gate, gates.hygiene_gate]
        if min(gates_raw) < 4:
            failed_gate = self._identify_failed_gate(gates)
            logger.info(f"STPF Gate Failed: {failed_gate}")
            return STPFResult(
                raw_score=0.0,
                score_1000=0,
                gate_passed=False,
                gate_failure_reason=failed_gate,
                go_nogo="NO-GO",
                why=f"Gate 실패: {failed_gate}",
                how=["해당 Gate 점수를 4 이상으로 개선 필요"],
            )
        
        # Gate Soft Factor (각 게이트/10의 곱)
        g_total = math.prod(g / 10.0 for g in gates_raw)
        
        # 2. 가치 (분자) - v3.1: Raw Score 사용으로 Vanishing Gradient 방지
        v = numerator.calculate_value()
        
        # 3. 마찰 (분모) - v3.1: (1 + normalized) 패턴으로 Division by Zero 방지
        f_total = denominator.calculate_friction()
        
        # 4. 승수 (네트워크는 5점 초과시 지수 부스트)
        m_boost = multipliers.calculate_boost()
        
        # 5. 엔트로피 보너스 (갭) - Rule 7
        entropy_boost = 1.0
        if expected_score is not None and actual_score is not None:
            entropy_boost = self.rules.apply_rule_7_gap_entropy(
                expected_score, 
                actual_score, 
                self.gamma
            )
        
        # 6. 최종 점수
        # Score = G × (V / F^ω) × M × Entropy
        raw_score = g_total * (v / (f_total ** self.omega)) * m_boost * entropy_boost
        
        # 7. 0~1000 리스케일 (v3.1: reference=500으로 Unicorn~5000 → 900+)
        # 공식: 1000 × raw / (raw + reference)
        score_1000 = int(1000 * raw_score / (raw_score + self.reference_score))
        score_1000 = min(1000, max(0, score_1000))  # 클램프
        
        # 8. Go/No-Go 결정
        if score_1000 >= 700:
            go_nogo = "GO"
            why = self._generate_go_reason(numerator, multipliers)
        elif score_1000 >= 400:
            go_nogo = "CONSIDER"
            why = self._generate_consider_reason(numerator, denominator)
        else:
            go_nogo = "NO-GO"
            why = self._generate_nogo_reason(numerator, denominator)
        
        how = self._generate_improvement_suggestions(
            gates, numerator, denominator, multipliers, score_1000
        )
        
        # 신뢰도 계산 (gate_total이 높을수록 신뢰도 높음)
        confidence = min(1.0, g_total * 1.2)  # 최대 1.0
        
        result = STPFResult(
            raw_score=raw_score,
            score_1000=score_1000,
            gate_passed=True,
            gate_total=g_total,
            value=v,
            friction=f_total,
            multiplier_boost=m_boost,
            entropy_boost=entropy_boost,
            components={
                "gates": gates.model_dump(),
                "numerator": numerator.model_dump(),
                "denominator": denominator.model_dump(),
                "multipliers": multipliers.model_dump(),
            },
            go_nogo=go_nogo,
            confidence=confidence,
            why=why,
            how=how,
        )
        
        logger.info(
            f"STPF Calculated: score={score_1000}, go_nogo={go_nogo}, "
            f"raw={raw_score:.2f}, v={v:.2f}, f={f_total:.2f}"
        )
        
        return result
    
    def _identify_failed_gate(self, gates: STPFGates) -> str:
        """실패한 Gate 식별"""
        if gates.trust_gate < 4:
            return "TRUST_GATE_FAILED (신뢰도 부족)"
        if gates.legality_gate < 4:
            return "LEGALITY_GATE_FAILED (규정 위반)"
        if gates.hygiene_gate < 4:
            return "HYGIENE_GATE_FAILED (기본 품질 미달)"
        return "UNKNOWN_GATE_FAILURE"
    
    def _generate_go_reason(
        self, 
        numerator: STPFNumerator, 
        multipliers: STPFMultipliers
    ) -> str:
        """GO 결정 근거 생성"""
        strengths = []
        if numerator.essence >= 7:
            strengths.append("강력한 본질/핵심 가치")
        if numerator.novelty >= 7:
            strengths.append("높은 차별성")
        if multipliers.network >= 7:
            strengths.append("강한 네트워크 효과")
        
        if strengths:
            return f"바이럴 성공 가능성 높음: {', '.join(strengths)}"
        return "전체적으로 우수한 점수"
    
    def _generate_consider_reason(
        self, 
        numerator: STPFNumerator, 
        denominator: STPFDenominator
    ) -> str:
        """CONSIDER 결정 근거 생성"""
        issues = []
        if denominator.risk >= 7:
            issues.append("높은 리스크")
        if denominator.uncertainty >= 7:
            issues.append("불확실성")
        if numerator.proof < 5:
            issues.append("증거 부족")
        
        if issues:
            return f"잠재력은 있으나 주의 필요: {', '.join(issues)}"
        return "중간 수준 - 추가 검토 권장"
    
    def _generate_nogo_reason(
        self, 
        numerator: STPFNumerator, 
        denominator: STPFDenominator
    ) -> str:
        """NO-GO 결정 근거 생성"""
        critical = []
        if numerator.essence < 4:
            critical.append("핵심 가치 부족")
        if denominator.risk >= 8:
            critical.append("과도한 리스크")
        if numerator.proof < 3:
            critical.append("증거 없음")
        
        if critical:
            return f"진행 불권장: {', '.join(critical)}"
        return "전체 점수 미달"
    
    def _generate_improvement_suggestions(
        self,
        gates: STPFGates,
        numerator: STPFNumerator,
        denominator: STPFDenominator,
        multipliers: STPFMultipliers,
        score: int,
    ) -> list:
        """개선 제안 생성 - Rule 11 (점수+Why+How)"""
        suggestions = []
        
        # 낮은 점수 변수 식별
        if numerator.essence < 6:
            suggestions.append("본질/핵심 가치 강화 (essence↑)")
        if numerator.proof < 5:
            suggestions.append("증거/사례 추가 (proof↑)")
        if denominator.risk >= 7:
            suggestions.append("리스크 완화 전략 수립 (risk↓)")
        if multipliers.network < 5:
            suggestions.append("네트워크 효과 활용 (network↑)")
        
        # 최소 1개 제안
        if not suggestions:
            if score < 700:
                suggestions.append("전체적인 품질 향상 권장")
            else:
                suggestions.append("현재 상태 유지")
        
        return suggestions[:3]  # 최대 3개


# Singleton instance
stpf_calculator = STPFCalculator()
