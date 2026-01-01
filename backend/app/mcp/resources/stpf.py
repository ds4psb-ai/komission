"""
MCP Resources - STPF 관련 리소스

stpf:// 스키마로 STPF 데이터 접근.
Claude Desktop에서 패턴 신뢰도, 시스템 상태 등 조회.
"""
from app.mcp.server import mcp, get_logger
from app.services.stpf import (
    stpf_service,
    bayesian_updater,
    kelly_engine,
    STPF_GRADE_BRACKETS,
)
from app.services.stpf.free_energy import free_energy_checker

logger = get_logger()


@mcp.resource("stpf://patterns/{pattern_id}")
async def get_pattern_confidence(pattern_id: str) -> str:
    """
    패턴 신뢰도 리소스
    
    베이지안 Prior 및 성공 확률 조회.
    
    Returns:
        패턴의 현재 성공 확률, 신뢰 구간, 샘플 수
    """
    logger.info(f"STPF Resource request: patterns/{pattern_id}")
    
    try:
        prior = bayesian_updater.get_prior(pattern_id)
        
        if prior:
            return f"""
# Pattern Confidence: {pattern_id}

**P(Success)**: {prior.p_success:.1%}
**Sample Count**: {prior.sample_count}
**Last Updated**: {prior.last_updated or 'N/A'}

## Prior Info
- Alpha (Successes): {prior.alpha}
- Beta (Failures): {prior.beta}

## Interpretation
{_interpret_confidence(prior.p_success, prior.sample_count)}
"""
        else:
            return f"""
# Pattern: {pattern_id}

**Status**: No prior data available
**Default P(Success)**: 50%

> 아직 이 패턴에 대한 증거가 축적되지 않았습니다.
> 첫 번째 예측 후 자동으로 갱신됩니다.
"""
    except Exception as e:
        logger.error(f"Error fetching pattern confidence: {e}")
        return f"❌ Error: {str(e)[:100]}"


@mcp.resource("stpf://grades")
async def get_all_grades() -> str:
    """
    STPF 등급 체계 조회
    
    S/A/B/C 등급 기준 및 권장 행동.
    """
    logger.info("STPF Resource request: grades")
    
    try:
        grades_text = ""
        for (low, high), info in sorted(STPF_GRADE_BRACKETS.items(), reverse=True):
            grades_text += f"""
### {info['grade']} ({info['label']})
- **Score Range**: {low} - {high-1}
- **Description**: {info['description']}
- **Action**: {info['action']}
- **Kelly Hint**: {info['kelly_hint']}

"""
        
        return f"""
# STPF Grade System

STPF v3.1 등급 체계 및 권장 행동.

{grades_text}

## Usage

```python
# 점수로 등급 조회
grade = kelly_engine.get_grade_info(750)
# → A (Cash Cow)
```
"""
    except Exception as e:
        logger.error(f"Error fetching grades: {e}")
        return f"❌ Error: {str(e)[:100]}"


@mcp.resource("stpf://health")
async def get_system_health() -> str:
    """
    STPF 시스템 상태 조회
    
    Free Energy, 캘리브레이션, 예측 정확도.
    """
    logger.info("STPF Resource request: health")
    
    try:
        # Free Energy 계산
        fe = free_energy_checker.calculate_free_energy()
        stats = free_energy_checker.get_stats()
        
        recommendations = "\n".join(f"- {r}" for r in fe.recommendations)
        
        return f"""
# STPF System Health

**Status**: {fe.health_status.upper()}

## Free Energy Analysis
- **Free Energy**: {fe.free_energy:.3f} (lower is better)
- **Entropy**: {fe.entropy:.3f} (prediction uncertainty)
- **Surprise**: {fe.surprise:.3f} (prediction error)

## Calibration Metrics
- **Brier Score**: {fe.calibration.brier_score:.4f}
- **Log Loss**: {fe.calibration.log_loss:.4f}
- **Calibration Error**: {fe.calibration.calibration_error:.1%}
- **MAE**: {fe.calibration.mean_absolute_error:.4f}
- **Sample Count**: {fe.calibration.sample_count}

## Prediction Stats
- **Total Predictions**: {stats['total_predictions']}
- **Completed**: {stats['completed_predictions']}
- **Success Rate**: {stats['success_rate']:.1%}
- **Accuracy Rate**: {stats['accuracy_rate']:.1%}

## Recommendations
{recommendations}

---
*Generated at: {fe.calibration.last_updated}*
"""
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        return f"❌ Error: {str(e)[:100]}"


@mcp.resource("stpf://variables")
async def get_all_variables() -> str:
    """
    STPF 변수 목록 조회
    
    16개 변수 설명 및 기본값.
    """
    logger.info("STPF Resource request: variables")
    
    try:
        defaults = stpf_service.get_default_variables()
        descriptions = stpf_service.get_variable_descriptions()
        
        # Gates
        gates_text = ""
        for var, val in defaults['gates'].items():
            desc = descriptions.get(var, {})
            gates_text += f"- **{var}**: {val} ({desc.get('korean_name', '')})\n"
        
        # Numerator
        num_text = ""
        for var, val in defaults['numerator'].items():
            desc = descriptions.get(var, {})
            num_text += f"- **{var}**: {val} ({desc.get('korean_name', '')})\n"
        
        # Denominator
        denom_text = ""
        for var, val in defaults['denominator'].items():
            desc = descriptions.get(var, {})
            denom_text += f"- **{var}**: {val} ({desc.get('korean_name', '')})\n"
        
        # Multipliers
        mult_text = ""
        for var, val in defaults['multipliers'].items():
            desc = descriptions.get(var, {})
            mult_text += f"- **{var}**: {val} ({desc.get('korean_name', '')})\n"
        
        return f"""
# STPF Variables (v3.1)

Total: 16 variables in 4 categories.

## Gates (Kill Switch)
{gates_text}
> Gate < 4 → 즉시 실패

## Numerator (Value)
{num_text}
> 높을수록 좋음, 지수적 영향

## Denominator (Friction)
{denom_text}
> 낮을수록 좋음, 마찰 요인

## Multipliers
{mult_text}
> 승수 효과, 네트워크는 지수적
"""
    except Exception as e:
        logger.error(f"Error fetching variables: {e}")
        return f"❌ Error: {str(e)[:100]}"


def _interpret_confidence(p_success: float, sample_count: int) -> str:
    """신뢰도 해석"""
    if sample_count < 5:
        return "> ⚠️ 샘플 수 부족 - 신뢰도 낮음"
    elif sample_count < 20:
        return "> 📊 초기 데이터 - 추가 증거 필요"
    elif p_success >= 0.7:
        return "> ✅ 강한 패턴 - 높은 성공 확률"
    elif p_success >= 0.5:
        return "> 📈 긍정적 패턴 - 검증 진행 중"
    elif p_success >= 0.3:
        return "> ⚠️ 약한 패턴 - 개선 필요"
    else:
        return "> ❌ 비효과적 패턴 - 사용 비추천"
