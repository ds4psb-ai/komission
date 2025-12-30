# Technical Overview (2025-12-30)

**Updated**: 2025-12-30  
**목표**: VDG v4.0 2-Pass + Director Pack + Audio Coaching 기술 스택 문서

---

## 1) 시스템 구성

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI + Python 3.11 |
| **DB** | PostgreSQL + Neo4j |
| **AI** | Gemini 2.5 Pro (VDG), Gemini 2.5 Flash (Coaching) |
| **Frontend** | Next.js 14 + TypeScript |
| **Infra** | Docker Compose |

### 핵심 AI 파이프라인
```
VDG 2-Pass Pipeline
├─ Semantic Pass: Gemini 2.5 Pro (Structured Output)
├─ Visual Pass: Gemini 2.5 Pro (frame extraction)
└─ Audio Coach: Gemini 2.5 Flash (native-audio-latest)
```

---

## 2) 핵심 데이터 흐름

```
영상 URL 입력
     ↓
┌─────────────────────────────────────┐
│  VDG 2-Pass Pipeline                │
│  ├─ Semantic Pass (30초)            │
│  ├─ Analysis Planner                │
│  └─ Visual Pass (2분)               │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  VDG Merger → VDGv4                 │
│  └─ contract_candidates 생성        │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Director Pack Compiler             │
│  └─ DirectorPack v1.0.2             │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Audio Coach (실시간 코칭)          │
│  └─ Pack 기반 One-Command 정책      │
└─────────────────────────────────────┘
```

---

## 3) 파일 구조

### Backend
```
backend/app/
├── schemas/
│   ├── vdg_v4.py             # VDG v4.0 (881 lines)
│   ├── director_pack.py      # Pack (355 lines)
│   └── metric_registry.py    # Metric SSoT (180 lines)
│
├── services/
│   ├── gemini_pipeline.py    # Main pipeline
│   ├── audio_coach.py        # Live coaching
│   └── evidence_updater.py   # RL weight update
│
├── services/vdg_2pass/
│   ├── semantic_pass.py      # Pass 1
│   ├── analysis_planner.py   # Plan
│   ├── visual_pass.py        # Pass 2
│   ├── vdg_merger.py         # Merge
│   ├── director_compiler.py  # Compile (810 lines)
│   └── frame_extractor.py    # Frames
│
└── routers/
    ├── outliers.py           # Outlier CRUD
    └── coaching.py           # Coaching API
```

### Frontend
```
frontend/src/
├── components/
│   ├── CoachingSession.tsx   # 실시간 코칭 (350 lines)
│   ├── FilmingGuide.tsx      # Ghost overlay
│   └── ViralGuideCard.tsx    # Guide display
│
└── app/video/[id]/
    └── page.tsx              # Card detail + coaching
```

---

## 4) API Endpoints

### Coaching API (NEW)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/coaching/sessions` | POST | 세션 생성 |
| `/coaching/sessions/{id}` | GET | 상태 조회 |
| `/coaching/sessions/{id}` | DELETE | 세션 종료 |
| `/coaching/sessions/{id}/feedback` | POST | 피드백 제출 |

### Outlier API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/outliers/items` | POST | 아웃라이어 추가 |
| `/outliers/items/{id}` | GET | 상세 조회 |
| `/outliers/items/{id}/guide` | GET | Director Pack 가이드 |

---

## 5) 환경변수

```bash
# AI
GEMINI_API_KEY=xxx
GOOGLE_AI_STUDIO_API_KEY=xxx  # for native audio

# DB
DATABASE_URL=postgresql://user:pass@localhost:5432/komission
NEO4J_URI=bolt://localhost:7687

# Auth
JWT_SECRET=xxx
```

---

## 6) 실행 (로컬)

```bash
# Infra
docker-compose up -d

# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## 7) 핵심 스키마

### VDGv4 (요약)
```python
class VDGv4(BaseModel):
    vdg_version: str = "4.0.2"
    content_id: str
    semantic: SemanticPassResult
    analysis_plan: AnalysisPlan
    visual: VisualPassResult
    contract_candidates: ContractCandidates
```

### DirectorPack (요약)
```python
class DirectorPack(BaseModel):
    pack_version: str = "1.0.2"
    dna_invariants: List[DNAInvariant]
    mutation_slots: List[MutationSlot]
    checkpoints: List[Checkpoint]
```

---

## 8) 통합 원칙

| 원칙 | 설명 |
|------|------|
| **SSoT** | DB = 진실의 단일원천 |
| **Contract-First** | Heuristic < Contract |
| **Metric Registry** | 메트릭 드리프트 방지 |
| **Deterministic ID** | RL 조인키 안정성 |

---

## 9) Reference

- [01_VDG_SYSTEM.md](01_VDG_SYSTEM.md) - VDG v4.0 상세
- [ARCHITECTURE_FINAL.md](ARCHITECTURE_FINAL.md) - 최종 아키텍처
- [vdg_v4_2pass_protocol.md](vdg_v4_2pass_protocol.md) - 프로토콜 상세
