# Canvas + Node Contracts (최신)

**작성**: 2026-01-07
**목표**: 노드 입력/출력 계약과 UI 노출 원칙을 고정

---

## 1) 노드 타입
- **Outlier Node**: 원본 링크/기초 메타
- **Parent Node**: 승격된 RemixNode (MASTER)
- **Notebook Library Node**: NotebookLM 해석 결과(DB 래핑)
- **Evidence Node**: Evidence Sheet 요약
- **Decision Node**: Decision Sheet 요약
- **Capsule Node**: 내부 체인 실행(숨김)
- **O2O Node**: 캠페인 타입/게이팅 규칙

---

## 2) Capsule Node 계약
**Input**
- parent_id
- evidence_snapshot (요약 JSON)
- insights_summary (NotebookLM 요약, DB 래핑)
- library_entry_id (Notebook Library 참조)
- constraints (budget/time/brand)

**Output**
- decision_json (GO/STOP/PIVOT + next_experiment)
- decision_sheet_row_id
- audit_log_id

### Capsule Output (Short-form 실행 브리프)
레거시처럼 긴 텍스트 가이드가 아니라, **실행 가능한 숏폼 브리프**만 노출합니다.

**필수 필드**
- `hook`: 0~2초 훅 문장/장면
- `shotlist`: 3~6개 샷 시퀀스
- `audio`: 추천 사운드/리듬/볼륨 레벨
- `scene`: 장소/소품/분위기
- `timing`: 컷 길이/템포 (예: 1.2s / 0.8s / 1.5s)
- `do_not`: 금지 요소(브랜드/법적/리스크)

> 이 출력은 Canvas에서 **Guide Node**로 표시됩니다.

**UI 노출 원칙**
- 사용자는 **입력/출력만** 본다
- 내부 체인(Opal/NotebookLM/n8n) 세부 로직은 **숨김**

---

## 3) Evidence/Decision 노드 UI 규칙
- Evidence: 상위 5개 패턴 + 리스크 2개
- Decision: 결론 1줄 + 근거 3개 + 다음 실험 1개
- 길고 무거운 설명은 접힘 처리

---

## 4) 템플릿 연결 원칙
- 템플릿은 **노드 결과를 소비**하는 레이어
- 사용자 커스터마이징은 **캡슐 입력 슬롯**만 허용
- 캔버스는 **설명 가능성**이 아니라 **실행 가능성**을 우선
