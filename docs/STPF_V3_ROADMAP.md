# 🚀 STPF v3.1 × Komission VDG
## Single Truth Pattern Formalization — Complete Implementation Roadmap

**작성**: 2026-01-01  
**버전**: STPF v3.1 + VDG v4.1  
**목표**: 바이럴 패턴의 단일 진실을 연산 가능한 동적 엔진으로 구현

---

## ⚠️ v3.1 Critical Fixes: 수학적 안전장치

> **v3.0 → v3.1 업그레이드 이유**: AI 시스템이 STPF를 연산할 때 발생하는 치명적 수학 버그 수정

### 🛑 Bug 1: Division by Zero (무한대 발산)

**문제**: 분모 변수(Cost 등)가 최적(1점)일 때, 정규화 값이 0 → 분모가 0 → 점수 무한대

```python
# ❌ v3.0 문제 코드
normalized = (cost - 1) / 9  # cost=1 → normalized=0
friction = normalized ** 1.0  # friction=0
score = value / friction  # 💥 Division by Zero!
```

**해결책 (v3.1)**: 분모는 **1에서 시작하여 저항만큼 증가**

```python
# ✅ v3.1 수정 코드
def safe_friction(raw_score: float, weight: float = 1.0) -> float:
    """저항 변수의 안전한 정규화 (1 + normalized * weight)"""
    normalized = (raw_score - 1) / 9  # 1-10 → 0-1
    return 1 + normalized * weight  # 항상 >= 1
```

### 🛑 Bug 2: Vanishing Gradient (본질 소멸)

**문제**: 0-1 소수를 제곱하면 작아짐 (0.8² = 0.64) → 본질이 좋을수록 점수가 낮아지는 역설

```python
# ❌ v3.0 문제 코드
normalized = (essence - 1) / 9  # essence=10 → normalized=1.0, essence=8 → 0.78
value = normalized ** 2.0  # 0.78² = 0.61 😱 본질 8점이 오히려 낮아짐
```

**해결책 (v3.1)**: 분자는 **Raw Score(1-10)** 그대로 사용, **Log-Probability** 적용

```python
# ✅ v3.1 수정 코드: Raw Score 사용 + Log-Sum
def calculate_value_v31(numerator: STPFNumerator) -> float:
    """v3.1: Raw Score 사용으로 본질 압도 보장"""
    return (
        (numerator.essence ** 2.0) *      # 10² = 100
        (numerator.capability ** 1.2) *   # 10^1.2 = 15.8
        (numerator.novelty ** 1.1) *
        (numerator.connection ** 1.0) *
        (numerator.proof ** 1.3)
    )
    # essence=10이면 100, essence=5이면 25 → 압도적 본질이 승리

def calculate_log_value(numerator: STPFNumerator) -> float:
    """Log-Probability 방식: 곱셈 → 덧셈 변환"""
    import math
    log_value = (
        2.0 * math.log(numerator.essence) +
        1.2 * math.log(numerator.capability) +
        1.1 * math.log(numerator.novelty) +
        1.0 * math.log(numerator.connection) +
        1.3 * math.log(numerator.proof)
    )
    return math.exp(log_value)  # 수치 안정성 보장
```

### 📊 v3.0 vs v3.1 비교

| 항목 | v3.0 | v3.1 |
|------|------|------|
| 분모 정규화 | `(x-1)/9` | `1 + (x-1)/9 * weight` |
| 분자 스케일 | 0-1 정규화 | **Raw 1-10 사용** |
| 곱셈 안정성 | 소수 곱 → 소멸 | **Log-Sum 변환** |
| Score 리스케일 | `1000 * s/(s+1)` | `1000 * s/(s+500)` |
| Kelly 안전장치 | 기본 | **Edge Check + Fractional** |

---

## 0. 핵심 약속: 단일 진실(Single Truth)의 정의

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SINGLE TRUTH = 6가지 정합                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  1) 제1원리       2) 변수 온톨로지    3) 수식/로직                          │
│     (불변 목적)      (분류 체계)        (연산 규칙)                         │
│         │               │                  │                                │
│         ▼               ▼                  ▼                                │
│  4) 측정 척도     5) 검증/튜닝       6) 의사결정                            │
│     (1~10 기준)      (시뮬레이션)       (행동/베팅)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 기존 "곱하고 나누는 공식"의 한계

| 한계 | 문제 | STPF 해결 |
|------|------|-----------|
| 정적 점수 | 한 번 채점 후 고정 | 베이지안 동적 갱신 |
| 선형 가정 | 모든 변수 동일 취급 | 지수/로그/시그모이드 함수 |
| 결과만 제시 | "왜"와 "어떻게" 없음 | Why + How 필수 출력 |
| 극단값 무시 | Outlier 설명 불가 | Reality Distortion Patch |

### STPF 출력 표준

```python
class STPFOutput(BaseModel):
    """STPF 표준 출력"""
    
    # 1. 정량 점수
    raw_score: float
    score_1000: float  # 0~1000 리스케일
    
    # 2. 확률 (베이지안)
    p_success: float  # P(Success|Evidence)
    confidence_interval: Tuple[float, float]
    
    # 3. 시나리오
    scenarios: Dict[str, ScenarioResult]  # worst/base/best
    
    # 4. 자원 배분
    kelly_fraction: float
    recommended_effort_percent: float
    go_nogo_signal: Literal["GO", "MODERATE", "CAUTION", "NO_GO"]
```

---

## 1. STPF 불변 규칙 12개 × VDG 매핑

### 1.1 규칙 정합성 테이블

