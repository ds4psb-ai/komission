# Implementation Roadmap (Phases + Micro Steps)

**작성**: 2026-01-07
**목표**: Evidence Loop MVP → 2개 Parent 파일럿

---

## Phase 0: Alignment & Setup (Day 0-2)
**목표**: 운영/데이터 기준 고정

- 소스 확정: 외부 구독 사이트 목록 + 크롤링 정책
- Drive 폴더 구조 확정: Evidence/Decision/Experiment/O2O
- 카테고리/패턴 택소노미 고정 (beauty/meme/etc + hook/scene/audio/subtitle/pacing)
- 영상 해석 파이프라인 범위 확정 (코드 기반 스키마 추출)
- NotebookLM/Opal 사용 범위 확정 (Pattern Engine, DB 래핑)
- Capsule IO 계약 정의 (입력/출력/로그)
 - Notebook Library 테이블 설계 확정 (분석 스키마/클러스터/요약)

**완료 기준**
- `.env`에 Drive/Sheet 설정 완료
- 템플릿 IO 계약 문서화

---

## Phase 1: Ingestion + SoR (Week 1)
**목표**: Outlier → Parent 승격까지 안정화

**마이크로 단계**
1. ✅ Outlier 수동 입력 API 정리 (링크 기반) - `/api/v1/outliers/items`
2. ✅ 중복 제거 규칙 확정 (URL hash) - `external_id` 기준
3. [ ] DB → Sheet 동기화 스크립트 연결 (선택)
4. ✅ 영상 해석(코드) + 클러스터링 → **NotebookLM(Pattern Engine)** 적재 (2025-12-25)
   - VDG 스키마 + Gemini Pipeline
   - microbeat sequence 유사도 점수 계산
4.1 ✅ JSON Schema 출력 강제 (Structured Output)
4.2 ✅ microbeat sequence 유사도 점수 계산 (DTW/sequence similarity)
5. ✅ 후보 리스트(Parent Candidates) 자동 생성 로직 - `/outliers` 페이지
6. ✅ Parent 승격 → RemixNode 생성 - `POST /outliers/items/{id}/promote`
7. ✅ 분석 호출(`/remix/{node_id}/analyze`) 경로 확정

**완료 기준**
- ✅ Outlier API 구현 완료
- ✅ Parent 승격 + 분석 결과 확보 (VDG pieline)
- [ ] `VDG_Outlier_Raw`와 `VDG_Parent_Candidates` Sheet 생성 (선택)

---

## Phase 2: Evidence Loop MVP (Week 2)
**목표**: Evidence → Decision 생성 자동화

**마이크로 단계**
1. [ ] Progress CSV 입력 연결(선택) - Sheet 기반 운영
2. ✅ Evidence 스냅샷 생성 로직 정리 - `EvidenceService.create_evidence_snapshot`
3. ✅ Evidence Sheet 업로드 확인 - `RealDataPipeline._generate_evidence_from_progress`
4. ✅ Opal Decision 생성 (또는 규칙 기반 대체) - `OpalEngine`
5. ✅ Notebook Library Insights → DB 래핑 - `NotebookLibraryEntry` 모델
6. ✅ Opal 템플릿 시드 생성 - `template_seeds.py` 라우터
7. ✅ NotebookLM Source Pack 생성 - `build_notebook_source_pack.py`

**완료 기준**
- ✅ Evidence/Decision Sheet 생성 로직 구현
- ✅ Evidence → Decision 데이터 흐름 검증 (`run_real_evidence_loop.py`)

---

## Phase 3: Capsule + Canvas (Week 3)
**목표**: Canvas 템플릿에 Evidence/Decision 연결

**마이크로 단계**
1. ✅ Capsule Node 계약 적용 (입력/출력/로그) - RemixNode 모델
2. ✅ Canvas 템플릿 A/B 연결 - `/canvas` 페이지
3. ✅ 핵심 CTA(촬영/신청) 위치 고정 - `CampaignPanel` 컴포넌트
4. ✅ O2O 타입 게이팅(즉시/방문/배송) UI - `O2OCampaign.campaign_type`
5. ✅ 템플릿 커스터마이징 로그 수집 시작 (2025-12-26)
   - `template_customization.py` 라우터: `/customize`, `/customizations/{id}`, `/summary/all`
   - RL-lite 학습용 패턴 수집
6. ✅ Opal 템플릿 시드 → Template Node 기본값 연결
7. ✅ **CrawlerOutlier Node** 구현 (2025-12-25)
   - `CrawlerOutlierNode` 컴포넌트 + `CrawlerOutlierSelector` 모달
   - 3-플랫폼 크롤러 아웃라이어 Canvas 통합
8. ✅ Creator 행동 이벤트 로깅 (2025-12-26)
   - `events.py` 라우터: `/track`, `/recent`, `/summary`
   - `tracker.ts` 프론트엔드 유틸리티
9. ✅ Taste Calibration (pairwise 5~8 선택) (2025-12-26)
   - `/calibration` 페이지 구현
   - `CalibrationPair` API 연동
10. ✅ `creator_style_fingerprint` 산출 (2025-12-26)
    - `CreatorFingerprintService` 구현
    - `/events/fingerprint/{user_id}` API 추가

**완료 기준**
- ✅ Canvas에서 Evidence/Decision 표시
- ✅ O2O 타입에 따라 UI가 분기

---

## Phase 4: Pilot + O2O (Week 4)
**목표**: 2개 Parent 파일럿 + 체험단 운영 베타

**마이크로 단계**
1. ✅ Parent 선정 UI - `/outliers` 페이지 + Promote API
2. ✅ Depth1 실험 실행 + 14일 추적 (2025-12-26)
   - `track_depth_experiment.py` 스크립트 구현
3. ✅ Decision 반영 후 Depth2 시작 (2025-12-26)
   - `depth_experiments.py` 서비스 구현
   - `/analytics/depth-experiments/{parent_id}`, `/depth2` API 추가
4. ✅ 체험단 캠페인 API - 등록/모집/선정/상태변경
   - `POST /o2o/admin/campaigns`, `/applications`
5. ✅ 배송/방문/촬영/제출 단계 - `O2OApplicationStatus` enum
6. ✅ Bandit/탐색 정책 적용 (2025-12-26)
   - `bandit_policy.py` Thompson Sampling 구현
   - exploration_rate 15% 적용
7. ✅ RL-lite 정책 업데이트 (2025-12-26)
   - `POST /analytics/rl-update` 배치 업데이트 API
   - 템플릿 커스터마이징 패턴 연동
8. ✅ KPI 리포트 생성 (2025-12-26)
   - `analytics.py` 대시보드 API
   - `/dashboard`, `/weekly-kpi`, `/pattern-lifts`, `/experiments`

**완료 기준**
- ✅ 주간 리포트 자동 생성 API
- [ ] 성공 구조 1개 이상 도출 (데이터 필요)

---

## 정의된 산출물 (요약)
- Evidence Sheet / Decision Sheet / Progress Sheet
- Capsule 실행 로그
- 2개 Parent 파일럿 결과
