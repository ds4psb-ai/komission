# Docs Index: Structure + Dependencies + SoR Rules

**작성**: 2025-12-28 (Updated: 2025-12-30 Evening)  
**목표**: 문서 체계/범주/의존관계/SoR 규칙을 단일 인덱스로 고정

---

## 1) 문서 체계 (범주)
### A. 전략/비전
- `docs/00_SINGLE_SOURCE_OF_TRUTH.md`
- `docs/00_EXECUTIVE_SUMMARY.md`
- `docs/ARCHITECTURE_FINAL.md` ← **NEW: 컨설팅용 최종 아키텍처**
- `docs/CHANGELOG.md` ← **NEW: 개발 이력**
- `docs/16_PDR.md`
- `docs/15_FINAL_ARCHITECTURE.md`
- `docs/11_VIRLO_BENCHMARK.md`
- `docs/10_UI_UX_STRATEGY.md`
- `docs/19_NEXT_STEP_ROADMAP.md`
- `docs/20_UI_COMPONENT_SPEC.md`
- `docs/21_PAGE_IA_REDESIGN.md`
- `docs/22_FRONTEND_FILE_AUDIT.md`
- `docs/vdg_v4_2pass_protocol.md` ← **VDG v4.0 2-Pass Protocol**

### B. 아키텍처/데이터
- `docs/01_VDG_SYSTEM.md`
- `docs/02_EVIDENCE_LOOP_CANVAS.md`
- `docs/04_TECHNICAL_OVERVIEW.md`
- `docs/08_CANVAS_NODE_CONTRACTS.md`
- `docs/12_KOMISSION_STUDIO_SPEC.md`
- `docs/13_PERIODIC_CRAWLING_SPEC.md`
- `docs/14_NOTEBOOK_LIBRARY_NODE_SPEC.md`
- `docs/14_OUTLIER_CRAWLER_INTEGRATION_DESIGN.md`
- `docs/17_NOTEBOOKLM_LIBRARY_STRATEGY.md`
- `docs/18_NOTEBOOKLM_ENTERPRISE_INTEGRATION.md`
- `docs/23_TIKTOK_EMBED_SPEC.md` ← **NEW: TikTok 임베드 역공학 문서 (Virlo 분석)**

### C. 운영/플로우
- `docs/05_DATA_SOURCES_O2O.md`
- `docs/06_USER_FLOW.md`
- `docs/07_PIPELINE_PLAYBOOK.md`
- `docs/09_OPERATIONS_RUNBOOK.md`

### D. 템플릿
- `docs/templates/opal_workflow.md`
- `docs/templates/debate_script.md`

---

## 2) 용어 표준 (Canonical Terms)
- **Answer-First (For You)**: 검색보다 추천을 먼저 제시하는 UX 원칙
- **PatternAnswerCard**: Answer-First (For You)의 핵심 카드 컴포넌트
- **EvidenceBar**: 베스트 댓글 + 재등장 근거를 보여주는 증거 바
- **Temporal Recurrence / Pattern Lineage**: 재등장 패턴 매칭 (배치 계산)
- **L1/L2 Retrieval**: 하이브리드 검색 + 리랭커 표준

## 3) SoR 규칙 (Source of Record)
1. **DB가 SoR**: 분석 스키마/클러스터/결정/템플릿 시드는 DB에만 기록
2. **Sheets는 운영/공유 버스**: 사람이 보는 표, 운영용 워크플로우에만 사용
3. **NotebookLM/Opal 출력은 반드시 DB로 래핑**: 결과를 직접 신뢰하지 않음
4. **영상 해석은 코드 기반**: Gemini 3.0 Pro로 스키마 추출 (재현성 우선)
5. **노드 UI는 입출력만 노출**: 내부 체인/로직은 숨김
6. **패턴 경계는 VDG/DB 고정**: NotebookLM은 Pattern Engine이지만, 패턴 경계(cluster_id)는 VDG/DB 기준선으로 고정
7. **PEGL v1.0 Phase 준수**: Phase 0(가드레일) → Phase 1(수집) → ... → Phase 6(UX) 순서 고정 (상세: `15_FINAL_ARCHITECTURE.md`)

---

## 4) 문서 의존관계 (상위 → 하위)
**최상위 설계**
- `docs/15_FINAL_ARCHITECTURE.md` → 전체 문서의 상위 기준
- `docs/15_FINAL_ARCHITECTURE.md` → `docs/16_PDR.md`

**기본 흐름**
- `docs/01_VDG_SYSTEM.md` → `docs/02_EVIDENCE_LOOP_CANVAS.md`
- `docs/02_EVIDENCE_LOOP_CANVAS.md` → `docs/08_CANVAS_NODE_CONTRACTS.md`
- `docs/02_EVIDENCE_LOOP_CANVAS.md` → `docs/07_PIPELINE_PLAYBOOK.md`
- `docs/02_EVIDENCE_LOOP_CANVAS.md` → `docs/06_USER_FLOW.md`

**데이터/운영 연계**
- `docs/05_DATA_SOURCES_O2O.md` → `docs/07_PIPELINE_PLAYBOOK.md`
- `docs/07_PIPELINE_PLAYBOOK.md` → `docs/09_OPERATIONS_RUNBOOK.md`

**스튜디오/캔버스**
- `docs/08_CANVAS_NODE_CONTRACTS.md` → `docs/12_KOMISSION_STUDIO_SPEC.md`
- `docs/10_UI_UX_STRATEGY.md` → `docs/12_KOMISSION_STUDIO_SPEC.md`

**크롤링**
- `docs/13_PERIODIC_CRAWLING_SPEC.md` → `docs/14_OUTLIER_CRAWLER_INTEGRATION_DESIGN.md`

**Notebook Library**
- `docs/14_NOTEBOOK_LIBRARY_NODE_SPEC.md` → `docs/08_CANVAS_NODE_CONTRACTS.md`
- `docs/17_NOTEBOOKLM_LIBRARY_STRATEGY.md` → `docs/14_NOTEBOOK_LIBRARY_NODE_SPEC.md`

---

## 5) 읽기 순서 (권장)
1. `docs/00_SINGLE_SOURCE_OF_TRUTH.md`
2. `docs/15_FINAL_ARCHITECTURE.md`
3. `docs/00_EXECUTIVE_SUMMARY.md`
4. `docs/16_PDR.md`
5. `docs/01_VDG_SYSTEM.md`
6. `docs/02_EVIDENCE_LOOP_CANVAS.md`
7. `docs/04_TECHNICAL_OVERVIEW.md`
8. `docs/05_DATA_SOURCES_O2O.md`
9. `docs/07_PIPELINE_PLAYBOOK.md`
10. `docs/08_CANVAS_NODE_CONTRACTS.md`
11. `docs/12_KOMISSION_STUDIO_SPEC.md`
12. `docs/09_OPERATIONS_RUNBOOK.md`

---

## 6) 변경 규칙
- 구조 변경 시 반드시 `docs/15_FINAL_ARCHITECTURE.md`와 이 인덱스를 먼저 갱신
- 기능/노드 추가 시 `docs/08_CANVAS_NODE_CONTRACTS.md`와 `docs/07_PIPELINE_PLAYBOOK.md` 동시 업데이트
