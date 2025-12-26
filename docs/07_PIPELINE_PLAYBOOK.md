# Pipeline Playbook (최신)

**작성**: 2026-01-07
**목표**: Evidence Loop 운영 단계를 표준화

---

## 1) 파이프라인 단계 요약
| 단계 | 트리거 | 입력 | 출력 |
| --- | --- | --- | --- |
| 수집 | 수동 입력/크롤링 | Outlier URL | `outlier_items` |
| 동기화 | 수동 실행 | DB Outliers | `VDG_Outlier_Raw` |
| 해석 | 코드 기반 분석 + 클러스터링 | Outlier Raw | `notebook_library` |
| 후보 선정 | 규칙/수동 | Outlier Raw + Notebook Library | `VDG_Parent_Candidates` |
| 승격 | Curator 승인 | 후보 | `remix_nodes`(Parent) |
| 분석 | 선택 실행 | Parent | 분석 요약 |
| Evidence | 주간/수동 | Progress | `VDG_Evidence` |
| Decision | 주간/수동 | Evidence | `VDG_Decision` |
| 템플릿 시드 | 선택 실행 | Notebook Library + Decision | `VDG_Template_Seeds` |
| 실행 | 승인 후 | Decision | Capsule/Template 실행 |

---

## 2) 최소 운영 루프 (MVP)
1. Outlier 수집 (수동 입력)
2. DB → Sheet 동기화
3. 영상 해석(코드) + 클러스터링 → Notebook Library 저장 (NotebookLM 요약은 선택)
4. NotebookLM Source Pack 생성(선택, Sheets/Docx)
5. NotebookLM 요약 생성(선택, 클러스터 분할 기준 적용)
6. Evidence Runner 실행
7. Opal 템플릿 시드 생성(선택)
8. Decision 검토 후 템플릿 적용
9. O2O/체험단 운영은 Phase 2+에서 활성화 (MVP는 타입 게이팅 표시만)

참고:
- TikTok 베스트 댓글은 comment/list API 캡처 방식이 기본.
- bdturing 차단 시 `refresh_tiktok_session.py`로 세션 갱신 후 재시도.

### 실행 커맨드
```bash
python backend/scripts/pull_provider_csv.py --config backend/provider_sources.json
python backend/scripts/ingest_outlier_csv_db.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_notebook_library.py --json /path/to/notebooklm.json
python backend/scripts/ingest_notebook_library_sheet.py --sheet VDG_Insights
python backend/scripts/sync_notebook_library_to_sheet.py --limit 200
python backend/scripts/build_notebook_source_pack.py --cluster-id CLUSTER_ID
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
python backend/scripts/run_selector.py
python backend/scripts/run_real_evidence_loop.py
python backend/scripts/refresh_tiktok_session.py
```

### One-shot (Provider → Candidates)
```bash
python backend/scripts/run_provider_pipeline.py --config backend/provider_sources.json
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
- NotebookLM: **요약/라벨 보조** 결과를 **DB에 저장**
- Opal: Decision 생성 **보조**
- SoR는 DB, Sheet는 **운영 버스**
