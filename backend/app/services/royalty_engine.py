"""
Creator Royalty Engine
Manages automatic point distribution when nodes are forked or achieve milestones.

Key Features:
- Fork Royalty: Original creator earns points when their node is forked
- View Milestone: Bonus points when forked nodes reach view milestones
- K-Success Bonus: Extra points when forked nodes achieve K-Success certification
- Genealogy Bonus: Ancestors in the fork tree also receive partial royalties

🛡️ Anti-Abuse Security (CTO Mandated):
- IP/Device fingerprint tracking to prevent farming
- Daily earning caps per user
- Deferred payout until fork reaches 100 views (impact verification)
"""

from datetime import datetime, timedelta
import hashlib
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from sqlalchemy.orm import selectinload

from app.models import (
    User, RemixNode, NodeRoyalty, RoyaltyReason
)


class RoyaltyConfig:
    """Configuration for royalty point calculations"""
    
    # Base points
    FORK_BASE_POINTS = 10              # Points earned when node is forked
    
    # View milestones (views: points)
    VIEW_MILESTONES = {
        1000: 20,
        5000: 50,
        10000: 100,
        50000: 250,
        100000: 500,
    }
    
    # K-Success bonuses
    K_SUCCESS_FORKER_BONUS = 200       # Forker gets this for K-Success
    K_SUCCESS_CREATOR_BONUS = 100      # Original creator also gets bonus
    
    # Genealogy distribution (depth: ratio of points)
    GENEALOGY_DECAY_RATIO = 0.25
    MAX_GENEALOGY_DEPTH = 3
    
    # 🛡️ Anti-Abuse Configuration
    IMPACT_VERIFICATION_THRESHOLD = 100  # Fork must get 100+ views for points
    DAILY_EARNING_CAP = 500              # Max points per user per day
    MAX_FORKS_PER_IP_PER_NODE = 3        # Same IP can only fork a node 3 times
    MAX_FORKS_PER_DEVICE_PER_NODE = 2    # Same device can only fork a node 2 times


