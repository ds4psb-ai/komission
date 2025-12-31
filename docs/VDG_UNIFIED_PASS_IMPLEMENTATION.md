# VDG Unified Pass 통합 구현 가이드 v4.0

> 작성일: 2025-12-31 | 두 컨설턴트 제안 통합

---

## 컨설팅 비교 및 채택

| 항목 | 컨설턴트 A | 컨설턴트 B | **채택** |
|------|-----------|-----------|----------|
| **스키마** | 전체 신규 생성 | 기존 SemanticPassResult 재사용 | **B** (리팩토링 최소화) |
| **비디오 입력** | VideoMetadata (10fps hook + 1fps full) | 언급 없음 | **A** (정밀도) |
| **Evidence 링크** | 일반적 | time range OR comment_idx 강제 | **B** (ID 안전) |
| **실패 모드** | 없음 | 3개 명시 | **B** (운영 안전) |
| **DoD 체크리스트** | 4개 | 6개 상세 | **B** (검증 명확) |
| **generate_content 확장** | 언급만 | `generate_content_typed` 코드 | **B** (바로 사용) |

---

## 0) 절대 규칙

### Pass 1이 하는 일
- **(A) 의미/인과**: "왜 바이럴인가" 가설/근거/재현 팁
- **(B) 미장센 의도**: 댓글 기반 의도된 미장센 추출
- **(C) 측정 지점**: CV가 봐야 할 시점/윈도우/metric_id 제안

### Pass 1이 절대 하면 안 되는 일
- ❌ `ap_id`, `evidence_id`, `pack_id`, `cluster_id` 생성
- ❌ 메트릭 수치 추정 (`brightness=0.7` 같은 것)
- ❌ Metric Registry 밖 metric_id 생성

---

## 1) 스키마: `vdg_v4.py`에 추가

**위치**: `backend/app/schemas/vdg_v4.py` (기존 파일에 추가)

```python
# =========================
# Unified Pro Pass (LLM 1회)
# =========================

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, model_validator

# 기존 SemanticPassResult, MetricRequest 재사용

ReasonCode = Literal[
    "hook_first_2s",
    "hook_microbeat",
    "pace_shift",
    "jump_cut",
    "comment_mise_en_scene",
    "comment_wardrobe",
    "comment_sfx",
    "comment_caption",
    "camera_motion",
    "audio_clarity",
    "cta_moment",
    "product_shot",
    "other",
]

PriorityLevel = Literal["critical", "high", "medium", "low"]


class CausalEvidence(BaseModel):
    """
    근거 링크: ID 금지 → 시간 구간 OR 댓글 인덱스만
    """
    t_start: Optional[float] = Field(default=None, ge=0.0)
    t_end: Optional[float] = Field(default=None, ge=0.0)
    comment_idx: Optional[int] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def _validate_one_of(self) -> "CausalEvidence":
        has_time = self.t_start is not None and self.t_end is not None
        has_comment = self.comment_idx is not None
        if not (has_time or has_comment):
            raise ValueError("CausalEvidence must have (t_start,t_end) OR comment_idx")
        return self


class CausalMetricPrediction(BaseModel):
    """
    수치 추정 금지 → 방향/안정성만
    """
    metric_id: str
    expected_direction: Literal["increase", "decrease", "stable", "unknown"] = "unknown"
    note: Optional[str] = None


class CausalMechanism(BaseModel):
    mechanism_id: str = Field(..., description="snake_case id")
    summary: str
    explanation: str
    evidence: List[CausalEvidence] = Field(default_factory=list)
    predictions: List[CausalMetricPrediction] = Field(default_factory=list)
    reproduction_tip: Optional[str] = None
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)


class CausalReasoning(BaseModel):
    why_it_works: str
    mechanisms: List[CausalMechanism] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)
    next_experiments: List[str] = Field(default_factory=list)


class AnalysisPointSeed(BaseModel):
    """
    CV 측정 지점 제안. ID 생성 금지, 수치 생성 금지.
    """
    t_center: float = Field(..., ge=0.0)
    t_window: Optional[List[float]] = Field(default=None, description="[start,end] seconds")
    priority: PriorityLevel = "medium"
    reason: ReasonCode = "other"
    metrics_requested: List["MetricRequest"] = Field(default_factory=list)
    target_entity_hint: Optional[str] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def _validate_window(self) -> "AnalysisPointSeed":
        if self.t_window is not None:
            if len(self.t_window) != 2:
                raise ValueError("t_window must be [start,end]")
            if self.t_window[0] > self.t_window[1]:
                raise ValueError("t_window start must be <= end")
        return self


class UnifiedPassLLMOutput(BaseModel):
    """
    Gemini 3.0 Pro 1회 호출 출력 계약
    """
    semantic: "SemanticPassResult"  # 기존 스키마 재사용
    analysis_point_seeds: List[AnalysisPointSeed] = Field(default_factory=list)
    causal_reasoning: Optional[CausalReasoning] = None
```

