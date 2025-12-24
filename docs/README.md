# Komission Docs (최신 정리본)

**최종 업데이트**: 2026-01-07 (KST)

이 폴더가 **유일한 최신 문서**입니다. 루트/기타 폴더에는 포인터만 유지합니다.

## 핵심 원칙
- **Evidence Loop 우선**: VDG + Evidence Table + Progress가 제품 엔진
- **Debate는 옵션**: 설명/설득 레이어로만 사용
- **DB가 SoR, Sheets는 버스**: 알고리즘 기록은 DB, 운영/공유는 Sheets
- **NotebookLM/Opal은 가속 레이어**: 결과는 **DB로 래핑** 후 사용
- **Pattern Library/Trace는 엔진**: 바이럴 공식 증명은 DB/규칙 기반으로 누적
- **Capsule/Template은 실행 레이어**: 내부 체인은 감추고 입력/출력 계약만 노출

## 핵심 플로우
Outlier 수동/크롤링 → NotebookLM 해석 → Notebook Library(DB) → Parent 후보 → Depth 실험
→ Pattern Trace/Lift → Evidence → Decision(Opal) → Capsule/Template 실행
→ 성과 반영 → 다음 Parent
- **Outlier 소스는 외부 구독 크롤링** (TikTok/Instagram 우선)

## 문서 목록
- `docs/00_EXECUTIVE_SUMMARY.md` — CEO용 1장 요약
- `docs/01_VDG_SYSTEM.md` — Viral Depth Genealogy 데이터 모델/계산
- `docs/02_EVIDENCE_LOOP_CANVAS.md` — Evidence Loop + Canvas 템플릿 설계
- `docs/03_IMPLEMENTATION_ROADMAP.md` — Phase + 마이크로 단계 실행 계획
- `docs/04_TECHNICAL_OVERVIEW.md` — 시스템 구조/스택/실행/핵심 API
- `docs/05_DATA_SOURCES_O2O.md` — Outlier 수집 + O2O 운영 구조
- `docs/06_USER_FLOW.md` — 사용자 흐름(관리자/크리에이터/O2O)
- `docs/07_PIPELINE_PLAYBOOK.md` — 파이프라인 운영 단계/트리거/산출물
- `docs/08_CANVAS_NODE_CONTRACTS.md` — 노드/캡슐 IO 계약 및 UI 노출 원칙
- `docs/09_OPERATIONS_RUNBOOK.md` — 운영 체크리스트/주기/지표
- `docs/10_UI_UX_STRATEGY.md` — UI/UX 원칙 및 화면 설계 기준
- `docs/11_VIRLO_BENCHMARK.md` — Virlo UI 벤치마크 + 적용 계획
- `docs/12_KOMISSION_STUDIO_SPEC.md` — Studio/Canvas 기술 사양
- `docs/13_PERIODIC_CRAWLING_SPEC.md` — 주기 크롤링 + 플랫폼 업데이트 수집 사양
- `docs/14_NOTEBOOK_LIBRARY_NODE_SPEC.md` — Notebook Library + Node 모듈 사양

## 템플릿(옵션)
- `docs/templates/opal_workflow.md` — Opal 의사결정 프롬프트 템플릿
- `docs/templates/debate_script.md` — Debate 조건/스크립트 템플릿

## 역할별 빠른 읽기
- CEO: `00` → `03`
- Tech Lead/CTO: `01` → `02` → `04`
- PM: `03` → `05`
- Front/Back Dev: `02` → `04`
- Ops/Curator: `06` → `07` → `09`
- Design/UX: `10`
- Research/Benchmark: `11`
- Notebook/LLM: `14`
