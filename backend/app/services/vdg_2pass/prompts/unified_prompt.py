# backend/app/services/vdg_2pass/prompts/unified_prompt.py
"""
VDG Unified Pass 프롬프트

핵심 원칙:
- metric_id는 Metric Registry에서 자동 생성하여 주입 (drift 방지)
- ID 생성 금지 강제
- 수치 추정 금지 강제
- Evidence Anchors 강제 (댓글 증거 Top5 + 바이럴 킥)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


PROMPT_VERSION_UNIFIED = "unified_pro_v2.0"


def format_ranked_comments(top_comments: List[str]) -> str:
    """
    댓글을 rank 라벨과 함께 포맷
    LLM이 comment_rank로 구조화된 참조 가능
    """
    if not top_comments:
        return "(no comments provided)"
    
    lines = []
    for i, c in enumerate(top_comments[:20], start=1):
        c = (c or "").strip().replace("\n", " ")
        if c:
            lines.append(f"C{i:02d} (rank={i}): {c}")
    return "\n".join(lines) if lines else "(no comments provided)"


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
    Unified Pass 프롬프트 생성 (v2.0 - Evidence Anchors 강제)
    
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

    # 댓글을 rank 라벨과 함께 포맷
    comments_block = format_ranked_comments(top_comments)

    return f"""
You are an expert short-form video analyst and director coach.
Your job is to analyze WHY the video is viral (causal reasoning),
infer the intended mise-en-scène (creative intent),
and output a CV measurement plan (what/where/when to measure).

INPUTS YOU RECEIVE IN THIS REQUEST:
- A short-form video (audio+visual). You may receive TWO video parts:
  (1) Hook clip: first few seconds with higher fps (for precise hook timing)
  (2) Full video: low fps sampling (for global context)
- Top user comments with rank labels (for audience reaction and signals)

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

TOP COMMENTS (ranked, use comment_rank to reference):
{comments_block}

=== CRITICAL EVIDENCE REQUIREMENTS (MUST) ===

1) COMMENT EVIDENCE (1~10 items):
   - Output 1~10 items for `comment_evidence_top5` (list can be smaller if fewer comments available).
   - Each item MUST reference a `comment_rank` from the provided Top Comments list (1-20).
   - For each comment, explain `signal_type` and `why_it_matters`.
   - If you can localize the comment to a video moment, set `anchor_ms`.
   - If no comments are available, output at least 1 placeholder with signal_type="other".

2) VIRAL KICKS (3-5 segments):
   - You MUST output 3~5 `viral_kicks`.
   - Each viral_kick MUST include:
     * `evidence_comment_ranks`: at least 1 rank from comment_evidence_top5
     * `evidence_cues`: at least 1 video cue (dialogue/on-screen text/action)
     * `creator_instruction`: actionable instruction in creator language (1-2 sentences)
     * `keyframes`: EXACTLY 3 keyframes with:
       - `t_ms`: precise timestamp in milliseconds (within the kick's window)
       - `role`: one of "start", "peak", "end"
       - `what_to_see`: what makes this frame viral-worthy (1 sentence, max 100 chars)
   - Each viral_kick MUST have a precise time range (`window.start_ms`, `window.end_ms`).

3) PLAN COVERAGE:
   - Your `analysis_plan.points` MUST cover EVERY viral_kick.
   - For each viral_kick, there must be at least 1 point whose t_window overlaps the kick range.
   - If needed, add additional points (but keep total points <= 12).

=== TASKS ===

A) Causal reasoning:
- **why_viral_one_liner** (REQUIRED): A single Korean sentence (max 80 chars) explaining WHY this video goes viral.
  Example: "기업 합병을 유머러스하게 풍자하여 공감과 웃음 유발"
- Provide a short causal chain (max 8 steps).
- Provide a replication recipe in creator language (max 8 bullets).
- List risks/unknowns (max 6).

B) Mise-en-scène intent:
- Extract 6~12 mise_en_scene_signals.
- Each must include: type, description, why_it_matters, anchor_ms(optional).

C) Hook genome (REQUIRED):
- **pattern** (REQUIRED): Hook pattern type. Must be one of:
  "question_hook", "visual_punch", "pattern_break", "unboxing", "tutorial_tease", 
  "reaction_bait", "before_after", "transformation", "controversy", "challenge", "other"
- **hook_summary** (REQUIRED): 1-2 Korean sentences describing the hook strategy.
  Example: "2026년 영화 인트로라는 가짜 맥락으로 시청자의 호기심을 유발"
- **strength** (REQUIRED): 0.0-1.0 score for hook effectiveness.
- Identify hook_start_ms (usually 0), hook_end_ms (when hook completes).
- Extract 4~8 microbeats with role, t_ms, description.

D) Evidence anchors (comment_evidence_top5 + viral_kicks):
- Follow the CRITICAL EVIDENCE REQUIREMENTS above.

E) Analysis plan seeds for deterministic CV measurement:
- Output analysis_plan.points (6~10 recommended, max 12).
- Each point must include:
  - t_center_ms (int)
  - t_window_ms (int, 200~6000)
  - kick_index (int, optional): if this measurement is for a specific viral_kick, reference its kick_index
  - priority (critical/high/medium/low)
  - reason (why this moment matters)
  - measurements[]: list of MeasurementSpec with allowed metric_id, aggregation, roi
  - target_entity_keys[]: refer to keys of entity_hints (e.g., "main_subject", "product")
- Also output entity_hints dict:
  - key -> {{entity_type, description, appears_windows[], cv_priority}}

F) Output schema_version as "unified_pass_llm.v2"

G) Scene segmentation (REQUIRED):
- Output `scenes`: 4~8 scenes that segment the video narrative.
- Each scene MUST include:
  - idx (int): scene index starting from 0
  - window.start_ms, window.end_ms: time boundaries
  - label: one of "hook", "setup", "demo", "reveal", "payoff", "cta", "bridge", "outro"
  - summary: 1-2 sentence description in Korean (크리에이터 언어)
- First scene should be the "hook" (first 3-5 seconds).
- Last scene should be "cta" or "outro" if applicable.

H) Capsule brief (director guidance):
- Output `capsule_brief` with:
  - shotlist: list of 3-6 shot descriptions (e.g., "클로즈업으로 제품 강조", "리액션 캡처")
  - do_not: list of 2-4 things to AVOID (e.g., "흔들리는 카메라", "너무 긴 인트로")
  - hook_script: 1-2 sentence spoken/on-screen hook script in Korean

OUTPUT JSON MUST MATCH THE PROVIDED JSON SCHEMA EXACTLY.
Language for text fields: Korean (natural creator language).
""".strip()

