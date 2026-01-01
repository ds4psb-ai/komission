"""
MCP Tools - STPF 분석 도구

Claude Desktop에서 STPF v3.1 기능 사용.
- 패턴 점수 계산
- Kelly Criterion 의사결정
- ToT/Monte Carlo 시뮬레이션
- 등급 및 권장 행동

모든 도구는 구조화된 데이터를 반환하여 Claude가 해석합니다.
"""
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import Context

from app.mcp.server import mcp, get_logger
from app.services.stpf import (
    stpf_service,
    stpf_simulator,
    kelly_engine,
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
    STPFVariables,
)

logger = get_logger()


@mcp.tool()
async def stpf_quick_score(
    essence: float,
    novelty: float,
    proof: float,
    risk: float,
    network: float,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    STPF 빠른 점수 계산 (핵심 5개 변수)
    
    Claude Desktop에서 빠르게 Go/No-Go 판단할 때 사용.
    
    Args:
        essence: 본질/핵심 가치 (1-10)
        novelty: 차별성 (1-10)
        proof: 증거 강도 (1-10)
        risk: 리스크 (1-10, 낮을수록 좋음)
        network: 네트워크 효과 (1-10)
    
    Returns:
        STPF 점수, 등급, 권장 행동
    """
    try:
        gates = STPFGates(trust_gate=7, legality_gate=8, hygiene_gate=7)
        numerator = STPFNumerator(
            essence=max(1, min(10, essence)),
            capability=5.0,
            novelty=max(1, min(10, novelty)),
            connection=5.0,
            proof=max(1, min(10, proof)),
        )
        denominator = STPFDenominator(
            cost=4.0,
            risk=max(1, min(10, risk)),
            threat=5.0,
            pressure=5.0,
            time_lag=4.0,
            uncertainty=5.0,
        )
        multipliers = STPFMultipliers(
            scarcity=5.0,
            network=max(1, min(10, network)),
            leverage=5.0,
        )
        
        response = await stpf_service.analyze_manual(
            gates=gates,
            numerator=numerator,
            denominator=denominator,
            multipliers=multipliers,
        )
        
        grade = stpf_service.get_grade_info(response.result.score_1000)
        
        return {
            "score_1000": response.result.score_1000,
            "go_nogo": response.result.go_nogo,
            "grade": grade.grade,
            "grade_label": grade.label,
            "recommended_action": grade.action,
            "kelly_hint": grade.kelly_hint,
            "why": response.result.why,
            "how": response.result.how[:3] if response.result.how else [],
            "anchor_interpretations": response.anchor_interpretations,
        }
    except Exception as e:
        logger.error(f"STPF quick score failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def stpf_full_analyze(
    trust: float = 7,
    legality: float = 8,
    hygiene: float = 7,
    essence: float = 5,
    capability: float = 5,
    novelty: float = 5,
    connection: float = 5,
    proof: float = 5,
    cost: float = 5,
    risk: float = 5,
    threat: float = 5,
    pressure: float = 5,
    time_lag: float = 5,
    uncertainty: float = 5,
    scarcity: float = 5,
    network: float = 5,
    leverage: float = 5,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    STPF 전체 변수 분석
    
    16개 변수를 모두 입력하여 정밀 분석.
    
    Returns:
        점수, 패치 정보, 앵커 해석, 등급, Kelly 결정
    """
    try:
        gates = STPFGates(
            trust_gate=max(1, min(10, trust)),
            legality_gate=max(1, min(10, legality)),
            hygiene_gate=max(1, min(10, hygiene)),
        )
        numerator = STPFNumerator(
            essence=max(1, min(10, essence)),
            capability=max(1, min(10, capability)),
            novelty=max(1, min(10, novelty)),
            connection=max(1, min(10, connection)),
            proof=max(1, min(10, proof)),
        )
        denominator = STPFDenominator(
            cost=max(1, min(10, cost)),
            risk=max(1, min(10, risk)),
            threat=max(1, min(10, threat)),
            pressure=max(1, min(10, pressure)),
            time_lag=max(1, min(10, time_lag)),
            uncertainty=max(1, min(10, uncertainty)),
        )
        multipliers = STPFMultipliers(
            scarcity=max(1, min(10, scarcity)),
            network=max(1, min(10, network)),
            leverage=max(1, min(10, leverage)),
        )
        
        response = await stpf_service.analyze_manual(
            gates=gates,
            numerator=numerator,
            denominator=denominator,
            multipliers=multipliers,
            apply_patches=True,
        )
        
        kelly = stpf_service.get_kelly_decision(response.result.score_1000)
        grade = stpf_service.get_grade_info(response.result.score_1000)
        
        return {
            "score_1000": response.result.score_1000,
            "raw_score": response.result.raw_score,
            "go_nogo": response.result.go_nogo,
            "gate_passed": response.result.gate_passed,
            "grade": {
                "grade": grade.grade,
                "label": grade.label,
                "description": grade.description,
                "action": grade.action,
            },
            "kelly": {
                "signal": kelly.signal,
                "recommended_effort_percent": kelly.recommended_effort_percent,
                "reason": kelly.reason,
                "action": kelly.action,
            },
            "patches_applied": len(response.patch_info.get("patches_applied", [])),
            "patch_details": response.patch_info.get("patches_applied", []),
            "why": response.result.why,
            "how": response.result.how,
            "anchor_interpretations": response.anchor_interpretations,
        }
    except Exception as e:
        logger.error(f"STPF full analyze failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def stpf_simulate_scenarios(
    essence: float = 5,
    novelty: float = 5,
    proof: float = 5,
    risk: float = 5,
    network: float = 5,
    variation: float = 0.2,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    STPF ToT 시뮬레이션 (Worst/Base/Best)
    
    3가지 시나리오 분석으로 불확실성 대비.
    
    Args:
        essence: 본질 (1-10)
        novelty: 차별성 (1-10)
        proof: 증거 (1-10)
        risk: 리스크 (1-10)
        network: 네트워크 (1-10)
        variation: 변동 비율 (0.1-0.5)
    
    Returns:
        3가지 시나리오 점수 및 추천
    """
    try:
        variables = STPFVariables(
            gates=STPFGates(trust_gate=7, legality_gate=8, hygiene_gate=7),
            numerator=STPFNumerator(
                essence=max(1, min(10, essence)),
                capability=5.0,
                novelty=max(1, min(10, novelty)),
                connection=5.0,
                proof=max(1, min(10, proof)),
            ),
            denominator=STPFDenominator(
                cost=4.0,
                risk=max(1, min(10, risk)),
                threat=5.0,
                pressure=5.0,
                time_lag=4.0,
                uncertainty=5.0,
            ),
            multipliers=STPFMultipliers(
                scarcity=5.0,
                network=max(1, min(10, network)),
                leverage=5.0,
            ),
        )
        
        result = stpf_simulator.run_tot_simulation(
            variables, 
            variation=max(0.05, min(0.5, variation))
        )
        
        return {
            "scenarios": {
                "worst": {
                    "score": result.worst.score_1000,
                    "go_nogo": result.worst.go_nogo,
                },
                "base": {
                    "score": result.base.score_1000,
                    "go_nogo": result.base.go_nogo,
                },
                "best": {
                    "score": result.best.score_1000,
                    "go_nogo": result.best.go_nogo,
                },
            },
            "weighted_score": result.weighted_score,
            "score_range": list(result.score_range),
            "recommendation": result.recommendation,
            "confidence": result.confidence,
        }
    except Exception as e:
        logger.error(f"STPF simulation failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def stpf_monte_carlo(
    essence: float = 5,
    novelty: float = 5,
    proof: float = 5,
    risk: float = 5,
    network: float = 5,
    n_simulations: int = 500,
    noise_std: float = 1.0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    STPF Monte Carlo 시뮬레이션
    
    랜덤 시뮬레이션으로 확률 분포 추정.
    
    Args:
        n_simulations: 시뮬레이션 횟수 (100-5000)
        noise_std: 노이즈 표준편차 (0.5-2.0)
    
    Returns:
        확률 분포, Go/Consider/No-Go 확률
    """
    try:
        variables = STPFVariables(
            gates=STPFGates(trust_gate=7, legality_gate=8, hygiene_gate=7),
            numerator=STPFNumerator(
                essence=max(1, min(10, essence)),
                capability=5.0,
                novelty=max(1, min(10, novelty)),
                connection=5.0,
                proof=max(1, min(10, proof)),
            ),
            denominator=STPFDenominator(
                cost=4.0,
                risk=max(1, min(10, risk)),
                threat=5.0,
                pressure=5.0,
                time_lag=4.0,
                uncertainty=5.0,
            ),
            multipliers=STPFMultipliers(
                scarcity=5.0,
                network=max(1, min(10, network)),
                leverage=5.0,
            ),
        )
        
        result = stpf_simulator.run_monte_carlo(
            variables,
            n_simulations=max(100, min(5000, n_simulations)),
            noise_std=max(0.5, min(2.0, noise_std)),
        )
        
        return {
            "n_simulations": result.n_simulations,
            "statistics": {
                "mean": round(result.mean, 1),
                "median": round(result.median, 1),
                "std": round(result.std, 1),
                "min": result.min_score,
                "max": result.max_score,
            },
            "percentiles": {
                "p10": round(result.percentile_10, 1),
                "p25": round(result.percentile_25, 1),
                "p75": round(result.percentile_75, 1),
                "p90": round(result.percentile_90, 1),
            },
            "probabilities": {
                "go": f"{result.go_probability:.1%}",
                "consider": f"{result.consider_probability:.1%}",
                "nogo": f"{result.nogo_probability:.1%}",
            },
            "run_time_ms": round(result.run_time_ms, 1),
        }
    except Exception as e:
        logger.error(f"STPF Monte Carlo failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def stpf_kelly_decision(
    score: int,
    time_investment_hours: float = 10.0,
    expected_view_multiplier: float = 3.0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Kelly Criterion 의사결정
    
    STPF 점수 기반 최적 투자 비율 계산.
    
    Args:
        score: STPF 점수 (0-1000)
        time_investment_hours: 예상 투자 시간
        expected_view_multiplier: 성공 시 조회수 배수
    
    Returns:
        Kelly 신호, 권장 노력 비율, 등급
    """
    try:
        decision = kelly_engine.calculate_from_stpf(
            score_1000=max(0, min(1000, score)),
            time_investment_hours=max(1, min(100, time_investment_hours)),
            expected_view_multiplier=max(1, min(100, expected_view_multiplier)),
        )
        
        return {
            "score": score,
            "signal": decision.signal,
            "recommended_effort_percent": decision.recommended_effort_percent,
            "reason": decision.reason,
            "action": decision.action,
            "kelly_fractions": {
                "raw": decision.raw_kelly_fraction,
                "safe": decision.safe_kelly_fraction,
            },
            "expected_value": decision.expected_value,
            "grade": decision.grade_info,
            "inputs": decision.inputs,
        }
    except Exception as e:
        logger.error(f"Kelly decision failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def stpf_get_anchor(
    variable: str,
    score: int,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    STPF 변수 앵커 조회
    
    1-10 점수의 의미를 해석.
    
    Args:
        variable: 변수명 (essence, proof, network, etc.)
        score: 점수 (1-10)
    
    Returns:
        앵커 해석
    """
    try:
        interpretation = stpf_service.anchor_lookup.interpret_score(
            variable, 
            max(1, min(10, score))
        )
        return interpretation
    except Exception as e:
        logger.error(f"Anchor lookup failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def stpf_compare_content(
    content_a: Dict[str, float],
    content_b: Dict[str, float],
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    두 콘텐츠 STPF 비교
    
    A/B 테스트나 옵션 비교에 사용.
    
    Args:
        content_a: {"essence": 7, "novelty": 6, "proof": 5, "risk": 4, "network": 6}
        content_b: {"essence": 6, "novelty": 8, "proof": 4, "risk": 5, "network": 7}
    
    Returns:
        두 콘텐츠 점수 비교 및 추천
    """
    try:
        async def get_score(data: Dict[str, float]) -> Dict[str, Any]:
            gates = STPFGates(trust_gate=7, legality_gate=8, hygiene_gate=7)
            numerator = STPFNumerator(
                essence=data.get("essence", 5),
                capability=data.get("capability", 5),
                novelty=data.get("novelty", 5),
                connection=data.get("connection", 5),
                proof=data.get("proof", 5),
            )
            denominator = STPFDenominator(
                cost=data.get("cost", 5),
                risk=data.get("risk", 5),
                threat=data.get("threat", 5),
                pressure=data.get("pressure", 5),
                time_lag=data.get("time_lag", 5),
                uncertainty=data.get("uncertainty", 5),
            )
            multipliers = STPFMultipliers(
                scarcity=data.get("scarcity", 5),
                network=data.get("network", 5),
                leverage=data.get("leverage", 5),
            )
            
            response = await stpf_service.analyze_manual(
                gates, numerator, denominator, multipliers
            )
            
            grade = stpf_service.get_grade_info(response.result.score_1000)
            return {
                "score": response.result.score_1000,
                "go_nogo": response.result.go_nogo,
                "grade": grade.grade,
            }
        
        result_a = await get_score(content_a)
        result_b = await get_score(content_b)
        
        diff = result_a["score"] - result_b["score"]
        winner = "A" if diff > 0 else "B" if diff < 0 else "tie"
        
        return {
            "content_a": result_a,
            "content_b": result_b,
            "score_difference": abs(diff),
            "recommendation": f"Content {winner}를 선택하세요" if winner != "tie" else "동점입니다",
            "winner": winner,
        }
    except Exception as e:
        logger.error(f"Content comparison failed: {e}")
        return {"error": str(e)}
