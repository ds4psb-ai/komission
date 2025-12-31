# VDG 파이프라인 리팩토링 컨설팅 요청서

> 작성일: 2025-12-31 | 버전: v3.0 (Pro 1-Pass + CV 아키텍처)

---

## 1. 요청 개요

### 목표
현재 **LLM 2-Pass 구조**를 **Gemini 3.0 Pro 1-Pass + 결정론적 CV 측정** 구조로 리팩토링하여:
1. Gemini 3.0 Pro의 통합 비디오 추론 능력 최대 활용
2. 영상 재현 가능한 수준의 정밀한 수치 데이터 확보
3. 비용 절감 (LLM 2회 → 1회)
4. 데이터 정합성 유지 (SSoT, Deterministic IDs, Metric Registry)

### 핵심 아키텍처 변경

```
[현재] LLM 2-Pass
├── Pass 1: Gemini Flash (Semantic) → AnalysisPlan 생성
└── Pass 2: Gemini Pro (Visual) → 메트릭 측정

[목표] Pro 1-Pass + CV
├── Pass 1: Gemini 3.0 Pro (Unified) → 의미/인과/Plan 통합 추출
└── Pass 2: ffmpeg + OpenCV (CV) → 결정론적 수치 측정
```

---

## 2. 필수 파일 목록 (17개)

### 2.1 핵심 파이프라인 (`/backend/app/services/vdg_2pass/`)

| # | 파일 | 크기 | 역할 | 리팩토링 범위 |
|---|------|------|------|--------------|
| 1 | `semantic_pass.py` | 4.3KB | Pass 1: Semantic 분석 | **폐기 → Unified Pass로 병합** |
| 2 | `visual_pass.py` | 8.7KB | Pass 2: Visual 측정 | **폐기 → CV Pass로 대체** |
| 3 | `analysis_planner.py` | 12.6KB | AnalysisPlan 생성 | 유지 (Pro 출력 정규화) |
| 4 | `merger.py` | 11.0KB | Semantic + Visual 병합 | **대폭 수정** |
| 5 | `director_compiler.py` | 33.2KB | DirectorPack 생성 | 유지 (입력 형식만 변경) |
| 6 | `frame_extractor.py` | 8.0KB | ffmpeg 프레임 추출 | **확장 (CV 측정 추가)** |
| 7 | `gemini_utils.py` | 5.8KB | retry/fallback 유틸 | 유지 |
| 8 | `evidence_id_utils.py` | 2.4KB | 결정론적 ID 생성 | 유지 |

### 2.2 프롬프트 (`/backend/app/services/vdg_2pass/prompts/`)

| # | 파일 | 역할 | 리팩토링 범위 |
|---|------|------|--------------|
| 9 | `semantic_prompt.py` | Semantic 프롬프트 | **병합 → unified_prompt.py** |
| 10 | `visual_prompt.py` | Visual 프롬프트 | **폐기 (CV로 대체)** |

### 2.3 스키마 (`/backend/app/schemas/`)

| # | 파일 | 크기 | 역할 | 리팩토링 범위 |
|---|------|------|------|--------------|
| 11 | `vdg_v4.py` | 34.7KB | VDG v4.0 전체 스키마 | **UnifiedPassResult 추가** |
| 12 | `vdg.py` | - | 레거시 스키마 | 참고용 |

### 2.4 상위 파이프라인 (`/backend/app/services/`)

| # | 파일 | 역할 | 리팩토링 범위 |
|---|------|------|--------------|
| 13 | `gemini_pipeline.py` | 파이프라인 오케스트레이터 | **핵심 수정 (새 아키텍처)** |
| 14 | `analysis_pipeline.py` | 레거시 1-Pass | 참고용 (폐기 예정) |
| 15 | `genai_client.py` | Gemini API 래퍼 | 유지 (이미 하드닝 완료) |

### 2.5 관련 라우터 (`/backend/app/routers/`)

| # | 파일 | 역할 | 리팩토링 범위 |
|---|------|------|--------------|
| 16 | `pipelines.py` | 파이프라인 API | 엔드포인트 수정 |

### 2.6 설정 (`/backend/app/`)

| # | 파일 | 역할 | 리팩토링 범위 |
|---|------|------|--------------|
| 17 | `config.py` | 환경 설정 | VDG_MODE 플래그 추가 |

---

## 3. 신규 생성 필요 파일

| # | 파일 | 역할 | 상세 |
|---|------|------|------|
| A | `unified_pass.py` | **Pro 1-Pass 통합 분석** | Gemini 3.0 Pro로 의미/인과/Plan 추출 |
| B | `cv_measurement_pass.py` | **CV 측정 Pass** | ffmpeg + OpenCV로 정밀 수치 측정 |
| C | `prompts/unified_prompt.py` | **통합 프롬프트** | Semantic + Visual 통합 |
| D | `cv_metrics.py` | **CV 메트릭 계산** | brightness, center_offset, blur 등 |

---

## 4. 상세 요구사항

### 4.1 Pass 1: Unified Pro Pass

**입력:**
- 전체 비디오 (오디오 포함)
- 댓글 컨텍스트 (상위 20개)
- 플랫폼 메타데이터

**출력 (UnifiedPassResult):**
```python
class UnifiedPassResult(BaseModel):
    # Semantic 영역
    scenes: List[Scene]
    hook_genome: HookGenome
    intent_layer: IntentLayer
    mise_en_scene_signals: List[MiseEnSceneSignal]
    
    # Analysis Plan (CV에게 전달)
    analysis_plan: AnalysisPlan  # 어디를 측정할지
    entity_hints: Dict[str, EntityHint]
    
    # 인과 추론 (Gemini 3.0 Pro 전용)
    causal_reasoning: CausalReasoning  # "왜" 이 영상이 작동하는가
    
    # Provenance
    provenance: UnifiedPassProvenance
```