---

## 2) 프롬프트: `unified_prompt.py`

**위치**: `backend/app/services/vdg_2pass/prompts/unified_prompt.py`

```python
from __future__ import annotations
from typing import Sequence, Any
from datetime import datetime

UNIFIED_PROMPT_VERSION = "unified_pro_v1.0"

REASON_CODES_HELP = """\
Allowed reason codes (choose exactly one):
- hook_first_2s: 첫 2초 훅 구조
- hook_microbeat: 훅 내부 마이크로비트
- pace_shift: 템포 변화 지점
- jump_cut: 점프컷 전환
- comment_mise_en_scene: 댓글 지목 미장센
- comment_wardrobe: 댓글 지목 의상
- comment_sfx: 댓글 지목 효과음
- comment_caption: 댓글 지목 자막
- camera_motion: 카메라 움직임
- audio_clarity: 음질/발화
- cta_moment: CTA 지점
- product_shot: 제품 샷
- other: 기타
"""

def _format_comments(comments: Sequence[str], max_items: int = 20) -> str:
    lines = []
    for i, c in enumerate(list(comments)[:max_items], start=1):
        c = (c or "").strip().replace("\n", " ")
        if c:
            lines.append(f"[C{i:02d}] {c}")
    return "\n".join(lines) if lines else "(no comments)"


def build_system_prompt(metric_registry_text: str) -> str:
    return f"""\
You are Komission's Viral DNA analyst.

Your job (single response):
1) Explain WHY the video works (causal reasoning)
2) Extract intended mise-en-scène (from video + comments)
3) Propose WHERE CV should measure (analysis_point_seeds)

HARD CONSTRAINTS:
- Output MUST be valid JSON only. No markdown.
- DO NOT generate IDs (ap_id, evidence_id, cluster_id)
- DO NOT guess numeric values. Only request what to measure.
- Timestamps in seconds (float). Keep within duration.
- metric_id MUST match Metric Registry exactly.
- reason MUST be from allowed codes.

For analysis_point_seeds:
- 6~12 seeds max
- Each seed: 1~3 metrics
- Default t_window: [t_center-0.25, t_center+0.25]
- target_entity_hint: "main_speaker" / "product" / "text_overlay"

Metric Registry (exact match required):
{metric_registry_text}

{REASON_CODES_HELP}

Language: Korean for explanations. Concrete, not academic.
"""


def build_user_prompt(
    *,
    content_id: str,
    platform: str,
    niche: str,
    duration_sec: float,
    top_comments: Sequence[str],
    extra_context: str | None = None,
) -> str:
    comments_block = _format_comments(top_comments)
    extra = extra_context.strip() if extra_context else "(none)"

    return f"""\
[VIDEO META]
- content_id: {content_id}
- platform: {platform}
- niche: {niche}
- duration_sec: {duration_sec:.3f}
- run_at_utc: {datetime.utcnow().isoformat()}Z

[TOP COMMENTS]
{comments_block}

[GOAL]
- 산출물: 증명 가능한 바이럴 DNA
- Pass2(CV)가 측정할 seeds 제안
- 왜 중요한지 causal_reasoning에 연결

[CONTEXT]
{extra}
"""
```

---

## 3) genai_client 확장: `generate_content_typed`

**위치**: `backend/app/services/genai_client.py`에 추가

