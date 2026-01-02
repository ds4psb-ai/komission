# VDG v4.0 Final Architecture (Updated 2026-01-02)

> **Consulting Reference Document**  
> AI가 발전해도 규칙은 명확하게 유지되는 구조

---

## Executive Summary

```
                        ┌─────────────────────────────┐
                        │        SHARED BACKEND        │
                        │     FastAPI + PostgreSQL     │
                        └──────────────┬───────────────┘
                                       │
         ┌─────────────────────────────┴─────────────────────────────┐
         ▼                                                           ▼
┌─────────────────────┐                                 ┌─────────────────────┐
│   MOBILE APP (NEW)  │                                 │      WEB APP        │
│   /mobile           │                                 │    /frontend        │
├─────────────────────┤                                 ├─────────────────────┤
│ ✅ 4K + H.265/H.264 │                                 │ • 아웃라이어 분석   │
│ ✅ 실시간 코칭      │                                 │ • 체험단 캠페인     │
│ ✅ 음성/텍스트 토글 │                                 │ • 캔버스 스튜디오   │
│ ✅ 적응형 스트리밍  │                                 │ • 대시보드          │
└─────────────────────┘                                 └─────────────────────┘

영상 + 댓글
     ↓
┌─────────────────────────────────────┐
│  VDG Unified Pipeline               │
│  ├─ Pass 1: Pro LLM (의미/인과/Plan)│  ← Gemini 3.0 Pro 1회
│  │   - 10fps hook + 1fps full       │
│  │   - JSON output (manual validation)│
│  └─ Pass 2: CV (결정론적 측정)       │  ← ffmpeg + OpenCV
│       - 3 MVP metrics               │
│       - 100% 재현 가능              │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Director Pack Compiler             │
│  └─ Contract-First (heuristic 폴백) │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Audio Coach (Gemini 2.5 Flash)     │
│  ├─ WebSocket: /coaching/live       │
│  ├─ frame_ack RTT 측정 (Phase 2)    │
│  └─ H.264 스트리밍 지원             │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  Evidence Loop + RL                 │
│  ├─ CoachingSession → Intervention  │
│  ├─ → Outcome → Upload 성과 연결    │
│  └─ 재귀개선 + 강화학습 준비        │
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
| **Platform Parity** | 모바일 + 웹 동일 백엔드 API 사용 |

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

### Mobile App Hardening (2026-01-02) ⭐ NEW
- ✅ H.265 (HEVC) 코덱 지원 + H.264 자동 폴백
- ✅ 프레임 레이트 안정화 (`useCameraFormat.ts`)
- ✅ 배터리/네트워크/저장공간 적응형 화질
- ✅ Phase 2: H.264 스트리밍 최적화 (50% 지연시간 감소)
- ✅ FrameThrottler + AdaptiveBitrateController
- ✅ frame_ack RTT 측정 (`coaching_ws.py`)
- ✅ 음성/텍스트 코칭 토글 UI
- ✅ 구도/빛/미장센 확장 슬롯 준비
- ✅ `useSessionPersistence.ts` DB 연동

### Flywheel Hardenings
- ✅ `DistillRun` schema (NotebookLM-ready)
- ✅ `SignalPerformance` tracking
- ✅ `InvariantCandidate` intermediate state
- ✅ `SignalTracker` auto-promotion

### Cluster SoR (NotebookLM Integration)
- ✅ `ContentCluster` schema (parent-kids)
- ✅ `ClusterSignature` for similarity

### RL Data Schema
- ✅ `CoachingSession` (session_id, pattern_id, pack_id)
- ✅ `CoachingIntervention` (rule_id, ap_id, evidence_id)
- ✅ `CoachingOutcome` (compliance, metric_before/after, upload_outcome)
- ✅ `SessionContext` (persona, environment, device)
- ✅ `compliance_unknown_reason` for RL data quality

### MCP Integration (2025-12-31)
- ✅ `/backend/app/mcp/` 디렉토리 구조
- ✅ `tools/`: smart_pattern_analysis, ai_batch_analysis 등
- ✅ `resources/`: 데이터 리소스
- ✅ Claude Desktop 연동 지원

---

## File Structure

### Backend (`/backend/app`)

```
routers/                           # 33 files
├── coaching_ws.py                 # ⭐ 실시간 코칭 WebSocket (1124 lines)
│   ├─ coaching_websocket()        # 메인 WS 엔드포인트
│   ├─ load_director_pack_from_video()
│   ├─ try_reconnect_gemini()      # H4: Gemini 재연결
│   ├─ run_checkpoint_evaluation_loop()
│   └─ generate_tts_fallback()     # H2: TTS 폴백
├── coaching.py                    # REST API (586 lines)
│   ├─ POST /coaching/sessions
│   ├─ GET /coaching/sessions/{id}
│   ├─ POST /coaching/sessions/{id}/events/intervention
│   ├─ POST /coaching/sessions/{id}/events/outcome
│   └─ GET /coaching/sessions/{id}/summary
├── outliers.py                    # 아웃라이어 CRUD (106KB)
├── agent.py                       # Chat Agent
├── auth.py                        # Firebase Auth
├── for_you.py                     # For You 페이지
├── o2o.py                         # O2O 체험단
├── remix.py                       # Remix 노드
└── stpf.py                        # STPF 스코어링

schemas/                           # 17 files
├── vdg_v4.py                      # VDG v4.0 (38KB)
├── vdg_unified_pass.py            # Unified Pass (15KB)
├── director_pack.py               # Director Pack (11KB)
├── metric_registry.py             # Metric SSoT (8KB)
├── session_log.py                 # 세션 로깅 (10KB)
└── session_events.py              # 이벤트 스키마

