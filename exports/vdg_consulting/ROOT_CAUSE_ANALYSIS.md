# VDG 빈 필드 근본 원인 분석

> 분석일: 2026-01-01
> 분석가: Antigravity

---

## 결론

**프롬프트에서 scenes/capsule_brief를 요청하지 않음**

---

## 1. 근본 원인

### 프롬프트 분석 (`unified_prompt.py`)

| 필드 | 프롬프트 요청 | 결과 |
|------|-------------|------|
| `hook_genome` | ✅ L136-138 | 정상 저장 |
| `viral_kicks` | ✅ L107-117 강제 | 정상 저장 |
| `mise_en_scene_signals` | ✅ L132-134 | 정상 저장 |
| `analysis_plan.points` | ✅ L143-155 | 정상 저장 |
| `scenes` | ❌ **요청 없음** | 빈 배열 |
| `capsule_brief` | ❌ **요청 없음** | 빈값 |

### 스키마 기본값 (`vdg_unified_pass.py L323`)

```python
scenes: List[SceneLLM] = Field(default_factory=list, max_length=12)
# LLM이 안 주면 → 빈 배열로 기본값 처리
```

---

## 2. 데이터 흐름

```
unified_prompt.py (scenes 요청 없음)
    ↓
Gemini LLM (scenes 생성 안 함)
    ↓
UnifiedPassLLMOutput.scenes → [] (default_factory=list)
    ↓
vdg_db_saver.py (빈 배열 저장)
    ↓
gemini_analysis.semantic.scenes = []
```

---

## 3. 해결 방법

### Option A: 프롬프트에 scenes 요청 추가
```python
# unified_prompt.py에 추가
G) Scene segmentation:
- Output 4-8 scenes with start_ms, end_ms, label, summary.
- Label: hook/setup/demo/reveal/payoff/cta 중 선택
```

### Option B: CV Pass에서 씬 분할
- ffmpeg scene detection으로 결정론적 분할
- LLM 의존성 제거

---

## 4. 파일 위치

- 프롬프트: `/backend/app/services/vdg_2pass/prompts/unified_prompt.py`
- 스키마: `/backend/app/schemas/vdg_unified_pass.py` L323
