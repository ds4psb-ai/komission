# VDG v4.0 2-Pass Pipeline Protocol (Final)

> **핵심 통찰:** 비용은 1/5로 줄고, 데이터 가치는 5배로 뜀  
> 이 프로토콜은 "AI가 발전해도 규칙은 명확하게 유지"되도록 설계됨

---

## Overview

```
영상 + 댓글
    │
    ▼
┌─────────────────────────────────────┐
│  1차: Semantic Pass (의미 해석)     │  ← 30초
│  - 구조/의도/텍스트 내용            │
│  - Entity Hints 구조화              │
│  - 댓글 기반 Mise-en-Scène 신호     │
└────────────────┬────────────────────┘
                 │
                 ▼  (Analysis Plan + Entity Hints)
┌─────────────────────────────────────┐
│  2차: Visual Pass (시각 해석)       │  ← 2분
│  - 구간 기반 측정 + 분포 통계       │
│  - Entity 검증 + 추적               │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  VDG Merger                         │
│  - Semantic-Visual Alignment 검증  │
│  - Contract Candidates 생성        │
│  → VDG v4.0 Full                   │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Director Pack Compiler             │
└─────────────────────────────────────┘
```

---

## 보강 1: Metric Registry (측정 사전)

> 💡 "center_offset이 정확히 무엇인지" 미래에도 명확하게 유지

```python
class MetricDefinition(BaseModel):
    metric_id: str  # "center_offset_xy"
    description: str
    unit: Literal["norm_0_1", "deg", "ratio", "bool", "enum", "px"]
    coordinate_frame: Literal[
        "raw_frame",
        "safe_area_adjusted",
        "cropped_primary_subject"
    ]
    aggregation_allowed: List[Literal["mean", "median", "trimmed_mean", "mode", "p10_p90", "variance"]]
    expected_range: Optional[List[float]] = None  # [0.0, 1.0]
    notes: Optional[str] = None
```

**표준 Metric 정의:**

| metric_id | unit | coordinate_frame | aggregation |
|-----------|------|------------------|-------------|
| `center_offset_xy` | norm_0_1 | safe_area_adjusted | median |
| `headroom_ratio` | ratio | raw_frame | mean |
| `subject_area_ratio` | ratio | raw_frame | mean |
| `stability_score` | norm_0_1 | - | variance |
| `visibility_ratio` | ratio | raw_frame | max |
| `dominant_color` | enum | - | mode |

---

## 보강 2: Entity Hints (구조화된 주인공 지정)

> 💡 단순 라벨이 아닌 "후보 + 검증 + 폴백"

```python
class EntityHint(BaseModel):
    hint_key: str  # "main_speaker"
    entity_type: Literal["person", "product", "text", "hand", "other"]
    label: str  # human-readable
    attributes: Dict[str, Any] = {
        "color": "yellow",
        "item": "shirt",
        "gender": "female",
        "location_prior": "center"
    }
    candidates: List[str] = []  # fallback 후보
    confidence: float = 0.7
    evidence_refs: List[str] = []  # link to evidence_items

class EntityResolution(BaseModel):
    """2차에서 검증 결과"""
    hint_key: str
    resolved_entity_id: Optional[str] = None
    resolution_method: Literal["direct", "fallback_largest", "fallback_speaker", "failed"]
    confidence: float
```

**Blind Spot #5 해결:** Hero 실패 시 폴백 규칙
```python
fallback_rules = [
    "largest_face_bbox",      # 가장 큰 얼굴
    "most_speech_overlap",    # 발화 구간과 가장 일치
    "center_screen_priority"  # 화면 중앙 우선
]
```

---

## 보강 3: Analysis Plan (예산/병합/클램프)

> 💡 analysis_points를 "Plan"으로 승격하여 비용 통제

