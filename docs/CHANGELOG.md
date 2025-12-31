# CHANGELOG

> VDG v4.0 Unified Pipeline + Audio Coaching 개발 이력

---

## 2025-12-31 (Documentation & Page Cleanup)

### 📝 문서 최신화
- **10개 문서 업데이트**: VDG Unified Pipeline 반영
- `ARCHITECTURE_FINAL.md`: File Structure + Pipeline 다이어그램
- `01_VDG_SYSTEM.md`: Overview 다이어그램 + File Structure
- `00_DOCS_INDEX.md`: 날짜 + 신규 문서 반영
- `18_PAGE_IA_REDESIGN.md`: /trending 삭제 반영

### 🔧 Virlo → Ops 파이프라인 브릿지 (하드닝)
- `virlo_scraper.py`: Supabase RPC 엔드포인트 수정
  - `get_viral_outliers_fresh_v2` 엔드포인트 사용
  - `sort_by_param=fresh_content` (타임아웃 방지)
  - Supabase anon key 하드코딩
- **`discover_and_enrich_urls()` 신규 함수**:
  - Virlo 발견 → `OutlierCrawlItem` 변환 → Ops 파이프라인 저장
  - `OutlierItemStatus.PENDING` enum 사용 (하드닝)
  - `outlier_tier` 자동 계산 (S/A/B/C)
- `scripts/run_virlo_bridge.sh`: 실행 스크립트 추가

### 🔌 MCP 문서 보강 (2025 리서치)
- `MCP_CLAUDE_DESKTOP_SETUP.md`: FastMCP 2.0 섹션 추가
  - Background Tasks, Context Object, Transport Layer
  - 2025 Best Practices (OAuth 2.1, RBAC, async)
- `16_NEXT_STEP_ROADMAP.md`: MCP 통합 전략 업데이트
  - FastMCP 2.0 신기능 활용 계획
  - 보안 강화 로드맵 (2025)

### 🧹 Page Structure Cleanup
- **`/trending` 페이지 삭제**: `/` (홈)으로 통합
- **Navigation 업데이트**:
  - `AppHeader.tsx`: "트렌딩" → "홈"
  - `CollapsibleSidebar.tsx`: "트렌딩" → "홈"
  - `BottomNav.tsx`: "Trending" → "Home"
  - `discover/page.tsx`: `/trending` → `/` 리다이렉트

### 🔐 Ops 권한 가드 추가
- `/ops/outliers` 페이지에 curator/admin 권한 가드
- 비로그인: `/login` 리다이렉트
- 일반 유저: "접근 권한 없음" UI 표시

### 🛡️ 기타 수정
- `useRealTimeMetrics.ts`: WebSocket 에러 graceful 처리
- `ted.taeeun.kim@gmail.com`: admin 권한 영구 부여

---

## 2025-12-31 (VDG Pro 1-Pass + CV Architecture)

### 🎯 VDG Unified Pipeline 구현

**아키텍처 변경**: LLM 2-Pass → Pro 1-Pass + CV 결정론적 측정

```
Pass 1: Gemini 3.0 Pro (1회)
├── 10fps hook + 1fps full (VideoMetadata)
├── Structured output (response_schema)
└── 출력: 의미/인과/Plan Seed

Pass 2: ffmpeg + OpenCV (결정론적)
├── 3개 MVP 메트릭
├── 100% 재현 가능
└── 출력: 수치/좌표
```

### 신규 파일 (5개, +2,058 lines)

| 파일 | 역할 | 라인 |
|------|------|------|
| `vdg_unified_pass.py` | 스키마 (15 types) | ~180 |
| `unified_prompt.py` | 프롬프트 | ~100 |
| `unified_pass.py` | Pass 1 (LLM) | ~270 |
| `cv_measurement_pass.py` | Pass 2 (CV) | ~510 |
| `vdg_unified_pipeline.py` | 오케스트레이터 | ~380 |

### 3개 MVP 메트릭 (결정론적)

| metric_id | 출력 | 범위 |
|-----------|------|------|
| `cmp.center_offset_xy.v1` | `[offset_x, offset_y]` | -1 ~ 1 |
| `lit.brightness_ratio.v1` | `float` | 0 ~ 1 |
| `cmp.blur_score.v1` | `float` | 0 ~ 1 |

