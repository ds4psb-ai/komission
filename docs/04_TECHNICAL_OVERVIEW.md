# Technical Overview (최신)

**작성**: 2026-01-06

---

## 1) 시스템 구성
- Backend: FastAPI
- DB: PostgreSQL + Neo4j
- Cache: Redis (옵션)
- Frontend: Next.js
- Automation: n8n or cron

---

## 2) 핵심 데이터 흐름
```
Outlier Source → vdg_parents/variants → vdg_metric_daily
  → vdg_evidence → Evidence Sheet → Decision Sheet → Canvas UI
```

---

## 3) 실행 (로컬)
```bash
# infra
docker-compose up -d

# backend
cd backend
python3.9 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
bun install
bun run dev
```

---

## 4) 핵심 API (요약)
- Remix
  - GET /api/v1/remix
  - GET /api/v1/remix/{node_id}
  - POST /api/v1/remix/{node_id}/analyze
  - POST /api/v1/remix/{node_id}/fork
  - POST /api/v1/remix/{node_id}/matching

- O2O
  - GET /api/v1/o2o/locations
  - GET /api/v1/o2o/campaigns
  - POST /api/v1/o2o/campaigns/{id}/apply
  - GET /api/v1/o2o/applications/me
  - POST /api/v1/o2o/verify

---

## 5) 통합 원칙
- **DB는 SoR**
- **Sheets는 공유/운영 버스**
- **NotebookLM/Opal은 옵션**
- **Canvas는 템플릿 UI**

