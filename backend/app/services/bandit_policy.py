"""
Bandit Exploration Policy Service
backend/app/services/bandit_policy.py

Implements Thompson Sampling for variant/mutation selection.
Based on 15_FINAL_ARCHITECTURE.md - RL-lite 전략

Reference: 
- 변주 생성은 유전(변이), 선택은 bandit 탐색으로 현실화
- 주간 배치 업데이트로 템플릿 기본값 개선
- Creator Customization Signals -> Template Seed Update
"""
import random
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import CONFIDENCE_MEDIUM, RL_MIN_SIGNAL_COUNT
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


@dataclass
class VariantArm:
    """Represents a variant in the multi-armed bandit"""
    variant_id: str
    pattern: str
    mutation_type: str
    successes: int = 0  # Number of successful outcomes
    failures: int = 0   # Number of failed outcomes
    
    @property
    def trials(self) -> int:
        return self.successes + self.failures
    
    @property
    def success_rate(self) -> float:
        if self.trials == 0:
            return 0.5  # Prior
        return self.successes / self.trials
    
    def sample_beta(self) -> float:
        """Thompson Sampling: sample from Beta distribution"""
        # Beta(successes + 1, failures + 1) - using prior of Beta(1, 1)
        alpha = self.successes + 1
        beta = self.failures + 1
        return random.betavariate(alpha, beta)


