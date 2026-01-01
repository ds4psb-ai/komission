"""
STPF v3.1 Bayesian Pattern Updater

정밀 베이지안 갱신기 - PatternCalibrator를 대체.

수식: P(S|E) = P(E|S) × P(S) / P(E)
- P(S): Prior (기존 성공 확률)
- P(E|S): Likelihood (성공했을 때 이 증거가 나올 확률)
- P(E): Evidence (이 증거가 나올 전체 확률)

출력: 확률 + 95% 신뢰구간 (Wilson Score Interval)
"""
import math
import logging
from typing import Dict, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)


class BayesianPrior(BaseModel):
    """Prior 데이터"""
    pattern_id: str = ""
    p_success: float = Field(default=0.5, ge=0, le=1, description="성공 확률")
    sample_count: int = Field(default=0, ge=0, description="샘플 수")
    last_updated: Optional[str] = None


class PatternEvidence(BaseModel):
    """패턴 증거 데이터"""
    pattern_id: str
    outcome: str = Field(description="success | failure | unknown")
    proof_strength: float = Field(ge=1, le=10, description="증거 강도 1-10")
    cost_paid: float = Field(default=0, ge=0, description="지불한 비용 (시간/노력)")
    
    # 추가 컨텍스트
    view_count: Optional[int] = None
    engagement_rate: Optional[float] = None
    content_id: Optional[str] = None
    observed_at: Optional[str] = None


class BayesianPosterior(BaseModel):
    """Posterior 결과"""
    pattern_id: str
    p_success: float = Field(ge=0, le=1, description="갱신된 성공 확률")
    confidence_interval: Tuple[float, float] = Field(description="95% 신뢰구간 (low, high)")
    sample_count: int = Field(ge=0, description="총 샘플 수")
    
    # 계산 상세
    likelihood: float = Field(ge=0, le=1, description="Likelihood P(E|S)")
    prior: float = Field(ge=0, le=1, description="Prior P(S)")
    evidence_probability: float = Field(default=0.5, description="Evidence P(E)")
    
    # 메타데이터
    updated_at: Optional[str] = None
    
    def get_confidence_level(self) -> str:
        """신뢰도 레벨 반환"""
        ci_width = self.confidence_interval[1] - self.confidence_interval[0]
        if ci_width < 0.1:
            return "HIGH"
        elif ci_width < 0.3:
            return "MEDIUM"
        else:
            return "LOW"


