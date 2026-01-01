"""
VDG → STPF Variable Mapper

VDGv4 분석 결과를 STPF 변수로 자동 변환하는 모듈.
실제 비디오 분석 데이터를 점수 계산에 연결합니다.
"""
import logging
from typing import Optional, Dict, Any

from app.schemas.vdg_v4 import VDGv4
from app.services.stpf.schemas import (
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
)

logger = logging.getLogger(__name__)


class VDGToSTPFMapper:
    """VDGv4 → STPF 변수 변환기"""
    
    VERSION = "1.0"
    
    def __init__(self):
        # 기본값 (VDG에서 추출 실패 시)
        self.defaults = {
            "gate": 5.0,
            "value": 5.0,
            "friction": 5.0,
            "multiplier": 5.0,
        }
    
    def map_to_stpf(self, vdg: VDGv4) -> Dict[str, Any]:
        """VDGv4를 STPF 변수로 변환
        
        Returns:
            {
                "gates": STPFGates,
                "numerator": STPFNumerator,
                "denominator": STPFDenominator,
                "multipliers": STPFMultipliers,
                "mapping_confidence": float,
                "unmapped_fields": list,
            }
        """
        unmapped = []
        confidence_factors = []
        
        # 1. Gates 매핑
        gates = self._map_gates(vdg, unmapped, confidence_factors)
        
        # 2. Numerator (가치) 매핑
        numerator = self._map_numerator(vdg, unmapped, confidence_factors)
        
        # 3. Denominator (마찰) 매핑
        denominator = self._map_denominator(vdg, unmapped, confidence_factors)
        
        # 4. Multipliers 매핑
        multipliers = self._map_multipliers(vdg, unmapped, confidence_factors)
        
        # 매핑 신뢰도 계산
        mapping_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        logger.info(
            f"VDG→STPF Mapping: confidence={mapping_confidence:.2f}, "
            f"unmapped={len(unmapped)}"
        )
        
        return {
            "gates": gates,
            "numerator": numerator,
            "denominator": denominator,
            "multipliers": multipliers,
            "mapping_confidence": mapping_confidence,
            "unmapped_fields": unmapped,
        }
    
    def _map_gates(
        self, 
        vdg: VDGv4, 
        unmapped: list, 
        confidence: list
    ) -> STPFGates:
        """Gate 변수 매핑"""
        
        # Trust Gate: proof_ready + evidence 품질
        trust = self.defaults["gate"]
        if vdg.meta.get("proof_ready"):
            trust = 8.0
            confidence.append(0.9)
        elif len(vdg.evidence_items) > 3:
            trust = 7.0
            confidence.append(0.7)
        else:
            trust = 5.0
            confidence.append(0.5)
            unmapped.append("trust_gate")
        
        # Legality Gate: 기본 통과 가정 (플랫폼 정책 위반 없으면)
        legality = 8.0  # 분석까지 왔으면 기본 통과
        confidence.append(0.8)
        
        # Hygiene Gate: 미디어 품질
        hygiene = self.defaults["gate"]
        if vdg.media and vdg.media.duration_ms:
            if vdg.media.duration_ms >= 5000:  # 5초 이상
                hygiene = 7.0
                confidence.append(0.8)
            else:
                hygiene = 5.0
                confidence.append(0.6)
        else:
            unmapped.append("hygiene_gate")
            confidence.append(0.4)
        
        return STPFGates(
            trust_gate=trust,
            legality_gate=legality,
            hygiene_gate=hygiene,
        )
    
    def _map_numerator(
        self, 
        vdg: VDGv4, 
        unmapped: list, 
        confidence: list
    ) -> STPFNumerator:
        """가치 변수 매핑"""
        
        # Essence: hook_genome.strength
        essence = self.defaults["value"]
        if vdg.semantic and vdg.semantic.hook_genome:
            strength = vdg.semantic.hook_genome.strength
            if strength is not None:
                # strength 0-1 → 1-10 스케일
                essence = max(1, min(10, strength * 9 + 1))
                confidence.append(0.9)
            else:
                unmapped.append("essence")
                confidence.append(0.5)
        else:
            unmapped.append("essence")
            confidence.append(0.4)
        
        # Capability: production quality (scenes, shots 기반)
        capability = self.defaults["value"]
        if vdg.semantic and vdg.semantic.scenes:
            scene_count = len(vdg.semantic.scenes)
            if scene_count >= 3:
                capability = 7.0
            elif scene_count >= 2:
                capability = 6.0
            else:
                capability = 5.0
            confidence.append(0.7)
        else:
            unmapped.append("capability")
            confidence.append(0.5)
        
        # Novelty: pattern 유형 기반
        novelty = self.defaults["value"]
        if vdg.semantic and vdg.semantic.hook_genome:
            pattern = vdg.semantic.hook_genome.pattern
            if pattern in ["subversion", "twist", "pattern_break"]:
                novelty = 8.0
            elif pattern in ["irony", "juxtaposition"]:
                novelty = 7.0
            elif pattern in ["problem_solution", "question"]:
                novelty = 6.0
            else:
                novelty = 5.0
            confidence.append(0.8)
        else:
            unmapped.append("novelty")
            confidence.append(0.5)
        
        # Connection: audience_reaction 기반
        connection = self.defaults["value"]
        if vdg.semantic and vdg.semantic.audience_reaction:
            if vdg.semantic.audience_reaction.best_comments:
                comment_count = len(vdg.semantic.audience_reaction.best_comments)
                connection = min(10, 4 + comment_count)
                confidence.append(0.8)
            else:
                unmapped.append("connection")
                confidence.append(0.5)
        else:
            unmapped.append("connection")
            confidence.append(0.5)
        
        # Proof: evidence_items 기반
        proof = self.defaults["value"]
        evidence_count = len(vdg.evidence_items)
        if evidence_count >= 5:
            proof = 8.0
            confidence.append(0.9)
        elif evidence_count >= 3:
            proof = 7.0
            confidence.append(0.7)
        elif evidence_count >= 1:
            proof = 5.0
            confidence.append(0.6)
        else:
            proof = 3.0  # Rule 2: 증거 없으면 최대 3점
            unmapped.append("proof")
            confidence.append(0.4)
        
        return STPFNumerator(
            essence=essence,
            capability=capability,
            novelty=novelty,
            connection=connection,
            proof=proof,
        )
    
    def _map_denominator(
        self, 
        vdg: VDGv4, 
        unmapped: list, 
        confidence: list
    ) -> STPFDenominator:
        """마찰 변수 매핑"""
        
        # Cost: production complexity (기본적으로 낮게 설정)
        cost = 4.0  # 숏폼은 일반적으로 저비용
        confidence.append(0.7)
        
        # Risk: 기본 낮음 (Gate 통과했으면)
        risk = 3.0
        confidence.append(0.7)
        
        # Threat: 경쟁 강도 (외부 데이터 필요, 기본값 사용)
        threat = 5.0
        unmapped.append("threat")
        confidence.append(0.5)
        
        # Pressure: trend fatigue (외부 데이터 필요)
        pressure = 5.0
        unmapped.append("pressure")
        confidence.append(0.5)
        
        # Time Lag: 기본 낮음 (숏폼은 빠른 결과)
        time_lag = 3.0
        confidence.append(0.7)
        
        # Uncertainty: multi_shot_analysis.ai_generation_likelihood 기반
        uncertainty = 5.0
        if vdg.multi_shot_analysis:
            ai_likelihood = vdg.multi_shot_analysis.ai_generation_likelihood
            # AI 생성 확률 높으면 불확실성 높음
            uncertainty = 3 + ai_likelihood * 7
            confidence.append(0.8)
        else:
            unmapped.append("uncertainty")
            confidence.append(0.5)
        
        return STPFDenominator(
            cost=cost,
            risk=risk,
            threat=threat,
            pressure=pressure,
            time_lag=time_lag,
            uncertainty=uncertainty,
        )
    
    def _map_multipliers(
        self, 
        vdg: VDGv4, 
        unmapped: list, 
        confidence: list
    ) -> STPFMultipliers:
        """승수 변수 매핑"""
        
        # Scarcity: unique format (pattern 기반)
        scarcity = 5.0
        if vdg.semantic and vdg.semantic.hook_genome:
            pattern = vdg.semantic.hook_genome.pattern
            if pattern in ["subversion", "pattern_break"]:
                scarcity = 7.0
                confidence.append(0.7)
            else:
                scarcity = 5.0
                confidence.append(0.6)
        else:
            unmapped.append("scarcity")
            confidence.append(0.5)
        
        # Network: viral_kicks 기반
        network = 5.0
        viral_kicks = vdg.provenance.get("viral_kicks", [])
        if viral_kicks:
            kick_count = len(viral_kicks)
            network = min(10, 4 + kick_count * 1.5)
            confidence.append(0.8)
        else:
            unmapped.append("network")
            confidence.append(0.5)
        
        # Leverage: capsule_brief 존재 여부 (재활용 가능성)
        leverage = 5.0
        if vdg.semantic and vdg.semantic.capsule_brief:
            if vdg.semantic.capsule_brief.shotlist:
                leverage = 7.0
                confidence.append(0.8)
            else:
                leverage = 5.0
                confidence.append(0.6)
        else:
            unmapped.append("leverage")
            confidence.append(0.5)
        
        return STPFMultipliers(
            scarcity=scarcity,
            network=network,
            leverage=leverage,
        )


# Singleton instance
vdg_to_stpf_mapper = VDGToSTPFMapper()