| # | STPF 불변 규칙 | VDG 현재 구현 | 상태 | 구현 위치 |
|---|---------------|--------------|------|-----------|
| 1 | **Gate 먼저** | `quality_gate.validate()` | ✅ | `quality_gate.py` |
| 2 | **Proof 없으면 0점** | `evidence_comment_ranks` | ✅ | `viral_kicks` |
| 3 | **분자=가치, 분모=마찰** | `invariant/variable` 분리 | ✅ | `CapsuleBrief` |
| 4 | **본질은 지수** | 미구현 | ❌ | - |
| 5 | **규모/스펙은 로그** | 미구현 | ❌ | - |
| 6 | **네트워크는 지수** | `viral_kicks.mechanism` | ⚠️ | 부분 |
| 7 | **Gap=Entropy** | 미구현 | ❌ | - |
| 8 | **베이지안 갱신** | `PatternCalibrator` | ⚠️ | 이동평균만 |
| 9 | **Outlier=Patch** | 미구현 | ❌ | - |
| 10 | **시뮬레이션 필수** | 미구현 | ❌ | - |
| 11 | **점수+Why+How** | `capsule_brief` | ⚠️ | 부분 |
| 12 | **스케일부터 튜닝** | 미구현 | ❌ | - |

### 1.2 불변 규칙 구현 코드

```python
# services/stpf/invariant_rules.py

class STPFInvariantRules:
    """STPF 12가지 불변 규칙 검증기"""
    
    RULES = [
        "gate_first",           # 1. Gate(입장권) 먼저
        "proof_or_zero",        # 2. Proof 없으면 0점
        "numerator_denominator", # 3. 분자=가치, 분모=마찰
        "essence_exponential",  # 4. 본질은 지수
        "scale_logarithmic",    # 5. 규모/스펙은 로그
        "network_exponential",  # 6. 네트워크는 지수
        "gap_is_entropy",       # 7. Gap=Entropy
        "bayesian_update",      # 8. 베이지안 갱신
        "outlier_patch",        # 9. Outlier=Patch
        "simulation_required",  # 10. 시뮬레이션 필수
        "score_why_how",        # 11. 점수+Why+How
        "scale_before_weight",  # 12. 스케일부터 튜닝
    ]
    
    def validate_rule_1_gate_first(self, gates: Dict[str, float]) -> bool:
        """Rule 1: Gate 통과 여부가 모든 계산보다 선행"""
        for gate_name, gate_value in gates.items():
            if gate_value < 0.5:  # 시그모이드 임계점
                return False
        return True
    
    def validate_rule_2_proof_or_zero(self, proof_score: float, claim_count: int) -> float:
        """Rule 2: 비용 지불 없는 주장은 0점"""
        if proof_score < 0.3 and claim_count > 0:
            return 0.0
        return proof_score
    
    def apply_rule_4_essence_exponential(self, essence: float, alpha: float = 2.0) -> float:
        """Rule 4: 본질은 제곱 이상으로 강제"""
        normalized = (essence - 1) / 9  # 1-10 → 0-1
        return normalized ** alpha
    
    def apply_rule_5_scale_logarithmic(self, scale: float, base: float = 10.0) -> float:
        """Rule 5: 규모/자본/스펙은 로그 체감"""
        normalized = (scale - 1) / 9
        return math.log(1 + normalized * base) / math.log(1 + base)
    
    def apply_rule_6_network_exponential(self, network: float, beta: float = 0.5) -> float:
        """Rule 6: 네트워크/커뮤니티는 지수적 성장"""
        g = (network - 1) / 9 * 10  # 0-10 스케일
        return 1 + (2 ** (g / 10) - 1) * beta
    
    def apply_rule_7_gap_entropy(self, expected: float, actual: float, gamma: float = 0.6) -> float:
        """Rule 7: 긍정 갭만 엔트로피 보너스"""
        gap = max(0, actual - expected)
        if gap < 0.01:
            return 1.0
        return 1 + gamma * math.log(1 + gap)
```

---

## 2. Phase 1: 제1원리 — Kernel 정의

### 2.1 Komission VDG Kernel

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VDG KERNEL (제1원리)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  "바이럴 성공은 시청자의 불확실성(스크롤 멈춤)을 유리하게 통제하면서  │
│   순가치(훅 강도 - 인지 마찰)를 누적하고, 그 패턴이 복제 가능할 때    │
│   발생한다."                                                         │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  Objective: 시청자 retention 최대화 + 복제 성공률 최대화             │
│  Agent: 크리에이터 (영상 제작자)                                     │
│  Environment: 플랫폼 알고리즘 + 경쟁 콘텐츠 + 시청자 피로도          │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Scale Invariance 체크

| 스케일 | 적용 | 검증 |
|--------|------|------|
| n=1 (개인 시청) | 한 명의 시청자가 스크롤 멈춤 | hook_genome.strength |
| n=1K (바이럴 시작) | 1000명이 공유 | viral_kicks |
| n=1M (대규모) | 백만 조회 패턴 | pattern_recurrence |

### 2.3 Free Energy 체크

```python
# 제1원리: Free Energy Principle 적용
class FreeEnergyChecker:
    """시청자 놀라움(Surprise) 최소화 검증"""
    
    def check_entropy_reduction(self, vdg: VDGv4) -> Dict[str, Any]:
        """훅이 시청자 불확실성을 줄이는지 검증"""
        
        hook = vdg.semantic.hook_genome
        
        # 1. 호기심 갭 생성 (불확실성 증가) → 시청 유도
        curiosity_created = hook.virality_analysis.curiosity_gap is not None
        
        # 2. 페이오프 제공 (불확실성 해소) → 만족
        payoff_delivered = any(
            s.narrative_role in ["payoff", "reveal", "punch"]
            for s in vdg.semantic.scenes
        )
        
        # 3. 패턴 예측 가능성 (다음 시청 불확실성 감소)
        pattern_predictable = hook.pattern != "other"
        
        return {
            "curiosity_created": curiosity_created,
            "payoff_delivered": payoff_delivered,
            "pattern_predictable": pattern_predictable,
            "free_energy_optimized": all([
                curiosity_created, payoff_delivered, pattern_predictable
            ])
        }
```

