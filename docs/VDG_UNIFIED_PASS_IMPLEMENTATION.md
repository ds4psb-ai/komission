# VDG Pro 1-Pass + CV 아키텍처 컨설팅 결과

> 작성일: 2025-12-31 | 컨설턴트 제공 구현 코드

---

## 설계 원칙

**Pass 1 (LLM)**: 의미/인과/측정설계(Plan)만 생성
**Pass 2 (CV)**: 수치/좌표/결정론적 측정만 수행

### 정합성 규칙 (깨면 안 됨)

1. **ID 생성은 LLM 금지** - `ap_id`, `evidence_id`는 코드에서만 생성
2. **Metric Registry 밖 metric_id 금지** - LLM은 허용 목록에서만 선택
3. **Plan은 "Seed"로 받음** - 정규화(overlap merge, window clamp, budget limit)는 코드에서

---

## 1. 스키마: `vdg_unified_pass.py`

**위치**: `backend/app/schemas/vdg_unified_pass.py`

### 주요 구조

```
UnifiedPassLLMOutput
├── schema_version: str
├── duration_ms: int
├── hook_genome: HookGenomeLLM
│   ├── strength: float (0-1)
│   ├── hook_start_ms, hook_end_ms
│   ├── microbeats: List[MicrobeatLLM]
│   └── spoken_hook, on_screen_text
├── scenes: List[SceneLLM]
├── intent_layer: IntentLayerLLM
├── mise_en_scene_signals: List[MiseEnSceneSignalLLM]
├── entity_hints: Dict[str, EntityHintLLM]  → CV에게 전달
├── analysis_plan: AnalysisPlanSeedLLM      → CV에게 전달
└── causal_reasoning: CausalReasoningLLM    → "왜 바이럴인가"
```

### 핵심 포인트

- **ID 없음**: ap_id, evidence_id 포함 안 함
- **metric_id**: METRIC_DEFINITIONS allow-list에서만 선택
- **타임스탬프**: 모두 milliseconds (int)
- **검증**: Pydantic model_validator로 범위 검증

---

## 2. 프롬프트: `unified_prompt.py`

**위치**: `backend/app/services/vdg_2pass/prompts/unified_prompt.py`

### 핵심 설계

```python
def build_unified_prompt(
    *,
    duration_ms: int,
    platform: str,
    caption: Optional[str],
    hashtags: Optional[List[str]],
    top_comments: List[str],
    metric_definitions: Dict[str, Any],  # METRIC_DEFINITIONS 주입
) -> str:
```

### 프롬프트 제약 조건

1. **JSON만 출력** (마크다운 금지)
2. **ID 생성 금지** (ap_id, evidence_id 절대 생성하지 않음)
3. **metric_id는 allow-list에서만 선택**
4. **모든 타임스탬프는 milliseconds (int)**
5. **analysis_plan.points: 6~10개 권장 (max 12)**

---

## 3. Pass 실행: `unified_pass.py`

**위치**: `backend/app/services/vdg_2pass/unified_pass.py`

### 핵심 API 설계

```python
class UnifiedPass:
    def __init__(
        self,
        model_id: str = "gemini-3.0-pro",
        media_resolution: str = "low",      # 토큰 비용 제어
        hook_clip_seconds: float = 4.0,     # 훅 구간 길이
        hook_clip_fps: float = 10.0,        # 훅만 10fps
        full_video_fps: float = 1.0,        # 나머지 1fps
    ):
        ...

    def run(
        self,
        video_path: str,
        platform: str,
        caption: Optional[str],
        hashtags: Optional[List[str]],
        top_comments: List[str],
    ) -> tuple[UnifiedPassLLMOutput, UnifiedPassProvenance]:
        ...
```

### API 호출 구조

```
1개 요청에 2개 비디오 파트:
├── Hook clip (0~4초): 10fps (정밀 microbeat 분석)
└── Full video: 1fps (전체 인과관계)
```

### Structured Output 설정

```python
generate_content(
    model=self.model_id,
    contents=contents,
    response_mime_type="application/json",
    response_schema=UnifiedPassLLMOutput.model_json_schema(),
    media_resolution=self.media_resolution,
)
```

---

## 4. genai_client.py 패치 필요

**문제**: SDK 버전에 따라 `response_schema` vs `response_json_schema` 필드명이 다름

**해결책**:

```python
# 둘 다 세팅 (SDK 버전 차이 흡수)
if response_schema is not None:
    try:
        setattr(config, "response_json_schema", response_schema)
    except Exception:
        pass
    try:
        setattr(config, "response_schema", response_schema)
    except Exception:
        pass
```

---

## 5. PR 체크리스트

### A. 호출/입력
- [ ] 비디오 업로드/uri 기반 Part 생성 동작
- [ ] hook clip + full video 2개 part가 1회 호출에 포함
- [ ] hook fps=10, full fps=1 세팅
- [ ] media_resolution 환경변수 제어

### B. 출력/정합성
- [ ] 응답이 JSON, 스키마로 파싱
- [ ] metric_id가 항상 allow-list 안에 있음
- [ ] LLM 출력에 ap_id, evidence_id 절대 없음

### C. 운영성
- [ ] provenance 기록 (prompt_version, model_id, run_at, fps)
- [ ] 실패 시 error_code/latency/usage 로그
- [ ] Sentry 관찰 가능

---

## 6. 다음 단계

### P0: Plan Seed → Deterministic AnalysisPlan 정규화
- overlap merge
- duration clamp
- metric validate/normalize
- budget limit

### P1: CV Pass MVP (3메트릭)
- `cmp.center_offset_xy.v1`
- `lit.brightness_ratio.v1`
- `cmp.blur_score.v1`

---

> 이 문서는 외부 컨설턴트가 제공한 구현 가이드입니다.
