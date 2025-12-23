"""
Pattern Calibrator - Feedback Loop for Self-Learning System
"데이터가 쌓이면 예측 정확도가 자동으로 향상되는 핵심 엔진"
"""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.schemas.viral_codebook import VisualPatternCode, AudioPatternCode, SemanticIntent


class PatternCalibrator:
    """
    실제 성과 데이터를 기반으로 패턴 신뢰도를 보정하는 서비스
    
    작동 방식:
    1. 영상 분석 시 predicted_retention 기록
    2. 실제 업로드 후 actual_retention 수집 (Platform API or 수동)
    3. 오차(error) 계산 → pattern_confidence 업데이트
    4. 다음 예측 시 confidence 가중치 적용
    """
    
    async def record_prediction(
        self,
        db: AsyncSession,
        node_id: str,
        pattern_code: str,
        pattern_type: str,  # "visual" | "audio" | "semantic"
        predicted_retention: float,
        segment_index: int = 0
    ) -> Dict:
        """
        예측값 기록 (영상 분석 직후 호출)
        """
        from app.models import PatternPrediction
        
        prediction = PatternPrediction(
            node_id=node_id,
            pattern_code=pattern_code,
            pattern_type=pattern_type,
            segment_index=segment_index,
            predicted_retention=predicted_retention,
            created_at=datetime.utcnow()
        )
        
        db.add(prediction)
        await db.commit()
        
        return {
            "recorded": True,
            "node_id": node_id,
            "pattern": pattern_code,
            "predicted": predicted_retention
        }
    
    async def record_actual_performance(
        self,
        db: AsyncSession,
        node_id: str,
        actual_retention: float,
        actual_views: int = 0,
        source: str = "manual"  # "tiktok_api" | "youtube_api" | "manual"
    ) -> Dict:
        """
        실제 성과 기록 및 신뢰도 보정 트리거
        """
        from app.models import PatternPrediction, PatternConfidence
        
        # 1. 해당 노드의 모든 예측 찾기
        result = await db.execute(
            select(PatternPrediction).where(PatternPrediction.node_id == node_id)
        )
        predictions = result.scalars().all()
        
        if not predictions:
            return {"calibrated": False, "reason": "No predictions found"}
        
        calibration_results = []
        
        # 2. 각 예측에 대해 오차 계산 및 신뢰도 업데이트
        for pred in predictions:
            error = actual_retention - pred.predicted_retention
            
            # 예측 레코드 업데이트
            pred.actual_retention = actual_retention
            pred.prediction_error = error
            pred.verified_at = datetime.utcnow()
            pred.verification_source = source
            
            # 패턴 신뢰도 테이블 업데이트
            await self._update_pattern_confidence(
                db=db,
                pattern_code=pred.pattern_code,
                pattern_type=pred.pattern_type,
                error=error
            )
            
            calibration_results.append({
                "pattern": pred.pattern_code,
                "predicted": pred.predicted_retention,
                "actual": actual_retention,
                "error": round(error, 3)
            })
        
        await db.commit()
        
        return {
            "calibrated": True,
            "node_id": node_id,
            "patterns_updated": len(calibration_results),
            "details": calibration_results
        }
    
    async def _update_pattern_confidence(
        self,
        db: AsyncSession,
        pattern_code: str,
        pattern_type: str,
        error: float
    ):
        """
        패턴 신뢰도 점수 업데이트 (이동 평균 방식)
        """
        from app.models import PatternConfidence
        
        # 기존 레코드 찾기
        result = await db.execute(
            select(PatternConfidence).where(
                PatternConfidence.pattern_code == pattern_code,
                PatternConfidence.pattern_type == pattern_type
            )
        )
        confidence = result.scalar_one_or_none()
        
        if confidence:
            # 이동 평균으로 업데이트
            new_sample_count = confidence.sample_count + 1
            # 새로운 평균 오차 = (이전 평균 * 이전 샘플수 + 새 오차) / 새 샘플수
            new_avg_error = (
                (confidence.avg_absolute_error * confidence.sample_count) + abs(error)
            ) / new_sample_count
            
            # 신뢰도 = 1 - 평균 오차 (오차가 작을수록 신뢰도 높음)
            new_confidence = max(0.0, min(1.0, 1.0 - new_avg_error))
            
            confidence.sample_count = new_sample_count
            confidence.avg_absolute_error = new_avg_error
            confidence.confidence_score = new_confidence
            confidence.last_updated = datetime.utcnow()
        else:
            # 새 레코드 생성
            new_confidence = PatternConfidence(
                pattern_code=pattern_code,
                pattern_type=pattern_type,
                sample_count=1,
                avg_absolute_error=abs(error),
                confidence_score=max(0.0, min(1.0, 1.0 - abs(error))),
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            db.add(new_confidence)
    
    async def get_pattern_confidence(
        self,
        db: AsyncSession,
        pattern_code: str,
        pattern_type: str = "visual"
    ) -> Dict:
        """
        특정 패턴의 신뢰도 조회
        """
        from app.models import PatternConfidence
        
        result = await db.execute(
            select(PatternConfidence).where(
                PatternConfidence.pattern_code == pattern_code,
                PatternConfidence.pattern_type == pattern_type
            )
        )
        confidence = result.scalar_one_or_none()
        
        if confidence:
            return {
                "pattern_code": confidence.pattern_code,
                "confidence_score": confidence.confidence_score,
                "sample_count": confidence.sample_count,
                "avg_error": confidence.avg_absolute_error,
                "status": "trained"
            }
        else:
            # 기본 신뢰도 (데이터 없음)
            return {
                "pattern_code": pattern_code,
                "confidence_score": 0.5,  # 중간값
                "sample_count": 0,
                "avg_error": None,
                "status": "untrained"
            }
    
    async def get_all_pattern_confidences(
        self,
        db: AsyncSession,
        min_samples: int = 5
    ) -> List[Dict]:
        """
        모든 패턴의 신뢰도 랭킹 조회
        """
        from app.models import PatternConfidence
        
        result = await db.execute(
            select(PatternConfidence)
            .where(PatternConfidence.sample_count >= min_samples)
            .order_by(PatternConfidence.confidence_score.desc())
        )
        confidences = result.scalars().all()
        
        return [
            {
                "pattern_code": c.pattern_code,
                "pattern_type": c.pattern_type,
                "confidence": c.confidence_score,
                "samples": c.sample_count,
                "avg_error": c.avg_absolute_error
            }
            for c in confidences
        ]


# Singleton instance
pattern_calibrator = PatternCalibrator()