---

## 3. Phase 2: 변수 아키텍처 — STPF 온톨로지

### 3.1 VDG 변수 온톨로지 매핑

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STPF VARIABLE ONTOLOGY                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  G (Gates)          임계값 통과 여부 (시그모이드)                    │
│  ├── Trust Gate     → quality_gate.proof_ready                      │
│  ├── Legality Gate  → platform_policy_check                         │
│  └── Hygiene Gate   → min_duration, min_resolution                  │
│                                                                      │
│  N (Numerator)      가치 생성 변수 (분자)                            │
│  ├── Essence (E)    → hook_genome.strength ^ 2.0                    │
│  ├── Capability (K) → production_quality                            │
│  ├── Novelty (Nᵥ)   → pattern_novelty_score                         │
│  ├── Connection (Cₙ)→ audience_reaction.engagement                  │
│  └── Proof (Pᵣ)     → evidence_comment_ranks                        │
│                                                                      │
│  D (Denominator)    저항 변수 (분모)                                 │
│  ├── Cost (C)       → production_complexity                         │
│  ├── Risk (R)       → platform_ban_risk                             │
│  ├── Threat (T)     → competition_intensity                         │
│  ├── Pressure (Pr)  → trend_fatigue                                 │
│  ├── Time Lag (L)   → time_to_viral                                 │
│  └── Uncertainty (U)→ confidence_variance                           │
│                                                                      │
│  M (Multipliers)    승수 변수                                        │
│  ├── Scarcity (S)   → unique_format_score                           │
│  ├── Network (NW)   → viral_kicks.mechanism ^ exp                   │
│  └── Leverage (LV)  → template_reusability                          │
│                                                                      │
│  Evd (Evidence)     증거 변수 (핸디캡)                               │
│  └── Proof Weight   → like_count, comment_rank                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 스키마 확장

```python
# schemas/stpf_variables.py

class STPFGates(BaseModel):
    """G: 시그모이드 임계값 통과 변수"""
    trust_gate: float = Field(ge=1, le=10, description="신뢰/일관성")
    legality_gate: float = Field(ge=1, le=10, description="법/규정 준수")
    hygiene_gate: float = Field(ge=1, le=10, description="기본 품질")
    
    def calculate_total(self, k: float = 1.5, x0: float = 6.0) -> float:
        """시그모이드 Gate 통과율"""
        gates = [self.trust_gate, self.legality_gate, self.hygiene_gate]
        sigmoid = lambda x: 1 / (1 + math.exp(-k * (x - x0)))
        return math.prod(sigmoid(g) for g in gates)


class STPFNumerator(BaseModel):
    """N: 가치 생성 변수 (분자)"""
    essence: float = Field(ge=1, le=10, description="본질/핵심 가치")
    capability: float = Field(ge=1, le=10, description="실행 역량")
    novelty: float = Field(ge=1, le=10, description="차별성/의외성")
    connection: float = Field(ge=1, le=10, description="전달력/공감")
    proof: float = Field(ge=1, le=10, description="증거/핸디캡")
    
    # 지수 설정 (본질 강조)
    EXPONENTS = {
        "essence": 2.0,      # 제곱 (핵심)
        "capability": 1.2,
        "novelty": 1.1,
        "connection": 1.0,
        "proof": 1.3,
    }
    
    def calculate_value(self) -> float:
        """V = E^α × K^β × Nᵥ^γ × Cₙ^δ × Pᵣ^ε"""
        normalized = {
            "essence": (self.essence - 1) / 9,
            "capability": (self.capability - 1) / 9,
            "novelty": (self.novelty - 1) / 9,
            "connection": (self.connection - 1) / 9,
            "proof": (self.proof - 1) / 9,
        }
        
        return math.prod(
            (normalized[k] + 0.01) ** v  # +0.01 for zero prevention
            for k, v in self.EXPONENTS.items()
        )


class STPFDenominator(BaseModel):
    """D: 저항 변수 (분모)"""
    cost: float = Field(ge=1, le=10, description="비용/복잡도")
    risk: float = Field(ge=1, le=10, description="실패 확률")
    threat: float = Field(ge=1, le=10, description="경쟁 강도")
    pressure: float = Field(ge=1, le=10, description="압박/피로도")
    time_lag: float = Field(ge=1, le=10, description="성과 지연")
    uncertainty: float = Field(ge=1, le=10, description="예측 불가성")
    
    EXPONENTS = {
        "cost": 1.0,
        "risk": 1.2,
        "threat": 1.0,
        "pressure": 1.0,
        "time_lag": 0.9,
        "uncertainty": 1.1,
    }
    
    def calculate_friction(self) -> float:
        """F = C^κ × R^λ × T^μ × Pr^ν × L^τ × U^υ"""
        normalized = {
            "cost": (self.cost - 1) / 9,
            "risk": (self.risk - 1) / 9,
            "threat": (self.threat - 1) / 9,
            "pressure": (self.pressure - 1) / 9,
            "time_lag": (self.time_lag - 1) / 9,
            "uncertainty": (self.uncertainty - 1) / 9,
        }
        
        return math.prod(
            (normalized[k] + 0.01) ** v
            for k, v in self.EXPONENTS.items()
        )


class STPFMultipliers(BaseModel):
    """M: 승수 변수"""
    scarcity: float = Field(ge=1, le=10, description="희소성")
    network: float = Field(ge=1, le=10, description="네트워크 효과")
    leverage: float = Field(ge=1, le=10, description="레버리지")
    
    def calculate_boost(self, beta: float = 0.5) -> float:
        """승수 계산 (네트워크는 지수적)"""
        s = (self.scarcity - 1) / 9
        nw = (self.network - 1) / 9
        lv = (self.leverage - 1) / 9
        
        # 네트워크만 지수적 (Reed's Law)
        nw_boost = 1 + (2 ** (nw * 10 / 10) - 1) * beta
        
        return (1 + s) * nw_boost * (1 + lv)
```

