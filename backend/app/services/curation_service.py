# backend/app/services/curation_service.py
"""
Curation Learning Service

VDG 분석 결과에서 피처를 추출하고
큐레이션 결정을 기록하는 서비스
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime
from statistics import median
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.time import utcnow

from app.models import (
    CurationDecision,
    CurationDecisionType,
    CurationRule,
    CurationRuleType,
    OutlierItem,
    RemixNode,
    User,
)

logger = logging.getLogger(__name__)

_NUMERIC_FEATURES = (
    "hook_strength",
    "hook_duration_ms",
    "microbeat_count",
    "viral_kick_count",
    "scene_count",
    "causal_chain_length",
    "replication_recipe_count",
    "mise_signal_count",
    "duration_sec",
    "outlier_score",
    "view_count",
    "like_count",
    "share_count",
)
_LIST_FEATURES = ("comment_signal_types", "mise_signal_types")
_CATEGORICAL_FEATURES = ("top_viral_kick_mechanism", "category")


# =====================================
# Feature Extraction
# =====================================

def extract_features_from_vdg(vdg_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    VDG 분석 결과에서 큐레이션 피처 추출
    
    Args:
        vdg_analysis: VDGv4 or VDGv5 분석 결과 dict
    
    Returns:
        추출된 피처 dict
    """
    features = {}
    
    # Hook 관련
    hook = vdg_analysis.get("hook_genome", {})
    features["hook_strength"] = hook.get("strength", 0.0)
    features["hook_duration_ms"] = (
        (hook.get("hook_end_ms") or hook.get("end_sec", 0) * 1000) -
        (hook.get("hook_start_ms") or hook.get("start_sec", 0) * 1000)
    )
    features["microbeat_count"] = len(hook.get("microbeats", []))
    
    # Viral kicks
    viral_kicks = vdg_analysis.get("viral_kicks", [])
    features["viral_kick_count"] = len(viral_kicks)
    if viral_kicks:
        mechanisms = [k.get("mechanism", "") for k in viral_kicks]
        features["top_viral_kick_mechanism"] = mechanisms[0] if mechanisms else None
    
    # Comment evidence
    comment_evidence = vdg_analysis.get("comment_evidence", vdg_analysis.get("comment_evidence_top5", []))
    if comment_evidence:
        signal_types = [c.get("signal_type") for c in comment_evidence if c.get("signal_type")]
        features["comment_signal_types"] = list(set(signal_types))
    
    # Scenes
    scenes = vdg_analysis.get("scenes", [])
    features["scene_count"] = len(scenes)
    
    # Causal reasoning
    causal = vdg_analysis.get("causal_reasoning", {})
    features["causal_chain_length"] = len(causal.get("causal_chain", []))
    features["replication_recipe_count"] = len(causal.get("replication_recipe", []))
    
    # Mise-en-scene
    mise_signals = vdg_analysis.get("mise_en_scene_signals", [])
    features["mise_signal_count"] = len(mise_signals)
    mise_types = [m.get("type") for m in mise_signals if m.get("type")]
    features["mise_signal_types"] = list(set(mise_types))
    
    # Focus windows / CV metrics
    focus_windows = vdg_analysis.get("focus_windows", [])
    if focus_windows:
        # 평균 메트릭 추출
        cv_metrics = {}
        for fw in focus_windows:
            metrics = fw.get("metrics", {})
            for metric_id, metric_data in metrics.items():
                if isinstance(metric_data, dict):
                    value = metric_data.get("value")
                    if isinstance(value, (int, float)):
                        if metric_id not in cv_metrics:
                            cv_metrics[metric_id] = []
                        cv_metrics[metric_id].append(value)
        
        # 평균 계산
        for metric_id, values in cv_metrics.items():
            if values:
                features[f"avg_{metric_id.replace('.', '_')}"] = sum(values) / len(values)
    
    # 메타데이터
    features["platform"] = vdg_analysis.get("platform", "unknown")
    features["duration_ms"] = vdg_analysis.get("duration_ms", 0)
    features["duration_sec"] = features["duration_ms"] / 1000.0 if features["duration_ms"] else 0
    
    return features


# =====================================
# Decision Recording
# =====================================

