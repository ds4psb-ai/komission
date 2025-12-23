# Google Sheets Setup Script

This script automates the creation of 9 Evidence Loop sheets in Google Drive.

## Prerequisites

1. **Google Cloud SDK** installed and authenticated.
2. **Drive & Sheets API** enabled in your Google Cloud Project.

## Authorization (One-time)

Your current gcloud session might not have Drive permissions. Run this to authorize:

```bash
gcloud auth login --enable-gdrive-access --update-adcs
```
*Note: `--enable-gdrive-access` is a conceptual flag; usually `gcloud auth login` requests standard scopes. If that fails, try:*

```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/cloud-platform
```

## Running the Script

Once authorized:

```bash
python3 backend/scripts/setup_sheets.py
```

This will:
1. Create 9 Sheets in your Drive root (or specified folder).
2. Write the contract headers defined in `docs/02_EVIDENCE_LOOP_CANVAS.md`.
3. Print the Sheet IDs.
