# VDG v4.0 Final Architecture (2024-12-30)

> **Consulting Reference Document**  
> AI가 발전해도 규칙은 명확하게 유지되는 구조

---

## Executive Summary

```
영상 + 댓글
     ↓
┌─────────────────────────────────────┐
│  VDG 2-Pass Pipeline                │
│  ├─ Semantic Pass (의미)            │
│  ├─ Analysis Planner (예산)         │
│  └─ Visual Pass (시각)              │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Director Pack Compiler             │
│  └─ Contract-First (heuristic 폴백) │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Audio Coach (Gemini 2.5 Flash)     │
│  └─ Real-time coaching              │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Evidence Loop                      │
│  └─ RL-ready intervention/outcome   │
└─────────────────────────────────────┘
```

---

## Core Philosophy

| 원칙 | 설명 |
|------|------|
| **SSoT** | VDG = 진실의 단일원천, Pack = 실행계약 |
| **Contract-First** | Heuristic은 폴백, Contract가 1순위 |
| **Metric Registry** | 메트릭 드리프트 방지 (domain.name.v1) |
| **Deterministic IDs** | RL 조인키 안정성 (ap_id, evidence_id) |
| **A→B Migration** | 데이터 축적 시 Signal → Invariant 자동 승격 |

---

## Completed Hardenings

### P0 Foundation (10/10)
1. ✅ 2-Pass 구조 (Semantic → Visual)
2. ✅ Metric Registry SSoT (`metric_registry.py`)
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
- ✅ `SignalTracker` auto-promotion

### Cluster SoR (NotebookLM Integration)
- ✅ `ContentCluster` schema (parent-kids)
- ✅ `ClusterSignature` for similarity

### RL Data Schema
- ✅ `CoachingIntervention` (rule_id, ap_id, evidence_id)
- ✅ `CoachingOutcome` (compliance, metric_before/after)
- ✅ `SessionContext` (persona, environment, device)

---

## Key Git Commits

```
24b9cd8  feat: Add CoachingSession component + Card Detail integration
b2166d0  feat: Final Comprehensive Hardening (6 Phases Complete)
3757b7b  feat: A→B Migration Architecture (Signal auto-promotion)
64dea27  feat: Flywheel Hardening (Evidence ID + Metric Validation)
1dbe068  feat: Expert Consensus Final Hardening (H5, H-1, H9)
84d25d7  feat: P0-2 Visual Pass Frame Extraction
98cb8de  feat: Expert Review Final Hardening (H1-H4)
c864ab2  feat: VDG v4.0 2-pass protocol and Director Pack v1.0
```

---

## File Structure

### Backend (`/backend/app`)

```
schemas/
├── vdg_v4.py              # VDG v4.0 schemas (881 lines)
├── director_pack.py       # Director Pack schemas (355 lines)
├── metric_registry.py     # Metric SSoT (180 lines)

services/
├── gemini_pipeline.py     # Main pipeline
├── audio_coach.py         # Gemini 2.5 Flash Live
├── evidence_updater.py    # RL weight adjustment + SignalTracker

services/vdg_2pass/
├── semantic_pass.py       # 1차: 의미 해석
├── analysis_planner.py    # Plan 생성 (예산/병합)
├── visual_pass.py         # 2차: 시각 측정
├── vdg_merger.py          # Semantic-Visual 병합
├── director_compiler.py   # VDG → Pack 변환
├── frame_extractor.py     # Plan-based frame extraction
```

### Frontend (`/frontend/src`)

```
components/
├── CoachingSession.tsx    # Real-time AI coaching (350 lines)
├── FilmingGuide.tsx       # Ghost overlay filming
├── ViralGuideCard.tsx     # Guide display

app/video/[id]/
└── page.tsx               # Card detail + coaching integration
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/outliers/items/{id}` | GET | Card detail with VDG |
| `/outliers/items/{id}/guide` | GET | Director Pack guide |
| `/coaching/sessions` | POST | Create coaching session |
| `/coaching/sessions/{id}` | GET | Session status |
| `/coaching/sessions/{id}/feedback` | POST | Submit feedback |

---

## UX Flow

```
[Card List] → [Card Detail] → [🎬 촬영 시작] → [Mode Select]
                                                    ↓
                                        ├─ 오마쥬 (DNA Lock)
                                        ├─ 변주 (Mutation Slot)
                                        └─ 체험단 (Campaign)
                                                    ↓
                                        [CoachingSession]
                                        ├─ Camera preview
                                        ├─ 🎙️ Audio feedback
                                        └─ Rule checklist
```

---

## Data Flywheel

```
Phase A: Signal → MutationSlot (즉시 코칭)
    ↓ 10 sessions + 70% 성공률 (Candidate 승격)
Phase B: InvariantCandidate (Distill 검증 대기)
    ↓ 50 sessions + 80% 성공률 + DistillRun 완료
Phase C: DNA Invariant (Pack 불변 규칙)
```

**Auto-promotion**: 코드 변경 없이 데이터(Intervention Outcome)만 쌓이면 자동 승격

### Promotion Criteria (Snapshot)
- **Slot → Candidate**: 신호 포착 (최소 10회, 7할 승률)
- **Candidate → DNA**: 법칙 확정 (최소 50회, 8할 승률, 교차증명)

---

## Remaining Work

| Priority | Item | Status |
|----------|------|--------|
| 🟡 | Cluster 10개 생성 (Parent-Kids) | Pending |
| 🟡 | DistillRun 주간 실행 | Pending |
| 🟡 | google.genai migration | Deferred |
| 🟢 | Real coaching API integration | Ready |
| 🟢 | WebSocket live feedback | Ready |

---

## Conclusion

> **현재 상태: NotebookLM-ready + MVP 실행 가능**
>
> 다음 단계: Cluster 적재 → Distill 실행 → NotebookLM-integrated

**→ "모델이 발전해도 Pack의 가치가 더 비싸지는" 구조 완성 ✅**