async def record_curation_decision(
    db: AsyncSession,
    *,
    outlier_item_id: UUID,
    remix_node_id: Optional[UUID],
    curator_id: UUID,
    decision_type: CurationDecisionType,
    vdg_analysis: Optional[Dict[str, Any]] = None,
    curator_notes: Optional[str] = None,
    matched_rule_id: Optional[UUID] = None,
    rule_followed: Optional[bool] = None,
) -> CurationDecision:
    """
    큐레이션 결정 기록
    
    Args:
        db: Database session
        outlier_item_id: 아웃라이어 아이템 ID
        remix_node_id: 승격된 노드 ID (거부 시 None)
        curator_id: 큐레이터 ID
        decision_type: 결정 유형
        vdg_analysis: VDG 분석 결과 (있을 경우)
        curator_notes: 큐레이터 메모
        matched_rule_id: 매칭된 규칙 ID
        rule_followed: 규칙 추천을 따랐는지
    
    Returns:
        생성된 CurationDecision
    """
    # 피처 추출
    extracted_features = None
    if vdg_analysis:
        extracted_features = extract_features_from_vdg(vdg_analysis)
    
    decision = CurationDecision(
        outlier_item_id=outlier_item_id,
        remix_node_id=remix_node_id,
        curator_id=curator_id,
        decision_type=decision_type,
        decision_at=utcnow(),
        vdg_snapshot=vdg_analysis,
        extracted_features=extracted_features,
        curator_notes=curator_notes,
        matched_rule_id=matched_rule_id,
        rule_followed=rule_followed,
    )
    
    db.add(decision)
    await db.flush()
    
    # 규칙 통계 업데이트
    if matched_rule_id:
        await _update_rule_stats(db, matched_rule_id, rule_followed or False)
    
    logger.info(
        f"📝 Curation decision recorded: "
        f"item={outlier_item_id}, type={decision_type.value}"
    )
    
    return decision


async def update_curation_decision_with_vdg(
    db: AsyncSession,
    *,
    outlier_item_id: UUID,
    vdg_analysis: Dict[str, Any],
    remix_node_id: Optional[UUID] = None,
) -> Optional[CurationDecision]:
    """
    Attach VDG snapshot/features to the most recent decision for an item.
    """
    if not vdg_analysis:
        return None

    query = select(CurationDecision).where(
        CurationDecision.outlier_item_id == outlier_item_id
    )
    if remix_node_id:
        query = query.where(CurationDecision.remix_node_id == remix_node_id)

    result = await db.execute(
        query.order_by(CurationDecision.decision_at.desc())
    )
    decision = result.scalars().first()

    if not decision:
        logger.warning(
            "No curation decision found to update for outlier_item_id=%s",
            outlier_item_id,
        )
        return None

    decision.vdg_snapshot = vdg_analysis
    decision.extracted_features = extract_features_from_vdg(vdg_analysis)
    await db.flush()

    return decision