class BanditPolicy:
    """
    Thompson Sampling based Bandit Policy for variant selection.
    
    Usage:
        policy = BanditPolicy(exploration_rate=0.15)
        selected = await policy.select_variant(db, parent_id)
        
        # After observing outcome
        await policy.update_reward(db, variant_id, success=True)
    """
    
    def __init__(self, exploration_rate: float = 0.15):
        """
        Args:
            exploration_rate: Probability of selecting a random variant
                             instead of the Thompson Sampling winner.
                             Ensures continued exploration of new variants.
        """
        self.exploration_rate = exploration_rate
    
    async def select_variant(
        self,
        db: AsyncSession,
        parent_id: str,
        available_variants: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select a variant using Thompson Sampling with epsilon-greedy exploration.
        
        Args:
            db: Database session
            parent_id: Parent node ID to select variants for
            available_variants: Optional list of variants. If None, fetches from DB.
        
        Returns:
            Selected variant dict or None if no variants available
        """
        # Get variant arms
        arms = await self._load_arms(db, parent_id, available_variants)
        
        if not arms:
            logger.warning(f"No variants available for parent {parent_id}")
            return None
        
        # Epsilon-greedy exploration
        if random.random() < self.exploration_rate:
            # Random exploration
            selected = random.choice(arms)
            logger.info(f"[Explore] Random selection: {selected.pattern}")
        else:
            # Thompson Sampling
            samples = [(arm, arm.sample_beta()) for arm in arms]
            selected, sample_value = max(samples, key=lambda x: x[1])
            logger.info(f"[Exploit] Thompson selection: {selected.pattern} (sample={sample_value:.3f})")
        
        return {
            "variant_id": selected.variant_id,
            "pattern": selected.pattern,
            "mutation_type": selected.mutation_type,
            "success_rate": selected.success_rate,
            "trials": selected.trials,
            "selection_method": "explore" if random.random() < self.exploration_rate else "exploit"
        }
    
    async def _load_arms(
        self,
        db: AsyncSession,
        parent_id: str,
        available_variants: Optional[List[Dict[str, Any]]] = None
    ) -> List[VariantArm]:
        """Load variant arms from database or provided list"""
        
        if available_variants:
            # Use provided variants
            return [
                VariantArm(
                    variant_id=v.get("variant_id", f"var_{i}"),
                    pattern=v.get("pattern", "unknown"),
                    mutation_type=v.get("mutation_type", "unknown"),
                    successes=int(v.get("successes", 0)),
                    failures=int(v.get("failures", 0))
                )
                for i, v in enumerate(available_variants)
            ]
        
        # Load from database - EvidenceSnapshot aggregation
        from app.models import EvidenceSnapshot, RemixNode
        
        try:
            # Get parent node
            parent = await db.execute(
                select(RemixNode).where(RemixNode.node_id == parent_id)
            )
            parent_node = parent.scalar_one_or_none()
            if not parent_node:
                return []
            
            # Get evidence snapshots
            evidence = await db.execute(
                select(EvidenceSnapshot)
                .where(EvidenceSnapshot.parent_node_id == parent_node.id)
                .order_by(EvidenceSnapshot.created_at.desc())
                .limit(10)
            )
            snapshots = evidence.scalars().all()
            
            # Aggregate into arms
            arms_dict: Dict[str, VariantArm] = {}
            for snap in snapshots:
                if not snap.depth1_summary:
                    continue
                    
                for mutation_type, patterns in snap.depth1_summary.items():
                    for pattern, stats in patterns.items():
                        key = f"{mutation_type}:{pattern}"
                        if key not in arms_dict:
                            arms_dict[key] = VariantArm(
                                variant_id=key,
                                pattern=pattern,
                                mutation_type=mutation_type
                            )
                        
                        # Estimate successes/failures from success_rate and sample_count
                        rate = stats.get("success_rate", 0.5)
                        count = stats.get("sample_count", 1)
                        arms_dict[key].successes += int(rate * count)
                        arms_dict[key].failures += int((1 - rate) * count)
            
            return list(arms_dict.values())
            
        except Exception as e:
            logger.error(f"Failed to load arms: {e}")
            return []
    
    async def update_reward(
        self,
        db: AsyncSession,
        variant_id: str,
        success: bool,
        reward_magnitude: float = 1.0
    ):
        """
        Update the bandit arm with observed reward.
        
        Args:
            variant_id: The variant that was used
            success: Whether the outcome was successful
            reward_magnitude: Optional reward scaling (default 1.0)
        
        Note: This is a lightweight update. Full updates happen during
              weekly batch policy updates.
        """
        logger.info(f"Reward update: {variant_id} -> {'success' if success else 'failure'}")
        # In a production system, this would update a dedicated bandit_arms table
        # For now, rewards flow through EvidenceSnapshot updates
    
    def calculate_ucb(self, arm: VariantArm, total_trials: int) -> float:
        """
        Calculate Upper Confidence Bound (UCB1) for comparison.
        UCB1 = success_rate + sqrt(2 * ln(total_trials) / arm_trials)
        """
        if arm.trials == 0:
            return float('inf')  # Explore unvisited arms
        
        exploitation = arm.success_rate
        exploration = math.sqrt(2 * math.log(max(1, total_trials)) / arm.trials)
        return exploitation + exploration


class BatchPolicyUpdater:
    """
    Weekly batch updater for RL-lite policy.
    Updates template defaults based on accumulated evidence.
    """
    
    async def update_template_defaults(self, db: AsyncSession):
        """
        Aggregate weekly evidence and update template default values.
        Called by scheduled job (e.g., every Sunday).
        """
        from app.models import TemplateSeed, EvidenceSnapshot
        
        logger.info("Starting weekly policy update...")
        
        # Get aggregated success patterns
        result = await db.execute(
            select(EvidenceSnapshot)
            .where(EvidenceSnapshot.confidence >= CONFIDENCE_MEDIUM)  # High confidence only
            .order_by(EvidenceSnapshot.created_at.desc())
            .limit(100)
        )
        snapshots = result.scalars().all()
        
        # Find winning patterns
        pattern_scores: Dict[str, Tuple[float, int]] = {}  # pattern -> (total_rate, count)
        for snap in snapshots:
            if snap.top_mutation_pattern:
                key = snap.top_mutation_pattern
                current = pattern_scores.get(key, (0.0, 0))
                conf = snap.confidence or 0.5
                pattern_scores[key] = (current[0] + conf, current[1] + 1)
        
        # Sort by average confidence
        winners = sorted(
            [(k, v[0]/v[1], v[1]) for k, v in pattern_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(f"Top patterns: {winners[:5]}")
        
        # Note: In production, this would update TemplateSeed defaults
        
        # 3. Incorporate Creator Customization Signals (RL-lite)
        # Import here to avoid circular dependency
        from app.routers.template_customization import get_customization_patterns
        
        customization_trends = get_customization_patterns()
        updated_templates = []
        
        if customization_trends:
            logger.info(f"Analyzing {len(customization_trends)} customization fields for policy update...")
            
            for field, data in customization_trends.items():
                change_count = data.get("change_count", 0)
                
                # If a field is changed frequently (e.g. > 5 times in MVP), consider it a strong signal
                if change_count >= RL_MIN_SIGNAL_COUNT:
                    logger.info(f"Strong signal detected for field '{field}' ({change_count} changes)")
                    
                    # Analyze the 'new' values to find a consensus
                    # For MVP, we just take the most recent change as the 'new default' candidate
                    samples = data.get("sample_changes", [])
                    if samples:
                        latest_value = samples[-1].get("new")
                        
                        # Find relevant TemplateSeeds to update
                        # In a real scenario, we'd link customization to specific template_ids
                        # Here, we verify if any template uses this field
                        
                        seeds = await db.execute(select(TemplateSeed))
                        all_seeds = seeds.scalars().all()
                        
                        for seed in all_seeds:
                            # Check if seed_json has this field
                            if seed.seed_json and field in seed.seed_json:
                                current_val = seed.seed_json[field]
                                
                                # Update the seed default
                                # Create a copy of the dict to ensure mutation is tracked
                                new_json = dict(seed.seed_json)
                                new_json[field] = latest_value
                                seed.seed_json = new_json
                                
                                # Create a version history
                                from app.models import TemplateVersion
                                version = TemplateVersion(
                                    seed_id=seed.id,
                                    version=f"v{seed.prompt_version or '1.0'}.{utcnow().strftime('%m%d')}",
                                    template_json=new_json,
                                    change_type="rl_update",
                                    change_reason=f"RL-lite: User preference consensus for {field} ({change_count} signals)"
                                )
                                db.add(version)
                                updated_templates.append({
                                    "seed_id": seed.seed_id,
                                    "field": field,
                                    "old": current_val,
                                    "new": latest_value
                                })
            
            if updated_templates:
                logger.info(f"Updated {len(updated_templates)} template defaults based on RL-lite feedback.")
                # await db.commit() # Caller handles commit
        
        return {
            "top_patterns": winners[:10],
            "rl_updates": updated_templates,
            "customization_signals": len(customization_trends)
        }


# Singleton instance
bandit_policy = BanditPolicy(exploration_rate=0.15)
batch_updater = BatchPolicyUpdater()
