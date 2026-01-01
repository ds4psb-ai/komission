"""
STPF Service Layer (Week 2 Hardened)

비즈니스 로직을 캡슐화한 서비스 레이어.
Week 2: Bayesian + Reality Patches + Anchors 통합.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.schemas.vdg_v4 import VDGv4
from app.services.stpf.schemas import (
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
    STPFResult,
)
from app.services.stpf.calculator import STPFCalculator
from app.services.stpf.vdg_mapper import VDGToSTPFMapper
from app.services.stpf.invariant_rules import STPFInvariantRules

# Week 2 imports
from app.services.stpf.bayesian_updater import (
    BayesianPatternUpdater,
    PatternEvidence,
    BayesianPosterior,
)
from app.services.stpf.reality_patches import (
    RealityDistortionPatches,
    PatchContext,
    PatchResult,
)
from app.services.stpf.anchors import VDG_SCALE_ANCHORS, VDGAnchorLookup

logger = logging.getLogger(__name__)


class STPFAnalysisResponse:
    """STPF 분석 응답 (Week 2 확장)"""
    def __init__(
        self,
        result: STPFResult,
        mapping_info: Optional[Dict[str, Any]] = None,
        validation_info: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        # Week 2 additions
        bayesian_info: Optional[Dict[str, Any]] = None,
        patch_info: Optional[Dict[str, Any]] = None,
        anchor_interpretations: Optional[Dict[str, Any]] = None,
    ):
        self.result = result
        self.mapping_info = mapping_info or {}
        self.validation_info = validation_info or {}
        self.metadata = metadata or {}
        # Week 2
        self.bayesian_info = bayesian_info or {}
        self.patch_info = patch_info or {}
        self.anchor_interpretations = anchor_interpretations or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result.model_dump(),
            "mapping_info": self.mapping_info,
            "validation_info": self.validation_info,
            "metadata": self.metadata,
            "bayesian_info": self.bayesian_info,
            "patch_info": self.patch_info,
            "anchor_interpretations": self.anchor_interpretations,
        }


class STPFService:
    """STPF 서비스 레이어 (Week 2 Hardened)"""
    
    VERSION = "2.0"  # Week 2
    
    def __init__(self):
        self.calculator = STPFCalculator()
        self.mapper = VDGToSTPFMapper()
        self.rules = STPFInvariantRules()
        # Week 2 modules
        self.bayesian = BayesianPatternUpdater()
        self.patches = RealityDistortionPatches()
        self.anchor_lookup = VDGAnchorLookup()
    
    async def analyze_vdg(
        self,
        vdg: VDGv4,
        expected_score: Optional[float] = None,
        actual_score: Optional[float] = None,
        apply_patches: bool = True,
        update_bayesian: bool = True,
    ) -> STPFAnalysisResponse:
        """VDG에서 STPF 분석 수행 (Week 2 통합)
        
        Args:
            vdg: VDGv4 분석 결과
            expected_score: 기대 점수 (엔트로피 보너스용)
            actual_score: 실제 점수 (엔트로피 보너스용)
            apply_patches: Reality Patches 적용 여부
            update_bayesian: 베이지안 갱신 여부
        """
        start_time = datetime.now()
        
        # 1. VDG → STPF 변수 매핑
        mapping = self.mapper.map_to_stpf(vdg)
        
        gates = mapping["gates"]
        numerator = mapping["numerator"]
        denominator = mapping["denominator"]
        multipliers = mapping["multipliers"]
        
        # 2. STPF 점수 계산 (기본)
        result = self.calculator.calculate(
            gates=gates,
            numerator=numerator,
            denominator=denominator,
            multipliers=multipliers,
            expected_score=expected_score,
            actual_score=actual_score,
        )
        
        # 3. Reality Patches 적용
        patch_info = {}
        if apply_patches and result.gate_passed:
            patch_ctx = PatchContext(
                essence=numerator.essence,
                proof=numerator.proof,
                trust=gates.trust_gate,
                network=multipliers.network,
                capital=0,  # VDG에서 추출 어려움
                confidence_level=5.0,
                retention=0.5,  # 기본값
                content_id=vdg.content_id,
            )
            patch_result = self.patches.apply_all_patches(
                result.raw_score, patch_ctx
            )
            patch_info = {
                "original_raw_score": patch_result.original_score,
                "patched_raw_score": patch_result.patched_score,
                "patches_applied": patch_result.patches_applied,
                "total_adjustment": patch_result.total_adjustment,
            }
            
            # 패치된 점수로 재계산 (raw_score만 교체)
            if patch_result.patches_applied:
                # 리스케일
                patched_score_1000 = int(
                    1000 * patch_result.patched_score / 
                    (patch_result.patched_score + self.calculator.reference_score)
                )
                result.raw_score = patch_result.patched_score
                result.score_1000 = min(1000, max(0, patched_score_1000))
        
        # 4. 베이지안 갱신
        bayesian_info = {}
        if update_bayesian and vdg.semantic and vdg.semantic.hook_genome:
            pattern_id = vdg.semantic.hook_genome.pattern or "unknown"
            
            # 증거 생성
            evidence = PatternEvidence(
                pattern_id=pattern_id,
                outcome="success" if result.score_1000 >= 500 else "failure",
                proof_strength=numerator.proof,
                cost_paid=0,
                content_id=vdg.content_id,
            )
            
            posterior = self.bayesian.update_posterior(pattern_id, evidence)
            bayesian_info = {
                "pattern_id": pattern_id,
                "p_success": posterior.p_success,
                "confidence_interval": posterior.confidence_interval,
                "sample_count": posterior.sample_count,
                "confidence_level": posterior.get_confidence_level(),
                "prior": posterior.prior,
            }
        
        # 5. 앵커 해석
        anchor_interpretations = self._get_anchor_interpretations(
            gates, numerator, denominator, multipliers
        )
        
        # 6. 규칙 검증
        validation = self.rules.validate_all({
            "gates": {
                "trust": gates.trust_gate,
                "legality": gates.legality_gate,
                "hygiene": gates.hygiene_gate,
            },
            "score": result.score_1000,
            "why": result.why,
            "how": result.how,
        })
        
        # 7. 메타데이터
        end_time = datetime.now()
        metadata = {
            "stpf_version": STPFCalculator.VERSION,
            "service_version": self.VERSION,
            "mapper_version": VDGToSTPFMapper.VERSION,
            "content_id": vdg.content_id,
            "vdg_version": vdg.vdg_version,
            "analysis_time_ms": (end_time - start_time).total_seconds() * 1000,
            "analyzed_at": end_time.isoformat(),
            "features": {
                "patches_enabled": apply_patches,
                "bayesian_enabled": update_bayesian,
            },
        }
        
        logger.info(
            f"STPF Analysis Complete: content_id={vdg.content_id}, "
            f"score={result.score_1000}, go_nogo={result.go_nogo}, "
            f"patches={len(patch_info.get('patches_applied', []))}"
        )
        
        return STPFAnalysisResponse(
            result=result,
            mapping_info={
                "confidence": mapping["mapping_confidence"],
                "unmapped_fields": mapping["unmapped_fields"],
            },
            validation_info=validation,
            metadata=metadata,
            bayesian_info=bayesian_info,
            patch_info=patch_info,
            anchor_interpretations=anchor_interpretations,
        )
    
    async def analyze_manual(
        self,
        gates: STPFGates,
        numerator: STPFNumerator,
        denominator: STPFDenominator,
        multipliers: STPFMultipliers,
        expected_score: Optional[float] = None,
        actual_score: Optional[float] = None,
        apply_patches: bool = True,
        capital: float = 0,
        confidence_level: float = 5.0,
        retention: float = 0.5,
    ) -> STPFAnalysisResponse:
        """수동 변수로 STPF 분석 수행 (Week 2 통합)"""
        start_time = datetime.now()
        
        # STPF 점수 계산
        result = self.calculator.calculate(
            gates=gates,
            numerator=numerator,
            denominator=denominator,
            multipliers=multipliers,
            expected_score=expected_score,
            actual_score=actual_score,
        )
        
        # Reality Patches 적용
        patch_info = {}
        if apply_patches and result.gate_passed:
            patch_ctx = PatchContext(
                essence=numerator.essence,
                proof=numerator.proof,
                trust=gates.trust_gate,
                network=multipliers.network,
                capital=capital,
                confidence_level=confidence_level,
                retention=retention,
            )
            patch_result = self.patches.apply_all_patches(
                result.raw_score, patch_ctx
            )
            patch_info = {
                "original_raw_score": patch_result.original_score,
                "patched_raw_score": patch_result.patched_score,
                "patches_applied": patch_result.patches_applied,
                "total_adjustment": patch_result.total_adjustment,
            }
            
            if patch_result.patches_applied:
                patched_score_1000 = int(
                    1000 * patch_result.patched_score / 
                    (patch_result.patched_score + self.calculator.reference_score)
                )
                result.raw_score = patch_result.patched_score
                result.score_1000 = min(1000, max(0, patched_score_1000))
        
        # 앵커 해석
        anchor_interpretations = self._get_anchor_interpretations(
            gates, numerator, denominator, multipliers
        )
        
        # 규칙 검증
        validation = self.rules.validate_all({
            "gates": {
                "trust": gates.trust_gate,
                "legality": gates.legality_gate,
                "hygiene": gates.hygiene_gate,
            },
            "score": result.score_1000,
            "why": result.why,
            "how": result.how,
        })
        
        end_time = datetime.now()
        metadata = {
            "stpf_version": STPFCalculator.VERSION,
            "service_version": self.VERSION,
            "mode": "manual",
            "analysis_time_ms": (end_time - start_time).total_seconds() * 1000,
            "analyzed_at": end_time.isoformat(),
        }
        
        logger.info(
            f"STPF Manual Analysis: score={result.score_1000}, go_nogo={result.go_nogo}"
        )
        
        return STPFAnalysisResponse(
            result=result,
            mapping_info={"mode": "manual", "confidence": 1.0},
            validation_info=validation,
            metadata=metadata,
            patch_info=patch_info,
            anchor_interpretations=anchor_interpretations,
        )
    
    def _get_anchor_interpretations(
        self,
        gates: STPFGates,
        numerator: STPFNumerator,
        denominator: STPFDenominator,
        multipliers: STPFMultipliers,
    ) -> Dict[str, Any]:
        """주요 변수의 앵커 해석 반환"""
        interpretations = {}
        
        # 핵심 변수만 해석
        key_vars = [
            ("essence", numerator.essence),
            ("proof", numerator.proof),
            ("network", multipliers.network),
            ("trust_gate", gates.trust_gate),
        ]
        
        for var_name, score in key_vars:
            interpretation = self.anchor_lookup.interpret_score(var_name, score)
            if "error" not in interpretation:
                interpretations[var_name] = interpretation
        
        return interpretations
    
    async def update_pattern_outcome(
        self,
        pattern_id: str,
        outcome: str,
        proof_strength: float,
        content_id: Optional[str] = None,
    ) -> BayesianPosterior:
        """패턴 결과 베이지안 갱신 (외부 호출용)"""
        evidence = PatternEvidence(
            pattern_id=pattern_id,
            outcome=outcome,
            proof_strength=proof_strength,
            content_id=content_id,
        )
        return self.bayesian.update_posterior(pattern_id, evidence)
    
    def get_pattern_probability(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """패턴 성공 확률 조회"""
        prior = self.bayesian.get_prior(pattern_id)
        if prior:
            return {
                "pattern_id": pattern_id,
                "p_success": prior.p_success,
                "sample_count": prior.sample_count,
                "last_updated": prior.last_updated,
            }
        return None
    
    def get_anchor(self, variable: str, score: int) -> Optional[str]:
        """특정 변수/점수의 앵커 조회"""
        return self.anchor_lookup.get_anchor(variable, score)
    
    def get_all_anchors(self, variable: str) -> Dict[int, str]:
        """변수의 모든 앵커 조회"""
        return self.anchor_lookup.get_all_anchors(variable)
    
    def get_default_variables(self) -> Dict[str, Any]:
        """기본 변수값 반환 (UI 초기값용)"""
        return {
            "gates": STPFGates().model_dump(),
            "numerator": STPFNumerator().model_dump(),
            "denominator": STPFDenominator().model_dump(),
            "multipliers": STPFMultipliers().model_dump(),
        }
    
    def get_variable_descriptions(self) -> Dict[str, Any]:
        """변수 설명 반환 - VDG_SCALE_ANCHORS에서 동적 생성"""
        descriptions = {}
        for var_name, config in VDG_SCALE_ANCHORS.items():
            descriptions[var_name] = {
                "korean_name": config.get("korean_name", var_name),
                "description": config.get("description", ""),
                "domain": config.get("domain", ""),
            }
        return descriptions


# Singleton instance
stpf_service = STPFService()

