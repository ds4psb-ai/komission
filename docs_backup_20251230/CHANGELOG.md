# CHANGELOG

> VDG v4.0 2-Pass Pipeline + Audio Coaching 개발 이력

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
