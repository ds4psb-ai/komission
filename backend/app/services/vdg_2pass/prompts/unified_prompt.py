# backend/app/services/vdg_2pass/prompts/unified_prompt.py
"""
VDG Unified Pass 프롬프트

핵심 원칙:
- metric_id는 Metric Registry에서 자동 생성하여 주입 (drift 방지)
- ID 생성 금지 강제
- 수치 추정 금지 강제
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


PROMPT_VERSION_UNIFIED = "unified_pro_v1.0"


def build_unified_prompt(
    *,
    duration_ms: int,
    platform: str,
    caption: Optional[str],
    hashtags: Optional[List[str]],
    top_comments: List[str],
    metric_definitions: Dict[str, Any],
) -> str:
    """
    Unified Pass 프롬프트 생성
    
    Args:
        duration_ms: 비디오 길이 (밀리초)
        platform: 플랫폼 (tiktok/youtube/instagram)
        caption: 영상 캡션
        hashtags: 해시태그 목록
        top_comments: 상위 댓글 목록
        metric_definitions: METRIC_DEFINITIONS from metric_registry.py
    
    Returns:
        완성된 프롬프트 문자열
    """
    allowed_metrics = sorted(metric_definitions.keys())
    hashtags = hashtags or []
    caption = caption or ""

    # comments: 너무 길면 모델 출력 안정성이 떨어지므로 상한 적용
    top_comments = [c.strip() for c in top_comments if c and c.strip()]
    top_comments = top_comments[:20]

    return f"""
You are an expert short-form video analyst and director coach.
Your job is to analyze WHY the video is viral (causal reasoning),
infer the intended mise-en-scène (creative intent),
and output a CV measurement plan (what/where/when to measure).

INPUTS YOU RECEIVE IN THIS REQUEST:
- A short-form video (audio+visual). You may receive TWO video parts:
  (1) Hook clip: first few seconds with higher fps (for precise hook timing)
  (2) Full video: low fps sampling (for global context)
- Top user comments (for audience reaction and signals)

HARD CONSTRAINTS (MUST FOLLOW):
1) Output MUST be VALID JSON only. No markdown. No extra keys.
2) DO NOT create any IDs (no ap_id, no evidence_id, no cluster_id).
   IDs are generated deterministically in code.
3) Any metric_id you output MUST be selected from this allow-list:
{allowed_metrics}
4) Use milliseconds (ms) for all timestamps. Integers only.
5) Keep the plan compact:
   - analysis_plan.points: 6~10 points recommended (max 12)
   - Each point should be a KEY moment that explains virality or mise-en-scène.
6) If uncertain about a measurement (occlusion/noise), mention in risks_or_unknowns.
7) DO NOT guess numeric metric values. Only request what to measure.

VIDEO METADATA:
- platform: {platform}
- duration_ms: {duration_ms}
- caption: {caption}
- hashtags: {hashtags}

TOP COMMENTS (audience signals):
{top_comments}

TASKS:
A) Causal reasoning:
- Explain in one line why it goes viral.
- Provide a short causal chain (max 8 steps).
- Provide a replication recipe in creator language (max 8 bullets).
- List risks/unknowns (max 6).

B) Mise-en-scène intent:
- Extract 6~12 mise_en_scene_signals.
- Each must include: type, description, why_it_matters, anchor_ms(optional).

C) Hook genome:
- Identify hook_start_ms, hook_end_ms, strength (0-1).
- Extract 4~8 microbeats with role, t_ms, description.

D) Analysis plan seeds for deterministic CV measurement:
- Output analysis_plan.points (6~10 recommended, max 12).
- Each point must include:
  - t_center_ms (int)
  - t_window_ms (int, 200~6000)
  - priority (critical/high/medium/low)
  - reason (why this moment matters)
  - measurements[]: list of MeasurementSpec with allowed metric_id, aggregation, roi
  - target_entity_keys[]: refer to keys of entity_hints (e.g., "main_subject", "product")
- Also output entity_hints dict:
  - key -> {{entity_type, description, appears_windows[], cv_priority}}

E) Output schema_version as "unified_pass_llm.v1"

OUTPUT JSON MUST MATCH THE PROVIDED JSON SCHEMA EXACTLY.
Language for text fields: Korean (natural creator language).
""".strip()