```python
class SamplingPolicy(BaseModel):
    target_fps: float = 12.0
    min_samples: int = 8
    max_samples: int = 24

class AnalysisPlan(BaseModel):
    plan_version: str = "1.0"
    max_points_total: int = 25
    budget_by_priority: Dict[str, int] = {
        "critical": 8, "high": 10, "medium": 7, "low": 0
    }
    merge_overlap_threshold: float = 0.6
    clamp_to_scene_boundaries: bool = True  # Blind Spot #4 해결
    sampling: SamplingPolicy
    points: List[AnalysisPoint]
```

**Blind Spot #4 해결:** 씬 경계 처리
```python
class AnalysisPoint(BaseModel):
    # ... 기존 필드 ...
    window_policy: Literal["clamp", "split"] = "clamp"
    # clamp: 씬 경계에서 잘림
    # split: 씬 경계에서 두 개로 분리
```

---

## 보강 4: 분포 통계 저장

> 💡 mean만 저장하지 말고 분산/사분위/결측 이유까지

```python
class MeasurementStats(BaseModel):
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    p10: Optional[float] = None
    p90: Optional[float] = None
    stability_score: Optional[float] = None  # 0~1

class MetricResult(BaseModel):
    metric_id: str
    value_type: Literal["scalar", "vector2", "ratio", "bool", "enum"]
    value: Optional[Any] = None
    stats: Optional[MeasurementStats] = None
    missing_reason: Optional[str] = None  # "occluded", "out_of_frame"
```

---

## 보강 5: Evidence 통합 규격

> 💡 모든 산출물에 통일된 증거 참조

```python
class EvidenceItem(BaseModel):
    evidence_id: str
    type: Literal["frame", "clip", "audio_segment", "asr_span", "ocr_span", "comment", "metric"]
    t_range: Optional[List[float]] = None
    uri: Optional[str] = None
    sha256: Optional[str] = None
    summary: Optional[str] = None

class EvidenceLink(BaseModel):
    evidence_refs: List[str] = []
    confidence: float = 0.8
    method: Literal["llm", "cv", "asr", "ocr", "hybrid"] = "hybrid"
    model_info: Optional[Dict[str, Any]] = None
```

---

## 보강 6: Contract Candidates (Pack 컴파일 입력)

> 💡 Merger에서 Pack 규칙 후보를 자동 생성

```python
class ContractCandidates(BaseModel):
    dna_invariants_candidates: List[Dict[str, Any]] = []
    mutation_slots_candidates: List[Dict[str, Any]] = []
    forbidden_mutations_candidates: List[Dict[str, Any]] = []
    weights_candidates: Dict[str, float] = {}
    tolerances_candidates: Dict[str, float] = {}
```

---

## 1차: Semantic Pass (최종)

### 출력 필드

| 필드 | 설명 |
|------|------|
| `scenes[]` | 씬/샷 경계 + 내러티브 역할 |
| `hook_genome` | 훅 타이밍, 패턴, microbeats |
| `intent_layer` | 심리 의도, dopamine_radar, sentiment_arc |
| `asr_transcript` | 전체 음성 텍스트 |
| `ocr_content[]` | 화면 텍스트 **내용만** |
| `audience_reaction` | 댓글 기반 바이럴 신호 |
| `mise_en_scene_signals[]` | **댓글 기반 미장센 신호** (신규) |
| `capsule_brief` | 실행 가이드 |
| `commerce` | 제품/브랜드 언급 |
| `entity_hints` | 구조화된 주인공 힌트 |

### 댓글 기반 Mise-en-Scène 신호 추출

```python
class MiseEnSceneSignal(BaseModel):
    element: Literal["outfit_color", "background", "lighting", "props", "makeup"]
    value: str  # "yellow", "cluttered", "dark"
    sentiment: Literal["positive", "negative", "neutral"]
    source_comment: str
    likes: int
    evidence_refs: List[str] = []
```

```json
{
  "mise_en_scene_signals": [
    {
      "element": "outfit_color",
      "value": "yellow",
      "sentiment": "positive",
      "source_comment": "노란 옷 미쳤다 ㅋㅋ",
      "likes": 1200
    },
    {
      "element": "background",
      "value": "cluttered",
      "sentiment": "negative",
      "source_comment": "배경 너무 지저분해",
      "likes": 300
    }
  ]
}
```