---

## 4. Phase 3: 관계의 수식화 — STPF 통합 공식

### 4.1 핵심 통합 공식

$$Score = G_{total} \cdot \frac{V}{F^{\omega}} \cdot M_{boost} \cdot EntropyBoost$$

| 항 | 의미 | VDG 매핑 |
|---|------|----------|
| $G_{total}$ | Gate 통과율 | `proof_ready` |
| $V$ | 가치 (분자) | `hook_genome` + `viral_kicks` |
| $F^\omega$ | 마찰 (분모) | `complexity` + `risk` |
| $M_{boost}$ | 승수 | `network_effect` |
| $EntropyBoost$ | 갭 보너스 | `expected - actual` |

### 4.2 통합 계산기 구현

```python
# services/stpf/calculator.py

class STPFCalculatorV31:
    """STPF v3.1 통합 점수 계산기 (수학적 안전장치 적용)"""
    
    def __init__(self):
        self.omega = 0.8  # 분모 완화 지수
        self.gamma = 0.6  # 엔트로피 보너스 계수
        self.reference_score = 500  # v3.1: 리스케일 기준값 (Unicorn ~5000 → 900+)
    
    def calculate(
        self,
        gates: STPFGates,
        numerator: STPFNumerator,
        denominator: STPFDenominator,
        multipliers: STPFMultipliers,
        expected_score: Optional[float] = None,
        actual_score: Optional[float] = None,
    ) -> STPFResult:
        """v3.1: 수학적 안정성이 보장된 통합 점수 계산"""
        
        # 1. Gate 통과율 (Kill Switch)
        gates_raw = [gates.trust_gate, gates.legality_gate, gates.hygiene_gate]
        if min(gates_raw) < 4:
            return STPFResult(
                raw_score=0.0,
                score_1000=0,
                gate_passed=False,
                gate_failure_reason=f"Gate Failed: {self._identify_failed_gate(gates)}",
            )
        
        # Gate Soft Factor (각 게이트/10의 곱)
        g_total = math.prod(g / 10.0 for g in gates_raw)
        
        # 2. 가치 (분자) - v3.1: Raw Score 사용으로 Vanishing Gradient 방지
        v = self._calculate_value_v31(numerator)
        
        # 3. 마찰 (분모) - v3.1: (1 + normalized) 패턴으로 Division by Zero 방지
        f_total = self._calculate_friction_v31(denominator)
        
        # 4. 승수 (네트워크는 5점 초과시 지수 부스트)
        m_boost = self._calculate_multipliers_v31(multipliers)
        
        # 5. 엔트로피 보너스 (갭)
        entropy_boost = 1.0
        if expected_score is not None and actual_score is not None:
            gap = max(0, actual_score - expected_score)
            entropy_boost = 1 + math.log1p(gap) * 0.5  # log1p for stability
        
        # 6. 최종 점수
        raw_score = g_total * (v / (f_total ** self.omega)) * m_boost * entropy_boost
        
        # 7. 0~1000 리스케일 (v3.1: reference=500으로 Unicorn~5000 → 900+)
        score_1000 = int(1000 * raw_score / (raw_score + self.reference_score))
        
        return STPFResult(
            raw_score=raw_score,
            score_1000=score_1000,
            gate_passed=True,
            gate_total=g_total,
            value=v,
            friction=f,
            multiplier_boost=m_boost,
            entropy_boost=entropy_boost,
            components={
                "gates": gates.model_dump(),
                "numerator": numerator.model_dump(),
                "denominator": denominator.model_dump(),
                "multipliers": multipliers.model_dump(),
            }
        )
    
    def _identify_failed_gate(self, gates: STPFGates) -> str:
        """실패한 Gate 식별"""
        if gates.trust_gate < 6:
            return "TRUST_GATE_FAILED"
        if gates.legality_gate < 6:
            return "LEGALITY_GATE_FAILED"
        if gates.hygiene_gate < 6:
            return "HYGIENE_GATE_FAILED"
        return "UNKNOWN"
```

---

## 5. Phase 3.7: 베이지안 갱신 — 동적 진실

### 5.1 현재 vs 목표

| 구분 | 현재 (PatternCalibrator) | 목표 (BayesianUpdater) |
|------|-------------------------|------------------------|
| 방식 | 이동 평균 | 정밀 베이지안 |
| 수식 | `avg = (old*n + new) / (n+1)` | `P(S|E) = P(E|S)*P(S) / P(E)` |
| 출력 | 신뢰도 점수 | 확률 + 신뢰구간 |

### 5.2 정밀 베이지안 구현