### Git Commits

- `bdcec4f` feat: Implement VDG Unified Pass (Pro 1-Pass)
- `26d68ae` feat: Implement CV Measurement Pass MVP
- `9bec673` feat: Add VDG Unified Pipeline orchestrator

---

## 2025-12-31 (Late Night Session)

### 🚀 google-genai SDK 마이그레이션
- **deprecated `google-generativeai` → 신규 `google-genai` v1.56.0**
- **genai_client.py** (130줄) 신규 모듈:
  - `get_genai_client()`: 싱글톤 클라이언트
  - `generate_content()`, `generate_content_async()` 래퍼
  - `DEFAULT_MODEL_FLASH`, `DEFAULT_MODEL_PRO` 상수
- 마이그레이션된 파일 6개:
  - `agent.py`, `template_seeds.py`
  - `analysis_pipeline.py`
  - `semantic_pass.py`, `visual_pass.py`

### 🛡️ Sentry 에러 모니터링
- **Frontend Sentry 설정** (Next.js):
  - `sentry.client.config.ts` (클라이언트)
  - `sentry.server.config.ts` (서버 SSR)
  - `sentry.edge.config.ts` (Edge 런타임)
  - `next.config.ts` Sentry wrapper 적용
- 설정: Production 전용, 10% 샘플링, 일반 오류 필터링

### 🔧 Turbopack 호환성 수정
- **styled-jsx 제거** (Turbopack 빌드 오류 해결):
  - `agent/page.tsx` (-11줄)
  - `Toast.tsx` (-16줄)
  - `CelebrationModal.tsx` (-24줄)
- **globals.css 애니메이션 추가**:
  - `slide-in` (Toast)
  - `confetti` (CelebrationModal)
- Root Cause: styled-jsx가 Next.js 16 Turbopack과 호환되지 않음

### 📂 Ops 격리 리팩토링
- `/pipelines` → `/ops/pipelines` 이동
- 리다이렉트 페이지 추가: `/canvas`, `/outliers`, `/pipelines`

### ⚡ API 응답시간 측정
- `/health`: 8ms ✅
- `/suggestions`: 2.7ms (401)
- `/chat`: 2ms (401)
- 목표 3초 대비 300배 이상 빠름

### 🛡️ P0 Hardening (H1-H6)
- **H1: GenAI Response Envelope**
  - `GenAIResponse` dataclass: success/error/latency_ms/usage
  - `GenAIErrorCode` enum: rate_limit, timeout, server_error 등 8종
- **H2: Timeout + Retry + Backoff**
  - 60s timeout, 3x retry, exponential backoff with jitter
- **H3: Provenance Tracking**
  - `PROMPT_VERSION` 상수 추가 (semantic_v4.1, visual_v4.1)
  - `provenance.prompt_version`, `model_id`, `run_at` 설정
- **H4: Session Log Idempotency**
  - `add_intervention_idempotent()`: t_sec 버킷 중복 방지
- **H5: Upload Outcome Two-Stage**
  - `PromotionSafetyError` 예외
  - `get_session_for_promotion()`: outcome 필수 검증
- **H6: Agent Abuse Hardening**
  - `INTENT_TOKEN_BUDGET`: 인텐트별 토큰 예산
  - `INTENT_ALLOWED_ACTIONS`: 인텐트별 액션 화이트리스트

### Git Commits (8개)
- `883e782` fix: Remove all styled-jsx for Turbopack compatibility
- `0aecb34` fix: Remove styled-jsx for Turbopack compatibility
- `72372d6` feat: Add Sentry error monitoring to frontend
- `dd18e1e` feat: Migrate from google-generativeai to google-genai SDK
- `49d83b6` refactor: Ops isolation - pipelines to /ops
- `7d32ab9` feat: Chat Agent UI Premium Upgrade

---

## 2024-12-31 (Major Release)

### 🤖 Chat Agent UI MVP + Hardening
- **agent.py** (470줄): 자연어 인터페이스 백엔드
  - 7가지 IntentClassifier (`ANALYZE_TREND`, `CREATE_HOOK`, `GET_COACHING` 등)
  - ChatContext: 대화 컨텍스트 관리
  - ActionExecutor: 액션 생성/실행
