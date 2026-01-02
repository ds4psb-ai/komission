# Docs Index: Structure + Dependencies + SoR Rules

**작성**: 2025-12-28 (Updated: 2026-01-02 전면 정리)  
**목표**: 문서 체계/범주/의존관계/SoR 규칙을 단일 인덱스로 고정

> **2026-01-02 정리 완료**: 7개 문서 아카이브, 4개 로드맵 통합, 모바일 앱 반영

---

## 1) 핵심 문서 (Always Up-to-Date)

### A. 전략/비전
| 문서 | 용도 | 최종 수정 |
|------|------|----------|
| `00_SINGLE_SOURCE_OF_TRUTH.md` | SoR 원칙 | 2026-01-07 |
| `00_EXECUTIVE_SUMMARY.md` | CEO 1장 요약 | **2026-01-02** |
| `ARCHITECTURE_FINAL.md` | 최종 아키텍처 | **2026-01-02** |
| `21_PARALLEL_DEVELOPMENT_STRATEGY.md` | 병렬 개발 현황 | **2026-01-02** |
| `22_DEVELOPER_ONBOARDING.md` | 개발자 온보딩 | **2026-01-02** |

### B. 개발 이력/로드맵
| 문서 | 용도 | 최종 수정 |
|------|------|----------|
| `CHANGELOG.md` | 개발 이력 | **2026-01-02** |
| `03_IMPLEMENTATION_ROADMAP.md` | **통합 로드맵** | **2026-01-02** |
| `LAUNCH_CHECKLIST.md` | 출시 체크리스트 | **2026-01-02** |
| `PROOF_PLAYBOOK.md` | 코칭 증명 전략 | **2026-01-02** |

### C. 기술 스펙
| 문서 | 용도 | 상태 |
|------|------|------|
| `01_VDG_SYSTEM.md` | VDG 데이터 모델 | 안정 |
| `vdg_v4_2pass_protocol.md` | VDG v4.0 프로토콜 | 안정 |
| `STPF_V3_ROADMAP.md` | Computational Truth | 참조용 |
| `MCP_CLAUDE_DESKTOP_SETUP.md` | MCP 연동 | 안정 |
| `NOTEBOOKLM_SPEC.md` | NotebookLM 통합 | 안정 |

### D. UI/운영 스펙
| 문서 | 용도 | 상태 |
|------|------|------|
| `02_EVIDENCE_LOOP_CANVAS.md` | Canvas 설계 | 안정 |
| `04_DATA_SOURCES_O2O.md` | 데이터 소스 | 안정 |
| `05_USER_FLOW.md` | 사용자 흐름 | 안정 |
| `06_PIPELINE_PLAYBOOK.md` | 파이프라인 | 안정 |
| `07_CANVAS_NODE_CONTRACTS.md` | 노드 계약 | 안정 |
| `08_OPERATIONS_RUNBOOK.md` | 운영 체크리스트 | 안정 |
| `09_UI_UX_STRATEGY.md` | UI/UX 원칙 | 안정 |

### E. 크롤링/임베드
| 문서 | 용도 | 상태 |
|------|------|------|
| `12_PERIODIC_CRAWLING_SPEC.md` | 크롤링 스펙 | 안정 |
| `13_OUTLIER_CRAWLER_INTEGRATION_DESIGN.md` | 크롤러 통합 | 안정 |
| `20_TIKTOK_EMBED_SPEC.md` | TikTok 임베드 | 안정 |
| `25_TIKTOK_COMMENT_EXTRACTION.md` | 댓글 추출 | 안정 |

---

## 2) 아카이브된 문서

`_archive_20260102/` 폴더로 이동:

| 문서 | 아카이브 이유 |
|------|--------------|
| `VDG_2PASS_CONSULTING_REQUEST.md` | 작업 완료 |
| `VDG_REFACTORING_CONSULTING_REQUEST.md` | 작업 완료 |
| `VDG_UNIFIED_PASS_IMPLEMENTATION.md` | ARCHITECTURE로 통합 |
| `VIDEO_ANALYSIS_VALIDATION_PLAN.md` | 작업 완료 |
| `STRATEGIC_PIVOT.md` | 21_PARALLEL로 대체 |
| `16_NEXT_STEP_ROADMAP.md` | 03_IMPLEMENTATION으로 통합 |
| `ROADMAP_MVP_TO_PERFECT.md` | 03_IMPLEMENTATION으로 통합 |
| `implementation_plan.md` | 임시 파일 |
| `walkthrough.md` | 임시 파일 |

---

## 3) 용어 표준 (Canonical Terms)

- **Answer-First (For You)**: 검색보다 추천을 먼저 제시하는 UX 원칙
- **PatternAnswerCard**: Answer-First의 핵심 카드 컴포넌트
- **EvidenceBar**: 베스트 댓글 + 재등장 근거를 보여주는 증거 바
- **Temporal Recurrence / Pattern Lineage**: 재등장 패턴 매칭 (배치 계산)
- **L1/L2 Retrieval**: 하이브리드 검색 + 리랭커 표준
- **Director Pack**: VDG → 코칭 규칙 컴파일 결과
- **H.264 Streaming**: Phase 2 모바일 최적화 스트리밍

---

## 4) SoR 규칙 (Source of Record)

1. **DB가 SoR**: 분석 스키마/클러스터/결정/템플릿 시드는 DB에만 기록
2. **Sheets는 운영/공유 버스**: 사람이 보는 표, 운영용 워크플로우에만 사용
3. **NotebookLM/Opal 출력은 반드시 DB로 래핑**: 결과를 직접 신뢰하지 않음
4. **영상 해석은 코드 기반**: Gemini 3.0 Pro로 스키마 추출 (재현성 우선)
5. **노드 UI는 입출력만 노출**: 내부 체인/로직은 숨김
6. **패턴 경계는 VDG/DB 고정**: NotebookLM은 Pattern Engine이지만, 패턴 경계는 DB 기준
7. **플랫폼 동등**: 모바일/웹 동일 백엔드 API 사용

---

## 5) 문서 의존관계

```
ARCHITECTURE_FINAL.md (최상위)
         │
         ├── 01_VDG_SYSTEM.md
         ├── 02_EVIDENCE_LOOP_CANVAS.md
         │       └── 07_CANVAS_NODE_CONTRACTS.md
         ├── 21_PARALLEL_DEVELOPMENT_STRATEGY.md
         │       └── 22_DEVELOPER_ONBOARDING.md
         └── PROOF_PLAYBOOK.md
```

---

## 6) 역할별 빠른 읽기

| 역할 | 문서 순서 |
|------|----------|
| **CEO/PM** | `00_EXECUTIVE_SUMMARY` → `21_PARALLEL` → `LAUNCH_CHECKLIST` |
| **모바일 개발자** | `21_PARALLEL` → `PROOF_PLAYBOOK` → `/mobile/README.md` |
| **웹 개발자** | `22_DEVELOPER_ONBOARDING` → `ARCHITECTURE_FINAL` |
| **Tech Lead** | `ARCHITECTURE_FINAL` → `01_VDG_SYSTEM` → `STPF_V3_ROADMAP` |

---

## 7) 변경 규칙

- 구조 변경 시 반드시 `ARCHITECTURE_FINAL.md`와 이 인덱스를 먼저 갱신
- 기능/노드 추가 시 `07_CANVAS_NODE_CONTRACTS.md`와 `06_PIPELINE_PLAYBOOK.md` 동시 업데이트
- 아카이브 시 `_archive_[날짜]/README.md`에 기록
