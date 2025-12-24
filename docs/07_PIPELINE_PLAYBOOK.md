# Pipeline Playbook (최신)

**작성**: 2026-01-07
**목표**: Evidence Loop 운영 단계를 표준화

---

## 1) 파이프라인 단계 요약
| 단계 | 트리거 | 입력 | 출력 |
| --- | --- | --- | --- |
| 수집 | 수동 입력/크롤링 | Outlier URL | `outlier_items` |
| 동기화 | 수동 실행 | DB Outliers | `VDG_Outlier_Raw` |
| 해석 | NotebookLM | Outlier Raw | `notebook_library` |
| 후보 선정 | 규칙/수동 | Outlier Raw + Notebook Library | `VDG_Parent_Candidates` |
| 승격 | Curator 승인 | 후보 | `remix_nodes`(Parent) |
| 분석 | 선택 실행 | Parent | 분석 요약 |
| Evidence | 주간/수동 | Progress | `VDG_Evidence` |
| Decision | 주간/수동 | Evidence | `VDG_Decision` |
| 실행 | 승인 후 | Decision | Capsule/Template 실행 |

---

## 2) 최소 운영 루프 (MVP)
1. Outlier 수집 (수동 입력)
2. DB → Sheet 동기화
3. NotebookLM 해석 → Notebook Library 저장
4. Evidence Runner 실행
5. Decision 검토 후 템플릿 적용

### 실행 커맨드
```bash
python backend/scripts/pull_provider_csv.py --config backend/provider_sources.json
python backend/scripts/ingest_outlier_csv_db.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_notebook_library.py --json /path/to/notebooklm.json
python backend/scripts/sync_notebook_library_to_sheet.py --limit 200
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
python backend/scripts/run_selector.py
python backend/scripts/run_real_evidence_loop.py
```

---

## 3) 단계별 체크리스트
**수집**
- 중복 URL 제거
- platform/category 채워짐

**후보 선정**
- 기준: 조회수/성장률/최근성
- status = candidate

**승격**
- Parent RemixNode 생성 확인
- node_id 기록

**Evidence/Decision**
- Evidence Sheet row 생성
- Decision Sheet 생성 확인

---

## 4) NotebookLM/Opal 사용 원칙
- NotebookLM: 해석/클러스터 결과를 **DB에 저장**
- Opal: Decision 생성 **보조**
- SoR는 DB, Sheet는 **운영 버스**
