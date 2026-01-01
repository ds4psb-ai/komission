"""
STPF v3.1 Kelly Criterion Decision Engine

Kelly Criterion 기반 최적 투자 비율 계산.

공식: f* = (bp - q) / b
- b: 배당률 (upside / downside)
- p: 성공 확률
- q: 실패 확률 (1 - p)

Fractional Kelly (안전 버전): f* × confidence × 0.5
"""
import logging
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ================================
# STPF 등급 구간
# ================================

STPF_GRADE_BRACKETS: Dict[Tuple[int, int], Dict[str, Any]] = {
    (800, 1001): {
        "grade": "S",
        "label": "Unicorn",
        "description": "압도적 바이럴 잠재력",
        "action": "즉시 확장, 템플릿화, 다중 플랫폼 배포",
        "kelly_hint": "40%+ 리소스 투입",
        "color": "#FFD700",  # Gold
    },
    (500, 800): {
        "grade": "A",
        "label": "Cash Cow",
        "description": "안정적 성과 예상",
        "action": "리텐션 최적화, 변주 확장",
        "kelly_hint": "20~40% 리소스 투입",
        "color": "#C0C0C0",  # Silver
    },
    (250, 500): {
        "grade": "B",
        "label": "So-so",
        "description": "차별화 필요",
        "action": "갭(novelty) 강화 또는 피벗",
        "kelly_hint": "10~20% 리소스 투입",
        "color": "#CD7F32",  # Bronze
    },
    (0, 250): {
        "grade": "C",
        "label": "Fail",
        "description": "진입 비추천",
        "action": "손절 또는 Gate/Proof 재구축",
        "kelly_hint": "5% 미만 또는 포기",
        "color": "#808080",  # Gray
    },
}


class KellyDecision(BaseModel):
    """Kelly Criterion 의사결정 결과"""
    # Kelly 계산 결과
    raw_kelly_fraction: float = Field(ge=0, le=1, description="원시 Kelly 비율")
    safe_kelly_fraction: float = Field(ge=0, le=1, description="안전 Kelly 비율")
    recommended_effort_percent: float = Field(description="권장 노력 비율 (%)")
    
    # 기대값
    expected_value: float = Field(description="기대값 (upside - downside)")
    
    # 의사결정 신호
    signal: str = Field(description="GO | MODERATE | CAUTION | NO_GO")
    reason: str = Field(description="결정 근거")
    action: str = Field(description="권장 행동")
    
    # 입력값
    inputs: Dict[str, Any] = Field(default_factory=dict)
    
    # 등급 정보 (STPF 점수 기준)
    grade_info: Optional[Dict[str, Any]] = None


class GradeInfo(BaseModel):
    """등급 정보"""
    score_1000: int
    grade: str
    label: str
    description: str
    action: str
    kelly_hint: str
    color: str


