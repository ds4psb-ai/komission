"""
STPF Service Layer

비즈니스 로직을 캡슐화한 서비스 레이어.
API 라우터와 계산기 사이의 중간 계층.
"""
import logging
from typing import Optional, Dict, Any
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

logger = logging.getLogger(__name__)


class STPFAnalysisRequest:
    """STPF 분석 요청"""
    def __init__(
        self,
        vdg: Optional[VDGv4] = None,
        manual_gates: Optional[STPFGates] = None,
        manual_numerator: Optional[STPFNumerator] = None,
        manual_denominator: Optional[STPFDenominator] = None,
        manual_multipliers: Optional[STPFMultipliers] = None,
        expected_score: Optional[float] = None,
        actual_score: Optional[float] = None,
    ):
        self.vdg = vdg
        self.manual_gates = manual_gates
        self.manual_numerator = manual_numerator
        self.manual_denominator = manual_denominator
        self.manual_multipliers = manual_multipliers
        self.expected_score = expected_score
        self.actual_score = actual_score


class STPFAnalysisResponse:
    """STPF 분석 응답"""
    def __init__(
        self,
        result: STPFResult,
        mapping_info: Optional[Dict[str, Any]] = None,
        validation_info: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.result = result
        self.mapping_info = mapping_info or {}
        self.validation_info = validation_info or {}
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result.model_dump(),
            "mapping_info": self.mapping_info,
            "validation_info": self.validation_info,
            "metadata": self.metadata,
        }


class STPFService:
    """STPF 서비스 레이어"""
    
    def __init__(self):
        self.calculator = STPFCalculator()
        self.mapper = VDGToSTPFMapper()
        self.rules = STPFInvariantRules()
    
    async def analyze_vdg(
        self,
        vdg: VDGv4,
        expected_score: Optional[float] = None,
        actual_score: Optional[float] = None,
    ) -> STPFAnalysisResponse:
        """VDG에서 STPF 분석 수행
        
        Args:
            vdg: VDGv4 분석 결과
            expected_score: 기대 점수 (엔트로피 보너스용)
            actual_score: 실제 점수 (엔트로피 보너스용)
        
        Returns:
            STPFAnalysisResponse: 분석 결과
        """
        start_time = datetime.now()
        
        # 1. VDG → STPF 변수 매핑
        mapping = self.mapper.map_to_stpf(vdg)
        
        gates = mapping["gates"]
        numerator = mapping["numerator"]
        denominator = mapping["denominator"]
        multipliers = mapping["multipliers"]
        
        # 2. STPF 점수 계산
        result = self.calculator.calculate(
            gates=gates,
            numerator=numerator,
            denominator=denominator,
            multipliers=multipliers,
            expected_score=expected_score,
            actual_score=actual_score,
        )
        
        # 3. 규칙 검증
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
        
        # 4. 메타데이터
        end_time = datetime.now()
        metadata = {
            "stpf_version": STPFCalculator.VERSION,
            "mapper_version": VDGToSTPFMapper.VERSION,
            "content_id": vdg.content_id,
            "vdg_version": vdg.vdg_version,
            "analysis_time_ms": (end_time - start_time).total_seconds() * 1000,
            "analyzed_at": end_time.isoformat(),
        }
        
        logger.info(
            f"STPF Analysis Complete: content_id={vdg.content_id}, "
            f"score={result.score_1000}, go_nogo={result.go_nogo}"
        )
        
        return STPFAnalysisResponse(
            result=result,
            mapping_info={
                "confidence": mapping["mapping_confidence"],
                "unmapped_fields": mapping["unmapped_fields"],
            },
            validation_info=validation,
            metadata=metadata,
        )
    
    async def analyze_manual(
        self,
        gates: STPFGates,
        numerator: STPFNumerator,
        denominator: STPFDenominator,
        multipliers: STPFMultipliers,
        expected_score: Optional[float] = None,
        actual_score: Optional[float] = None,
    ) -> STPFAnalysisResponse:
        """수동 변수로 STPF 분석 수행
        
        시뮬레이션, 테스트, 또는 수동 평가용.
        """
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
        )
    
    def get_default_variables(self) -> Dict[str, Any]:
        """기본 변수값 반환 (UI 초기값용)"""
        return {
            "gates": STPFGates().model_dump(),
            "numerator": STPFNumerator().model_dump(),
            "denominator": STPFDenominator().model_dump(),
            "multipliers": STPFMultipliers().model_dump(),
        }
    
    def get_variable_descriptions(self) -> Dict[str, Any]:
        """변수 설명 반환 (UI 도움말용)"""
        return {
            "gates": {
                "trust_gate": "신뢰도/일관성 (1-10). 4 미만 = 실패",
                "legality_gate": "법/규정 준수 (1-10). 4 미만 = 실패",
                "hygiene_gate": "기본 품질 (1-10). 4 미만 = 실패",
            },
            "numerator": {
                "essence": "본질/핵심 가치 (지수적 영향)",
                "capability": "실행 역량/프로덕션 품질",
                "novelty": "차별성/의외성",
                "connection": "전달력/공감/참여도",
                "proof": "증거/핸디캡 (증거 없으면 최대 3점)",
            },
            "denominator": {
                "cost": "비용/복잡도",
                "risk": "실패 확률",
                "threat": "경쟁 강도",
                "pressure": "압박/피로도",
                "time_lag": "성과 지연",
                "uncertainty": "예측 불가성",
            },
            "multipliers": {
                "scarcity": "희소성",
                "network": "네트워크 효과 (지수적 성장)",
                "leverage": "레버리지/재활용 가능성",
            },
        }


# Singleton instance
stpf_service = STPFService()
