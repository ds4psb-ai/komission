"""
STPF Behavior Connector v1.0

코칭 세션, Ops 승격 등 실제 행동 데이터를
STPF Bayesian 학습 시스템과 연결합니다.

연결점:
1. CoachingSession.compliance_rate → PatternEvidence
2. CoachingUploadOutcome.early_views_bucket → Bayesian update_outcome
3. OutlierItem PROMOTED → STPF score 기록
"""
import logging
from typing import Optional, Dict, Any, Literal
from datetime import datetime

from app.services.stpf.bayesian_updater import (
    BayesianPatternUpdater, 
    PatternEvidence,
    BayesianPrior,
    bayesian_updater
)
from app.services.stpf.free_energy import (
    FreeEnergyChecker,
    free_energy_checker
)

logger = logging.getLogger(__name__)


class STPFBehaviorConnector:
    """
    행동 데이터 → STPF 학습 연결기
    
    v1.0:
    - 코칭 세션 완료 시 패턴 신뢰도 업데이트
    - 업로드 성과 시 Free Energy 캘리브레이션
    - Ops 승격 시 STPF 점수 기록
    """
    
    VERSION = "1.0"
    
    # 성과 버킷 → 성공 여부 매핑
    VIEWS_BUCKET_SUCCESS = {
        "0-100": False,      # 실패
        "100-1K": False,     # 실패
        "1K-10K": None,      # 불확실 (무시)
        "10K-100K": True,    # 성공
        "100K+": True,       # 확실한 성공
    }
    
    # Compliance rate 임계값
    COMPLIANCE_SUCCESS_THRESHOLD = 0.7  # 70% 이상 준수 = 성공적 코칭
    
    def __init__(
        self,
        bayesian: Optional[BayesianPatternUpdater] = None,
        free_energy: Optional[FreeEnergyChecker] = None,
    ):
        self.bayesian = bayesian or bayesian_updater
        self.free_energy = free_energy or free_energy_checker
        self._stpf_records: Dict[str, Dict[str, Any]] = {}  # outlier_id → STPF data
    
    # ==================
    # P2: COACHING → BAYESIAN
    # ==================
    
    def on_coaching_session_end(
        self,
        pattern_id: str,
        compliance_rate: Optional[float],
        intervention_count: int,
        uploaded: bool = False,
        early_views_bucket: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        코칭 세션 종료 시 호출
        
        Args:
            pattern_id: 연습한 패턴 ID
            compliance_rate: 준수율 (0.0~1.0)
            intervention_count: 개입 횟수
            uploaded: 업로드 여부
            early_views_bucket: 조회수 버킷 (있으면)
        
        Returns:
            업데이트 결과
        """
        result = {
            "pattern_id": pattern_id,
            "action": None,
            "prior_before": None,
            "prior_after": None,
            "confidence_updated": False,
        }
        
        # 1. Compliance rate 기반 패턴 신뢰도 업데이트
        if compliance_rate is not None and intervention_count > 0:
            # 높은 compliance = 패턴이 잘 학습됨 = 성공 증거
            success = compliance_rate >= self.COMPLIANCE_SUCCESS_THRESHOLD
            
            try:
                # Get existing prior or create default
                default_prior = BayesianPrior(
                    pattern_id=pattern_id, 
                    p_success=0.5, 
                    sample_count=0
                )
                prior_before = self.bayesian.prior_database.get(pattern_id, default_prior)
                
                evidence = PatternEvidence(
                    pattern_id=pattern_id,
                    outcome="success" if success else "failure",
                    confidence=min(compliance_rate, 1.0),
                    source="coaching_session",
                )
                posterior = self.bayesian.update_posterior(pattern_id, evidence)
                
                result["prior_before"] = prior_before.p_success
                result["prior_after"] = posterior.p_success
                result["confidence_updated"] = True
                result["action"] = "bayesian_update"
                
                logger.info(
                    f"STPF Bayesian updated: {pattern_id}, "
                    f"compliance={compliance_rate:.2f}, "
                    f"prior: {prior_before.p_success:.3f} → {posterior.p_success:.3f}"
                )
            except Exception as e:
                logger.error(f"Bayesian update failed: {e}")
        
        # 2. 업로드 성과 기반 Free Energy 캘리브레이션
        if uploaded and early_views_bucket:
            try:
                bucket_success = self.VIEWS_BUCKET_SUCCESS.get(early_views_bucket)
                if bucket_success is not None:
                    # Free Energy에 실제 성과 피드백
                    predicted_score = 500  # 기본 예측 점수
                    actual_success = 1.0 if bucket_success else 0.0
                    
                    self.free_energy.add_prediction(
                        pattern_id=pattern_id,
                        predicted=predicted_score / 1000,  # 0~1 정규화
                        actual=actual_success,
                    )
                    
                    result["free_energy_updated"] = True
                    result["views_bucket"] = early_views_bucket
                    result["bucket_success"] = bucket_success
                    
                    logger.info(
                        f"STPF Free Energy updated: {pattern_id}, "
                        f"bucket={early_views_bucket}, success={bucket_success}"
                    )
            except Exception as e:
                logger.error(f"Free Energy update failed: {e}")
        
        return result
    
    # ==================
    # P3: OPS PROMOTION → STPF
    # ==================
    
    def on_outlier_promoted(
        self,
        outlier_id: str,
        stpf_score: int,
        stpf_grade: str,
        stpf_signal: str,
        promoter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Outlier 승격 시 STPF 점수 기록
        
        Args:
            outlier_id: OutlierItem ID
            stpf_score: STPF 점수 (0~1000)
            stpf_grade: 등급 (S/A/B/C)
            stpf_signal: 신호 (GO/CONSIDER/NO-GO)
            promoter_id: 승격한 운영자 ID
        
        Returns:
            기록 결과
        """
        record = {
            "outlier_id": outlier_id,
            "stpf_score": stpf_score,
            "stpf_grade": stpf_grade,
            "stpf_signal": stpf_signal,
            "promoter_id": promoter_id,
            "promoted_at": datetime.now().isoformat(),
        }
        
        self._stpf_records[outlier_id] = record
        
        logger.info(
            f"STPF Promotion recorded: {outlier_id}, "
            f"score={stpf_score}, grade={stpf_grade}, signal={stpf_signal}"
        )
        
        return record
    
    def get_promotion_stpf_correlation(self) -> Dict[str, Any]:
        """
        승격된 아웃라이어들의 STPF 점수 분포 분석
        
        Returns:
            상관관계 분석 결과
        """
        if not self._stpf_records:
            return {"status": "no_data", "count": 0}
        
        records = list(self._stpf_records.values())
        scores = [r["stpf_score"] for r in records]
        grades = [r["stpf_grade"] for r in records]
        
        # 통계
        avg_score = sum(scores) / len(scores) if scores else 0
        grade_counts = {}
        for g in grades:
            grade_counts[g] = grade_counts.get(g, 0) + 1
        
        return {
            "status": "ok",
            "count": len(records),
            "avg_score": round(avg_score, 1),
            "grade_distribution": grade_counts,
            "go_rate": sum(1 for r in records if r["stpf_signal"] == "GO") / len(records),
        }
    
    # ==================
    # PATTERN FEEDBACK QUERY
    # ==================
    
    def get_pattern_learning_stats(self, pattern_id: str) -> Dict[str, Any]:
        """
        특정 패턴의 학습 통계 조회
        
        Returns:
            Bayesian prior, Free Energy 상태
        """
        try:
            default_prior = BayesianPrior(
                pattern_id=pattern_id, 
                p_success=0.5, 
                sample_count=0
            )
            prior = self.bayesian.prior_database.get(pattern_id, default_prior)
            fe_result = self.free_energy.calculate_free_energy()
            
            return {
                "pattern_id": pattern_id,
                "bayesian": {
                    "p_success": prior.p_success,
                    "sample_count": prior.sample_count,
                    "last_updated": getattr(prior, 'last_updated', None),
                },
                "free_energy": {
                    "entropy": fe_result.entropy,
                    "surprise": fe_result.surprise,
                    "free_energy": fe_result.free_energy,
                    "health_status": fe_result.health_status,
                },
            }
        except Exception as e:
            logger.error(f"Pattern stats query failed: {e}")
            return {"error": str(e)}


# Singleton instance
_connector_instance: Optional[STPFBehaviorConnector] = None


def get_behavior_connector() -> STPFBehaviorConnector:
    """Get singleton behavior connector."""
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = STPFBehaviorConnector()
    return _connector_instance
