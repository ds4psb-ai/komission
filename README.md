# Komission | Viral Depth Genealogy

Komission is a **Viral Depth Genealogy + Evidence Loop** platform for short-form remix experimentation.

## Core Loop (요약)
Outlier 수집 → Parent 승격 → Depth 실험 → Evidence/Decision → Capsule 실행 → O2O 연결

## System Snapshot
- **DB is SoR**, Sheets are the ops/share bus
- NotebookLM/Opal are **accelerators**; outputs are **DB‑wrapped**
- Canvas shows only **inputs/outputs** (capsule chain stays hidden)

## Canonical Docs
All up-to-date docs live under `docs/`. Start here:
- `docs/README.md`
- `docs/00_EXECUTIVE_SUMMARY.md`
- `docs/01_VDG_SYSTEM.md`
- `docs/02_EVIDENCE_LOOP_CANVAS.md`
- `docs/03_IMPLEMENTATION_ROADMAP.md`
- `docs/04_TECHNICAL_OVERVIEW.md`
- `docs/05_DATA_SOURCES_O2O.md`
- `docs/06_USER_FLOW.md`
- `docs/07_PIPELINE_PLAYBOOK.md`
- `docs/08_CANVAS_NODE_CONTRACTS.md`
- `docs/09_OPERATIONS_RUNBOOK.md`
- `docs/10_UI_UX_STRATEGY.md`
- `docs/11_VIRLO_BENCHMARK.md`
- `docs/12_KOMISSION_STUDIO_SPEC.md`
- `docs/13_PERIODIC_CRAWLING_SPEC.md`
- `docs/14_NOTEBOOK_LIBRARY_NODE_SPEC.md`

## Quick Start (Local)
```bash
docker-compose up -d
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd ../frontend && bun install && bun run dev
```

## Evidence Loop Quick Run
```bash
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
python backend/scripts/run_real_evidence_loop.py
```

See `docs/04_TECHNICAL_OVERVIEW.md` for full setup and env vars.