async def _update_rule_stats(
    db: AsyncSession,
    rule_id: UUID,
    followed: bool,
) -> None:
    """규칙 통계 업데이트"""
    result = await db.execute(
        select(CurationRule).where(CurationRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if rule:
        rule.match_count += 1
        if followed:
            rule.follow_count += 1
        rule.accuracy = rule.follow_count / rule.match_count if rule.match_count > 0 else 0.0


# =====================================
# Rule Matching
# =====================================

async def find_matching_rules(
    db: AsyncSession,
    features: Dict[str, Any],
) -> List[CurationRule]:
    """
    피처에 매칭되는 규칙 찾기
    
    Args:
        db: Database session
        features: 추출된 피처
    
    Returns:
        매칭된 규칙 목록 (우선순위 순)
    """
    result = await db.execute(
        select(CurationRule)
        .where(CurationRule.is_active == True)
        .order_by(CurationRule.priority.desc())
    )
    rules = result.scalars().all()
    
    matched = []
    for rule in rules:
        if _matches_conditions(features, rule.conditions):
            matched.append(rule)
    
    return matched


def _matches_conditions(features: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
    """
    피처가 조건을 만족하는지 검사
    
    조건 형식:
    - {"field": "value"} → 값 일치
    - {"field": {">=": 0.8}} → 비교 연산
    - {"field": {"in": ["a", "b"]}} → 포함 검사
    """
    for field, condition in conditions.items():
        value = features.get(field)
        
        if isinstance(condition, dict):
            # 비교 연산
            for op, target in condition.items():
                if op == ">=" and (value is None or value < target):
                    return False
                elif op == "<=" and (value is None or value > target):
                    return False
                elif op == ">" and (value is None or value <= target):
                    return False
                elif op == "<" and (value is None or value >= target):
                    return False
                elif op == "==" and value != target:
                    return False
                elif op == "in" and value not in target:
                    return False
                elif op == "contains" and (value is None or target not in value):
                    return False
        else:
            # 값 일치
            if value != condition:
                return False
    
    return True


# =====================================
# Rule Learning
# =====================================

_DECISION_TO_RULE_TYPE = {
    CurationDecisionType.NORMAL: CurationRuleType.AUTO_NORMAL,
    CurationDecisionType.CAMPAIGN: CurationRuleType.AUTO_CAMPAIGN,
    CurationDecisionType.REJECTED: CurationRuleType.AUTO_REJECT,
}


def _normalize_decision_type(value: Any) -> Optional[CurationDecisionType]:
    if isinstance(value, CurationDecisionType):
        return value
    if isinstance(value, str):
        try:
            return CurationDecisionType(value)
        except ValueError:
            return None
    return None


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _coerce_threshold(values: List[Any], threshold: float) -> Any:
    if values and all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        return int(round(threshold))
    return round(float(threshold), 4)


def _most_common(values: List[str]) -> Tuple[Optional[str], float]:
    if not values:
        return None, 0.0
    counter = Counter(values)
    top_value, count = counter.most_common(1)[0]
    return top_value, count / len(values)


def _most_common_from_lists(values_list: List[List[str]]) -> Tuple[Optional[str], float]:
    flattened: List[str] = []
    for values in values_list:
        if isinstance(values, list):
            flattened.extend([v for v in values if isinstance(v, str) and v])
    return _most_common(flattened)


def _build_rule_conditions(
    features_list: List[Dict[str, Any]],
    decision_type: CurationDecisionType,
    platform: str,
    *,
    min_support_ratio: float,
    max_numeric_conditions: int,
) -> Dict[str, Any]:
    conditions: Dict[str, Any] = {"platform": platform}
    min_feature_samples = max(3, int(len(features_list) * min_support_ratio))
    op = "<=" if decision_type == CurationDecisionType.REJECTED else ">="

    numeric_added = 0
    for feature in _NUMERIC_FEATURES:
        values = [f.get(feature) for f in features_list if _is_numeric(f.get(feature))]
        if len(values) < min_feature_samples:
            continue
        threshold = _coerce_threshold(values, median(values))
        conditions[feature] = {op: threshold}
        numeric_added += 1
        if numeric_added >= max_numeric_conditions:
            break

    max_total_conditions = max_numeric_conditions + 2
    if len(conditions) < max_total_conditions:
        for feature in _LIST_FEATURES:
            values_list = [
                f.get(feature) for f in features_list if isinstance(f.get(feature), list)
            ]
            common_value, ratio = _most_common_from_lists(values_list)
            if common_value and ratio >= min_support_ratio:
                conditions[feature] = {"contains": common_value}
                break

    if len(conditions) < max_total_conditions:
        for feature in _CATEGORICAL_FEATURES:
            values = [
                f.get(feature)
                for f in features_list
                if isinstance(f.get(feature), str) and f.get(feature)
            ]
            common_value, ratio = _most_common(values)
            if common_value and ratio >= min_support_ratio:
                conditions[feature] = common_value
                break

    return conditions


async def learn_curation_rules_from_decisions(
    db: AsyncSession,
    *,
    min_samples: int = 10,
    min_support_ratio: float = 0.6,
    max_numeric_conditions: int = 2,
    platform: Optional[str] = None,
    decision_type: Optional[CurationDecisionType] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Generate or update learned curation rules from decision history.
    """
    if min_samples < 1:
        raise ValueError("min_samples must be >= 1")
    if min_support_ratio <= 0 or min_support_ratio > 1:
        raise ValueError("min_support_ratio must be within (0, 1]")
    if max_numeric_conditions < 0:
        raise ValueError("max_numeric_conditions must be >= 0")

    result = await db.execute(
        select(CurationDecision).where(CurationDecision.extracted_features.isnot(None))
    )
    decisions = result.scalars().all()

    groups: Dict[Tuple[CurationDecisionType, str], List[Dict[str, Any]]] = defaultdict(list)
    for decision in decisions:
        normalized_type = _normalize_decision_type(decision.decision_type)
        if not normalized_type:
            continue
        if decision_type and normalized_type != decision_type:
            continue
        features = decision.extracted_features
        if not isinstance(features, dict):
            continue
        platform_value = features.get("platform") or "unknown"
        if isinstance(platform_value, str):
            platform_value = platform_value.strip() or "unknown"
        if platform and platform_value != platform:
            continue
        groups[(normalized_type, str(platform_value))].append(features)

    created = 0
    updated = 0
    skipped = 0
    ignored = 0
    rules: List[Dict[str, Any]] = []

    for (normalized_type, platform_value), features_list in groups.items():
        if len(features_list) < min_samples:
            ignored += 1
            continue

        conditions = _build_rule_conditions(
            features_list,
            normalized_type,
            platform_value,
            min_support_ratio=min_support_ratio,
            max_numeric_conditions=max_numeric_conditions,
        )
        if len(conditions) <= 1:
            ignored += 1
            continue

        rule_type = _DECISION_TO_RULE_TYPE.get(normalized_type)
        if not rule_type:
            ignored += 1
            continue

        rule_name = f"learned_{normalized_type.value}_{platform_value}"
        existing = await db.execute(
            select(CurationRule).where(
                CurationRule.rule_name == rule_name,
                CurationRule.rule_type == rule_type,
                CurationRule.source == "learned",
            )
        )
        rule = existing.scalar_one_or_none()

        action = "skipped"
        if rule:
            if rule.conditions != conditions or rule.sample_size != len(features_list):
                if not dry_run:
                    rule.conditions = conditions
                    rule.sample_size = len(features_list)
                    rule.priority = len(features_list)
                    rule.updated_at = utcnow()
                updated += 1
                action = "updated"
            else:
                skipped += 1
        else:
            if not dry_run:
                db.add(
                    CurationRule(
                        rule_name=rule_name,
                        rule_type=rule_type,
                        conditions=conditions,
                        source="learned",
                        sample_size=len(features_list),
                        priority=len(features_list),
                        description=f"Learned from {len(features_list)} decisions",
                    )
                )
            created += 1
            action = "created"

        rules.append(
            {
                "rule_name": rule_name,
                "rule_type": rule_type.value,
                "decision_type": normalized_type.value,
                "platform": platform_value,
                "sample_size": len(features_list),
                "action": action,
            }
        )

    if not dry_run:
        await db.commit()

    return {
        "total_decisions": len(decisions),
        "total_groups": len(groups),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "ignored": ignored,
        "dry_run": dry_run,
        "rules": rules,
    }


# =====================================
# Recommendation
# =====================================

async def get_recommendation(
    db: AsyncSession,
    outlier_item_id: UUID,
    vdg_analysis: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    아이템에 대한 큐레이션 추천 반환
    
    Args:
        db: Database session
        outlier_item_id: 아웃라이어 아이템 ID
        vdg_analysis: VDG 분석 결과
    
    Returns:
        추천 정보 또는 None
    """
    if not vdg_analysis:
        # DB에서 분석 결과 조회
        result = await db.execute(
            select(OutlierItem).where(OutlierItem.id == outlier_item_id)
        )
        item = result.scalar_one_or_none()
        
        if item and item.promoted_to_node_id:
            node_result = await db.execute(
                select(RemixNode).where(RemixNode.id == item.promoted_to_node_id)
            )
            node = node_result.scalar_one_or_none()
            if node and node.gemini_analysis:
                vdg_analysis = node.gemini_analysis
    
    if not vdg_analysis:
        return None
    
    # 피처 추출
    features = extract_features_from_vdg(vdg_analysis)
    
    # 매칭 규칙 찾기
    matched_rules = await find_matching_rules(db, features)
    
    if not matched_rules:
        return None
    
    top_rule = matched_rules[0]
    
    return {
        "rule_id": str(top_rule.id),
        "rule_name": top_rule.rule_name,
        "rule_type": top_rule.rule_type.value,
        "confidence": top_rule.accuracy or 0.5,
        "recommendation": (
            "campaign" if top_rule.rule_type == CurationRuleType.AUTO_CAMPAIGN else
            "normal" if top_rule.rule_type == CurationRuleType.AUTO_NORMAL else
            "reject" if top_rule.rule_type == CurationRuleType.AUTO_REJECT else
            None
        ),
        "matched_conditions": top_rule.conditions,
        "features": features,
    }
