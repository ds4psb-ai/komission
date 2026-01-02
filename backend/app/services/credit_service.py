"""
Credit Service for Audio Coaching

코칭 모드별 크레딧 관리 시스템

Pricing:
- basic: 1 크레딧/분 (규칙 기반 TTS)
- pro: 3 크레딧/분 (Gemini Live + TTS)

Features:
- 크레딧 잔액 조회/차감
- 체험단 크레딧 지원
- 트랜잭션 로그
"""
import logging
from datetime import datetime
from typing import Dict, Literal, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ==================
# CONSTANTS
# ==================

COACHING_COSTS: Dict[str, int] = {
    "basic": 1,  # 1 크레딧/분
    "pro": 3,    # 3 크레딧/분
}

# Free tier: 새 사용자 기본 지급
FREE_TIER_CREDITS = 10

CoachingTier = Literal["basic", "pro"]
TransactionType = Literal[
    "coaching",          # 코칭 사용
    "campaign_grant",    # 체험단 지원
    "purchase",          # 구매
    "refund",            # 환불
    "bonus",             # 보너스
]


# ==================
# IN-MEMORY STORE (MVP)
# Production: DB 사용
# ==================

_user_credits: Dict[str, int] = {}
_transactions: list = []


# ==================
# CORE FUNCTIONS
# ==================

def get_user_credits(user_id: str) -> int:
    """
    사용자 크레딧 잔액 조회
    
    새 사용자인 경우 FREE_TIER_CREDITS 지급
    """
    if user_id not in _user_credits:
        _user_credits[user_id] = FREE_TIER_CREDITS
        _record_transaction(
            user_id=user_id,
            amount=FREE_TIER_CREDITS,
            tx_type="bonus",
            metadata={"reason": "new_user_free_tier"}
        )
        logger.info(f"New user {user_id[:8]}... granted {FREE_TIER_CREDITS} free credits")
    
    return _user_credits[user_id]


def check_sufficient_credits(user_id: str, tier: CoachingTier, duration_sec: float) -> bool:
    """
    코칭에 필요한 크레딧이 충분한지 확인
    """
    required = calculate_coaching_cost(tier, duration_sec)
    balance = get_user_credits(user_id)
    return balance >= required