```python
# services/stpf/bayesian_updater.py

class BayesianPatternUpdater:
    """정밀 베이지안 갱신기"""
    
    def __init__(self):
        self.prior_database: Dict[str, BayesianPrior] = {}
    
    def update_posterior(
        self,
        pattern_id: str,
        evidence: PatternEvidence,
    ) -> BayesianPosterior:
        """
        베이지안 정리: P(S|E) = P(E|S) × P(S) / P(E)
        
        - P(S): Prior (기존 성공 확률)
        - P(E|S): Likelihood (성공했을 때 이 증거가 나올 확률)
        - P(E): Evidence (이 증거가 나올 전체 확률)
        """
        
        # 1. Prior 로드 (없으면 기본값)
        prior = self.prior_database.get(
            pattern_id, 
            BayesianPrior(p_success=0.5, sample_count=0)
        )
        
        # 2. Likelihood 계산
        if evidence.outcome == "success":
            # 성공했을 때 이 패턴이 나올 확률
            likelihood = self._calculate_success_likelihood(evidence)
        else:
            # 실패했을 때 이 패턴이 나올 확률
            likelihood = 1 - self._calculate_success_likelihood(evidence)
        
        # 3. Evidence Probability (전체 데이터에서 추정)
        p_evidence = self._estimate_evidence_probability(pattern_id, evidence)
        
        # 4. Posterior 계산
        odds_prior = prior.p_success / (1 - prior.p_success + 1e-10)
        likelihood_ratio = likelihood / (1 - likelihood + 1e-10)
        odds_posterior = odds_prior * likelihood_ratio
        
        p_posterior = odds_posterior / (1 + odds_posterior)
        
        # 5. 신뢰구간 (Wilson Score Interval)
        n = prior.sample_count + 1
        z = 1.96  # 95% CI
        
        ci_low = (p_posterior + z*z/(2*n) - z*math.sqrt((p_posterior*(1-p_posterior)+z*z/(4*n))/n)) / (1 + z*z/n)
        ci_high = (p_posterior + z*z/(2*n) + z*math.sqrt((p_posterior*(1-p_posterior)+z*z/(4*n))/n)) / (1 + z*z/n)
        
        # 6. Prior 업데이트
        self.prior_database[pattern_id] = BayesianPrior(
            p_success=p_posterior,
            sample_count=n,
        )
        
        return BayesianPosterior(
            pattern_id=pattern_id,
            p_success=p_posterior,
            confidence_interval=(max(0, ci_low), min(1, ci_high)),
            sample_count=n,
            likelihood=likelihood,
            prior=prior.p_success,
        )
    
    def _calculate_success_likelihood(self, evidence: PatternEvidence) -> float:
        """성공 시 해당 증거 발생 확률"""
        base_likelihood = 0.7  # 기본 신뢰도
        
        # Proof 강도에 따른 조정
        if evidence.proof_strength > 7:
            base_likelihood += 0.2
        elif evidence.proof_strength < 4:
            base_likelihood -= 0.3
        
        # 비용 지불 증거에 따른 조정 (Handicap)
        if evidence.cost_paid > 0:
            base_likelihood += min(0.1, evidence.cost_paid / 100)
        
        return min(0.95, max(0.1, base_likelihood))
```

---

## 6. Phase 3.8: Reality Distortion Patches

### 6.1 패치 목록

```python
# services/stpf/reality_patches.py

class RealityDistortionPatches:
    """일반 공식으로 설명 안 되는 Outlier 처리"""
    
    def apply_all_patches(self, score: float, context: PatchContext) -> float:
        """모든 패치 순차 적용"""
        score = self.patch_a_capital_override(score, context)
        score = self.patch_b_overconfidence_penalty(score, context)
        score = self.patch_c_trust_collapse(score, context)
        score = self.patch_d_network_winner_takes_all(score, context)
        return score
    
    def patch_a_capital_override(self, score: float, ctx: PatchContext) -> float:
        """
        Patch A: 규모의 경제 보정
        본질 낮아도 자본이 압도적이면 생존
        """
        if ctx.essence <= 3 and ctx.capital > 1_000_000:
            boost = math.log10(1 + ctx.capital)
            return score * (1 + boost * 0.1)
        return score
    
    def patch_b_overconfidence_penalty(self, score: float, ctx: PatchContext) -> float:
        """
        Patch B: 자신감의 역설
        Proof 없는 자신감은 감점
        """
        eta = 0.3
        if ctx.proof < 5 and ctx.confidence_level > 7:
            penalty = ctx.confidence_level * eta * 0.1
            return score * (1 - penalty)
        return score
    
    def patch_c_trust_collapse(self, score: float, ctx: PatchContext) -> float:
        """
        Patch C: 신뢰 붕괴
        Trust Gate 하락 시 급락
        """
        if ctx.trust < 6:
            return score * 0.2
        return score
    
    def patch_d_network_winner_takes_all(self, score: float, ctx: PatchContext) -> float:
        """
        Patch D: 네트워크 승자독식
        임계점 돌파 시 가속
        """
        if ctx.network > 8 and ctx.retention > 7:
            return score * 1.3
        return score
```

---

## 7. Phase 4: 정량 척도 — 1~10 앵커

### 7.1 VDG 도메인 앵커

```python
# schemas/stpf_anchors.py

VDG_SCALE_ANCHORS = {
    "essence": {
        "domain": "바이럴 영상",
        "description": "시청자의 스크롤을 멈추는 핵심 힘",
        "anchors": {
            1: "훅 없음, 즉시 스킵",
            3: "약한 호기심, 3초 시청",
            5: "평균 훅, 끝까지 시청 50%",
            7: "강한 훅, 댓글 유도",
            10: "압도적 훅, 저장+공유+루프",
        }
    },
    "proof": {
        "domain": "바이럴 증거",
        "description": "패턴 성공의 비용 지불 증거",
        "anchors": {
            1: "증거 없음, 추측만",
            3: "1회 성공, 우연 가능",
            5: "3회 이상 반복, 일관성 있음",
            7: "다수 크리에이터 재현, 외부 검증",
            10: "플랫폼 공식 사례, 장기 누적 증거",
        }
    },
    "network": {
        "domain": "네트워크 효과",
        "description": "사람이 사람을 데려오는 구조",
        "anchors": {
            1: "개인 의존, 확산 없음",
            3: "일부 공유, 선형 성장",
            5: "추천 루프 존재, 중간 바이럴",
            7: "커뮤니티 자생, 지수 성장 시작",
            10: "밈화, 리믹스 폭발, 플랫폼 트렌드",
        }
    },
    "threat": {
        "domain": "경쟁 위협",
        "description": "동일 패턴 경쟁 강도 (낮을수록 좋음)",
        "anchors": {
            1: "블루오션, 경쟁자 없음",
            3: "틈새 시장, 경쟁 약함",
            5: "일반 경쟁, 차별화 필요",
            7: "레드오션, 대형 크리에이터 다수",
            10: "포화 상태, 진입 무의미",
        }
    },
}
```