class BayesianPatternUpdater:
    """정밀 베이지안 갱신기
    
    PatternCalibrator를 대체하는 정밀 베이지안 업데이터.
    패턴별 성공 확률을 증거 기반으로 갱신합니다.
    """
    
    VERSION = "1.0"
    
    def __init__(self):
        # In-memory prior database (실제로는 DB 연동 필요)
        self.prior_database: Dict[str, BayesianPrior] = {}
        
        # 기본 하이퍼파라미터
        self.default_prior = 0.5  # 50% 성공률 시작
        self.likelihood_base = 0.7  # 기본 likelihood
        self.z_score = 1.96  # 95% CI
    
    def update_posterior(
        self,
        pattern_id: str,
        evidence: PatternEvidence,
    ) -> BayesianPosterior:
        """베이지안 정리로 Posterior 업데이트
        
        P(S|E) = P(E|S) × P(S) / P(E)
        
        Args:
            pattern_id: 패턴 ID
            evidence: 관찰된 증거
        
        Returns:
            BayesianPosterior: 갱신된 확률 + 신뢰구간
        """
        
        # 1. Prior 로드 (없으면 기본값)
        prior = self.prior_database.get(
            pattern_id,
            BayesianPrior(pattern_id=pattern_id, p_success=self.default_prior, sample_count=0)
        )
        
        # 2. Likelihood 계산 P(E|S)
        if evidence.outcome == "success":
            likelihood = self._calculate_success_likelihood(evidence)
        elif evidence.outcome == "failure":
            likelihood = 1 - self._calculate_success_likelihood(evidence)
        else:
            # unknown - 약한 positive 신호로 처리
            likelihood = 0.5 + (evidence.proof_strength - 5) * 0.02
            likelihood = max(0.1, min(0.9, likelihood))
        
        # 3. Evidence Probability P(E) 추정
        p_evidence = self._estimate_evidence_probability(pattern_id, evidence)
        
        # 4. Odds 방식 Posterior 계산 (수치 안정성)
        # Log-odds 방식으로 overflow 방지
        epsilon = 1e-10
        
        odds_prior = prior.p_success / (1 - prior.p_success + epsilon)
        likelihood_ratio = likelihood / (1 - likelihood + epsilon)
        odds_posterior = odds_prior * likelihood_ratio
        
        # Posterior 확률
        p_posterior = odds_posterior / (1 + odds_posterior)
        p_posterior = max(0.01, min(0.99, p_posterior))  # 극단값 방지
        
        # 5. Wilson Score Interval (95% CI)
        n = prior.sample_count + 1
        ci_low, ci_high = self._wilson_confidence_interval(p_posterior, n)
        
        # 6. Prior 업데이트 (in-memory)
        self.prior_database[pattern_id] = BayesianPrior(
            pattern_id=pattern_id,
            p_success=p_posterior,
            sample_count=n,
            last_updated=datetime.now().isoformat(),
        )
        
        posterior = BayesianPosterior(
            pattern_id=pattern_id,
            p_success=p_posterior,
            confidence_interval=(ci_low, ci_high),
            sample_count=n,
            likelihood=likelihood,
            prior=prior.p_success,
            evidence_probability=p_evidence,
            updated_at=datetime.now().isoformat(),
        )
        
        logger.info(
            f"Bayesian Update: pattern={pattern_id}, "
            f"prior={prior.p_success:.3f} → posterior={p_posterior:.3f}, "
            f"CI=({ci_low:.3f}, {ci_high:.3f}), n={n}"
        )
        
        return posterior
    
    def _calculate_success_likelihood(self, evidence: PatternEvidence) -> float:
        """성공 시 해당 증거 발생 확률 P(E|S)
        
        강한 증거 = 성공과 강하게 연관
        """
        base_likelihood = self.likelihood_base
        
        # Proof 강도에 따른 조정 (Rule 2: 증거가 핵심)
        if evidence.proof_strength > 7:
            base_likelihood += 0.2
        elif evidence.proof_strength > 5:
            base_likelihood += 0.1
        elif evidence.proof_strength < 4:
            base_likelihood -= 0.3
        elif evidence.proof_strength < 3:
            base_likelihood -= 0.4
        
        # 비용 지불 증거 (Handicap Principle)
        if evidence.cost_paid > 0:
            # 비용 지불 = 신호 신뢰도 증가
            cost_boost = min(0.15, evidence.cost_paid / 100)
            base_likelihood += cost_boost
        
        # Engagement rate가 있으면 추가 조정
        if evidence.engagement_rate is not None:
            if evidence.engagement_rate > 0.1:  # 10% 이상
                base_likelihood += 0.1
            elif evidence.engagement_rate > 0.05:
                base_likelihood += 0.05
        
        return max(0.1, min(0.95, base_likelihood))
    
    def _estimate_evidence_probability(
        self, 
        pattern_id: str, 
        evidence: PatternEvidence
    ) -> float:
        """Evidence 발생 확률 P(E) 추정
        
        전체 데이터에서 이 증거가 나올 확률.
        정확한 추정이 어려우므로 휴리스틱 사용.
        """
        # 기본: 0.5 (최대 엔트로피)
        p_evidence = 0.5
        
        # 증거 강도가 극단적이면 희귀한 증거
        if evidence.proof_strength > 8 or evidence.proof_strength < 2:
            p_evidence = 0.3
        
        return p_evidence
    
    def _wilson_confidence_interval(
        self, 
        p: float, 
        n: int
    ) -> Tuple[float, float]:
        """Wilson Score Interval 계산
        
        작은 샘플에서도 안정적인 신뢰구간.
        """
        if n == 0:
            return (0.0, 1.0)
        
        z = self.z_score
        z2 = z * z
        
        denominator = 1 + z2 / n
        center = p + z2 / (2 * n)
        
        # sqrt 내부가 음수가 되지 않도록
        variance = (p * (1 - p) + z2 / (4 * n)) / n
        if variance < 0:
            variance = 0
        
        half_width = z * math.sqrt(variance)
        
        ci_low = (center - half_width) / denominator
        ci_high = (center + half_width) / denominator
        
        return (max(0.0, ci_low), min(1.0, ci_high))
    
    def get_prior(self, pattern_id: str) -> Optional[BayesianPrior]:
        """패턴의 현재 Prior 조회"""
        return self.prior_database.get(pattern_id)
    
    def set_prior(self, prior: BayesianPrior) -> None:
        """패턴 Prior 직접 설정 (DB 로드 등)"""
        self.prior_database[prior.pattern_id] = prior
    
    def reset_pattern(self, pattern_id: str) -> None:
        """패턴 데이터 리셋"""
        if pattern_id in self.prior_database:
            del self.prior_database[pattern_id]


# Singleton instance
bayesian_updater = BayesianPatternUpdater()
