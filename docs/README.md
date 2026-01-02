# Komission Docs (최신 정리본)

**최종 업데이트**: 2026-01-02 (모바일 앱 하드닝 완료)

이 폴더가 **유일한 최신 문서**입니다. 루트/기타 폴더에는 포인터만 유지합니다.

## 핵심 원칙
핵심 원칙은 `docs/00_SINGLE_SOURCE_OF_TRUTH.md`, `docs/00_DOCS_INDEX.md`, `docs/ARCHITECTURE_FINAL.md`를 단일 기준으로 따른다.

## 현재 상태 (2026-01-02) ⭐ NEW

| 트랙 | 상태 | 담당 |
|------|------|------|
| **모바일 앱** | ✅ Week 1 완료 | Claude |
| **웹앱 고도화** | 🟡 대기 | 새 개발자 |
| **백엔드** | ✅ 안정 | 공유 |

## 핵심 플로우

```
[모바일 앱]                         [웹앱]
    │                                 │
    │  ┌─ 4K/H.265 촬영              │  ┌─ 아웃라이어 분석
    │  ├─ 음성/텍스트 코칭           │  ├─ 체험단 캠페인
    │  └─ 세션 DB 저장               │  └─ 캔버스 스튜디오
    │                                 │
    └────────────┬────────────────────┘
                 ▼
         [VDG 2-Pass Pipeline]
         ├─ Semantic Pass (Gemini)
         └─ Visual Pass (CV)
                 ↓
         [Director Pack 컴파일]
                 ↓
         [Audio Coach 실시간]
                 ↓
         [Evidence Loop + RL]
```

## 문서 목록

### 전략/비전
- `docs/00_SINGLE_SOURCE_OF_TRUTH.md` — SoR/계약/라인리지 단일 기준 문서
- `docs/00_EXECUTIVE_SUMMARY.md` — CEO용 1장 요약 (**2026-01-02 업데이트**)
- `docs/00_DOCS_INDEX.md` — 문서 구조/의존관계/SoR 규칙 인덱스
- `docs/ARCHITECTURE_FINAL.md` — 최종 아키텍처 (**2026-01-02 업데이트**)

### 병렬 개발 (⭐ NEW)
- `docs/21_PARALLEL_DEVELOPMENT_STRATEGY.md` — 모바일+웹 병렬 개발 (**최신**)
- `docs/22_DEVELOPER_ONBOARDING.md` — 새 개발자 온보딩 (**최신**)

### VDG/코칭
- `docs/01_VDG_SYSTEM.md` — Viral Depth Genealogy 데이터 모델
- `docs/PROOF_PLAYBOOK.md` — 코칭 효과 증명 전략 (**2026-01-02 업데이트**)
- `docs/vdg_v4_2pass_protocol.md` — VDG v4.0 2-Pass Protocol

### 아키텍처/데이터
- `docs/02_EVIDENCE_LOOP_CANVAS.md` — Evidence Loop + Canvas 설계
- `docs/07_CANVAS_NODE_CONTRACTS.md` — 노드/캡슐 IO 계약
- `docs/11_KOMISSION_STUDIO_SPEC.md` — Studio/Canvas 기술 사양
- `docs/NOTEBOOKLM_SPEC.md` — NotebookLM 통합 스펙

### 운영/출시
- `docs/LAUNCH_CHECKLIST.md` — 출시 체크리스트 (**2026-01-02 업데이트**)
- `docs/CHANGELOG.md` — 개발 이력 (**2026-01-02 업데이트**)
- `docs/MCP_CLAUDE_DESKTOP_SETUP.md` — MCP Claude Desktop 연동

### 데이터 소스
- `docs/04_DATA_SOURCES_O2O.md` — Outlier 수집 + O2O 운영 구조
- `docs/12_PERIODIC_CRAWLING_SPEC.md` — 주기 크롤링 사양
- `docs/13_OUTLIER_CRAWLER_INTEGRATION_DESIGN.md` — 크롤러 통합 설계

### UI/UX
- `docs/09_UI_UX_STRATEGY.md` — UI/UX 원칙
- `docs/10_VIRLO_BENCHMARK.md` — Virlo UI 벤치마크
- `docs/17_UI_COMPONENT_SPEC.md` — UI 컴포넌트 사양

## 역할별 빠른 읽기

### 모바일 개발자
1. `docs/21_PARALLEL_DEVELOPMENT_STRATEGY.md` ← **최신 구현 상태**
2. `docs/PROOF_PLAYBOOK.md` ← WebSocket 프로토콜
3. `/mobile/README.md` ← 폴더 구조

### 웹 개발자 (새 개발자)
1. `docs/22_DEVELOPER_ONBOARDING.md` ← **온보딩 가이드**
2. `docs/ARCHITECTURE_FINAL.md` ← 전체 구조
3. `docs/PROOF_PLAYBOOK.md` ← 코칭 시스템

### CEO / PM
1. `docs/00_EXECUTIVE_SUMMARY.md` ← 1장 요약
2. `docs/21_PARALLEL_DEVELOPMENT_STRATEGY.md` ← 병렬 전략
3. `docs/LAUNCH_CHECKLIST.md` ← 출시 준비

### Tech Lead
1. `docs/ARCHITECTURE_FINAL.md` ← 최종 아키텍처
2. `docs/01_VDG_SYSTEM.md` ← VDG 시스템
3. `docs/PROOF_PLAYBOOK.md` ← RL 데이터 스키마