---

## 8. Phase 5: 시뮬레이션 — ToT + 몬테카를로

### 8.1 3분기 시나리오 (Tree of Thoughts)

```python
# services/stpf/simulation.py

class STPFSimulator:
    """STPF 시뮬레이션 엔진"""
    
    def run_tot_simulation(
        self,
        base_variables: STPFVariables,
        variation: float = 0.2,
    ) -> Dict[str, STPFResult]:
        """Tree of Thoughts: 3가지 시나리오"""
        
        calculator = STPFCalculator()
        
        # Worst Case: 분자↓, 분모↑, Gate↓
        worst = self._apply_variation(base_variables, -variation)
        worst_result = calculator.calculate(
            gates=worst.gates,
            numerator=worst.numerator,
            denominator=STPFDenominator(
                **{k: min(10, v * (1 + variation)) 
                   for k, v in worst.denominator.model_dump().items()}
            ),
            multipliers=worst.multipliers,
        )
        
        # Base Case: 현재 추정
        base_result = calculator.calculate(**base_variables.model_dump())
        
        # Best Case: 분자↑, 분모↓, Network↑
        best = self._apply_variation(base_variables, variation)
        best.multipliers.network = min(10, best.multipliers.network * 1.3)
        best_result = calculator.calculate(**best.model_dump())
        
        return {
            "worst": worst_result,
            "base": base_result,
            "best": best_result,
            "weighted_average": self._weighted_avg(
                worst_result, base_result, best_result,
                weights=(0.3, 0.4, 0.3)
            ),
        }
    
    def run_monte_carlo(
        self,
        base_variables: STPFVariables,
        n_simulations: int = 1000,
        uncertainty: Dict[str, float] = None,
    ) -> MonteCarloResult:
        """몬테카를로 시뮬레이션"""
        
        uncertainty = uncertainty or {"default": 1.0}  # ±1점
        calculator = STPFCalculator()
        scores = []
        
        for _ in range(n_simulations):
            # 각 변수에 노이즈 추가
            noisy_vars = self._add_noise(base_variables, uncertainty)
            result = calculator.calculate(**noisy_vars.model_dump())
            scores.append(result.score_1000)
        
        return MonteCarloResult(
            mean=statistics.mean(scores),
            median=statistics.median(scores),
            std=statistics.stdev(scores),
            percentile_10=np.percentile(scores, 10),
            percentile_90=np.percentile(scores, 90),
            distribution=scores,
        )
```

---

## 9. Phase 6: 의사결정 — Kelly Criterion

### 9.1 완전한 Kelly 구현

```python
# services/stpf/kelly_criterion.py

class KellyDecisionEngine:
    """켈리 기준 의사결정 엔진"""
    
    def calculate_optimal_bet(
        self,
        p_success: float,          # 베이지안 성공 확률
        upside: float,             # 성공 시 이익 (예: 조회수 배수)
        downside: float,           # 실패 시 손실 (예: 시간 투자)
        confidence: float = 1.0,   # 확률 추정 신뢰도
    ) -> KellyDecision:
        """
        Kelly Criterion: f* = (bp - q) / b
        
        - b: 배당률 (upside / downside)
        - p: 성공 확률
        - q: 실패 확률 (1 - p)
        """
        
        b = upside / (downside + 1e-10)
        p = p_success
        q = 1 - p
        
        # 기본 켈리
        kelly_fraction = (b * p - q) / b
        
        # Fractional Kelly (안전 버전)
        safe_kelly = kelly_fraction * confidence * 0.5
        
        # 기대값
        expected_value = p * upside - q * downside
        
        # 신호 결정
        if kelly_fraction < 0:
            signal = "NO_GO"
            reason = "기대값 음수: 진입 금지"
            action = "손절 또는 포기"
        elif safe_kelly < 0.1:
            signal = "CAUTION"
            reason = "낮은 기대값: 최소 투자만"
            action = "실험적 시도만"
        elif safe_kelly < 0.25:
            signal = "MODERATE"
            reason = "적정 기대값: 중간 투자"
            action = "표준 리소스 배분"
        else:
            signal = "GO"
            reason = "높은 기대값: 적극 투자"
            action = "집중 투자 권장"
        
        return KellyDecision(
            raw_kelly_fraction=max(0, kelly_fraction),
            safe_kelly_fraction=max(0, safe_kelly),
            recommended_effort_percent=round(max(0, safe_kelly) * 100, 1),
            expected_value=expected_value,
            signal=signal,
            reason=reason,
            action=action,
            inputs={
                "p_success": p,
                "upside": upside,
                "downside": downside,
                "odds_ratio": b,
            }
        )
```

### 9.2 등급 구간

```python
# schemas/stpf_grades.py

STPF_GRADE_BRACKETS = {
    (800, 1001): {
        "grade": "S (Unicorn)",
        "label": "압도적 바이럴 잠재력",
        "action": "즉시 확장, 템플릿화, 다중 플랫폼 배포",
        "kelly_hint": "40%+ 리소스 투입",
    },
    (500, 800): {
        "grade": "A (Cash Cow)",
        "label": "안정적 성과 예상",
        "action": "리텐션 최적화, 변주 확장",
        "kelly_hint": "20~40% 리소스 투입",
    },
    (250, 500): {
        "grade": "B (So-so)",
        "label": "차별화 필요",
        "action": "갭(novelty) 강화 또는 피벗",
        "kelly_hint": "10~20% 리소스 투입",
    },
    (0, 250): {
        "grade": "C (Fail)",
        "label": "진입 비추천",
        "action": "손절 또는 Gate/Proof 재구축",
        "kelly_hint": "투자 금지",
    },
}
```

