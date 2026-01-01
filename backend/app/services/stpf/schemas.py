"""
STPF v3.1 Pydantic Schemas

Defines the core data structures for STPF computation:
- STPFGates: Gate variables (Trust, Legality, Hygiene)
- STPFNumerator: Value variables (Essence, Capability, Novelty, Connection, Proof)
- STPFDenominator: Friction variables (Cost, Risk, Threat, Pressure, Time Lag, Uncertainty)
- STPFMultipliers: Boost variables (Scarcity, Network, Leverage)
- STPFResult: Final calculation result
"""
import math
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class STPFGates(BaseModel):
    """G: 시그모이드 임계값 통과 변수 (Gate)
    
    v3.1 하드 룰: Gate < 4 → 즉시 0점 (Kill Switch)
    """
    trust_gate: float = Field(ge=1, le=10, default=5.0, description="신뢰/일관성")
    legality_gate: float = Field(ge=1, le=10, default=5.0, description="법/규정 준수")
    hygiene_gate: float = Field(ge=1, le=10, default=5.0, description="기본 품질")
    
    def calculate_total(self, k: float = 1.5, x0: float = 6.0) -> float:
        """시그모이드 Gate 통과율
        
        k: 시그모이드 기울기
        x0: 시그모이드 중점
        """
        gates = [self.trust_gate, self.legality_gate, self.hygiene_gate]
        sigmoid = lambda x: 1 / (1 + math.exp(-k * (x - x0)))
        return math.prod(sigmoid(g) for g in gates)
    
    def is_passed(self) -> bool:
        """Gate 통과 여부 (하나라도 4 미만이면 실패)"""
        return min(self.trust_gate, self.legality_gate, self.hygiene_gate) >= 4


class STPFNumerator(BaseModel):
    """N: 가치 생성 변수 (분자)
    
    v3.1 Safe Math: Raw Score 1-10 사용 (Vanishing Gradient 방지)
    """
    essence: float = Field(ge=1, le=10, default=5.0, description="본질/핵심 가치 (E)")
    capability: float = Field(ge=1, le=10, default=5.0, description="실행 역량 (K)")
    novelty: float = Field(ge=1, le=10, default=5.0, description="차별성/의외성 (Nᵥ)")
    connection: float = Field(ge=1, le=10, default=5.0, description="전달력/공감 (Cₙ)")
    proof: float = Field(ge=1, le=10, default=5.0, description="증거/핸디캡 (Pᵣ)")
    
    # 지수 설정 (본질 강조)
    EXPONENTS: Dict[str, float] = {
        "essence": 2.0,      # 제곱 (핵심) - Rule 4
        "capability": 1.2,
        "novelty": 1.1,
        "connection": 1.0,
        "proof": 1.3,
    }
    
    def calculate_value(self) -> float:
        """V = E^α × K^β × Nᵥ^γ × Cₙ^δ × Pᵣ^ε
        
        v3.1 Safe Math: Raw Score 1-10 직접 사용 (정규화 X)
        - 최소값 1 → 절대 0 안됨 (Vanishing Gradient 방지)
        """
        return (
            (self.essence ** self.EXPONENTS["essence"]) *
            (self.capability ** self.EXPONENTS["capability"]) *
            (self.novelty ** self.EXPONENTS["novelty"]) *
            (self.connection ** self.EXPONENTS["connection"]) *
            (self.proof ** self.EXPONENTS["proof"])
        )


