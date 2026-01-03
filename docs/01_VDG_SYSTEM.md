# VDG System v4.0: Unified Pipeline Architecture (Final)

**작성**: 2025-12-28  
**Updated**: 2026-01-01  
**목표**: VDG v4.0 Unified Pipeline (Pro 1-Pass + CV) + Director Pack + Audio Coaching 통합 문서

---

## 1) Overview: VDG v4.0 Unified Pipeline

```
영상 + 댓글
     ↓
┌─────────────────────────────────────┐
│  Pass 1: Pro LLM (의미/인과/Plan)   │  ← Gemini 3.0 Pro 1회
│  - 10fps hook + 1fps full           │
│  - JSON output (manual validation)    │
│  - Entity Hints → CV 전달           │
│  - 댓글 기반 Mise-en-Scène 신호     │
└────────────────┬────────────────────┘
                 ↓  (UnifiedPassLLMOutput)
┌─────────────────────────────────────┐
│  Pass 2: CV (결정론적 측정)          │  ← ffmpeg + OpenCV
│  - 3 MVP 메트릭 (100% 재현 가능)    │
│  - Plan 기반 프레임 추출            │
│  - Metric Registry 검증             │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  VDG Merger / Orchestrator          │
│  - Semantic-Visual 정합성 검증      │
│  - Contract Candidates 생성         │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Director Pack Compiler             │
│  - Contract-First + heuristic 보강 │
│  - Metric Validation                │
│  → DirectorPack v1.0.2              │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Audio Coach (Gemini 2.5 Flash)     │
│  - Pack 기반 실시간 코칭            │
│  - One-Command 정책                 │
└─────────────────────────────────────┘
```

---

## 2) 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **1차는 의미** | "무엇을, 왜" - 구조/의도/댓글 미장센 |
| **2차는 시각** | "어떻게, 어디에" - 프레임/객체/구도 |
| **Metric Registry** | 단위/좌표계 명확 → 검출기 교체 가능 |
| **Entity 검증** | 후보 + 폴백 → multi-person 안정화 |
| **Analysis Plan** | 예산/병합/클램프 → 비용 통제 |
| **분포 저장** | 평균 + 분산 → 미래 재사용 |
| **Evidence 통합** | URI/해시/타임코드 → 규칙 근거 추적 |
| **Contract-First** | VDG → Pack 연결고리 고정 (heuristic 보강/폴백 포함) |

---

## 3) Core Schemas

### 3.1 VDGv4 Main Structure
```python
class VDGv4(BaseModel):
    # Core identifiers
    vdg_version: str = "4.0.2"
    content_id: str
    duration_sec: float
    
    # Pass 1: Semantic
    semantic: SemanticPassResult
    
    # Bridge: Analysis Plan
    analysis_plan: AnalysisPlan
    
    # Pass 2: Visual
    visual: VisualPassResult
    
    # Quality check
    merger_quality: MergerQuality
    
    # Pack input
    contract_candidates: ContractCandidates
    
    # Evidence
    evidence_items: List[EvidenceItem]
    
    # Flywheel
    distill_runs: List[DistillRun]
```

### 3.2 Metric Registry (SSoT)
```python
# app/schemas/metric_registry.py
class MetricDefinition(BaseModel):
    metric_id: str  # "cmp.center_offset_xy.v1"
    description: str
    unit: str  # "norm_0_1", "ratio", "bool"
    coordinate_frame: str
    aggregation_allowed: List[str]
```

### 3.3 Director Pack
```python
class DirectorPack(BaseModel):
    pack_version: str = "1.0.2"
    pattern_id: str
    goal: str
    
    # Rules
    dna_invariants: List[DNAInvariant]
    mutation_slots: List[MutationSlot]
    forbidden_mutations: List[ForbiddenMutation]
    
    # Coaching
    checkpoints: List[Checkpoint]
    policy: Policy
```

---

## 4) Hardenings (완료)