---

## 10. VDG 도메인 어댑터

### 10.1 바이럴 영상 어댑터

```python
# adapters/viral_video_adapter.py

class ViralVideoAdapter:
    """VDG → STPF 변수 매핑"""
    
    def convert_vdg_to_stpf(self, vdg: VDGv4) -> STPFVariables:
        """VDG v4를 STPF 변수로 변환"""
        
        hook = vdg.semantic.hook_genome
        scenes = vdg.semantic.scenes
        kicks = vdg.provenance.get("viral_kicks", [])
        
        return STPFVariables(
            gates=STPFGates(
                trust_gate=10 if vdg.meta.get("proof_ready") else 4,
                legality_gate=8,  # 기본 통과 가정
                hygiene_gate=self._calculate_hygiene(vdg),
            ),
            numerator=STPFNumerator(
                essence=self._hook_to_essence(hook),
                capability=self._calculate_production_quality(vdg),
                novelty=self._calculate_novelty(hook, kicks),
                connection=self._calculate_connection(vdg),
                proof=self._calculate_proof(kicks, vdg),
            ),
            denominator=STPFDenominator(
                cost=self._estimate_production_cost(vdg),
                risk=self._estimate_platform_risk(vdg),
                threat=self._estimate_competition(vdg),
                pressure=self._estimate_trend_fatigue(vdg),
                time_lag=3,  # 기본값 (바이럴은 빠름)
                uncertainty=self._calculate_confidence_variance(vdg),
            ),
            multipliers=STPFMultipliers(
                scarcity=self._calculate_format_uniqueness(vdg),
                network=self._calculate_network_potential(kicks),
                leverage=self._calculate_template_reusability(vdg),
            ),
        )
    
    def _hook_to_essence(self, hook: HookGenome) -> float:
        """훅 강도 → Essence 점수"""
        base = hook.strength * 10  # 0-1 → 0-10
        
        # 패턴이 명확하면 보너스
        if hook.pattern not in ["other", None]:
            base += 0.5
        
        return min(10, max(1, base))
```

---

## 11. 최종 출력 규격

### 11.1 STPF 표준 리포트

```python
# schemas/stpf_report.py

class STPFReport(BaseModel):
    """STPF 최종 산출물"""
    
    # A. Kernel
    kernel: STPFKernel
    
    # B. Variable Table
    variables: STPFVariables
    variable_facts: Dict[str, List[str]]  # 각 변수별 근거
    
    # C. Scores
    raw_score: float
    score_1000: int
    p_success: float
    confidence_interval: Tuple[float, float]
    scenarios: Dict[str, ScenarioResult]
    
    # D. Why (Diagnosis)
    top_contributors: List[VariableContribution]  # 상위 3개
    critical_friction: VariableContribution       # 치명적 분모 1개
    
    # E. How (Action Plan)
    numerator_actions: List[ActionItem]   # 분자 올리기 3개
    denominator_actions: List[ActionItem] # 분모 줄이기 3개
    gate_actions: List[ActionItem]        # Gate 통과 2개
    timeline: Dict[str, List[ActionItem]] # 7일/30일/90일
    
    # F. Verdict
    grade: str                    # S/A/B/C
    grade_bracket: Tuple[int, int]
    recommended_action: str
    kelly_fraction: float
    recommended_effort_percent: float
    signal: Literal["GO", "MODERATE", "CAUTION", "NO_GO"]
```

---

## 12. 구현 로드맵

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STPF v3.1 × VDG 구현 로드맵                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Week 1                                                              │
│  ├── [ ] STPFInvariantRules 클래스                                 │
│  ├── [ ] STPF 스키마 (Gates, Numerator, Denominator, Multipliers)  │
│  └── [ ] STPFCalculator 기본 버전                                  │
│                                                                      │
│  Week 2                                                              │
│  ├── [ ] BayesianPatternUpdater (PatternCalibrator 교체)            │
│  ├── [ ] RealityDistortionPatches                                  │
│  └── [ ] VDG 앵커 정의 (1~10 스케일)                                │
│                                                                      │
│  Week 3                                                              │
│  ├── [ ] STPFSimulator (ToT + Monte Carlo)                         │
│  ├── [ ] KellyDecisionEngine                                       │
│  └── [ ] ViralVideoAdapter (VDG → STPF 변환)                       │
│                                                                      │
│  Week 4                                                              │
│  ├── [ ] STPFReport 생성기                                         │
│  ├── [ ] API 엔드포인트 (/stpf/analyze)                            │
│  └── [ ] 프론트엔드 Go/No-Go 표시                                  │
│                                                                      │
│  Week 5+                                                             │
│  ├── [ ] NotebookLM 다중 깊이 연동                                  │
│  ├── [ ] 실시간 코칭 STPF 갱신                                     │
│  └── [ ] A/B 테스트 및 가중치 튜닝                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 한 줄 요약

> **"STPF v3.1은 VDG의 훅/킥/패턴을 12가지 불변 규칙과 베이지안 갱신으로 감싸,
> '점수'를 넘어 '확률 + 기대값 + 최적 베팅 비율'을 출력하는 단일 진실 엔진이다."**

---

## 13. Best Practices (2024 Research)

> 웹 리서치 결과를 반영한 산업 표준 권장사항

### 13.1 Kelly Criterion + ML 강화

