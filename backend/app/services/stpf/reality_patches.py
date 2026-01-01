"""
STPF v3.1 Reality Distortion Patches

일반 공식으로 설명 안 되는 Outlier 처리.

4가지 패치:
- Patch A: Capital Override (자본 보정)
- Patch B: Overconfidence Penalty (자신감의 역설)
- Patch C: Trust Collapse (신뢰 붕괴)
- Patch D: Network Winner-Takes-All (승자독식)
"""
import math
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PatchContext(BaseModel):
    """패치 적용을 위한 컨텍스트"""
    # Core variables
    essence: float = Field(ge=1, le=10, default=5.0)
    proof: float = Field(ge=1, le=10, default=5.0)
    trust: float = Field(ge=1, le=10, default=5.0)
    network: float = Field(ge=1, le=10, default=5.0)
    
    # Extended context
    capital: float = Field(default=0, description="투입 자본 (원)")
    confidence_level: float = Field(ge=1, le=10, default=5.0, description="자신감 수준")
    retention: float = Field(ge=0, le=1, default=0.5, description="시청 유지율")
    
    # Optional
    content_id: Optional[str] = None
    pattern_id: Optional[str] = None


class PatchResult(BaseModel):
    """패치 적용 결과"""
    original_score: float
    patched_score: float
    patches_applied: list = Field(default_factory=list)
    total_adjustment: float = 0.0