- **page.tsx** 하드닝: localStorage 저장, 재시도 로직, 에러 핸들링

### 🗄️ Session Log DB Schema (Coaching Proof)
- **SQLAlchemy 모델** 4개 추가:
  - `CoachingSession`: 세션 메타 + 통계
  - `CoachingIntervention`: 개입 기록
  - `CoachingOutcome`: 결과 기록
  - `CoachingUploadOutcome`: 업로드 결과
- **Alembic 마이그레이션**: `c4d78e9f1a2b_add_coaching_session_log_tables.py`

### 🛡️ CoachingRepository v2.0 Hardening  
- **Pydantic 입력 스키마** 4개: `CreateSessionInput`, `AddInterventionInput` 등
- **커스텀 예외** 4개: `SessionNotFoundError`, `SessionAlreadyExistsError` 등
- **CoachingConstants**: `MAX_INTERVENTIONS=100`, `COOLDOWN=4s`
- **신규 메서드**: `get_session_or_raise()`, `count_sessions()`, `get_aggregated_stats()`

### 🎯 Cluster Determinism (Consultant Feedback)
- **cluster_determinism.py** (220줄): 결정론 유틸리티
  - `generate_cluster_id()`: `cl.{pattern}.{niche}.{week}.{hash8}`
  - `compute_signature_hash()`: `sig.{hash12}` 정규화
  - `dedupe_sort_kids()`: 중복 제거 + 정렬
- **ContentCluster 하드닝**: 
  - `signature_hash` 필드 추가
  - `@field_validator`: kid_vdg_ids 자동 dedup
  - `min_kids_required`: 3 → 6

### 📋 Launch Infrastructure
- **LAUNCH_CHECKLIST.md** (179줄): Phase 0-5 체크리스트
- **Alembic Heads Merge**: `0ed31a82d1aa_merge_heads.py`
- **Coaching Router 등록**: main.py 404 해결

### Git Commits (8개)
- `a16012f` Chat Agent UI Hardening
- `8109834` Session Log DB Schema
- `2208719` CoachingRepository v1.0
- `ef35123` CoachingRepository v2.0 Hardening
- `0a7be4b` Cluster Determinism Hardening
- `9539787` Launch Checklist
- `d162952` Alembic Heads Merge
- `5bdfe85` Coaching Router Fix

---

## 2024-12-30 (Evening Session)

### 🎯 Campaign Eligible Feature (O2O Integration)
- **DB**: `outlier_items.campaign_eligible` 필드 추가 (boolean, default=False)
- **API**: `POST /outliers/items/{id}/promote` 엔드포인트에 `campaign_eligible` 파라미터 지원
- **UI**: `OutlierDetailModal` 승격 버튼 분리
  - `[승격]`: 일반 RemixNode 생성
  - `[체험단 선정]`: RemixNode 생성 + campaign_eligible=True 마킹 (O2O 후보군 등록)

### 🛡️ Duplicate Crawling Prevention Hardening
- **취약점 발견**: `video_url` 중복 체크 없음 → 동일 영상 중복 등록 가능
- **Application Layer**: `create_item`, `bulk_import` 엔드포인트에 `video_url` 기준 중복 체크 추가
- **Database Layer**: `outlier_items.video_url`에 UNIQUE 제약조건 + INDEX 추가
- **결과**: 이중 방어 (API + DB)로 중복 크롤링 완전 차단

### 🎨 UI Fine-tuning
- **버튼 텍스트 개선**: "체험단" → "체험단 선정" (명확성 향상)
- **Unified Components**: `OutlierDetailModal`, `UnifiedOutlierCard` 일관성 유지

### 🧹 Data Cleanup
- **Mock 데이터 정리**: 중복된 5개 가짜 아이템 삭제 (source: `virlo_crawl`)
- **원인 분석**: 서로 다른 `external_id` 생성 규칙으로 UNIQUE 제약 우회됨

---

## 2024-12-30

### 🎯 Expert Feedback Hardenings (Senior Dev Review)
- **ddbee21** `fix: Add compliance_unknown_reason to CoachingOutcome`
  - `compliance_unknown_reason`: occluded/out_of_frame/no_audio/ambiguous

