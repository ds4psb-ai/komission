"""
STPF v3.1 Simulator

Tree of Thoughts (ToT) + Monte Carlo 시뮬레이션 엔진.

사용 케이스:
1. ToT: Worst/Base/Best 3가지 시나리오 분석
2. Monte Carlo: 1000회 랜덤 시뮬레이션으로 확률 분포 추정
"""
import math
import random
import statistics
import logging
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.stpf.schemas import (
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
    STPFResult,
)
from app.services.stpf.calculator import STPFCalculator

logger = logging.getLogger(__name__)


class STPFVariables(BaseModel):
    """STPF 변수 묶음"""
    gates: STPFGates = Field(default_factory=STPFGates)
    numerator: STPFNumerator = Field(default_factory=STPFNumerator)
    denominator: STPFDenominator = Field(default_factory=STPFDenominator)
    multipliers: STPFMultipliers = Field(default_factory=STPFMultipliers)


class ScenarioResult(BaseModel):
    """시나리오 결과"""
    scenario: str  # worst, base, best
    score_1000: int
    raw_score: float
    go_nogo: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)


class ToTResult(BaseModel):
    """Tree of Thoughts 결과"""
    worst: ScenarioResult
    base: ScenarioResult
    best: ScenarioResult
    weighted_score: float  # 가중 평균
    score_range: Tuple[int, int]  # (min, max)
    recommendation: str
    confidence: str  # HIGH, MEDIUM, LOW


class MonteCarloResult(BaseModel):
    """Monte Carlo 시뮬레이션 결과"""
    n_simulations: int
    mean: float
    median: float
    std: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    min_score: int
    max_score: int
    go_probability: float  # P(score >= 700)
    consider_probability: float  # P(400 <= score < 700)
    nogo_probability: float  # P(score < 400)
    distribution_summary: Dict[str, int] = Field(default_factory=dict)
    run_time_ms: float = 0.0


