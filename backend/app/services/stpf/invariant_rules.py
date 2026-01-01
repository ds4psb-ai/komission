"""
STPF v3.1 불변 규칙 검증기

12가지 불변 규칙 (Invariant Rules)을 검증하고 적용하는 모듈.
이 규칙들은 STPF 계산의 수학적 일관성을 보장합니다.
"""
import math
from typing import Dict, Any, Optional, Tuple


class STPFInvariantRules:
    """STPF 12가지 불변 규칙 검증기
    
    모든 STPF 계산은 이 규칙을 따라야 합니다.
    규칙 위반 시 점수 신뢰도가 0으로 하락합니다.
    """
    
    RULES = [
        "gate_first",           # 1. Gate(입장권) 먼저
        "proof_or_max3",        # 2. Proof 없으면 최대 3점
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
    
    # ========== Rule 1: Gate First ==========
    
    def validate_rule_1_gate_first(self, gates: Dict[str, float]) -> Tuple[bool, Optional[str]]:
        """Rule 1: Gate 통과 여부가 모든 계산보다 선행
        
        v3.1 하드 룰: Gate < 4 → 즉시 0점 (1-10 스케일 기준)
        
        Returns:
            (passed, failure_reason)
        """
        for gate_name, gate_value in gates.items():
            if gate_value < 4:  # 1-10 스케일에서 4 미만 = Kill Switch
                return False, f"{gate_name} < 4 (Kill Switch)"
        return True, None
    
    # ========== Rule 2: Proof or Max 3 ==========
    
    def apply_rule_2_proof_or_max3(
        self, 
        variable_score: float, 
        has_evidence: bool
    ) -> float:
        """Rule 2: 비용 지불 없는 주장은 최대 3점
        
        v3.1 하드 룰: Evidence 없으면 해당 변수 최대 3점으로 제한
        """
        if not has_evidence and variable_score > 3:
            return 3.0
        return variable_score
    
    # ========== Rule 4: Essence Exponential ==========
    
    def apply_rule_4_essence_exponential(
        self, 
        essence: float, 
        alpha: float = 2.0
    ) -> float:
        """Rule 4: 본질은 제곱 이상으로 강제
        
        본질(Essence)은 가장 중요한 변수이므로 지수적 영향을 미침.
        """
        return essence ** alpha
    
    # ========== Rule 5: Scale Logarithmic ==========
    
    def apply_rule_5_scale_logarithmic(
        self, 
        scale: float, 
        base: float = 10.0
    ) -> float:
        """Rule 5: 규모/자본/스펙은 로그 체감
        
        대규모 리소스의 한계 효용 체감 반영.
        """
        normalized = (scale - 1) / 9  # 1-10 → 0-1
        return math.log(1 + normalized * base) / math.log(1 + base)
    
    # ========== Rule 6: Network Exponential ==========
    
    def apply_rule_6_network_exponential(
        self, 
        network: float, 
        beta: float = 0.5
    ) -> float:
        """Rule 6: 네트워크/커뮤니티는 지수적 성장
        
        Reed's Law: 네트워크 가치 = 2^N
        """
        g = (network - 1) / 9 * 10  # 0-10 스케일
        return 1 + (2 ** (g / 10) - 1) * beta
    
    # ========== Rule 7: Gap is Entropy ==========
    
    def apply_rule_7_gap_entropy(
        self, 
        expected: float, 
        actual: float, 
        gamma: float = 0.6
    ) -> float:
        """Rule 7: 긍정 갭만 엔트로피 보너스
        
        기대 이상의 성과(positive gap)에만 보너스 부여.
        """
        gap = max(0, actual - expected)
        if gap < 0.01:
            return 1.0
        return 1 + gamma * math.log(1 + gap)
    
    # ========== Rule 9: Outlier Patch ==========
    
    def apply_rule_9_outlier_patch(
        self, 
        score: float, 
        is_outlier: bool,
        outlier_weight: float = 0.5
    ) -> float:
        """Rule 9: Outlier는 패치로 처리
        
        극단적 아웃라이어는 점수에 덜 영향을 미치도록 조정.
        """
        if is_outlier:
            return score * outlier_weight
        return score
    
    # ========== Rule 11: Score + Why + How ==========
    
    def validate_rule_11_score_why_how(
        self, 
        score: float,
        why: Optional[str],
        how: Optional[list]
    ) -> bool:
        """Rule 11: 점수는 반드시 Why + How와 함께
        
        점수만 있고 설명이 없으면 규칙 위반.
        """
        return why is not None and how is not None and len(how) > 0
    
    # ========== Batch Validation ==========
    
    def validate_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """모든 규칙 일괄 검증
        
        Args:
            context: {
                "gates": {"trust": 6, "legality": 7, "hygiene": 8},
                "has_evidence": {"essence": True, "capability": False, ...},
                "expected_score": 500,
                "actual_score": 600,
                "why": "reason",
                "how": ["action1", "action2"],
            }
        
        Returns:
            {
                "all_passed": bool,
                "violations": [...],
                "adjustments": {...},
            }
        """
        violations = []
        adjustments = {}
        
        # Rule 1: Gate First
        gates = context.get("gates", {})
        gate_passed, gate_reason = self.validate_rule_1_gate_first(gates)
        if not gate_passed:
            violations.append(f"Rule 1 (Gate First): {gate_reason}")
        
        # Rule 11: Score + Why + How
        if not self.validate_rule_11_score_why_how(
            context.get("score", 0),
            context.get("why"),
            context.get("how")
        ):
            violations.append("Rule 11 (Score+Why+How): Missing explanation")
        
        return {
            "all_passed": len(violations) == 0,
            "violations": violations,
            "adjustments": adjustments,
        }
