"""
Evidence Loop → DirectorPack Updater (Phase 2 + A→B Migration)

EvidenceSnapshot 기반으로 DirectorPack 규칙 가중치 자동 업데이트

Blueprint Philosophy:
- 성공률 높은 규칙 → weight 증가
- 실패율 높은 규칙 → priority 상향 (더 자주 체크)
- NotebookLM Parent-Kids 분석 → 불변/가변 경계 조정

A→B Migration:
- 신호 성능 추적 (SignalPerformance)
- 자동 승격 (Slot → Candidate → Invariant)
"""
import logging
from typing import Dict, List, Optional, Any
import hashlib

from app.utils.time import iso_now
from app.schemas.director_pack import (
    DirectorPack,
    DNAInvariant,
    MutationSlot,
    Checkpoint,
    CoachLineTemplates
)
from app.schemas.vdg_v4 import (
    SignalPerformance,
    InvariantCandidate,
    PROMOTION_THRESHOLDS
)

logger = logging.getLogger(__name__)


class EvidenceUpdater:
    """
    Evidence Loop Integration
    
    EvidenceSnapshot의 성공률 데이터를 기반으로
    DirectorPack의 규칙 가중치와 우선순위를 조정
    """
    
    # Priority escalation thresholds
    ESCALATE_THRESHOLD = 0.4  # 40% 미만 성공률 → priority 상향
    DEMOTE_THRESHOLD = 0.9    # 90% 이상 성공률 → priority 하향 고려
    
    @classmethod
    def update_pack_from_evidence(
        cls,
        pack: DirectorPack,
        evidence_summary: Dict[str, Any]
    ) -> DirectorPack:
        """
        Evidence 기반 Pack 업데이트
        
        Args:
            pack: 기존 DirectorPack
            evidence_summary: EvidenceSnapshot.depth1_summary
                {
                    "hook": {
                        "pattern_break": {
                            "success_rate": 0.75,
                            "sample_count": 10
                        }
                    }
                }
        
        Returns:
            업데이트된 DirectorPack (새 객체)
        """
        updated_invariants: List[DNAInvariant] = []
        
        for rule in pack.dna_invariants:
            success_rate = cls._get_success_rate(rule.rule_id, evidence_summary)
            
            if success_rate is None:
                # No evidence for this rule, keep as-is
                updated_invariants.append(rule)
                continue
            
            # Apply evidence-based adjustments
            updated_rule = cls._adjust_rule_priority(rule, success_rate)
            updated_invariants.append(updated_rule)
            
            logger.info(f"📊 Rule {rule.rule_id}: success_rate={success_rate:.2f} → {updated_rule.priority}")
        
        # Create updated pack (copy all fields, replace invariants)
        return DirectorPack(
            pack_version=pack.pack_version,
            pattern_id=pack.pattern_id,
            goal=pack.goal,
            pack_meta=pack.pack_meta,
            target=pack.target,
            runtime_contract=pack.runtime_contract,
            persona=pack.persona,
            scoring=pack.scoring,
            dna_invariants=updated_invariants,
            mutation_slots=pack.mutation_slots,
            forbidden_mutations=pack.forbidden_mutations,
            checkpoints=pack.checkpoints,
            policy=pack.policy,
            logging_spec=pack.logging_spec,
            extensions=pack.extensions,
        )
    
    @classmethod
    def _get_success_rate(
        cls,
        rule_id: str,
        evidence_summary: Dict[str, Any]
    ) -> Optional[float]:
        """Evidence에서 규칙별 성공률 추출"""
        # Search in all domains
        for domain, patterns in evidence_summary.items():
            if not isinstance(patterns, dict):
                continue
            for pattern_id, stats in patterns.items():
                if not isinstance(stats, dict):
                    continue
                # Match by rule_id or pattern
                if rule_id in str(pattern_id) or pattern_id in rule_id:
                    return stats.get("success_rate")
        return None
    
    @classmethod
    def _adjust_rule_priority(
        cls,
        rule: DNAInvariant,
        success_rate: float
    ) -> DNAInvariant:
        """
        성공률 기반 규칙 우선순위 조정
        
        - 낮은 성공률 → priority 상향 (더 자주 체크)
        - 높은 성공률 → weight 증가 (중요도 높음)
        """
        priority_order = ["critical", "high", "medium", "low"]
        current_idx = priority_order.index(rule.priority)
        
        new_priority = rule.priority
        new_weight = rule.weight or 1.0
        
        # Low success rate → escalate priority
        if success_rate < cls.ESCALATE_THRESHOLD:
            if current_idx > 0:  # Not already critical
                new_priority = priority_order[current_idx - 1]
                logger.info(f"⬆️ {rule.rule_id}: priority {rule.priority} → {new_priority}")
        
        # High success rate → increase weight
        elif success_rate >= cls.DEMOTE_THRESHOLD:
            new_weight = min((rule.weight or 1.0) * 1.2, 2.0)  # Cap at 2.0
            logger.info(f"📈 {rule.rule_id}: weight {rule.weight} → {new_weight:.2f}")
        
        # Create updated rule
        return DNAInvariant(
            rule_id=rule.rule_id,
            domain=rule.domain,
            priority=new_priority,
            tolerance=rule.tolerance,
            weight=new_weight,
            time_scope=rule.time_scope,
            spec=rule.spec,
            check_hint=rule.check_hint,
            coach_line_templates=rule.coach_line_templates,
            evidence_refs=rule.evidence_refs,
            fallback=rule.fallback,
        )
    
    @classmethod
    def generate_learning_report(
        cls,
        old_pack: DirectorPack,
        new_pack: DirectorPack
    ) -> Dict[str, Any]:
        """변경 사항 리포트 생성"""
        changes = []
        
        old_rules = {r.rule_id: r for r in old_pack.dna_invariants}
        new_rules = {r.rule_id: r for r in new_pack.dna_invariants}
        
        for rule_id, new_rule in new_rules.items():
            old_rule = old_rules.get(rule_id)
            if not old_rule:
                continue
            
            if old_rule.priority != new_rule.priority:
                changes.append({
                    "rule_id": rule_id,
                    "field": "priority",
                    "old": old_rule.priority,
                    "new": new_rule.priority,
                })
            
            if (old_rule.weight or 1.0) != (new_rule.weight or 1.0):
                changes.append({
                    "rule_id": rule_id,
                    "field": "weight",
                    "old": old_rule.weight,
                    "new": new_rule.weight,
                })
        
        return {
            "timestamp": iso_now(),
            "total_rules": len(new_pack.dna_invariants),
            "changes": changes,
            "summary": f"{len(changes)} rules updated based on evidence"
        }