class STPFDenominator(BaseModel):
    """D: 저항 변수 (분모)
    
    v3.1 Safe Math: 1 + normalized * weight 패턴 (Division by Zero 방지)
    """
    cost: float = Field(ge=1, le=10, default=5.0, description="비용/복잡도 (C)")
    risk: float = Field(ge=1, le=10, default=5.0, description="실패 확률 (R)")
    threat: float = Field(ge=1, le=10, default=5.0, description="경쟁 강도 (T)")
    pressure: float = Field(ge=1, le=10, default=5.0, description="압박/피로도 (Pr)")
    time_lag: float = Field(ge=1, le=10, default=5.0, description="성과 지연 (L)")
    uncertainty: float = Field(ge=1, le=10, default=5.0, description="예측 불가성 (U)")
    
    EXPONENTS: Dict[str, float] = {
        "cost": 1.0,
        "risk": 1.2,
        "threat": 1.0,
        "pressure": 1.0,
        "time_lag": 0.9,
        "uncertainty": 1.1,
    }
    
    def calculate_friction(self) -> float:
        """F = Π(1 + w * norm(x))
        
        v3.1 Safe Math:
        - 저항=1(최소) → norm=0 → friction=1 (점수 보존)
        - 저항=10(최대) → norm=1 → friction 증가 (점수 하락)
        """
        def safe_friction_term(raw_score: float, weight: float) -> float:
            normalized = (raw_score - 1) / 9  # 1-10 → 0-1
            return 1 + normalized * weight
        
        return (
            safe_friction_term(self.cost, self.EXPONENTS["cost"]) *
            safe_friction_term(self.risk, self.EXPONENTS["risk"]) *
            safe_friction_term(self.threat, self.EXPONENTS["threat"]) *
            safe_friction_term(self.pressure, self.EXPONENTS["pressure"]) *
            safe_friction_term(self.time_lag, self.EXPONENTS["time_lag"]) *
            safe_friction_term(self.uncertainty, self.EXPONENTS["uncertainty"])
        )


class STPFMultipliers(BaseModel):
    """M: 승수 변수
    
    네트워크 효과는 지수적 성장 (Reed's Law)
    """
    scarcity: float = Field(ge=1, le=10, default=5.0, description="희소성 (S)")
    network: float = Field(ge=1, le=10, default=5.0, description="네트워크 효과 (NW)")
    leverage: float = Field(ge=1, le=10, default=5.0, description="레버리지 (LV)")
    
    # 추가 승수 (Week 2+)
    timing: float = Field(ge=1, le=10, default=5.0, description="타이밍 (TM)")
    platform_fit: float = Field(ge=1, le=10, default=5.0, description="플랫폼 적합도 (PF)")
    creator_authority: float = Field(ge=1, le=10, default=5.0, description="크리에이터 영향력 (CA)")
    
    def calculate_boost(self, beta: float = 0.5) -> float:
        """승수 계산 (네트워크는 지수적)
        
        beta: 네트워크 효과 강도 (0.5 = 보수적)
        """
        s = (self.scarcity - 1) / 9
        nw = (self.network - 1) / 9
        lv = (self.leverage - 1) / 9
        
        # 네트워크만 지수적 (Reed's Law) - Rule 6
        nw_boost = 1 + (2 ** (nw * 10 / 10) - 1) * beta
        
        return (1 + s) * nw_boost * (1 + lv)


class STPFResult(BaseModel):
    """STPF 계산 결과"""
    # 핵심 점수
    raw_score: float = Field(default=0.0, description="원시 점수")
    score_1000: int = Field(default=0, ge=0, le=1000, description="0-1000 스케일 점수")
    
    # Gate 결과
    gate_passed: bool = Field(default=False, description="Gate 통과 여부")
    gate_failure_reason: Optional[str] = Field(default=None, description="Gate 실패 사유")
    gate_total: Optional[float] = Field(default=None, description="Gate 통과율")
    
    # 구성 요소
    value: Optional[float] = Field(default=None, description="분자 (가치)")
    friction: Optional[float] = Field(default=None, description="분모 (마찰)")
    multiplier_boost: Optional[float] = Field(default=None, description="승수")
    entropy_boost: Optional[float] = Field(default=None, description="엔트로피 보너스")
    
    # 상세 정보
    components: Dict[str, Any] = Field(default_factory=dict, description="입력 변수 상세")
    
    # 의사결정
    go_nogo: Optional[str] = Field(default=None, description="GO / CONSIDER / NO-GO")
    confidence: Optional[float] = Field(default=None, description="신뢰도 0-1")
    
    # 추적
    why: Optional[str] = Field(default=None, description="점수 근거")
    how: Optional[List[str]] = Field(default=None, description="개선 방법")
    
    def get_decision(self) -> str:
        """Go/No-Go 결정"""
        if not self.gate_passed:
            return "NO-GO"
        if self.score_1000 >= 700:
            return "GO"
        if self.score_1000 >= 400:
            return "CONSIDER"
        return "NO-GO"