---

## Bridge: Analysis Plan 생성

### 자동 생성 규칙

| 1차 증거 출처 | 생성되는 AnalysisPoint |
|--------------|----------------------|
| `hook_genome.microbeats[]` | `reason: "hook_punch/start/build"` |
| `scenes[].time_start` | `reason: "scene_boundary"` |
| `mise_en_scene_signals[]` | `reason: "comment_mise_en_scene"` |
| `commerce.product_mentions[]` | `reason: "product_mention"` |
| `intent_layer.sentiment_arc.micro_shifts[]` | `reason: "sentiment_shift"` |

---

## 2차: Visual Pass (최종)

### 출력 필드

| 필드 | 1차 참조 | 설명 |
|------|---------|------|
| `entity_catalog[]` | entity_hints | 등장 객체 카탈로그 |
| `entity_resolutions` | entity_hints | 힌트 → 실제 ID 매핑 |
| `entity_tracks[]` | entity_resolutions | 객체 추적 |
| `text_geometries[]` | ocr_content | 텍스트 위치/BBox |
| `analysis_results` | Analysis Plan | 지령별 측정 결과 |

---

## Merger: VDG v4.0 Full

```python
class VDGv4(BaseModel):
    vdg_version: str = "4.0.0"

    # Identity / Media / Provenance
    content_id: str
    platform: str
    title: str = ""
    duration_sec: float
    media: Dict[str, Any] = {}  # width/height/fps/aspect
    provenance: Dict[str, Any] = {}  # run_id, pipeline_version

    # Evidence Graph (shared)
    evidence_items: List[EvidenceItem] = []
    
    # Metric Registry
    metric_registry_version: str = "1.0"
    metric_definitions: Dict[str, MetricDefinition] = {}

    # Pass 1 outputs
    semantic: SemanticPassResult

    # Bridge (Plan)
    analysis_plan: AnalysisPlan

    # Pass 2 outputs
    visual: VisualPassResult

    # Quality
    merger_quality: MergerQuality

    # Contract candidates (for Pack compiler)
    contract_candidates: ContractCandidates

    # Feature vectors
    feature_store_version: str = "0.1"
    feature_vectors: Dict[str, Any] = {}

    # v3 compatibility
    legacy_flat_view: Optional[Dict[str, Any]] = None
```

---

## VDG → Director Pack 변환

### Contract Candidates → Pack Rules

```
contract_candidates.dna_invariants_candidates[]
    ↓
dna_invariants[] (rule_id, domain, priority, spec, coach_line_templates)

contract_candidates.forbidden_mutations_candidates[]
    ↓
forbidden_mutations[] (mutation_id, reason, severity)

contract_candidates.weights_candidates
    ↓
scoring.dna_weights
```

---

## 핵심 원칙 (최종)

| 원칙 | 설명 |
|------|------|
| **1차는 의미** | "무엇을, 왜" - 구조/의도/댓글 미장센 |
| **2차는 시각** | "어떻게, 어디에" - 프레임/객체/구도 |
| **Metric Registry** | 단위/좌표계 명확 → 검출기 교체 가능 |
| **Entity 검증** | 후보 + 폴백 → multi-person 안정화 |
| **Analysis Plan** | 예산/병합/클램프 → 비용 통제 |
| **분포 저장** | 평균 + 분산 → 미래 재사용 |
| **Evidence 통합** | URI/해시/타임코드 → 규칙 근거 추적 |
| **Contract Candidates** | VDG → Pack 연결고리 고정 |

---

## 인과관계 데이터 완성 (3단계)

```
1. VDG 2-Pass     → Context + Metric (상관관계)
2. Live 코칭 로그 → Intervention + Outcome (개입)
3. 둘의 조인      → 진짜 인과 데이터
```

**연결 키:** `analysis_point_id`, `rule_id`, `entity_id`