def calculate_coaching_cost(tier: CoachingTier, duration_sec: float) -> int:
    """
    코칭 비용 계산
    
    Args:
        tier: "basic" or "pro"
        duration_sec: 코칭 시간 (초)
    
    Returns:
        필요 크레딧 (올림 처리)
    """
    cost_per_min = COACHING_COSTS.get(tier, 1)
    minutes = max(1, int((duration_sec + 59) // 60))  # 올림
    return cost_per_min * minutes


def deduct_coaching_credits(
    user_id: str,
    tier: CoachingTier,
    duration_sec: float,
    session_id: Optional[str] = None,
) -> bool:
    """
    코칭 세션에 대한 크레딧 차감
    
    Returns:
        True if successful, False if insufficient balance
    """
    cost = calculate_coaching_cost(tier, duration_sec)
    balance = get_user_credits(user_id)
    
    if balance < cost:
        logger.warning(f"Insufficient credits: {user_id[:8]}... has {balance}, needs {cost}")
        return False
    
    _user_credits[user_id] = balance - cost
    
    _record_transaction(
        user_id=user_id,
        amount=-cost,
        tx_type="coaching",
        metadata={
            "tier": tier,
            "duration_sec": duration_sec,
            "session_id": session_id,
        }
    )
    
    logger.info(f"Deducted {cost} credits from {user_id[:8]}... (tier={tier}, {duration_sec:.0f}s)")
    return True


def grant_campaign_credits(
    user_id: str,
    campaign_id: str,
    amount: int,
    granted_by: Optional[str] = None,
) -> bool:
    """
    체험단 캠페인에서 크리에이터에게 크레딧 지원
    
    Args:
        user_id: 크리에이터 ID
        campaign_id: 캠페인 ID
        amount: 지원 크레딧
        granted_by: 지원자 (브랜드/관리자)
    
    Returns:
        True if successful
    """
    if amount <= 0:
        return False
    
    balance = get_user_credits(user_id)
    _user_credits[user_id] = balance + amount
    
    _record_transaction(
        user_id=user_id,
        amount=amount,
        tx_type="campaign_grant",
        metadata={
            "campaign_id": campaign_id,
            "granted_by": granted_by,
        }
    )
    
    logger.info(f"Granted {amount} credits to {user_id[:8]}... for campaign {campaign_id[:8]}...")
    return True


def refund_credits(
    user_id: str,
    amount: int,
    reason: str,
) -> bool:
    """
    크레딧 환불
    
    코칭 실패, 오류 등으로 인한 환불
    """
    if amount <= 0:
        return False
    
    balance = get_user_credits(user_id)
    _user_credits[user_id] = balance + amount
    
    _record_transaction(
        user_id=user_id,
        amount=amount,
        tx_type="refund",
        metadata={"reason": reason}
    )
    
    logger.info(f"Refunded {amount} credits to {user_id[:8]}...: {reason}")
    return True


def add_credits(
    user_id: str,
    amount: int,
    tx_type: TransactionType = "purchase",
    metadata: Optional[dict] = None,
) -> bool:
    """
    크레딧 추가 (구매, 보너스 등)
    """
    if amount <= 0:
        return False
    
    balance = get_user_credits(user_id)
    _user_credits[user_id] = balance + amount
    
    _record_transaction(
        user_id=user_id,
        amount=amount,
        tx_type=tx_type,
        metadata=metadata or {}
    )
    
    logger.info(f"Added {amount} credits to {user_id[:8]}... ({tx_type})")
    return True


# ==================
# TRANSACTION LOG
# ==================

def _record_transaction(
    user_id: str,
    amount: int,
    tx_type: TransactionType,
    metadata: Optional[dict] = None,
):
    """트랜잭션 기록"""
    tx = {
        "id": str(uuid4()),
        "user_id": user_id,
        "amount": amount,
        "type": tx_type,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }
    _transactions.append(tx)
    return tx


def get_user_transactions(user_id: str, limit: int = 50) -> list:
    """사용자 트랜잭션 조회"""
    user_txs = [tx for tx in _transactions if tx["user_id"] == user_id]
    return sorted(user_txs, key=lambda x: x["created_at"], reverse=True)[:limit]


# ==================
# COACHING SESSION HELPERS
# ==================

class CoachingCreditManager:
    """
    코칭 세션 크레딧 관리자
    
    Usage:
        manager = CoachingCreditManager(user_id, tier="pro")
        
        if not manager.can_start():
            raise InsufficientCredits()
        
        manager.start_session(session_id)
        # ... coaching ...
        manager.end_session(duration_sec=45)
    """
    
    def __init__(self, user_id: str, tier: CoachingTier = "basic"):
        self.user_id = user_id
        self.tier = tier
        self.session_id: Optional[str] = None
        self.started_at: Optional[datetime] = None
    
    @property
    def balance(self) -> int:
        return get_user_credits(self.user_id)
    
    @property
    def cost_per_minute(self) -> int:
        return COACHING_COSTS.get(self.tier, 1)
    
    def can_start(self, min_duration_sec: float = 60) -> bool:
        """최소 시간 코칭 가능한지 확인"""
        return check_sufficient_credits(self.user_id, self.tier, min_duration_sec)
    
    def start_session(self, session_id: str):
        """세션 시작"""
        self.session_id = session_id
        self.started_at = datetime.utcnow()
        logger.info(f"Credit session started: {session_id}, tier={self.tier}")
    
    def end_session(self, duration_sec: float) -> dict:
        """
        세션 종료 및 크레딧 차감
        
        Returns:
            {"success": bool, "cost": int, "balance": int}
        """
        cost = calculate_coaching_cost(self.tier, duration_sec)
        success = deduct_coaching_credits(
            self.user_id, self.tier, duration_sec, self.session_id
        )
        
        return {
            "success": success,
            "cost": cost if success else 0,
            "balance": get_user_credits(self.user_id),
            "tier": self.tier,
            "duration_sec": duration_sec,
        }
    
    def refund_session(self, reason: str = "session_error"):
        """세션 환불 (오류 발생 시)"""
        if self.started_at:
            duration = (datetime.utcnow() - self.started_at).total_seconds()
            cost = calculate_coaching_cost(self.tier, duration)
            refund_credits(self.user_id, cost, reason)


# ==================
# TESTING
# ==================

if __name__ == "__main__":
    # Basic test
    test_user = "test-user-123"
    
    print(f"Initial balance: {get_user_credits(test_user)}")
    
    # Test coaching deduction
    success = deduct_coaching_credits(test_user, "basic", 120)
    print(f"Deducted 2 min basic: {success}, balance: {get_user_credits(test_user)}")
    
    # Test campaign grant
    grant_campaign_credits(test_user, "campaign-abc", 20)
    print(f"After grant: {get_user_credits(test_user)}")
    
    # Test pro tier
    success = deduct_coaching_credits(test_user, "pro", 60)
    print(f"Deducted 1 min pro: {success}, balance: {get_user_credits(test_user)}")
    
    # Show transactions
    print("\nTransactions:")
    for tx in get_user_transactions(test_user):
        print(f"  {tx['type']}: {tx['amount']:+d}")