class STPFSimulator:
    """STPF 시뮬레이션 엔진
    
    불확실성 하에서 의사결정을 지원하는 시뮬레이션 도구.
    """
    
    VERSION = "1.0"
    
    def __init__(self):
        self.calculator = STPFCalculator()
        
        # ToT 가중치 (Worst:Base:Best)
        self.tot_weights = (0.3, 0.4, 0.3)
        
        # Monte Carlo 기본 설정
        self.default_n_simulations = 1000
        self.default_noise_std = 1.0  # 변수당 ±1점 노이즈
    
    def run_tot_simulation(
        self,
        base_variables: STPFVariables,
        variation: float = 0.2,  # ±20% 변동
    ) -> ToTResult:
        """Tree of Thoughts: 3가지 시나리오
        
        Args:
            base_variables: 기본 변수값
            variation: 변동 비율 (0.0~1.0)
        
        Returns:
            ToTResult: Worst/Base/Best 시나리오 결과
        """
        start_time = datetime.now()
        
        # 1. Worst Case: 분자↓, 분모↑
        worst_vars = self._apply_variation(base_variables, -variation, "pessimistic")
        worst_result = self._calculate(worst_vars)
        
        # 2. Base Case: 현재 추정
        base_result = self._calculate(base_variables)
        
        # 3. Best Case: 분자↑, 분모↓, Network↑
        best_vars = self._apply_variation(base_variables, variation, "optimistic")
        best_result = self._calculate(best_vars)
        
        # 가중 평균 점수
        weighted_score = (
            self.tot_weights[0] * worst_result.score_1000 +
            self.tot_weights[1] * base_result.score_1000 +
            self.tot_weights[2] * best_result.score_1000
        )
        
        # 점수 범위
        score_range = (worst_result.score_1000, best_result.score_1000)
        range_width = score_range[1] - score_range[0]
        
        # 신뢰도 (범위가 좁을수록 높음)
        if range_width < 100:
            confidence = "HIGH"
        elif range_width < 250:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # 추천
        if weighted_score >= 700:
            recommendation = "GO - 3가지 시나리오 모두 긍정적"
        elif weighted_score >= 400:
            if worst_result.score_1000 >= 400:
                recommendation = "CONSIDER - 최악의 경우에도 가능성 있음"
            else:
                recommendation = "CONSIDER - 리스크 관리 필요"
        else:
            recommendation = "NO-GO - 대부분의 시나리오에서 부정적"
        
        end_time = datetime.now()
        run_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"ToT Simulation: worst={worst_result.score_1000}, "
            f"base={base_result.score_1000}, best={best_result.score_1000}, "
            f"weighted={weighted_score:.0f}, {run_time_ms:.1f}ms"
        )
        
        return ToTResult(
            worst=ScenarioResult(
                scenario="worst",
                score_1000=worst_result.score_1000,
                raw_score=worst_result.raw_score,
                go_nogo=worst_result.go_nogo,
                variables=worst_vars.model_dump(),
            ),
            base=ScenarioResult(
                scenario="base",
                score_1000=base_result.score_1000,
                raw_score=base_result.raw_score,
                go_nogo=base_result.go_nogo,
                variables=base_variables.model_dump(),
            ),
            best=ScenarioResult(
                scenario="best",
                score_1000=best_result.score_1000,
                raw_score=best_result.raw_score,
                go_nogo=best_result.go_nogo,
                variables=best_vars.model_dump(),
            ),
            weighted_score=weighted_score,
            score_range=score_range,
            recommendation=recommendation,
            confidence=confidence,
        )
    
    def run_monte_carlo(
        self,
        base_variables: STPFVariables,
        n_simulations: int = 1000,
        noise_std: float = 1.0,
        uncertainty: Optional[Dict[str, float]] = None,
    ) -> MonteCarloResult:
        """Monte Carlo 시뮬레이션
        
        Args:
            base_variables: 기본 변수값
            n_simulations: 시뮬레이션 횟수
            noise_std: 기본 노이즈 표준편차
            uncertainty: 변수별 불확실성 (변수명 → 표준편차)
        
        Returns:
            MonteCarloResult: 확률 분포 및 통계
        """
        start_time = datetime.now()
        
        uncertainty = uncertainty or {}
        scores: List[int] = []
        
        for _ in range(n_simulations):
            # 각 변수에 노이즈 추가
            noisy_vars = self._add_noise(base_variables, noise_std, uncertainty)
            result = self._calculate(noisy_vars)
            scores.append(result.score_1000)
        
        # 통계 계산
        scores_sorted = sorted(scores)
        mean = statistics.mean(scores)
        median = statistics.median(scores)
        std = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # 백분위수
        def percentile(data: List[int], p: float) -> float:
            k = (len(data) - 1) * (p / 100)
            f = int(k)
            c = f + 1 if f < len(data) - 1 else f
            return data[f] + (k - f) * (data[c] - data[f])
        
        p10 = percentile(scores_sorted, 10)
        p25 = percentile(scores_sorted, 25)
        p75 = percentile(scores_sorted, 75)
        p90 = percentile(scores_sorted, 90)
        
        # 의사결정 확률
        go_count = sum(1 for s in scores if s >= 700)
        consider_count = sum(1 for s in scores if 400 <= s < 700)
        nogo_count = sum(1 for s in scores if s < 400)
        
        go_prob = go_count / n_simulations
        consider_prob = consider_count / n_simulations
        nogo_prob = nogo_count / n_simulations
        
        # 분포 요약 (100점 단위)
        distribution = {}
        for bucket in range(0, 1100, 100):
            bucket_key = f"{bucket}-{bucket+99}"
            distribution[bucket_key] = sum(1 for s in scores if bucket <= s < bucket + 100)
        
        end_time = datetime.now()
        run_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"Monte Carlo: n={n_simulations}, mean={mean:.0f}, "
            f"std={std:.0f}, P(GO)={go_prob:.2%}, {run_time_ms:.1f}ms"
        )
        
        return MonteCarloResult(
            n_simulations=n_simulations,
            mean=mean,
            median=median,
            std=std,
            percentile_10=p10,
            percentile_25=p25,
            percentile_75=p75,
            percentile_90=p90,
            min_score=min(scores),
            max_score=max(scores),
            go_probability=go_prob,
            consider_probability=consider_prob,
            nogo_probability=nogo_prob,
            distribution_summary=distribution,
            run_time_ms=run_time_ms,
        )
    
    def _calculate(self, variables: STPFVariables) -> STPFResult:
        """STPF 점수 계산"""
        return self.calculator.calculate(
            gates=variables.gates,
            numerator=variables.numerator,
            denominator=variables.denominator,
            multipliers=variables.multipliers,
        )
    
    def _apply_variation(
        self,
        base: STPFVariables,
        variation: float,
        mode: str = "symmetric",
    ) -> STPFVariables:
        """변동 적용
        
        Args:
            base: 기본 변수
            variation: 변동 비율 (-1.0 ~ 1.0)
            mode: symmetric, optimistic, pessimistic
        """
        def adjust(value: float, is_positive: bool, var: float) -> float:
            """값 조정 (1-10 범위 유지)"""
            if mode == "pessimistic":
                # 분자는 감소, 분모는 증가
                if is_positive:
                    new_val = value * (1 - abs(var))
                else:
                    new_val = value * (1 + abs(var))
            elif mode == "optimistic":
                # 분자는 증가, 분모는 감소
                if is_positive:
                    new_val = value * (1 + abs(var))
                else:
                    new_val = value * (1 - abs(var))
            else:
                # symmetric
                new_val = value * (1 + var)
            
            return max(1.0, min(10.0, new_val))
        
        # Gates
        new_gates = STPFGates(
            trust_gate=adjust(base.gates.trust_gate, True, variation),
            legality_gate=base.gates.legality_gate,  # 법적 준수는 변동 없음
            hygiene_gate=adjust(base.gates.hygiene_gate, True, variation * 0.5),
        )
        
        # Numerator (가치 - 양의 변수)
        new_num = STPFNumerator(
            essence=adjust(base.numerator.essence, True, variation),
            capability=adjust(base.numerator.capability, True, variation * 0.5),
            novelty=adjust(base.numerator.novelty, True, variation),
            connection=adjust(base.numerator.connection, True, variation * 0.7),
            proof=adjust(base.numerator.proof, True, variation * 0.3),  # 증거는 덜 변동
        )
        
        # Denominator (마찰 - 음의 변수)
        new_denom = STPFDenominator(
            cost=adjust(base.denominator.cost, False, variation * 0.5),
            risk=adjust(base.denominator.risk, False, variation),
            threat=adjust(base.denominator.threat, False, variation * 0.7),
            pressure=adjust(base.denominator.pressure, False, variation * 0.5),
            time_lag=adjust(base.denominator.time_lag, False, variation * 0.3),
            uncertainty=adjust(base.denominator.uncertainty, False, variation),
        )
        
        # Multipliers
        new_mult = STPFMultipliers(
            scarcity=adjust(base.multipliers.scarcity, True, variation * 0.5),
            network=adjust(base.multipliers.network, True, variation * 1.3),  # 네트워크 효과 강조
            leverage=adjust(base.multipliers.leverage, True, variation * 0.5),
        )
        
        return STPFVariables(
            gates=new_gates,
            numerator=new_num,
            denominator=new_denom,
            multipliers=new_mult,
        )
    
    def _add_noise(
        self,
        base: STPFVariables,
        noise_std: float,
        uncertainty: Dict[str, float],
    ) -> STPFVariables:
        """변수에 가우시안 노이즈 추가"""
        def noisy(value: float, name: str) -> float:
            std = uncertainty.get(name, noise_std)
            noise = random.gauss(0, std)
            return max(1.0, min(10.0, value + noise))
        
        new_gates = STPFGates(
            trust_gate=noisy(base.gates.trust_gate, "trust_gate"),
            legality_gate=base.gates.legality_gate,  # 법적 준수는 노이즈 없음
            hygiene_gate=noisy(base.gates.hygiene_gate, "hygiene_gate"),
        )
        
        new_num = STPFNumerator(
            essence=noisy(base.numerator.essence, "essence"),
            capability=noisy(base.numerator.capability, "capability"),
            novelty=noisy(base.numerator.novelty, "novelty"),
            connection=noisy(base.numerator.connection, "connection"),
            proof=noisy(base.numerator.proof, "proof"),
        )
        
        new_denom = STPFDenominator(
            cost=noisy(base.denominator.cost, "cost"),
            risk=noisy(base.denominator.risk, "risk"),
            threat=noisy(base.denominator.threat, "threat"),
            pressure=noisy(base.denominator.pressure, "pressure"),
            time_lag=noisy(base.denominator.time_lag, "time_lag"),
            uncertainty=noisy(base.denominator.uncertainty, "uncertainty_var"),
        )
        
        new_mult = STPFMultipliers(
            scarcity=noisy(base.multipliers.scarcity, "scarcity"),
            network=noisy(base.multipliers.network, "network"),
            leverage=noisy(base.multipliers.leverage, "leverage"),
        )
        
        return STPFVariables(
            gates=new_gates,
            numerator=new_num,
            denominator=new_denom,
            multipliers=new_mult,
        )


# Singleton instance
stpf_simulator = STPFSimulator()