```python
# genai_client.py에 추가

from dataclasses import dataclass
from typing import Any, Optional, TypeVar, Generic

T = TypeVar("T")

@dataclass
class GenAIResponseTyped(Generic[T]):
    success: bool
    text: Optional[str] = None
    parsed: Optional[T] = None
    latency_ms: int = 0
    usage: dict[str, Any] | None = None
    error: Optional[str] = None
    error_code: Optional[str] = None


def generate_content_typed(
    *,
    client,
    model_id: str,
    contents: list,
    system_instruction: str,
    response_schema: Any,
    temperature: float = 0.2,
    top_p: float = 0.95,
    max_output_tokens: int = 8192,
    hook_clip_fps: float = 10.0,  # A 컨설턴트 채택
    full_video_fps: float = 1.0,  # A 컨설턴트 채택
) -> GenAIResponseTyped[T]:
    """
    Structured output with Pydantic parsing.
    Hook clip: 10fps, Full video: 1fps (A 컨설턴트 방식)
    """
    from google.genai import types
    import time
    
    start_time = time.time()
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
        response_mime_type="application/json",
        response_schema=response_schema,
    )

    try:
        resp = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=config,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return GenAIResponseTyped(
            success=True,
            text=getattr(resp, "text", None),
            parsed=getattr(resp, "parsed", None),
            usage=getattr(resp, "usage_metadata", None) or {},
            latency_ms=latency_ms,
        )
    except Exception as e:
        return GenAIResponseTyped(
            success=False,
            error=str(e),
            error_code=type(e).__name__,
        )
```

---

## 4) Pass 실행: `unified_pass.py`

**위치**: `backend/app/services/vdg_2pass/unified_pass.py`

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence, Optional

from google.genai import types

from app.schemas.vdg_v4 import (
    UnifiedPassLLMOutput, 
    SemanticPassProvenance,
)
from app.schemas.metric_registry import METRIC_DEFINITIONS, validate_metric_id
from app.services.genai_client import get_genai_client, generate_content_typed
from app.services.vdg_2pass.prompts.unified_prompt import (
    UNIFIED_PROMPT_VERSION,
    build_system_prompt,
    build_user_prompt,
)


def _render_metric_registry() -> str:
    """Metric Registry SSoT → 프롬프트 텍스트 (drift 0)"""
    lines = []
    for metric_id, meta in METRIC_DEFINITIONS.items():
        desc = ""
        if isinstance(meta, dict):
            desc = meta.get("description", "")
        else:
            desc = getattr(meta, "description", "")
        desc = (desc or "").strip().replace("\n", " ")
        lines.append(f"- {metric_id}" + (f": {desc}" if desc else ""))
    return "\n".join(lines)


@dataclass(frozen=True)
class UnifiedPassConfig:
    model_id: str = "gemini-3.0-pro"
    temperature: float = 0.2
    top_p: float = 0.95
    max_output_tokens: int = 8192
    hook_clip_seconds: float = 4.0  # A 컨설턴트
    hook_clip_fps: float = 10.0     # A 컨설턴트
    full_video_fps: float = 1.0     # A 컨설턴트