| Best Practice | 적용 | STPF 구현 |
|---------------|------|-----------|
| **Fractional Kelly** | 추정 오차 대비 0.5x~0.33x | `safe_kelly = kelly * 0.5` |
| **Ensemble Learning** | 다중 모델 예측 평균 | `BayesianPatternUpdater` |
| **Reinforcement Learning** | 동적 환경 적응 | `CoachingOutcome` 피드백 루프 |
| **Transaction Costs** | 실제 비용 반영 | `Denominator.cost` 변수 |
| **Risk-Constrained** | Drawdown 제한 | `Gate.trust_gate < 4` → Kill |

```python
# 개선: Confidence-Adjusted Kelly
def calculate_safe_kelly(p: float, b: float, confidence: float) -> float:
    """신뢰도 낮으면 베팅 축소"""
    raw_kelly = (b * p - (1 - p)) / b
    
    # Fractional Kelly (0.5x) + Confidence 조정
    safe_kelly = raw_kelly * 0.5 * confidence
    
    # 음수면 NO_GO
    return max(0, safe_kelly)
```

### 13.2 MCP (Model Context Protocol) 통합 — 2025 Latest

> **MCP Spec June 2025** 기준 최신 기능 반영

| 구성요소 | 설명 | STPF 적용 |
|----------|------|-----------|
| **Tools** | AI 실행 가능 액션 | `/stpf/analyze`, `/stpf/simulate` |
| **Resources** | 구조화된 데이터 | `VDG v4.1`, `PatternConfidence` |
| **Prompts** | 사전 정의 템플릿 | `STPF Master Prompt v3.1` |
| **Elicitation** ⭐ | 서버→사용자 추가 입력 요청 | 변수 확인, 시나리오 선택 |

#### 2025 신규 기능

| 기능 | 설명 | 적용 시점 |
|------|------|-----------|
| **Streamable HTTP** | SSE 대체 전송 프로토콜 | Week 5+ |
| **Elicitation** | Multi-step 워크플로우 (사용자 입력 대기) | Week 5+ |
| **OAuth 2.1 + PKCE** | 필수 보안 (Dynamic Client Registration) | Week 5+ |
| **Server Discovery** | 서버 자동 발견 (11월 2025 예정) | TBD |

#### 보안 요구사항 (Enterprise)

```python
# OAuth 2.1 PKCE 필수 (RFC 7636)
MCP_SECURITY_CONFIG = {
    "oauth_version": "2.1",
    "pkce_required": True,                    # 필수
    "token_audience_validation": True,        # RFC 8707
    "dynamic_client_registration": True,      # RFC 7591
    "https_only": True,
    "token_expiry_seconds": 3600,
    "refresh_token_rotation": True,
}
```

```python
# MCP 서버 구조
@mcp_server.tool()
async def stpf_analyze(vdg_id: str) -> STPFReport:
    """STPF v3.1 분석 실행"""
    vdg = await get_vdg(vdg_id)
    variables = ViralVideoAdapter().convert_vdg_to_stpf(vdg)
    return STPFCalculatorV31().calculate(**variables.model_dump())

@mcp_server.resource("stpf://patterns/{pattern_id}")
async def get_pattern_confidence(pattern_id: str) -> Dict:
    """패턴 신뢰도 리소스"""
    return await bayesian_updater.get_posterior(pattern_id)

# Elicitation 예시 (2025 신규)
@mcp_server.tool()
async def stpf_interactive_analyze(vdg_id: str, ctx: MCPContext) -> STPFReport:
    """Elicitation을 통한 대화형 STPF 분석"""
    vdg = await get_vdg(vdg_id)
    
    # 사용자에게 시나리오 선택 요청 (Elicitation)
    scenario = await ctx.elicit(
        message="어떤 시나리오로 분석할까요?",
        options=["worst", "base", "best"]
    )
    
    return STPFSimulator().run_scenario(vdg, scenario)
```

### 13.3 NotebookLM 파이프라인

| 단계 | Best Practice | 구현 |
|------|---------------|------|
| **Ontology** | 명확한 엔티티/관계 정의 | `parent_node_id`, `genealogy_depth` |
| **Ingestion** | 자동화된 청크 업로드 | `upload_source_pack_to_notebook.py` |
| **Quality** | 소스 품질이 출력 품질 | Outlier 큐레이션 |
| **Extraction** | Mind Map → Knowledge Graph | `DistillRun` 스키마 |

```python
# NotebookLM 다중 깊이 연동
class NotebookLMPipeline:
    """Parent-Kids 계층 자동 확장"""
    
    async def ingest_cluster(self, cluster_id: str, max_depth: int = 3):
        """클러스터의 모든 노드를 NotebookLM에 업로드"""
        nodes = await self._get_nodes_by_depth(cluster_id, max_depth)
        
        for depth in range(max_depth + 1):
            depth_nodes = [n for n in nodes if n.genealogy_depth == depth]
            
            # 각 깊이별 소스팩 생성
            source_pack = self._create_source_pack(depth_nodes)
            
            # NotebookLM API로 업로드
            await self._upload_to_notebook(source_pack, f"depth_{depth}")
    
    async def extract_invariants(self, notebook_id: str) -> List[str]:
        """NotebookLM Mind Map에서 불변요소 추출"""
        mind_map = await self._get_mind_map(notebook_id)
        return self._parse_invariants(mind_map)
```

### 13.4 수치 안정성 체크리스트

- [x] **Division by Zero**: `1 + normalized * weight` 패턴
- [x] **Vanishing Gradient**: Raw Score 1-10 사용
- [x] **Log Underflow**: `math.log1p()` 사용
- [x] **Probability Bounds**: `min(0.95, max(0.1, p))` 강제
- [x] **Kelly Edge Check**: `bp - q > 0` 사전 검증
- [ ] **Monte Carlo Variance**: 1000회 이상 시뮬레이션