### P0 Foundation (10/10)
1. ✅ 2-Pass 구조 (Semantic → Visual)
2. ✅ Metric Registry SSoT
3. ✅ Plan-based frame extraction
4. ✅ AP ID deterministic (`ap.{domain}.{idx}.{hash}`)
5. ✅ Evidence ID structural (`ev.frame.{id}.{ap_id}.{t_ms}`)
6. ✅ Contract-first compiler
7. ✅ Pack fallback rules (silent director 방지)
8. ✅ Compiler metric validation
9. ✅ Compiler fallback warnings
10. ✅ VisualPass metric validation

### Flywheel Hardenings
- ✅ `DistillRun` schema (NotebookLM-ready)
- ✅ `SignalPerformance` tracking
- ✅ `InvariantCandidate` intermediate state
- ✅ A→B Migration (Signal → Invariant 자동 승격)

### Cluster SoR
- ✅ `ContentCluster` (parent-kids)
- ✅ `ClusterSignature` for similarity

### RL Data Schema
- ✅ `CoachingIntervention` (rule_id, ap_id, evidence_id)
- ✅ `CoachingOutcome` (compliance, metric_before/after)
- ✅ `SessionContext` (persona, environment, device)

### Normalized Evidence Tables (Added 2026-01-01)
- ✅ `viral_kicks` (23 columns): 바이럴 킥 정규화 테이블
- ✅ `keyframe_evidences` (14 columns): 프레임 증거 테이블
- ✅ `comment_evidences` (8 columns): 댓글 증거 테이블

### Coaching System Phase 1-5+ (Added 2026-01-03) ⭐ NEW
- ✅ 출력 모드 4종: graphic | text | audio | graphic_audio
- ✅ 페르소나 4종: drill_sergeant | bestie | chill_guide | hype_coach (aliases: strict_pd | close_friend | calm_mentor | energetic)
- ✅ LLM 기반 적응형 코칭 (`AdaptiveCoachingService`)
- ✅ VDG 데이터 활용 (shotlist, kicks, mise_en_scene)
- ✅ 고급 자동학습 (`AdvancedSessionAnalyzer`, `WeightedSignal`, `LiveAxisMetrics`)

---

## 5) File Structure (Updated 2026-01-01)

```
backend/app/
├── schemas/
│   ├── vdg_v4.py             # VDG v4.0 schemas (881 lines)
│   ├── vdg_unified_pass.py   # Unified Pass output (333 lines) + pattern/delivery/hook_summary
│   ├── director_pack.py      # Director Pack (355 lines)
│   └── metric_registry.py    # Metric SSoT (180 lines)
│
├── services/
│   ├── gemini_pipeline.py    # [WRAPPER] → vdg_pipeline/ 패키지로 위임
│   ├── vdg_extractor.py      # [NEW] VDG 헬퍼 함수 (extract_*, translate_*)
│   ├── genai_client.py       # google-genai SDK client
│   ├── audio_coach.py        # Gemini 2.5 Flash Live
│   └── evidence_updater.py   # RL weight adjustment
│
├── services/vdg_pipeline/    # [NEW] Phase 2 리팩토링 (2026-01-01)
│   ├── __init__.py           # 공개 API (GeminiPipeline, gemini_pipeline)
│   ├── constants.py          # VDG_PROMPT (7771 chars)
│   ├── prompt_builder.py     # 영상 길이별 프롬프트 빌더
│   ├── sanitizer.py          # 페이로드 정제, 레거시 필드
│   ├── converter.py          # UnifiedResult → VDGv4 변환
│   └── analyzer.py           # GeminiPipeline 클래스 (main entry)
│
└── services/vdg_2pass/
    ├── unified_pass.py       # Pass 1: Pro LLM (433 lines)
    ├── cv_measurement_pass.py # Pass 2: CV (510 lines)
    ├── vdg_unified_pipeline.py # 오케스트레이터 (380 lines)
    ├── director_compiler.py  # Pack 컴파일러 (810 lines)
    ├── quality_gate.py       # Proof Grade validation
    ├── frame_extractor.py    # Plan-based frames
    └── prompts/
        ├── unified_prompt.py # Pro 1-Pass 프롬프트
        └── semantic_prompt.py # pattern/delivery/hook_summary 지시
```