**설정:**
- 모델: `gemini-3.0-pro` (환경변수로 전환 가능)
- 10fps: hook 구간 ±0.5s, 빠른 동작 구간
- Deep Think: 옵션 (복잡한 인과 추론 시)

### 4.2 Pass 2: CV Measurement Pass

**입력:**
- 비디오 파일
- AnalysisPlan (Pass 1에서 받은 "어디를 측정할지")
- Entity Hints

**출력 (CVMeasurementResult):**
```python
class CVMeasurementResult(BaseModel):
    metrics: Dict[str, MetricResult]  # ap_id → 측정값
    
    # 각 MetricResult 예시:
    # - center_offset_xy: [0.42, 0.18]
    # - brightness: 0.73
    # - blur_score: 0.12
    # - face_bbox: [x, y, w, h]
    # - scene_cuts: [2.3, 5.1, 8.7]  # 초 단위
    
    evidence_frames: Dict[str, FrameEvidence]  # 증거 프레임
    provenance: CVMeasurementProvenance
```

**측정 항목 (결정론적):**

| 메트릭 | 도구 | 출력 | 용도 |
|--------|------|------|------|
| `center_offset_xy` | OpenCV face/object detect | `[float, float]` | 피사체 위치 재현 |
| `brightness` | OpenCV histogram | `float 0-1` | 조명 재현 |
| `contrast` | OpenCV | `float` | 그레이딩 재현 |
| `blur_score` | Laplacian variance | `float` | 카메라 움직임 |
| `scene_cuts` | ffmpeg scene detect | `List[float]` | 편집 리듬 재현 |
| `dominant_colors` | K-means clustering | `List[RGB]` | 색감 재현 |
| `face_bbox` | OpenCV/MTCNN | `[x,y,w,h]` | 구도 재현 |
| `motion_vectors` | optical flow | `[dx, dy]` | 움직임 재현 |

---

## 5. 제약 조건 (반드시 유지)

### 5.1 데이터 정합성 (깨면 안 됨)

| 항목 | 설명 | 파일 |
|------|------|------|
| **Deterministic IDs** | ap_id, evidence_id는 코드가 생성 (LLM X) | `evidence_id_utils.py` |
| **Metric Registry** | 메트릭 ID 정규화/검증 | `vdg_v4.py`, `visual_prompt.py` |
| **SSoT** | mise_en_scene_signals는 Semantic에서만 | `semantic_pass.py` → `unified_pass.py` |
| **Provenance** | prompt_version, model_id, run_at 필수 | 모든 Pass |

### 5.2 하위 호환성

- 기존 VDG v4.0 스키마 유지 (필드 추가 가능, 제거 불가)
- DirectorPack 출력 형식 유지
- Coaching 연동 인터페이스 유지

### 5.3 Feature Flag

```python
# config.py
VDG_PIPELINE_MODE = os.getenv("VDG_PIPELINE_MODE", "pro_unified")
# Options: "legacy_2pass" | "pro_unified" | "pro_unified_cv"
```

---

## 6. 평가 기준

### 6.1 A/B 테스트 (10개 샘플)

| 지표 | 현재 2-Pass | 목표 Pro+CV |
|------|------------|-------------|
| Hook 타이밍 정확도 | 기준 | ≥ 기준 |
| 수치 재현성 (같은 영상 3회) | 분산 있음 | 분산 0 |
| API 비용 | Flash + Pro | Pro만 |
| 지연시간 | ~10초 | ≤ 8초 |

### 6.2 코드 품질

- 타입 힌트 100%
- 단위 테스트 커버리지 ≥ 80%
- 프롬프트/스키마 버전 관리

---

## 7. 우선순위

| Phase | 작업 | 기간 |
|-------|------|------|
| **P0** | unified_pass.py + unified_prompt.py | 3일 |
| **P0** | cv_measurement_pass.py (핵심 3개 메트릭) | 2일 |
| **P1** | merger.py 수정 | 1일 |
| **P1** | gemini_pipeline.py 오케스트레이터 | 2일 |
| **P2** | A/B 테스트 + 평가 | 2일 |

---

## 8. 첨부 파일

다음 파일들을 함께 전달합니다:

```
/backend/app/services/vdg_2pass/
├── semantic_pass.py          # 현재 Pass 1
├── visual_pass.py            # 현재 Pass 2
├── analysis_planner.py       # Plan 생성
├── merger.py                 # 병합
├── director_compiler.py      # Pack 생성
├── frame_extractor.py        # ffmpeg 래퍼
├── gemini_utils.py           # retry/fallback
├── evidence_id_utils.py      # 결정론적 ID
└── prompts/
    ├── semantic_prompt.py
    └── visual_prompt.py

/backend/app/schemas/
├── vdg_v4.py                 # VDG 스키마

/backend/app/services/
├── gemini_pipeline.py        # 파이프라인 오케스트레이터
├── genai_client.py           # Gemini API 래퍼
└── analysis_pipeline.py      # 레거시 (참고용)
```

---

## 9. 기대 산출물

1. **리팩토링된 파이프라인 코드** (unified_pass.py, cv_measurement_pass.py)
2. **통합 프롬프트** (unified_prompt.py)
3. **수정된 스키마** (vdg_v4.py에 UnifiedPassResult 추가)
4. **A/B 테스트 결과 리포트**
5. **마이그레이션 가이드** (기존 데이터 호환성)

---

> 본 요청서는 VDG 파이프라인을 "Gemini 3.0 Pro 1-Pass + CV 결정론적 측정" 아키텍처로 완전히 리팩토링하기 위해 작성되었습니다.