class RealityDistortionPatches:
    """일반 공식으로 설명 안 되는 Outlier 처리기
    
    현실은 수식보다 복잡합니다.
    이 패치들은 예외적인 상황을 보정합니다.
    """
    
    VERSION = "1.0"
    
    # 패치 파라미터
    CAPITAL_THRESHOLD = 1_000_000  # 100만원
    CAPITAL_BOOST_FACTOR = 0.1
    
    OVERCONFIDENCE_PENALTY = 0.3  # eta
    OVERCONFIDENCE_PROOF_THRESHOLD = 5
    OVERCONFIDENCE_CONFIDENCE_THRESHOLD = 7
    
    TRUST_COLLAPSE_THRESHOLD = 6
    TRUST_COLLAPSE_FACTOR = 0.2
    
    NETWORK_THRESHOLD = 8
    RETENTION_THRESHOLD = 0.7
    NETWORK_BOOST_FACTOR = 1.3
    
    def apply_all_patches(
        self, 
        score: float, 
        context: PatchContext
    ) -> PatchResult:
        """모든 패치 순차 적용
        
        Args:
            score: 원본 STPF 점수
            context: 패치 컨텍스트
        
        Returns:
            PatchResult: 패치 결과
        """
        original_score = score
        patches_applied = []
        
        # Patch A: Capital Override
        new_score, applied = self.patch_a_capital_override(score, context)
        if applied:
            patches_applied.append({
                "patch": "A_CAPITAL_OVERRIDE",
                "before": score,
                "after": new_score,
                "reason": f"capital={context.capital:,.0f} > {self.CAPITAL_THRESHOLD:,}",
            })
            score = new_score
        
        # Patch B: Overconfidence Penalty
        new_score, applied = self.patch_b_overconfidence_penalty(score, context)
        if applied:
            patches_applied.append({
                "patch": "B_OVERCONFIDENCE_PENALTY",
                "before": score,
                "after": new_score,
                "reason": f"proof={context.proof} < 5, confidence={context.confidence_level} > 7",
            })
            score = new_score
        
        # Patch C: Trust Collapse
        new_score, applied = self.patch_c_trust_collapse(score, context)
        if applied:
            patches_applied.append({
                "patch": "C_TRUST_COLLAPSE",
                "before": score,
                "after": new_score,
                "reason": f"trust={context.trust} < {self.TRUST_COLLAPSE_THRESHOLD}",
            })
            score = new_score
        
        # Patch D: Network Winner-Takes-All
        new_score, applied = self.patch_d_network_winner_takes_all(score, context)
        if applied:
            patches_applied.append({
                "patch": "D_NETWORK_WINNER_TAKES_ALL",
                "before": score,
                "after": new_score,
                "reason": f"network={context.network} > 8, retention={context.retention:.2f} > 0.7",
            })
            score = new_score
        
        result = PatchResult(
            original_score=original_score,
            patched_score=score,
            patches_applied=patches_applied,
            total_adjustment=score - original_score,
        )
        
        if patches_applied:
            logger.info(
                f"Reality Patches Applied: {len(patches_applied)} patches, "
                f"score {original_score:.2f} → {score:.2f}"
            )
        
        return result
    
    def patch_a_capital_override(
        self, 
        score: float, 
        ctx: PatchContext
    ) -> tuple[float, bool]:
        """Patch A: 규모의 경제 보정
        
        본질 낮아도 자본이 압도적이면 생존.
        대형 프로덕션의 중저품질 콘텐츠가 그래도 성공하는 현상.
        """
        if ctx.essence <= 3 and ctx.capital > self.CAPITAL_THRESHOLD:
            boost = math.log10(1 + ctx.capital)
            new_score = score * (1 + boost * self.CAPITAL_BOOST_FACTOR)
            return new_score, True
        return score, False
    
    def patch_b_overconfidence_penalty(
        self, 
        score: float, 
        ctx: PatchContext
    ) -> tuple[float, bool]:
        """Patch B: 자신감의 역설
        
        증거 없는 자신감은 감점.
        "확신하는데 증거가 없다" = 위험 신호.
        """
        if (ctx.proof < self.OVERCONFIDENCE_PROOF_THRESHOLD and 
            ctx.confidence_level > self.OVERCONFIDENCE_CONFIDENCE_THRESHOLD):
            penalty = ctx.confidence_level * self.OVERCONFIDENCE_PENALTY * 0.1
            new_score = score * (1 - penalty)
            return new_score, True
        return score, False
    
    def patch_c_trust_collapse(
        self, 
        score: float, 
        ctx: PatchContext
    ) -> tuple[float, bool]:
        """Patch C: 신뢰 붕괴
        
        Trust Gate 하락 시 급락.
        신뢰가 무너지면 다른 모든 것이 무의미.
        """
        if ctx.trust < self.TRUST_COLLAPSE_THRESHOLD:
            new_score = score * self.TRUST_COLLAPSE_FACTOR
            return new_score, True
        return score, False
    
    def patch_d_network_winner_takes_all(
        self, 
        score: float, 
        ctx: PatchContext
    ) -> tuple[float, bool]:
        """Patch D: 네트워크 승자독식
        
        임계점 돌파 시 가속.
        바이럴이 바이럴을 낳는 자기강화 루프.
        """
        if (ctx.network > self.NETWORK_THRESHOLD and 
            ctx.retention > self.RETENTION_THRESHOLD):
            new_score = score * self.NETWORK_BOOST_FACTOR
            return new_score, True
        return score, False
    
    def get_applicable_patches(self, ctx: PatchContext) -> list[str]:
        """적용 가능한 패치 목록 미리보기"""
        applicable = []
        
        if ctx.essence <= 3 and ctx.capital > self.CAPITAL_THRESHOLD:
            applicable.append("A_CAPITAL_OVERRIDE")
        
        if (ctx.proof < self.OVERCONFIDENCE_PROOF_THRESHOLD and 
            ctx.confidence_level > self.OVERCONFIDENCE_CONFIDENCE_THRESHOLD):
            applicable.append("B_OVERCONFIDENCE_PENALTY")
        
        if ctx.trust < self.TRUST_COLLAPSE_THRESHOLD:
            applicable.append("C_TRUST_COLLAPSE")
        
        if (ctx.network > self.NETWORK_THRESHOLD and 
            ctx.retention > self.RETENTION_THRESHOLD):
            applicable.append("D_NETWORK_WINNER_TAKES_ALL")
        
        return applicable


# Singleton instance
reality_patches = RealityDistortionPatches()