---

## 6) Data Flywheel (A→B Migration)

**핵심**: 코드 변경 없이 데이터만 쌓이면 자동 승격되는 메커니즘

### 6.1 Signal → Invariant 승격 임계값 (Configurable)

| 승격 단계 | 조건 | 설명 |
|-----------|------|------|
| **Slot → Candidate** | 10 sessions + 70% success | 초기 신호 포착. `InvariantCandidate` 생성 |
| **Candidate → DNA** | 50 sessions + 80% success | 강력한 패턴 증명. `DNAInvariant` 승격 (Distill 검증 필수) |

**용어 정의**
- **Sessions**: 해당 Slot/Signal이 제안된 코칭 세션 수
- **Success**: 사용자가 가이드를 따랐고(Outcome.compliance=True), 메트릭이 개선됨

### 6.2 Cluster SoR & Distill

**ContentCluster (Parent-Kids)**
- **Parent**: 원본 영상 (VDG Source)
- **Kids**: 해당 Parent를 보고 만든 변주들 (VDG Variants)
- **Cluster Signature**: 훅/오디오/인텐트 유사도로 묶임

**Distill Pipeline**
1. Cluster 내 Parent + Kids의 VDG 모음
2. NotebookLM에 투입
3. **공통 성공 요인** 추출 → `DistillRun` 결과로 저장
4. Candidate의 `distill_validated=True` 마킹 → DNA 승격

---

## 7) Evidence 계산

### 7.1 R_ES Score (Rule Execution Score)
```python
R_ES = (checked_rules / total_rules) × 100
```

### 7.2 Pattern Lift
```python
Lift = (Variant_metric - Parent_metric) / Parent_metric
```

---

## 8) Integration Points

### 8.1 Frontend Flow
```
[Card Detail] → [촬영 시작] → [Mode Select] → [CoachingSession]
```

### 8.2 API Endpoints
- `POST /api/v1/coaching/sessions` - 세션 생성
- `GET /api/v1/coaching/sessions` - 세션 목록 (Admin)
- `GET /api/v1/coaching/sessions/{session_id}` - 상태 조회
- `POST /api/v1/coaching/sessions/{session_id}/feedback` - 피드백 제출
- `POST /api/v1/coaching/sessions/{session_id}/events/rule-evaluated` - 규칙 평가 로깅
- `POST /api/v1/coaching/sessions/{session_id}/events/intervention` - 개입 로깅
- `POST /api/v1/coaching/sessions/{session_id}/events/outcome` - 결과 로깅
- `GET /api/v1/coaching/sessions/{session_id}/events` - 이벤트 조회
- `GET /api/v1/coaching/sessions/{session_id}/summary` - 세션 요약
- `POST /api/v1/coaching/sessions/{session_id}/end` - 세션 종료 (JSON body 지원)
- `DELETE /api/v1/coaching/sessions/{session_id}` - 세션 종료

> Legacy alias: `/coaching/*` (non-versioned)도 노출되어 있으나, 문서/연동은 `/api/v1/coaching/*` 사용을 권장합니다.

---

## 9) 다음 단계

| Priority | Item | Status |
|----------|------|--------|
| 🟡 | Cluster 10개 생성 (Parent-Kids) | Pending |
| 🟡 | DistillRun 주간 실행 | Pending |
| 🟡 | google.genai migration | Deferred |
| 🟢 | Real coaching API integration | Ready |

---

## 10) Reference

- [vdg_v4_2pass_protocol.md](vdg_v4_2pass_protocol.md) - 상세 프로토콜
- [ARCHITECTURE_FINAL.md](ARCHITECTURE_FINAL.md) - 최종 아키텍처
- [CHANGELOG.md](CHANGELOG.md) - 개발 이력