services/                          # 50+ files
├── audio_coach.py                 # Gemini 2.5 Flash Live (30KB)
├── genai_client.py                # google-genai SDK (15KB)
├── coaching_repository.py         # 코칭 DB 레포지토리 (33KB)
├── coaching_session.py            # 세션 관리 (13KB)
├── frame_analyzer.py              # CV 프레임 분석 (10KB)
├── pattern_calibrator.py          # 베이지안 보정 (8KB)
├── comment_extractor.py           # TikTok 댓글 (43KB)
└── tiktok_extractor.py            # TikTok 메타데이터 (24KB)

services/vdg_2pass/                # 16 files
├── unified_pass.py                # Pass 1: Pro LLM
├── cv_measurement_pass.py         # Pass 2: CV 측정
├── vdg_unified_pipeline.py        # 오케스트레이터
├── director_compiler.py           # VDG → Pack 컴파일러

mcp/                               # MCP 서버
├── tools/                         # 6 analysis tools
├── resources/                     # 5 data resources
├── prompts/                       # 4 prompt templates
└── server.py
```

### Mobile (`/mobile`) ⭐ NEW

```
mobile/
├── app.json                       # Expo 설정
├── package.json
├── tsconfig.json
│
├── app/                           # expo-router
│   ├── _layout.tsx                # 루트 레이아웃
│   ├── index.tsx                  # 홈 화면
│   └── camera.tsx                 # ⭐ 4K 촬영 화면 (550+ lines)
│
└── src/
    ├── config/
    │   └── recordingConfig.ts     # H.265/H.264 코덱 (236 lines)
    │
    ├── hooks/                     # 4 hooks
    │   ├── useCoachingWebSocket.ts   # Phase 2 스트리밍 (13KB)
    │   ├── useCameraFormat.ts        # 프레임 레이트 안정화 (7KB)
    │   ├── useDeviceStatus.ts        # 배터리/네트워크 (8KB)
    │   └── useSessionPersistence.ts  # DB 연동 (10KB)
    │
    ├── services/
    │   └── videoStreamService.ts     # H.264 + AdaptiveBitrate
    │
    └── components/                # 4 components
        ├── CoachingOverlay.tsx       # ⭐ 음성/텍스트 토글 (14KB)
        ├── RecordButton.tsx          # 녹화 버튼 애니메이션
        ├── QualityBadge.tsx          # 4K/HEVC 배지
        └── DeviceStatusBar.tsx       # 디바이스 상태 표시
```

### Frontend (`/frontend/src`)

```
components/                        # 29 files + 7 subdirs
├── CoachingSession.tsx            # ⭐ 실시간 코칭 (45KB, 979 lines)
│   └─ voiceEnabled 토글 지원
├── FilmingGuide.tsx               # Ghost overlay (19KB)
├── ViralGuideCard.tsx             # 가이드 카드 (11KB)
├── UnifiedOutlierCard.tsx         # 통합 카드
├── PatternAnswerCard.tsx          # For You 카드
├── EvidenceBar.tsx                # 증거 바

hooks/
└── useCoachingWebSocket.ts        # 웹 버전 WS 훅

components/outlier/                # 9 files
├── TikTokPlayer.tsx
├── TierBadge.tsx
├── OutlierMetrics.tsx
└── OutlierDetailModal.tsx
```

---

## API Endpoints

### Coaching WebSocket
```
ws://localhost:8000/api/v1/coaching/live/{session_id}

Messages (Server → Client):
- feedback: { message, audio_b64, rule_id, priority }
- frame_ack: { frame_t, codec } ← Phase 2 NEW
- pong: { client_t, timestamp }

Messages (Client → Server):
- video_frame: { frame_b64, t_sec, t_ms, codec, quality_hint }
- control: { action: start|stop|pause }
- ping: { t }
```

### REST API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/coaching/sessions` | POST | Create session |
| `/coaching/sessions/{id}/events/intervention` | POST | Log intervention |
| `/coaching/sessions/{id}/events/outcome` | POST | Log outcome |
| `/coaching/sessions/{id}/end` | POST | End session |
| `/outliers/items/{id}` | GET | Card detail with VDG |
| `/outliers/items/{id}/guide` | GET | Director Pack guide |

---

## Data Flywheel

```
Phase A: Signal → MutationSlot (즉시 코칭)
    ↓ 10 sessions + 70% 성공률 (Candidate 승격)
Phase B: InvariantCandidate (Distill 검증 대기)
    ↓ 50 sessions + 80% 성공률 + DistillRun 완료
Phase C: DNA Invariant (Pack 불변 규칙)
```

---

## Current Status (2026-01-02)

| Priority | Item | Status |
|----------|------|--------|
| ✅ | Mobile 4K App (Week 1) | **Complete** |
| ✅ | H.265/H.264 Codec | **Complete** |
| ✅ | Phase 2 Streaming | **Complete** |
| ✅ | Voice/Text Toggle | **Complete** |
| ✅ | DB Session Persistence | **Complete** |
| 🟡 | Cluster 10개 생성 | Pending |
| 🟡 | DistillRun 주간 실행 | Pending |
| 🟡 | 앱스토어 등록 | Week 2 |
| 🟢 | 웹앱 고도화 | 새 개발자 담당 |

---

## Conclusion

> **현재 상태: 모바일 앱 Week 1 하드닝 완료 + NotebookLM-ready**
>
> 다음 단계: TestFlight → 앱스토어 등록 → 웹앱 고도화

**→ "모델이 발전해도 Pack의 가치가 더 비싸지는" 구조 완성 ✅**
