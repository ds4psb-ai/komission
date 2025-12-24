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
- `ingest_outlier_csv.py` — import external outlier CSV into `VDG_Outlier_Raw`
- `ingest_progress_csv.py` — import progress CSV into `VDG_Progress`
- `setup_sheets.py` — create initial `VDG_*` sheets
