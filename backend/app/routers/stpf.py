"""
STPF API Router (Week 2 Hardened)

/api/v1/stpf/* 엔드포인트 정의.
Week 2: Bayesian + Patches + Anchors API 추가.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import logging

from app.services.stpf.schemas import (
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
    STPFResult,
)
from app.services.stpf.service import stpf_service, STPFService
from app.schemas.vdg_v4 import VDGv4

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stpf", tags=["STPF"])


# ========== Request/Response Schemas ==========

class STPFManualAnalyzeRequest(BaseModel):
    """수동 STPF 분석 요청 (Week 2 확장)"""
    gates: STPFGates
    numerator: STPFNumerator
    denominator: STPFDenominator
    multipliers: STPFMultipliers
    expected_score: Optional[float] = None
    actual_score: Optional[float] = None
    # Week 2 options
    apply_patches: bool = True
    capital: float = 0
    confidence_level: float = 5.0
    retention: float = 0.5


class STPFVDGAnalyzeRequest(BaseModel):
    """VDG 기반 STPF 분석 요청 (Week 2 확장)"""
    vdg: Dict[str, Any]
    expected_score: Optional[float] = None
    actual_score: Optional[float] = None
    apply_patches: bool = True
    update_bayesian: bool = True


class STPFAnalyzeResponse(BaseModel):
    """STPF 분석 응답 (Week 2 확장)"""
    success: bool
    result: Optional[STPFResult] = None
    mapping_info: Dict[str, Any] = Field(default_factory=dict)
    validation_info: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Week 2 additions
    bayesian_info: Dict[str, Any] = Field(default_factory=dict)
    patch_info: Dict[str, Any] = Field(default_factory=dict)
    anchor_interpretations: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class STPFVariablesResponse(BaseModel):
    """변수 정보 응답"""
    defaults: Dict[str, Any]
    descriptions: Dict[str, Any]


class STPFQuickScoreRequest(BaseModel):
    """빠른 점수 계산 요청"""
    essence: float = Field(ge=1, le=10, description="본질/핵심 가치")
    novelty: float = Field(ge=1, le=10, description="차별성")
    proof: float = Field(ge=1, le=10, description="증거")
    risk: float = Field(ge=1, le=10, description="리스크")
    network: float = Field(ge=1, le=10, description="네트워크 효과")


class STPFQuickScoreResponse(BaseModel):
    """빠른 점수 계산 응답"""
    score_1000: int
    go_nogo: str
    why: str
    how: List[str]
    anchor_interpretations: Dict[str, Any] = Field(default_factory=dict)


class PatternProbabilityResponse(BaseModel):
    """패턴 확률 응답"""
    pattern_id: str
    p_success: float
    sample_count: int
    last_updated: Optional[str] = None


class AnchorResponse(BaseModel):
    """앵커 조회 응답"""
    variable: str
    score: int
    interpretation: Optional[str] = None
    korean_name: Optional[str] = None
    description: Optional[str] = None


# ========== Endpoints ==========

@router.post("/analyze/manual", response_model=STPFAnalyzeResponse)
async def analyze_manual(request: STPFManualAnalyzeRequest):
    """수동 변수로 STPF 분석 (Week 2 통합)
    
    Reality Patches와 앵커 해석 포함.
    """
    try:
        response = await stpf_service.analyze_manual(
            gates=request.gates,
            numerator=request.numerator,
            denominator=request.denominator,
            multipliers=request.multipliers,
            expected_score=request.expected_score,
            actual_score=request.actual_score,
            apply_patches=request.apply_patches,
            capital=request.capital,
            confidence_level=request.confidence_level,
            retention=request.retention,
        )
        
        return STPFAnalyzeResponse(
            success=True,
            result=response.result,
            mapping_info=response.mapping_info,
            validation_info=response.validation_info,
            metadata=response.metadata,
            patch_info=response.patch_info,
            anchor_interpretations=response.anchor_interpretations,
        )
    except Exception as e:
        logger.exception(f"STPF manual analysis failed: {e}")
        return STPFAnalyzeResponse(success=False, error=str(e))


@router.post("/analyze/vdg", response_model=STPFAnalyzeResponse)
async def analyze_vdg(request: STPFVDGAnalyzeRequest):
    """VDG 분석 결과로 STPF 분석 (Week 2 통합)
    
    베이지안 갱신, Reality Patches, 앵커 해석 포함.
    """
    try:
        vdg = VDGv4(**request.vdg)
        
        response = await stpf_service.analyze_vdg(
            vdg=vdg,
            expected_score=request.expected_score,
            actual_score=request.actual_score,
            apply_patches=request.apply_patches,
            update_bayesian=request.update_bayesian,
        )
        
        return STPFAnalyzeResponse(
            success=True,
            result=response.result,
            mapping_info=response.mapping_info,
            validation_info=response.validation_info,
            metadata=response.metadata,
            bayesian_info=response.bayesian_info,
            patch_info=response.patch_info,
            anchor_interpretations=response.anchor_interpretations,
        )
    except Exception as e:
        logger.exception(f"STPF VDG analysis failed: {e}")
        return STPFAnalyzeResponse(success=False, error=str(e))


@router.post("/quick-score", response_model=STPFQuickScoreResponse)
async def quick_score(request: STPFQuickScoreRequest):
    """빠른 점수 계산 (핵심 변수만)
    
    5개의 핵심 변수로 빠르게 Go/No-Go 결정.
    """
    try:
        gates = STPFGates(trust_gate=7, legality_gate=8, hygiene_gate=7)
        numerator = STPFNumerator(
            essence=request.essence,
            capability=5.0,
            novelty=request.novelty,
            connection=5.0,
            proof=request.proof,
        )
        denominator = STPFDenominator(
            cost=4.0,
            risk=request.risk,
            threat=5.0,
            pressure=5.0,
            time_lag=4.0,
            uncertainty=5.0,
        )
        multipliers = STPFMultipliers(
            scarcity=5.0,
            network=request.network,
            leverage=5.0,
        )
        
        response = await stpf_service.analyze_manual(
            gates=gates,
            numerator=numerator,
            denominator=denominator,
            multipliers=multipliers,
        )
        
        return STPFQuickScoreResponse(
            score_1000=response.result.score_1000,
            go_nogo=response.result.go_nogo,
            why=response.result.why or "",
            how=response.result.how or [],
            anchor_interpretations=response.anchor_interpretations,
        )
    except Exception as e:
        logger.exception(f"STPF quick score failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variables", response_model=STPFVariablesResponse)
async def get_variables():
    """STPF 변수 기본값 및 설명 조회"""
    return STPFVariablesResponse(
        defaults=stpf_service.get_default_variables(),
        descriptions=stpf_service.get_variable_descriptions(),
    )


# ========== Week 2 Endpoints ==========

@router.get("/pattern/{pattern_id}/probability")
async def get_pattern_probability(pattern_id: str):
    """패턴 성공 확률 조회 (베이지안)
    
    해당 패턴의 현재 성공 확률과 샘플 수 반환.
    """
    result = stpf_service.get_pattern_probability(pattern_id)
    if result:
        return result
    return {
        "pattern_id": pattern_id,
        "p_success": 0.5,
        "sample_count": 0,
        "last_updated": None,
        "message": "No prior data, using default 50%",
    }


@router.post("/pattern/{pattern_id}/update")
async def update_pattern_outcome(
    pattern_id: str,
    outcome: str = Query(..., description="success | failure"),
    proof_strength: float = Query(5.0, ge=1, le=10),
    content_id: Optional[str] = None,
):
    """패턴 결과 베이지안 갱신
    
    새로운 증거로 패턴 성공 확률 갱신.
    """
    try:
        posterior = await stpf_service.update_pattern_outcome(
            pattern_id=pattern_id,
            outcome=outcome,
            proof_strength=proof_strength,
            content_id=content_id,
        )
        return {
            "pattern_id": pattern_id,
            "p_success": posterior.p_success,
            "confidence_interval": posterior.confidence_interval,
            "sample_count": posterior.sample_count,
            "prior": posterior.prior,
            "updated_at": posterior.updated_at,
        }
    except Exception as e:
        logger.exception(f"Pattern update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anchor/{variable}/{score}")
async def get_anchor(
    variable: str = Path(..., description="변수명"),
    score: int = Path(..., ge=1, le=10, description="1-10 점수"),
):
    """특정 변수/점수의 앵커 조회
    
    1-10 점수에 해당하는 해석 반환.
    """
    interpretation = stpf_service.anchor_lookup.interpret_score(variable, score)
    if "error" in interpretation:
        raise HTTPException(status_code=404, detail=interpretation["error"])
    return interpretation


@router.get("/anchors/{variable}")
async def get_all_anchors(variable: str):
    """변수의 모든 앵커 조회"""
    anchors = stpf_service.get_all_anchors(variable)
    if not anchors:
        raise HTTPException(status_code=404, detail=f"Unknown variable: {variable}")
    return {
        "variable": variable,
        "anchors": anchors,
    }


# ========== Week 3 Endpoints ==========

class SimulationRequest(BaseModel):
    """시뮬레이션 요청"""
    gates: STPFGates
    numerator: STPFNumerator
    denominator: STPFDenominator
    multipliers: STPFMultipliers
    variation: float = Field(0.2, ge=0.05, le=0.5, description="변동 비율")


class MonteCarloRequest(BaseModel):
    """Monte Carlo 요청"""
    gates: STPFGates
    numerator: STPFNumerator
    denominator: STPFDenominator
    multipliers: STPFMultipliers
    n_simulations: int = Field(1000, ge=100, le=10000)
    noise_std: float = Field(1.0, ge=0.1, le=3.0)


@router.post("/simulate/tot")
async def simulate_tot(request: SimulationRequest):
    """Tree of Thoughts 시뮬레이션
    
    Worst/Base/Best 3가지 시나리오 분석.
    """
    try:
        result = stpf_service.run_tot_simulation(
            gates=request.gates,
            numerator=request.numerator,
            denominator=request.denominator,
            multipliers=request.multipliers,
            variation=request.variation,
        )
        return {
            "success": True,
            "worst": result.worst.model_dump(),
            "base": result.base.model_dump(),
            "best": result.best.model_dump(),
            "weighted_score": result.weighted_score,
            "score_range": result.score_range,
            "recommendation": result.recommendation,
            "confidence": result.confidence,
        }
    except Exception as e:
        logger.exception(f"ToT simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate/monte-carlo")
async def simulate_monte_carlo(request: MonteCarloRequest):
    """Monte Carlo 시뮬레이션
    
    n회 랜덤 시뮬레이션으로 확률 분포 추정.
    """
    try:
        result = stpf_service.run_monte_carlo(
            gates=request.gates,
            numerator=request.numerator,
            denominator=request.denominator,
            multipliers=request.multipliers,
            n_simulations=request.n_simulations,
            noise_std=request.noise_std,
        )
        return {
            "success": True,
            "n_simulations": result.n_simulations,
            "mean": result.mean,
            "median": result.median,
            "std": result.std,
            "percentile_10": result.percentile_10,
            "percentile_90": result.percentile_90,
            "min_score": result.min_score,
            "max_score": result.max_score,
            "go_probability": result.go_probability,
            "consider_probability": result.consider_probability,
            "nogo_probability": result.nogo_probability,
            "distribution_summary": result.distribution_summary,
            "run_time_ms": result.run_time_ms,
        }
    except Exception as e:
        logger.exception(f"Monte Carlo simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kelly/{score}")
async def get_kelly_decision(
    score: int = Path(..., ge=0, le=1000, description="STPF 점수"),
    time_investment_hours: float = Query(10.0, ge=1, le=100),
    expected_view_multiplier: float = Query(3.0, ge=1, le=100),
):
    """Kelly Criterion 의사결정
    
    STPF 점수 기반 최적 투자 비율 계산.
    """
    try:
        decision = stpf_service.get_kelly_decision(
            score_1000=score,
            time_investment_hours=time_investment_hours,
            expected_view_multiplier=expected_view_multiplier,
        )
        return decision.model_dump()
    except Exception as e:
        logger.exception(f"Kelly decision failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grade/{score}")
async def get_grade_info(score: int = Path(..., ge=0, le=1000, description="STPF 점수")):
    """STPF 점수 등급 조회
    
    S/A/B/C 등급 및 권장 행동 반환.
    """
    grade = stpf_service.get_grade_info(score)
    return grade.model_dump()


@router.get("/health")
async def health_check():
    """STPF 서비스 상태 확인"""
    from app.services.stpf.calculator import STPFCalculator
    from app.services.stpf.vdg_mapper import VDGToSTPFMapper
    from app.services.stpf.bayesian_updater import BayesianPatternUpdater
    from app.services.stpf.reality_patches import RealityDistortionPatches
    from app.services.stpf.simulation import STPFSimulator
    from app.services.stpf.kelly_criterion import KellyDecisionEngine
    
    return {
        "status": "healthy",
        "version": {
            "stpf_calculator": STPFCalculator.VERSION,
            "service": STPFService.VERSION,
            "mapper": VDGToSTPFMapper.VERSION,
            "bayesian": BayesianPatternUpdater.VERSION,
            "patches": RealityDistortionPatches.VERSION,
            "simulator": STPFSimulator.VERSION,
            "kelly": KellyDecisionEngine.VERSION,
        },
        "endpoints": [
            "POST /stpf/analyze/manual",
            "POST /stpf/analyze/vdg",
            "POST /stpf/quick-score",
            "GET /stpf/variables",
            # Week 2
            "GET /stpf/pattern/{id}/probability",
            "POST /stpf/pattern/{id}/update",
            "GET /stpf/anchor/{variable}/{score}",
            "GET /stpf/anchors/{variable}",
            # Week 3
            "POST /stpf/simulate/tot",
            "POST /stpf/simulate/monte-carlo",
            "GET /stpf/kelly/{score}",
            "GET /stpf/grade/{score}",
        ],
    }