- **f648f0b** `feat: Causal Outcome + Promotion Safety Hardenings`
  - Two-stage Outcome: `upload_outcome_proxy`, `reported_views/likes/saves`
  - Canary mode: `canary_enabled`, `canary_session_ratio` (10%)
  - Cluster diversity: `cluster_ids_verified`, `min_clusters_required` (2)
  - Rollback: `rollback_eligible`, `rollback_reason`

- **d0aa83b** `feat: Final Hardenings (H-Final-1, H-Final-2)`
  - PackMeta: `prompt_version`, `model_version`, `parent_pack_id`, `experiment_id`
  - Evidence ID: comment/asr/ocr/metric generators (`evidence_id_utils.py`)

### 🎨 Frontend UX Integration
- **24b9cd8** `feat: Add CoachingSession component + Card Detail integration`
  - `CoachingSession.tsx` (350줄): 실시간 AI 코칭 오버레이
  - `/video/[id]` 페이지에 촬영 시작 CTA + 모드 선택 추가
  - 오마쥬/변주/체험단 3가지 모드 지원

### 🔧 Final Comprehensive Hardening (6 Phases)
- **b2166d0** `feat: Final Comprehensive Hardening (6 Phases Complete)`
  - Phase 1: Evidence ID structural only (sha 분리)
  - Phase 2: Compiler fallback warnings (`pack_meta.compiler_warnings`)
  - Phase 3: Cluster SoR (`ContentCluster`, `ClusterSignature`)
  - Phase 4: Compiler metric validation
  - Phase 5: RL Log Schema (`CoachingIntervention`, `CoachingOutcome`, `SessionContext`)

### 🔄 A→B Migration Architecture
- **3757b7b** `feat: A→B Migration Architecture (Signal auto-promotion)`
  - `SignalPerformance`: 신호 성공률 추적
  - `InvariantCandidate`: 중간 승격 상태
  - `SignalTracker`: 자동 승격 로직
  - 마이그레이션 코드 없이 데이터만 쌓이면 Slot→Candidate→DNA 승격

### 🧹 Code Consolidation
- **0dbb7b0** `refactor: Remove duplicate METRIC_REGISTRY from visual_prompt.py`
  - SSoT 기반 통합 (127줄 → 75줄)

### ⚙️ Flywheel Hardening
- **64dea27** `feat: Flywheel Hardening (Evidence ID + Metric Validation + Distill Schema)`
  - Deterministic evidence_id 생성
  - VisualPass metric validation
  - `DistillRun` schema 추가

### 🛡️ Expert Consensus Hardening
- **1dbe068** `feat: Expert Consensus Final Hardening (H5, H-1, H9)`
  - H5: Mise-en-scène canonicalization
  - H-1: Deterministic AP ID generation
  - H9: Fallback invariants (silent director 방지)

---

## 2024-12-29

### 📊 P0 Hardenings
- **84d25d7** `feat: P0-2 Visual Pass Frame Extraction`
- **6a044b6** `feat: P0-3 Metric Registry Validation`
- **98cb8de** `feat: Expert Review Final Hardening (H1-H4)`
  - H1: Deterministic analysis_point_id
  - H2: Remove root_duplicates from Merger
  - H3: Director Compiler contract-only
  - H4: Overlap merge in Analysis Planner

### 🏗️ Phase 2 Blueprint
- **2b98ffb** `feat: Phase 2 Blueprint 미비점 구현`
- **7695f69** `chore: sync latest local changes`

---

## 2024-12-28

### 🎬 VDG v4.0 Core
- **c864ab2** `feat: add VDG v4.0 2-pass protocol and Director Pack v1.0 schemas`
- **3a2e242** `fix: apply protocol freeze patches to VDG v4.0.2 and Director Pack v1.0.2`
- **26c8eb8** `fix: apply 8 essential patches to VDG v4.0.1 and Director Pack v1.0.1`

---

## Summary

| Category | Count |
|----------|-------|
| Total Commits | 20+ |
| New Components | 15+ |
| Lines Changed | 3000+ |
| Hardening Items | 16 |

**Current Status**: NotebookLM-ready + MVP 실행 가능
