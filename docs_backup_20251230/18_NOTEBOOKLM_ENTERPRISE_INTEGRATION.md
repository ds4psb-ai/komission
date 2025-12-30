# NotebookLM Enterprise Integration (Registry + Lifecycle)

**작성**: 2026-01-07  
**목표**: NotebookLM Enterprise API를 Komission SoR 규칙에 맞춰 **노트북 레지스트리 + 라이프사이클 자동화**로 통합한다.

---

## 1) 범위와 원칙
### 1.1 범위
- NotebookLM **노트북 관리 API** 연동만 다룬다.
  - create / get / listRecentlyViewed / share / batchDelete
- 소스 추가/분석 결과 ingest는 **별도 파이프라인**으로 유지한다.

### 1.2 원칙 (SoR 준수)
- **DB = SoR**: NotebookLM 자체는 운영 UI, 진실은 DB.
- **DB-wrapped**: NotebookLM 산출물은 반드시 DB에 구조화 저장.
- **run_id + idempotency_key**: 모든 NotebookLM API 호출은 추적 가능해야 한다.

---

## 2) 아키텍처 위치
```
VDG Cluster (DB 기준선)
  → Source Pack (DB metadata + Drive artifact)
  → NotebookLM Notebook (Enterprise API)
  → NotebookLM Output (ops/summary)
  → DB-wrapped Pattern Library / Notebook Library
  → Evidence Loop / Decision
```

---

## 3) Notebook Registry (DB) — 단일 진실

### 3.1 테이블 개요 (권장)
**table: notebooklm_registry**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | uuid | 내부 PK |
| cluster_id | text | VDG 기준 패턴 경계 |
| temporal_phase | text | T0~T4 |
| source_pack_id | uuid | 입력팩 참조 |
| notebook_id | text | NotebookLM ID |
| notebook_name | text | projects/{project}/locations/{location}/notebooks/{id} |
| project_number | text | GCP 프로젝트 번호 |
| location | text | global/us/eu |
| status | text | planned/created/shared/archived/deleted/error |
| share_role | text | owner/writer/reader |
| created_at | timestamp | 생성 시간 |
| updated_at | timestamp | 갱신 시간 |
| last_synced_at | timestamp | 최근 동기화 |
| run_id | text | 생성/동기화 run 추적 |
| inputs_hash | text | Source Pack 해시 |

### 3.2 고정 규칙
- **cluster_id + temporal_phase** 단위로 1개의 NotebookLM 노트북을 유지한다.
- NotebookLM ID는 **DB가 소유**하고 UI/시트에는 표시용으로만 사용한다.

---

## 4) 라이프사이클 상태
1. **planned**: Source Pack 생성됨 (아직 Notebook 없음)
2. **created**: notebooks.create 성공
3. **shared**: notebooks.share 완료
4. **archived**: 운영 대상 제외(삭제 전 보존)
5. **deleted**: notebooks.batchDelete 완료
6. **error**: 실패/재시도 대상

---

## 5) API 매핑 (Enterprise)

### 5.1 notebooks.create
- **입력**: title, project_number, location
- **출력**: notebook_id, notebook_name
- **DB**: registry 생성/업데이트

### 5.2 notebooks.get
- **용도**: 상태/메타데이터 확인
- **DB**: last_synced_at 업데이트

### 5.3 notebooks.listRecentlyViewed
- **용도**: 운영 관측/누락 감지
- **DB**: registry와 diff 비교

### 5.4 notebooks.share
- **용도**: 운영자/서비스 계정 공유
- **DB**: share_role 기록

### 5.5 notebooks.batchDelete
- **용도**: 클러스터 폐기/정리
- **DB**: status=deleted로 갱신

---

## 6) Naming Rule (권장)
Notebook Title 예시:
```
NL_{platform}_{category}_{cluster_id}_{temporal_phase}_v{n}
```
예:
```
NL_tiktok_beauty_hook-2s-textpunch_T1_v2
```

---

## 7) 자동화 플로우 (Runner)

### 7.1 create_notebook_run
1. Source Pack 생성
2. registry upsert (planned)
3. notebooks.create 호출
4. registry status=created
5. notebooks.share (옵션)
6. registry status=shared

### 7.2 reconcile_notebook_run
1. listRecentlyViewed 조회
2. registry와 diff 비교
3. 누락/삭제/권한 문제 정리

### 7.3 cleanup_notebook_run
1. “archived” 상태 대상 batchDelete
2. registry status=deleted

---

## 8) run_id / idempotency 규칙
- 모든 API 호출은 `run_id`, `idempotency_key` 기록
- 동일 Source Pack 재실행은 **같은 notebook_id 재사용**을 우선
- 입력 해시가 바뀌면 **revision 상승** 후 새 노트북 생성

---

## 9) 보안/권한
- IAM 역할은 **최소 권한 원칙** 준수
- share는 운영 전용 계정으로 제한
- 토큰은 환경변수/런타임에서만 주입 (문서에 키 저장 금지)

---

## 10) 통합 지점 (코드/문서 연계)
- Source Pack: `backend/scripts/build_notebook_source_pack.py`
- NotebookLM 요약 ingest: `backend/scripts/ingest_notebook_library_sheet.py`
- Evidence Loop 연결: `docs/07_PIPELINE_PLAYBOOK.md`
- SoR 규칙: `docs/00_SINGLE_SOURCE_OF_TRUTH.md`

---

## 11) 체크리스트
- [ ] registry 테이블 생성
- [ ] create/get/share/batchDelete runner 스크립트
- [ ] Source Pack → notebook create 자동 연결
- [ ] listRecentlyViewed 기반 reconcile
- [ ] ops 로그(run_id, idempotency_key) 기록
