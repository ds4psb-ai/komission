"""
STPF API Router

/api/v1/stpf/* 엔드포인트 정의.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import logging

from app.services.stpf.schemas import (
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
    STPFResult,
)
from app.services.stpf.service import stpf_service
from app.schemas.vdg_v4 import VDGv4

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stpf", tags=["STPF"])


# ========== Request/Response Schemas ==========

class STPFManualAnalyzeRequest(BaseModel):
    """수동 STPF 분석 요청"""
    gates: STPFGates
    numerator: STPFNumerator
    denominator: STPFDenominator
    multipliers: STPFMultipliers
    expected_score: Optional[float] = None
    actual_score: Optional[float] = None


class STPFVDGAnalyzeRequest(BaseModel):
    """VDG 기반 STPF 분석 요청"""
    vdg: Dict[str, Any]  # VDGv4 JSON
    expected_score: Optional[float] = None
    actual_score: Optional[float] = None


class STPFAnalyzeResponse(BaseModel):
    """STPF 분석 응답"""
    success: bool
    result: Optional[STPFResult] = None
    mapping_info: Dict[str, Any] = Field(default_factory=dict)
    validation_info: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class STPFVariablesResponse(BaseModel):
    """변수 정보 응답"""
    defaults: Dict[str, Any]
    descriptions: Dict[str, Any]


class STPFQuickScoreRequest(BaseModel):
    """빠른 점수 계산 요청 (핵심 변수만)"""
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


# ========== Endpoints ==========

@router.post("/analyze/manual", response_model=STPFAnalyzeResponse)
async def analyze_manual(request: STPFManualAnalyzeRequest):
    """수동 변수로 STPF 분석
    
    시뮬레이션, 테스트, 또는 수동 평가에 사용.
    """
    try:
        response = await stpf_service.analyze_manual(
            gates=request.gates,
            numerator=request.numerator,
            denominator=request.denominator,
            multipliers=request.multipliers,
            expected_score=request.expected_score,
            actual_score=request.actual_score,
        )
        
        return STPFAnalyzeResponse(
            success=True,
            result=response.result,
            mapping_info=response.mapping_info,
            validation_info=response.validation_info,
            metadata=response.metadata,
        )
    except Exception as e:
        logger.exception(f"STPF manual analysis failed: {e}")
        return STPFAnalyzeResponse(
            success=False,
            error=str(e),
        )


@router.post("/analyze/vdg", response_model=STPFAnalyzeResponse)
async def analyze_vdg(request: STPFVDGAnalyzeRequest):
    """VDG 분석 결과로 STPF 분석
    
    VDGv4 JSON을 입력받아 STPF 변수로 변환 후 분석.
    """
    try:
        # VDG JSON → VDGv4 모델 변환
        vdg = VDGv4(**request.vdg)
        
        response = await stpf_service.analyze_vdg(
            vdg=vdg,
            expected_score=request.expected_score,
            actual_score=request.actual_score,
        )
        
        return STPFAnalyzeResponse(
            success=True,
            result=response.result,
            mapping_info=response.mapping_info,
            validation_info=response.validation_info,
            metadata=response.metadata,
        )
    except Exception as e:
        logger.exception(f"STPF VDG analysis failed: {e}")
        return STPFAnalyzeResponse(
            success=False,
            error=str(e),
        )


@router.post("/quick-score", response_model=STPFQuickScoreResponse)
async def quick_score(request: STPFQuickScoreRequest):
    """빠른 점수 계산 (핵심 변수만)
    
    5개의 핵심 변수로 빠르게 Go/No-Go 결정.
    나머지 변수는 기본값 5.0 사용.
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
        )
    except Exception as e:
        logger.exception(f"STPF quick score failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variables", response_model=STPFVariablesResponse)
async def get_variables():
    """STPF 변수 기본값 및 설명 조회
    
    UI 초기값 설정 및 도움말 표시용.
    """
    return STPFVariablesResponse(
        defaults=stpf_service.get_default_variables(),
        descriptions=stpf_service.get_variable_descriptions(),
    )


@router.get("/health")
async def health_check():
    """STPF 서비스 상태 확인"""
    from app.services.stpf.calculator import STPFCalculator
    from app.services.stpf.vdg_mapper import VDGToSTPFMapper
    
    return {
        "status": "healthy",
        "stpf_version": STPFCalculator.VERSION,
        "mapper_version": VDGToSTPFMapper.VERSION,
        "endpoints": [
            "POST /stpf/analyze/manual",
            "POST /stpf/analyze/vdg",
            "POST /stpf/quick-score",
            "GET /stpf/variables",
        ],
    }