class UnifiedProPass:
    def __init__(self, cfg: Optional[UnifiedPassConfig] = None) -> None:
        default_model = os.getenv("GEMINI_MODEL_PRO", "gemini-3.0-pro")
        self.cfg = cfg or UnifiedPassConfig(model_id=default_model)
        self.client = get_genai_client()

    def run(
        self,
        *,
        content_id: str,
        video_uri_or_path: str,
        duration_sec: float,
        platform: str,
        niche: str,
        top_comments: Sequence[str],
        extra_context: Optional[str] = None,
    ) -> UnifiedPassLLMOutput:
        # 1) 프롬프트 빌드
        metric_registry_text = _render_metric_registry()
        system_prompt = build_system_prompt(metric_registry_text)
        user_prompt = build_user_prompt(
            content_id=content_id,
            platform=platform,
            niche=niche,
            duration_sec=duration_sec,
            top_comments=top_comments,
            extra_context=extra_context,
        )

        # 2) 비디오 파트 (A 컨설턴트: 10fps hook + 1fps full)
        video_parts = self._build_video_parts(video_uri_or_path)

        contents = [
            types.Content(
                role="user",
                parts=video_parts + [types.Part(text=user_prompt)],
            )
        ]

        # 3) API 호출
        resp = generate_content_typed(
            client=self.client,
            model_id=self.cfg.model_id,
            contents=contents,
            system_instruction=system_prompt,
            response_schema=UnifiedPassLLMOutput,
            temperature=self.cfg.temperature,
            top_p=self.cfg.top_p,
            max_output_tokens=self.cfg.max_output_tokens,
        )

        if not resp.success or resp.parsed is None:
            raise RuntimeError(f"UnifiedProPass failed: {resp.error_code} {resp.error}")

        out: UnifiedPassLLMOutput = resp.parsed

        # 4) Metric ID 정규화 (B 컨설턴트)
        for seed in out.analysis_point_seeds:
            for mr in seed.metrics_requested:
                mr.metric_id = validate_metric_id(mr.metric_id)

        # 5) Provenance 주입 (LLM이 만들면 안 됨)
        out.semantic.provenance = SemanticPassProvenance(
            model_id=self.cfg.model_id,
            prompt_version=UNIFIED_PROMPT_VERSION,
            run_at=datetime.now(timezone.utc).isoformat(),
        )

        return out

    def _build_video_parts(self, video_uri_or_path: str) -> list:
        """
        A 컨설턴트 방식: Hook clip (10fps) + Full video (1fps)
        """
        if video_uri_or_path.startswith(("gs://", "https://")):
            # URI 방식
            hook_part = types.Part.from_uri(
                file_uri=video_uri_or_path,
                mime_type="video/mp4",
                video_metadata=types.VideoMetadata(
                    start_offset="0s",
                    end_offset=f"{self.cfg.hook_clip_seconds}s",
                    fps=self.cfg.hook_clip_fps,
                ),
            )
            full_part = types.Part.from_uri(
                file_uri=video_uri_or_path,
                mime_type="video/mp4",
                video_metadata=types.VideoMetadata(
                    fps=self.cfg.full_video_fps,
                ),
            )
            return [hook_part, full_part]
        else:
            # 로컬 파일 (bytes)
            with open(video_uri_or_path, "rb") as f:
                data = f.read()
            return [types.Part.from_bytes(data=data, mime_type="video/mp4")]
```

---

## 5) 치명적 결함 방지 (B 컨설턴트)

| 결함 | 방지책 |
|------|--------|
| **LLM이 metric_id 발명** | Registry list 자동 생성 + `validate_metric_id()` |
| **Evidence를 ID로 링크** | `CausalEvidence`: time range OR comment_idx만 허용 |
| **Pass 1에서 수치 추정** | 프롬프트에 "numeric guess 금지" 강제 |

---

## 6) DoD 체크리스트 (B 컨설턴트)

1. ✅ Gemini 호출 **딱 1번** (UnifiedProPass.run)
2. ✅ response_schema로 **파싱** (`resp.parsed` 존재)
3. ✅ LLM 출력에 **ap_id/evidence_id 없음**
4. ✅ analysis_point_seeds **6~12개**, metric_id **registry 내**
5. ✅ semantic.provenance **코드가 주입**
6. ✅ Pass 1 결과에 **brightness 같은 수치 없음**

---

## 7) AnalysisPlanner 연결

Pass 1 출력을 기존 파이프라인에 연결:

```python
# vdg.semantic = out.semantic
# analysis_plan = AnalysisPlanner.plan(
#     semantic=out.semantic, 
#     seeds=out.analysis_point_seeds,
#     duration=duration_sec
# )
# → CV Pass가 analysis_plan.points 기반으로 측정
```

AnalysisPlanner 수정:
- 기존: `plan(semantic)`
- 변경: `plan(semantic, seeds=None)`
  - (a) semantic 기반 기본 seeds + (b) LLM seeds 병합
  - overlap merge → ap_id 생성 → validate_metric_id

---

## 8) 다음 단계

### P0: Pass 2 (CV MVP)
```python
# cv_measurement_pass.py
# 3 메트릭만 먼저:
# - cmp.center_offset_xy.v1
# - lit.brightness_ratio.v1
# - cmp.blur_score.v1
```

### P1: Full CV Pass
- 전체 metric registry 지원
- deterministic evidence_id 생성
- evidence frame 저장

---

> 이 문서는 두 컨설턴트(A/B)의 장점을 통합한 최종 구현 가이드입니다.