# ==================
# Convenience Function
# ==================

def update_director_pack_from_evidence(
    pack: DirectorPack,
    evidence_summary: Dict[str, Any]
) -> DirectorPack:
    """
    DirectorPack을 Evidence 기반으로 업데이트하는 편의 함수
    
    Usage:
        from app.services.evidence_updater import update_director_pack_from_evidence
        
        updated_pack = update_director_pack_from_evidence(
            pack=director_pack,
            evidence_summary=evidence_snapshot.depth1_summary
        )
    """
    return EvidenceUpdater.update_pack_from_evidence(pack, evidence_summary)


# ====================
# A→B MIGRATION: SIGNAL TRACKER
# ====================

class SignalTracker:
    """
    A→B Migration: Tracks mise_en_scene signal performance.
    
    As data accumulates, signals with high success rates
    are automatically promoted to InvariantCandidate.
    
    Usage:
        tracker = SignalTracker()
        tracker.track_outcome("outfit_color.yellow", success=True, content_id="abc")
        candidates = tracker.check_promotions()
    """
    
    def __init__(self):
        self._signals: Dict[str, SignalPerformance] = {}
        self._candidates: List[InvariantCandidate] = []
    
    def get_or_create_signal(
        self,
        element: str,
        value: str,
        sentiment: str = "positive"
    ) -> SignalPerformance:
        """Get or create a SignalPerformance tracker."""
        signal_key = f"{element}.{value}"
        
        if signal_key not in self._signals:
            self._signals[signal_key] = SignalPerformance(
                signal_key=signal_key,
                element=element,
                value=value,
                sentiment=sentiment,
                first_seen_at=iso_now()
            )
        
        return self._signals[signal_key]
    
    def track_outcome(
        self,
        element: str,
        value: str,
        success: bool,
        content_id: str,
        sentiment: str = "positive"
    ):
        """
        Track a coaching outcome for a signal.
        
        Args:
            element: outfit_color, background, lighting, props
            value: yellow, minimal, bright, etc.
            success: Did the user follow the advice?
            content_id: Which content this was applied to
        """
        signal = self.get_or_create_signal(element, value, sentiment)
        signal.sessions_applied += 1
        
        if success:
            signal.success_count += 1
        else:
            signal.violation_count += 1
        
        if content_id and content_id not in signal.distinct_content_ids:
            signal.distinct_content_ids.append(content_id)
        
        logger.debug(f"📊 Signal {signal.signal_key}: sessions={signal.sessions_applied}, success_rate={signal.success_rate:.2f}")
    
    def check_promotions(self) -> List[InvariantCandidate]:
        """
        Check all signals and promote those meeting thresholds.
        
        Returns:
            List of newly created InvariantCandidate objects
        """
        new_candidates = []
        
        for signal_key, signal in self._signals.items():
            if signal.should_promote_to_candidate():
                # Check if already promoted
                existing = [c for c in self._candidates if c.signal_key == signal_key]
                if existing:
                    continue
                
                # Create new candidate
                candidate = self._create_candidate(signal)
                self._candidates.append(candidate)
                new_candidates.append(candidate)
                
                logger.info(f"🎉 Signal promoted to candidate: {signal_key} (success_rate={signal.success_rate:.2f})")
        
        return new_candidates
    
    def _create_candidate(self, signal: SignalPerformance) -> InvariantCandidate:
        """Create an InvariantCandidate from a SignalPerformance."""
        candidate_id = hashlib.sha256(
            f"{signal.signal_key}|{iso_now()}".encode()
        ).hexdigest()[:12]
        
        return InvariantCandidate(
            candidate_id=f"cand_{candidate_id}",
            source="signal_promotion",
            signal_key=signal.signal_key,
            element=signal.element,
            value=signal.value,
            sentiment=signal.sentiment,
            source_content_ids=signal.distinct_content_ids.copy(),
            performance_summary={
                "sessions_applied": signal.sessions_applied,
                "success_count": signal.success_count,
                "violation_count": signal.violation_count,
                "success_rate": signal.success_rate,
                "confidence_tier": signal.confidence_tier
            },
            proposed_domain="composition" if signal.element in ["background", "outfit_color"] else "performance",
            proposed_priority="medium" if signal.sentiment == "positive" else "high",
            status="pending",
            created_at=iso_now()
        )
    
    def get_all_signals(self) -> Dict[str, SignalPerformance]:
        """Get all tracked signals."""
        return self._signals.copy()
    
    def get_pending_candidates(self) -> List[InvariantCandidate]:
        """Get all pending candidates (not yet promoted to DNA)."""
        return [c for c in self._candidates if c.status == "pending"]


# Global tracker instance (singleton pattern for simplicity)
_signal_tracker: Optional[SignalTracker] = None


def get_signal_tracker() -> SignalTracker:
    """Get or create the global SignalTracker instance."""
    global _signal_tracker
    if _signal_tracker is None:
        _signal_tracker = SignalTracker()
    return _signal_tracker
