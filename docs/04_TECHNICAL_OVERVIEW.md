# Technical Overview (최신)

**작성**: 2026-01-07

---

## 1) 시스템 구성
- Backend: FastAPI
- DB: PostgreSQL + Neo4j
- Cache: Redis (옵션)
- Frontend: Next.js
- Automation: n8n or cron
- Capsule: Opal/NotebookLM/Sheets 래핑 실행 노드

**핵심 DB 테이블(확장)**
- `notebook_library` (NotebookLM 요약/클러스터 저장)
- `template_versions`, `template_feedback`, `template_policy` (템플릿 학습)

---

## 2) 핵심 데이터 흐름
```
Outlier Source(수동/크롤링) → NotebookLM 요약 → notebook_library(DB)
  → remix_nodes(Parent/Variants) + metric_daily
  → evidence_snapshots → Evidence Sheet → Decision Sheet → Capsule → Canvas UI
```

---

## 3) 실행 (로컬)
```bash
# infra
docker-compose up -d

# backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
bun install
bun run dev
```

## 4) Evidence Loop Runner (Sheets + Opal)
환경변수는 `backend/.env`에서 로드됩니다.

필수:
- `KOMISSION_SHARE_EMAIL`
- `GOOGLE_APPLICATION_CREDENTIALS` (서비스 계정 JSON 경로, 없으면 `backend/credentials.json` 시도)

옵션:
- `KOMISSION_FOLDER_ID`
- `KOMISSION_PRIMARY_PLATFORMS` (기본: tiktok,instagram)
- `KOMISSION_PRIMARY_VIEW_THRESHOLD`
- `KOMISSION_PRIMARY_GROWTH_THRESHOLD`
- `KOMISSION_SECONDARY_VIEW_THRESHOLD`
- `KOMISSION_SECONDARY_GROWTH_THRESHOLD`
- `GEMINI_MODEL` (고정: gemini-3.0-pro, 다른 값은 차단)

실행:
```bash
python backend/scripts/run_real_evidence_loop.py
```

---

## 5) CSV 수동 수집 (초기 운영용)
```bash
python backend/scripts/ingest_outlier_csv_db.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_outlier_csv.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_progress_csv.py --csv /path/to/progress.csv
```

## 5.1) DB → Sheet 동기화 (수동 입력 연동)
API로 들어온 Outlier를 Evidence Loop 시트에 반영:
```bash
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
```

## 5.2) NotebookLM → DB → Insights Sheet
NotebookLM 결과를 DB에 적재 후 공유용 시트로 동기화:
```bash
python backend/scripts/ingest_notebook_library.py --json /path/to/notebooklm.json
python backend/scripts/ingest_notebook_library_sheet.py --sheet VDG_Insights
python backend/scripts/sync_notebook_library_to_sheet.py --limit 200
```

---

## 6) 핵심 API (요약)
- Outliers
  - POST /api/v1/outliers/sources
  - GET /api/v1/outliers/sources
  - POST /api/v1/outliers/items
  - POST /api/v1/outliers/items/manual
  - GET /api/v1/outliers/candidates
  - PATCH /api/v1/outliers/items/{item_id}/status
  - POST /api/v1/outliers/items/{item_id}/promote

- Remix
  - GET /api/v1/remix
  - GET /api/v1/remix/{node_id}
  - POST /api/v1/remix/{node_id}/analyze
  - POST /api/v1/remix/{node_id}/fork
  - POST /api/v1/remix/{node_id}/matching

- Pipelines
  - GET /api/v1/pipelines/public
  - GET /api/v1/pipelines/
  - POST /api/v1/pipelines/
  - GET /api/v1/pipelines/{id}
  - PATCH /api/v1/pipelines/{id}
  - DELETE /api/v1/pipelines/{id}

- O2O
  - GET /api/v1/o2o/locations
  - GET /api/v1/o2o/campaigns
  - POST /api/v1/o2o/campaigns/{id}/apply
  - GET /api/v1/o2o/applications/me
  - POST /api/v1/o2o/verify

---

## 7) 통합 원칙
- **DB는 SoR**
- **Sheets는 공유/운영 버스**
- **NotebookLM 결과는 DB로 래핑**
- **Pattern Library/Trace는 엔진**
- **Capsule은 실행 레이어**
- **Canvas는 템플릿 UI**