class KellyDecisionEngine:
    """Kelly Criterion 의사결정 엔진
    
    베이지안 확률과 기대 손익을 기반으로 최적 투자 비율 계산.
    """
    
    VERSION = "1.0"
    
    def __init__(self):
        # Fractional Kelly 계수 (보수적)
        self.fractional_multiplier = 0.5
        
        # 신호 임계값
        self.go_threshold = 0.25
        self.moderate_threshold = 0.1
        self.caution_threshold = 0.0
    
    def calculate_optimal_bet(
        self,
        p_success: float,
        upside: float,
        downside: float,
        confidence: float = 1.0,
    ) -> KellyDecision:
        """최적 투자 비율 계산
        
        Args:
            p_success: 성공 확률 (0-1)
            upside: 성공 시 이익 (예: 기대 조회수 배수)
            downside: 실패 시 손실 (예: 시간 투자 시간)
            confidence: 확률 추정 신뢰도 (0-1)
        
        Returns:
            KellyDecision: 의사결정 결과
        """
        # 입력 검증
        p_success = max(0.01, min(0.99, p_success))
        confidence = max(0.1, min(1.0, confidence))
        
        # Kelly Criterion 계산
        b = upside / (downside + 1e-10)  # 배당률
        p = p_success
        q = 1 - p
        
        # 기본 Kelly: f* = (bp - q) / b
        kelly_fraction = (b * p - q) / b if b > 0 else 0
        kelly_fraction = max(0, min(1, kelly_fraction))
        
        # Fractional Kelly (안전 버전)
        safe_kelly = kelly_fraction * confidence * self.fractional_multiplier
        safe_kelly = max(0, min(1, safe_kelly))
        
        # 기대값
        expected_value = p * upside - q * downside
        
        # 신호 결정
        if kelly_fraction <= 0 or expected_value < 0:
            signal = "NO_GO"
            reason = "기대값 음수: 진입 금지"
            action = "손절 또는 포기"
        elif safe_kelly < self.moderate_threshold:
            signal = "CAUTION"
            reason = "낮은 기대값: 최소 투자만"
            action = "실험적 시도만"
        elif safe_kelly < self.go_threshold:
            signal = "MODERATE"
            reason = "적정 기대값: 중간 투자"
            action = "표준 리소스 배분"
        else:
            signal = "GO"
            reason = "높은 기대값: 적극 투자"
            action = "집중 투자 권장"
        
        decision = KellyDecision(
            raw_kelly_fraction=round(kelly_fraction, 4),
            safe_kelly_fraction=round(safe_kelly, 4),
            recommended_effort_percent=round(safe_kelly * 100, 1),
            expected_value=round(expected_value, 2),
            signal=signal,
            reason=reason,
            action=action,
            inputs={
                "p_success": round(p, 4),
                "upside": upside,
                "downside": downside,
                "confidence": confidence,
                "odds_ratio": round(b, 4),
            },
        )
        
        logger.info(
            f"Kelly Decision: p={p:.2%}, b={b:.2f}, "
            f"kelly={kelly_fraction:.2%}, safe={safe_kelly:.2%}, "
            f"signal={signal}"
        )
        
        return decision
    
    def calculate_from_stpf(
        self,
        score_1000: int,
        p_success: Optional[float] = None,
        time_investment_hours: float = 10.0,
        expected_view_multiplier: float = 3.0,
    ) -> KellyDecision:
        """STPF 점수에서 Kelly 계산
        
        Args:
            score_1000: STPF 점수 (0-1000)
            p_success: 성공 확률 (없으면 점수에서 추정)
            time_investment_hours: 예상 투자 시간 (시간)
            expected_view_multiplier: 성공 시 평균 대비 조회수 배수
        
        Returns:
            KellyDecision: 의사결정 결과
        """
        # 점수에서 성공 확률 추정 (없는 경우)
        if p_success is None:
            # 시그모이드 변환: S자 곡선
            # score 500 → p = 0.5
            # score 800 → p = 0.88
            # score 300 → p = 0.27
            k = 0.01
            x0 = 500
            p_success = 1 / (1 + pow(2.718, -k * (score_1000 - x0)))
        
        # 손익 기반 계산
        upside = expected_view_multiplier
        downside = time_investment_hours / 10.0  # 시간을 노력 단위로 정규화
        
        # 점수에서 신뢰도 추정
        confidence = min(1.0, 0.5 + (score_1000 - 500) / 1000)
        confidence = max(0.3, confidence)
        
        decision = self.calculate_optimal_bet(
            p_success=p_success,
            upside=upside,
            downside=downside,
            confidence=confidence,
        )
        
        # 등급 정보 추가
        decision.grade_info = self.get_grade_info(score_1000).model_dump()
        
        return decision
    
    def get_grade_info(self, score_1000: int) -> GradeInfo:
        """STPF 점수에서 등급 정보 반환"""
        for (low, high), info in STPF_GRADE_BRACKETS.items():
            if low <= score_1000 < high:
                return GradeInfo(
                    score_1000=score_1000,
                    grade=info["grade"],
                    label=info["label"],
                    description=info["description"],
                    action=info["action"],
                    kelly_hint=info["kelly_hint"],
                    color=info["color"],
                )
        
        # 기본값 (C 등급)
        fallback = STPF_GRADE_BRACKETS[(0, 250)]
        return GradeInfo(
            score_1000=score_1000,
            grade=fallback["grade"],
            label=fallback["label"],
            description=fallback["description"],
            action=fallback["action"],
            kelly_hint=fallback["kelly_hint"],
            color=fallback["color"],
        )
    
    def compare_options(
        self,
        options: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """여러 옵션 비교
        
        Args:
            options: [{"name": str, "p_success": float, "upside": float, "downside": float}, ...]
        
        Returns:
            비교 결과 및 추천
        """
        results = []
        
        for opt in options:
            decision = self.calculate_optimal_bet(
                p_success=opt["p_success"],
                upside=opt["upside"],
                downside=opt["downside"],
                confidence=opt.get("confidence", 1.0),
            )
            results.append({
                "name": opt["name"],
                "decision": decision.model_dump(),
                "expected_value": decision.expected_value,
                "recommended_effort": decision.recommended_effort_percent,
            })
        
        # 기대값 순 정렬
        results.sort(key=lambda x: x["expected_value"], reverse=True)
        
        # 추천
        if results and results[0]["expected_value"] > 0:
            recommended = results[0]["name"]
        else:
            recommended = None
        
        return {
            "options": results,
            "recommended": recommended,
            "total_options": len(options),
        }


# Singleton instance
kelly_engine = KellyDecisionEngine()