class RoyaltyEngine:
    """
    Handles all royalty calculations and distributions.
    Includes anti-abuse detection and deferred payout.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.config = RoyaltyConfig()
    
    @staticmethod
    def hash_ip(ip_address: str) -> str:
        """Hash IP address for privacy-safe storage"""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    
    async def check_abuse(
        self, 
        source_node_id, 
        ip_hash: Optional[str], 
        device_fp: Optional[str]
    ) -> Tuple[bool, str]:
        """
        Check if this fork request looks like abuse.
        Returns (is_abuse, reason)
        """
        if not ip_hash and not device_fp:
            # Can't verify, allow but mark as unverified
            return False, "no_tracking"
        
        # Check IP abuse
        if ip_hash:
            ip_count = await self.db.scalar(
                select(func.count(NodeRoyalty.id))
                .where(
                    and_(
                        NodeRoyalty.source_node_id == source_node_id,
                        NodeRoyalty.forker_ip_hash == ip_hash
                    )
                )
            )
            if ip_count >= self.config.MAX_FORKS_PER_IP_PER_NODE:
                return True, f"ip_limit_exceeded:{ip_count}"
        
        # Check device fingerprint abuse
        if device_fp:
            device_count = await self.db.scalar(
                select(func.count(NodeRoyalty.id))
                .where(
                    and_(
                        NodeRoyalty.source_node_id == source_node_id,
                        NodeRoyalty.forker_device_fp == device_fp
                    )
                )
            )
            if device_count >= self.config.MAX_FORKS_PER_DEVICE_PER_NODE:
                return True, f"device_limit_exceeded:{device_count}"
        
        return False, "clean"
    
    async def check_daily_cap(self, user_id) -> Tuple[bool, int]:
        """
        Check if user has reached daily earning cap.
        Returns (is_capped, remaining_points)
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_earned = await self.db.scalar(
            select(func.sum(NodeRoyalty.points_earned))
            .where(
                and_(
                    NodeRoyalty.creator_id == user_id,
                    NodeRoyalty.created_at >= today_start
                )
            )
        ) or 0
        
        remaining = max(0, self.config.DAILY_EARNING_CAP - today_earned)
        is_capped = remaining == 0
        
        return is_capped, remaining
    
    async def on_fork(
        self, 
        parent_node: RemixNode, 
        child_node: RemixNode, 
        forker: User,
        ip_address: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> Optional[NodeRoyalty]:
        """
        Called when a node is forked.
        Awards points to the original creator with anti-abuse checks.
        
        🛡️ Security Flow:
        1. Check for IP/device farming
        2. Check daily earning cap
        3. Create transaction with is_impact_verified=False (points pending)
        4. Points only count when fork reaches 100 views
        
        Returns the created NodeRoyalty record, or None if blocked by anti-abuse.
        """
        creator_id = parent_node.created_by
        
        # Don't award points if forking your own node
        if forker.id == creator_id:
            return None
        
        ip_hash = self.hash_ip(ip_address) if ip_address else None
        
        # 🛡️ Anti-Abuse Check
        is_abuse, abuse_reason = await self.check_abuse(parent_node.id, ip_hash, device_fingerprint)
        if is_abuse:
            print(f"⚠️ Royalty blocked: abuse detected ({abuse_reason})")
            # Still create record but with 0 points for audit trail
            royalty = NodeRoyalty(
                creator_id=creator_id,
                source_node_id=parent_node.id,
                forked_node_id=child_node.id,
                forker_id=forker.id,
                forker_ip_hash=ip_hash,
                forker_device_fp=device_fingerprint,
                points_earned=0,  # No points for abuse
                reason=RoyaltyReason.FORK,
                is_impact_verified=False
            )
            self.db.add(royalty)
            await self.db.commit()
            return royalty
        
        # 🛡️ Daily Cap Check
        is_capped, remaining = await self.check_daily_cap(creator_id)
        points = min(self.config.FORK_BASE_POINTS, remaining)
        
        if points <= 0:
            print(f"⚠️ Royalty capped: user {creator_id} hit daily limit")
            points = 0
        
        # Create royalty transaction (pending until impact verified)
        royalty = NodeRoyalty(
            creator_id=creator_id,
            source_node_id=parent_node.id,
            forked_node_id=child_node.id,
            forker_id=forker.id,
            forker_ip_hash=ip_hash,
            forker_device_fp=device_fingerprint,
            points_earned=points,
            reason=RoyaltyReason.FORK,
            is_impact_verified=False  # Points don't count until fork gets views
        )
        self.db.add(royalty)
        
        # Update fork count (always counted)
        await self.db.execute(
            update(RemixNode)
            .where(RemixNode.id == parent_node.id)
            .values(total_fork_count=RemixNode.total_fork_count + 1)
        )
        
        # 💡 Points are NOT added to user balance yet!
        # They will be added when verify_impact() is called
        
        await self.db.commit()
        return royalty
    
    async def verify_impact(self, forked_node_id) -> bool:
        """
        Called when a forked node reaches the view threshold.
        Verifies impact and releases pending royalty points to creator.
        
        This should be called by a background job or view counter.
        """
        # Get all unverified royalties for this fork
        result = await self.db.execute(
            select(NodeRoyalty)
            .where(
                and_(
                    NodeRoyalty.forked_node_id == forked_node_id,
                    NodeRoyalty.is_impact_verified == False,
                    NodeRoyalty.points_earned > 0
                )
            )
        )
        pending_royalties = result.scalars().all()
        
        if not pending_royalties:
            return False
        
        for royalty in pending_royalties:
            # Mark as verified
            royalty.is_impact_verified = True
            
            # Now add points to creator's balance
            await self.db.execute(
                update(User)
                .where(User.id == royalty.creator_id)
                .values(
                    total_royalty_received=User.total_royalty_received + royalty.points_earned,
                    pending_royalty=User.pending_royalty + royalty.points_earned,
                    k_points=User.k_points + royalty.points_earned
                )
            )
            
            # Update node's royalty earned
            await self.db.execute(
                update(RemixNode)
                .where(RemixNode.id == royalty.source_node_id)
                .values(
                    total_royalty_earned=RemixNode.total_royalty_earned + royalty.points_earned
                )
            )
        
        await self.db.commit()
        return True

    
    async def on_view_milestone(
        self, 
        node: RemixNode, 
        new_view_count: int
    ) -> Optional[NodeRoyalty]:
        """
        Called when a node reaches a view milestone.
        Awards bonus points to the creator.
        """
        # Check which milestone was crossed
        bonus_points = 0
        for threshold, points in self.config.VIEW_MILESTONES.items():
            if new_view_count >= threshold and node.view_count < threshold:
                bonus_points = points
                break
        
        if bonus_points == 0:
            return None
        
        # Create royalty transaction
        royalty = NodeRoyalty(
            creator_id=node.created_by,
            source_node_id=node.id,
            forked_node_id=None,
            forker_id=None,
            points_earned=bonus_points,
            reason=RoyaltyReason.VIEW_MILESTONE
        )
        self.db.add(royalty)
        
        # Update creator's balance
        await self.db.execute(
            update(User)
            .where(User.id == node.created_by)
            .values(
                total_royalty_received=User.total_royalty_received + bonus_points,
                pending_royalty=User.pending_royalty + bonus_points,
                k_points=User.k_points + bonus_points
            )
        )
        
        # Update node's royalty earned
        await self.db.execute(
            update(RemixNode)
            .where(RemixNode.id == node.id)
            .values(
                total_royalty_earned=RemixNode.total_royalty_earned + bonus_points
            )
        )
        
        await self.db.commit()
        return royalty
    
    async def on_k_success(
        self, 
        node: RemixNode, 
        achiever: User
    ) -> List[NodeRoyalty]:
        """
        Called when a node achieves K-Success certification.
        Awards bonus to both the forker and original creator.
        """
        royalties = []
        
        # 1. Bonus to the node creator (forker)
        forker_royalty = NodeRoyalty(
            creator_id=achiever.id,
            source_node_id=node.id,
            forked_node_id=None,
            forker_id=None,
            points_earned=self.config.K_SUCCESS_FORKER_BONUS,
            reason=RoyaltyReason.K_SUCCESS
        )
        self.db.add(forker_royalty)
        royalties.append(forker_royalty)
        
        # Update achiever's balance
        await self.db.execute(
            update(User)
            .where(User.id == achiever.id)
            .values(
                total_royalty_received=User.total_royalty_received + self.config.K_SUCCESS_FORKER_BONUS,
                k_points=User.k_points + self.config.K_SUCCESS_FORKER_BONUS
            )
        )
        
        # 2. If this is a fork, also reward the original creator
        if node.parent_node_id:
            # Get parent node to find original creator
            parent = await self.db.get(RemixNode, node.parent_node_id)
            if parent and parent.created_by != achiever.id:
                creator_royalty = NodeRoyalty(
                    creator_id=parent.created_by,
                    source_node_id=parent.id,
                    forked_node_id=node.id,
                    forker_id=achiever.id,
                    points_earned=self.config.K_SUCCESS_CREATOR_BONUS,
                    reason=RoyaltyReason.K_SUCCESS
                )
                self.db.add(creator_royalty)
                royalties.append(creator_royalty)
                
                # Update original creator's balance
                await self.db.execute(
                    update(User)
                    .where(User.id == parent.created_by)
                    .values(
                        total_royalty_received=User.total_royalty_received + self.config.K_SUCCESS_CREATOR_BONUS,
                        pending_royalty=User.pending_royalty + self.config.K_SUCCESS_CREATOR_BONUS,
                        k_points=User.k_points + self.config.K_SUCCESS_CREATOR_BONUS
                    )
                )
        
        await self.db.commit()
        return royalties
    
    async def _award_genealogy_bonus(
        self, 
        node: RemixNode, 
        base_points: int,
        depth: int = 0
    ):
        """
        Recursively award genealogy bonus to ancestors.
        Each ancestor gets a decayed portion of the points.
        """
        if depth >= self.config.MAX_GENEALOGY_DEPTH:
            return
        
        if not node.parent_node_id:
            return
        
        # Get parent node
        parent = await self.db.get(RemixNode, node.parent_node_id)
        if not parent:
            return
        
        # Calculate decayed points
        points = int(base_points * (self.config.GENEALOGY_DECAY_RATIO ** (depth + 1)))
        if points < 1:
            return
        
        # Create genealogy bonus royalty
        royalty = NodeRoyalty(
            creator_id=parent.created_by,
            source_node_id=parent.id,
            forked_node_id=node.id,
            forker_id=node.created_by,
            points_earned=points,
            reason=RoyaltyReason.GENEALOGY_BONUS
        )
        self.db.add(royalty)
        
        # Update ancestor's balance
        await self.db.execute(
            update(User)
            .where(User.id == parent.created_by)
            .values(
                total_royalty_received=User.total_royalty_received + points,
                pending_royalty=User.pending_royalty + points,
                k_points=User.k_points + points
            )
        )
        
        # Recurse to grandparent
        await self._award_genealogy_bonus(parent, base_points, depth + 1)
    
    async def get_user_royalty_summary(self, user_id) -> dict:
        """
        Get royalty summary for a user.
        """
        user = await self.db.get(User, user_id)
        if not user:
            return None
        
        # Get recent royalty transactions
        result = await self.db.execute(
            select(NodeRoyalty)
            .where(NodeRoyalty.creator_id == user_id)
            .order_by(NodeRoyalty.created_at.desc())
            .limit(20)
        )
        recent_royalties = result.scalars().all()
        
        return {
            "user_id": str(user_id),
            "total_earned": user.total_royalty_received,
            "pending": user.pending_royalty,
            "k_points": user.k_points,
            "recent_transactions": [
                {
                    "id": str(r.id),
                    "points": r.points_earned,
                    "reason": r.reason.value,
                    "created_at": r.created_at.isoformat()
                }
                for r in recent_royalties
            ]
        }
    
    async def get_node_earnings(self, node_id: str) -> dict:
        """
        Get earnings summary for a specific node.
        """
        result = await self.db.execute(
            select(RemixNode).where(RemixNode.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        if not node:
            return None
        
        # Get royalty transactions for this node
        result = await self.db.execute(
            select(NodeRoyalty)
            .where(NodeRoyalty.source_node_id == node.id)
            .order_by(NodeRoyalty.created_at.desc())
        )
        royalties = result.scalars().all()
        
        return {
            "node_id": node_id,
            "title": node.title,
            "total_fork_count": node.total_fork_count,
            "total_royalty_earned": node.total_royalty_earned,
            "view_count": node.view_count,
            "transactions": [
                {
                    "id": str(r.id),
                    "points": r.points_earned,
                    "reason": r.reason.value,
                    "forker_id": str(r.forker_id) if r.forker_id else None,
                    "created_at": r.created_at.isoformat()
                }
                for r in royalties
            ]
        }
