# Technical Overview (최신)

**작성**: 2026-01-07

---

## 1) 시스템 구성
- Backend: FastAPI
- DB: PostgreSQL + Neo4j
- Cache: Redis (옵션)
- Frontend: Next.js
- Automation: n8n or cron
- Capsule: Opal/NotebookLM/Sheets 래핑 실행 노드 (분석은 별도 파이프라인)
- Analysis: Gemini 3.0 Pro 기반 코드 파이프라인
- Output: JSON Schema 강제 (Structured Output)

**핵심 DB 테이블(확장)**
- `notebook_library` (분석 스키마/클러스터 + NotebookLM 요약 저장)
- `template_seeds` (Opal 템플릿 시드 저장)
- `template_versions`, `template_feedback`, `template_policy` (템플릿 학습)

---

## 2) 핵심 데이터 흐름
```
Outlier Source(수동/크롤링) → 영상 해석(코드) → 유사도 클러스터링 → notebook_library(DB)
  → remix_nodes(Parent/Variants) + metric_daily
  → evidence_snapshots → Evidence Sheet → Decision Sheet → Template Seeds(Opal)
  → Capsule/Template → Canvas UI
```

**클러스터링 핵심**
- VDG v3.2 `microbeats` 기반 **sequence similarity**를 포함
- 패턴 set 유사도(훅/씬/오디오/타이밍)와 결합해 최종 점수 산출

---

## 3) Creator Persona Signals (Phase 3)
**목표**: 자기선택 없이 **암묵 신호 기반**으로 크리에이터 스타일을 추정한다.

**핵심 원칙**
- 자기보고(“내 톤은?”) 대신 **행동/콘텐츠 기반 추론**
- 저장은 DB(SoR), Sheet는 공유 버스
- 추론 결과는 `persona_context_json`으로 캡슐 입력에 주입

**핵심 테이블(초기 스키마 제안)**
1) `creator_behavior_events`
   - `event_id` (uuid)
   - `creator_id` (uuid)
   - `event_type` (enum)
   - `node_id` (uuid, optional)
   - `template_id` (uuid, optional)
   - `payload_json` (jsonb)
   - `created_at` (timestamptz)

   **event_type 예시**
   - `template_open`, `slot_change`, `run_start`, `run_complete`
   - `rewatch`, `abandon`, `export`, `quest_apply`

2) `creator_style_fingerprint`
   - `creator_id` (uuid, pk)
   - `style_vector` (jsonb)  
   - `signal_summary` (jsonb)  (최근 30일 행동/성과 요약)
   - `updated_at` (timestamptz)
   - `version` (text)

3) `creator_calibration_choices` (Taste Calibration)
   - `choice_id` (uuid)
   - `creator_id` (uuid)
   - `pair_id` (text)
   - `option_a_id` (text)
   - `option_b_id` (text)
   - `selected` (enum: A/B)
   - `created_at` (timestamptz)

**도출 결과**
- `persona_context_json` (예: 톤/페이스/훅/자막 밀도/샷 구성)
- Template Seed/ Capsule 입력으로 사용 (Optional)

---

## 4) 실행 (로컬)
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

## 5) Evidence Loop Runner (Sheets + Opal)
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

## 6) CSV 수동 수집 (초기 운영용)
```bash
python backend/scripts/ingest_outlier_csv_db.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_outlier_csv.py --csv /path/to/outliers.csv --source-name "ProviderName"
python backend/scripts/ingest_progress_csv.py --csv /path/to/progress.csv
```

## 6.1) DB → Sheet 동기화 (수동 입력 연동)
API로 들어온 Outlier를 Evidence Loop 시트에 반영:
```bash
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
```

## 6.2) Notebook Library → DB → Insights Sheet
Notebook Library 요약/클러스터 결과를 DB에 적재 후 공유용 시트로 동기화:
```bash
python backend/scripts/ingest_notebook_library.py --json /path/to/notebooklm.json
python backend/scripts/ingest_notebook_library_sheet.py --sheet VDG_Insights
python backend/scripts/sync_notebook_library_to_sheet.py --limit 200
```

## 6.3) Opal Template Seeds → DB → Sheet (planned)
Opal이 생성한 템플릿 시드를 DB에 적재 후 공유용 시트로 동기화 (구현 예정).

---

## 7) 핵심 API (요약)
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

## 8) 통합 원칙
- **DB는 SoR**
- **Sheets는 공유/운영 버스**
- **NotebookLM 요약은 DB로 래핑**
- **NotebookLM 소스는 정적 스냅샷**이며, 클러스터 분할 전략으로 운영
- **Pattern Library/Trace는 엔진**
- **Capsule은 실행 레이어**
- **Canvas는 템플릿 UI**
