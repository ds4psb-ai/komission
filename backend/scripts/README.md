# Backend Scripts

Canonical docs live in `docs/README.md`. Refer to:
- `docs/04_TECHNICAL_OVERVIEW.md` for execution and environment setup
- `docs/05_DATA_SOURCES_O2O.md` for CSV ingestion flows

This directory contains operational scripts for the Evidence Loop.

Common runs:
```bash
python backend/scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
python backend/scripts/run_real_evidence_loop.py
```

Other utilities:
- `run_crawler.py` — crawler → DB ingest (SoR)
- `run_selector.py` — DB outliers → Parent Candidates (Sheet)
- `ingest_notebook_library.py` — NotebookLM JSON/JSONL → notebook_library (DB)
- `sync_notebook_library_to_sheet.py` — notebook_library → VDG_Insights
- `ingest_outlier_csv_db.py` — provider CSV → DB outliers (SoR)
- `pull_provider_csv.py` — provider CSV fetch → DB ingest
- `run_provider_pipeline.py` — pull → sync → select (one-shot)
- `ingest_outlier_csv.py` — import external outlier CSV into `VDG_Outlier_Raw`
- `ingest_progress_csv.py` — import progress CSV into `VDG_Progress`
- `setup_sheets.py` — create initial `VDG_*` sheets
- `create_sheets_user_quota.py` — user-auth sheet creation (Drive quota bypass)
- `auto_setup_full.sh` — auth + sheets + sync + evidence loop (local bootstrap)
