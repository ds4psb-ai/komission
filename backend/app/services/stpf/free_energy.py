"""
STPF v3.1 Free Energy Checker

시스템 엔트로피/예측 품질 모니터링.
실제 결과와 예측의 차이를 추적하여 모델 캘리브레이션.
"""
import math
import logging
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class PredictionRecord(BaseModel):
    """예측 기록"""
    content_id: str
    predicted_score: int
    actual_outcome: Optional[str] = None  # success, failure, unknown
    actual_views: Optional[int] = None
    expected_views: Optional[int] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    error: Optional[float] = None


class CalibrationMetrics(BaseModel):
    """캘리브레이션 메트릭"""
    brier_score: float  # 낮을수록 좋음
    log_loss: float
    calibration_error: float
    mean_absolute_error: float
    sample_count: int
    last_updated: datetime = Field(default_factory=datetime.now)


class FreeEnergyResult(BaseModel):
    """자유 에너지 결과"""
    free_energy: float  # 낮을수록 좋음 (시스템이 안정적)
    entropy: float  # 예측 불확실성
    surprise: float  # 예측 오차
    calibration: CalibrationMetrics
    health_status: str  # healthy, degraded, critical
    recommendations: List[str] = Field(default_factory=list)


class FreeEnergyChecker:
    """시스템 자유 에너지 모니터링
    
    Free Energy = Entropy + Surprise
    - Entropy: 예측의 불확실성 (분산)
    - Surprise: 예측과 실제의 차이
    
    목표: Free Energy 최소화 = 정확하고 확신있는 예측
    """
    
    VERSION = "1.0"
    
    def __init__(self, max_history: int = 1000):
        self.predictions: deque = deque(maxlen=max_history)
        self.max_history = max_history
        
        # 임계값
        self.entropy_threshold = 0.5  # 높으면 불확실
        self.surprise_threshold = 0.3  # 높으면 예측 실패
        self.free_energy_threshold = 0.7  # 높으면 시스템 불안정
    
    def record_prediction(
        self,
        content_id: str,
        predicted_score: int,
        predicted_probability: float = 0.5,
    ) -> PredictionRecord:
        """예측 기록"""
        record = PredictionRecord(
            content_id=content_id,
            predicted_score=predicted_score,
        )
        self.predictions.append(record)
        
        logger.info(f"Prediction recorded: {content_id}, score={predicted_score}")
        return record
    
    def update_outcome(
        self,
        content_id: str,
        actual_views: int,
        expected_views: int = 10000,
    ) -> Optional[PredictionRecord]:
        """실제 결과로 예측 갱신"""
        
        for record in reversed(self.predictions):
            if record.content_id == content_id:
                record.actual_views = actual_views
                record.expected_views = expected_views
                
                # 성공/실패 판정
                if actual_views >= expected_views:
                    record.actual_outcome = "success"
                else:
                    record.actual_outcome = "failure"
                
                # 오차 계산 (정규화)
                predicted_success = record.predicted_score >= 500
                actual_success = record.actual_outcome == "success"
                record.error = 0.0 if predicted_success == actual_success else 1.0
                
                logger.info(
                    f"Outcome updated: {content_id}, views={actual_views}, "
                    f"outcome={record.actual_outcome}, error={record.error}"
                )
                return record
        
        logger.warning(f"Prediction not found: {content_id}")
        return None
    
    def calculate_free_energy(self) -> FreeEnergyResult:
        """현재 자유 에너지 계산"""
        
        # 완료된 예측만 사용
        completed = [r for r in self.predictions if r.error is not None]
        
        if len(completed) < 5:
            return FreeEnergyResult(
                free_energy=0.5,
                entropy=0.5,
                surprise=0.0,
                calibration=CalibrationMetrics(
                    brier_score=0.25,
                    log_loss=0.69,
                    calibration_error=0.0,
                    mean_absolute_error=0.0,
                    sample_count=len(completed),
                ),
                health_status="unknown",
                recommendations=["최소 5개 이상의 예측 결과 필요"],
            )
        
        # 1. Entropy 계산 (예측 점수 분산)
        scores = [r.predicted_score for r in completed]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        entropy = min(1.0, variance / 250000)  # 정규화 (500^2)
        
        # 2. Surprise 계산 (예측 오차 평균)
        errors = [r.error for r in completed]
        surprise = sum(errors) / len(errors)
        
        # 3. Free Energy = Entropy + Surprise
        free_energy = entropy + surprise
        
        # 4. Calibration Metrics
        calibration = self._calculate_calibration(completed)
        
        # 5. Health Status
        if free_energy < self.free_energy_threshold * 0.5:
            health_status = "healthy"
        elif free_energy < self.free_energy_threshold:
            health_status = "degraded"
        else:
            health_status = "critical"
        
        # 6. Recommendations
        recommendations = self._generate_recommendations(
            entropy, surprise, calibration
        )
        
        logger.info(
            f"Free Energy: {free_energy:.3f} (E={entropy:.3f}, S={surprise:.3f}), "
            f"status={health_status}"
        )
        
        return FreeEnergyResult(
            free_energy=free_energy,
            entropy=entropy,
            surprise=surprise,
            calibration=calibration,
            health_status=health_status,
            recommendations=recommendations,
        )
    
    def _calculate_calibration(
        self,
        records: List[PredictionRecord],
    ) -> CalibrationMetrics:
        """캘리브레이션 메트릭 계산"""
        
        n = len(records)
        
        # Brier Score: mean((predicted_prob - actual_outcome)^2)
        # 여기서는 score >= 500 → prob 0.5+
        brier_sum = 0.0
        log_loss_sum = 0.0
        abs_error_sum = 0.0
        
        for r in records:
            # 예측 확률 (점수 기반 변환)
            pred_prob = min(0.95, max(0.05, r.predicted_score / 1000))
            actual = 1.0 if r.actual_outcome == "success" else 0.0
            
            # Brier Score
            brier_sum += (pred_prob - actual) ** 2
            
            # Log Loss
            if actual == 1:
                log_loss_sum -= math.log(max(0.001, pred_prob))
            else:
                log_loss_sum -= math.log(max(0.001, 1 - pred_prob))
            
            # MAE
            abs_error_sum += abs(pred_prob - actual)
        
        brier_score = brier_sum / n
        log_loss = log_loss_sum / n
        mae = abs_error_sum / n
        
        # Calibration Error (bin별 차이)
        # 단순화: 전체 예측 정확도와 실제 성공률 차이
        predicted_success = sum(1 for r in records if r.predicted_score >= 500) / n
        actual_success = sum(1 for r in records if r.actual_outcome == "success") / n
        calibration_error = abs(predicted_success - actual_success)
        
        return CalibrationMetrics(
            brier_score=round(brier_score, 4),
            log_loss=round(log_loss, 4),
            calibration_error=round(calibration_error, 4),
            mean_absolute_error=round(mae, 4),
            sample_count=n,
        )
    
    def _generate_recommendations(
        self,
        entropy: float,
        surprise: float,
        calibration: CalibrationMetrics,
    ) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        if entropy > self.entropy_threshold:
            recommendations.append(
                "예측 분산이 높음 - 변수 가중치 조정 검토"
            )
        
        if surprise > self.surprise_threshold:
            recommendations.append(
                "예측 오차가 높음 - 베이지안 Prior 재조정 필요"
            )
        
        if calibration.calibration_error > 0.1:
            recommendations.append(
                f"캘리브레이션 오차 {calibration.calibration_error:.1%} - "
                "점수-확률 매핑 재조정"
            )
        
        if calibration.brier_score > 0.25:
            recommendations.append(
                "Brier Score 높음 - 모델 재훈련 고려"
            )
        
        if not recommendations:
            recommendations.append("시스템 상태 양호")
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 요약"""
        completed = [r for r in self.predictions if r.error is not None]
        
        return {
            "total_predictions": len(self.predictions),
            "completed_predictions": len(completed),
            "success_rate": sum(1 for r in completed if r.actual_outcome == "success") / max(1, len(completed)),
            "accuracy_rate": sum(1 for r in completed if r.error == 0) / max(1, len(completed)),
        }


# Singleton instance
free_energy_checker = FreeEnergyChecker()
