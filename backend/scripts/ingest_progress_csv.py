"""
ingest_progress_csv.py

Import progress rows from CSV into VDG_Progress.

Usage:
  python scripts/ingest_progress_csv.py --csv /path/to/progress.csv
"""
import argparse
import csv
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager

SHEET_PROGRESS = "VDG_Progress"
PROGRESS_HEADERS = [
    "variant_id", "date", "views", "engagement_rate",
    "retention_rate", "confidence_score", "status",
    "parent_id", "variant_name"
]

FIELD_ALIASES = {
    "variant_id": ["variant_id", "variant", "variantid", "variation_id"],
    "variant_name": ["variant_name", "variation_name", "name"],
    "parent_id": ["parent_id", "parent", "parentid"],
    "date": ["date", "day", "timestamp", "observed_at", "posted_at"],
    "views": ["views", "view_count", "viewcount", "plays", "play_count"],
    "engagement_rate": ["engagement_rate", "engagement", "er"],
    "retention_rate": ["retention_rate", "retention", "rr"],
    "confidence_score": ["confidence_score", "confidence", "score"],
    "status": ["status", "state"],
}


def parse_number(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    if text.endswith("%"):
        try:
            return float(text.rstrip("%")) / 100
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def resolve_field(row: Dict[str, str], key: str) -> str:
    for alias in FIELD_ALIASES.get(key, []):
        if alias in row and row[alias]:
            return row[alias]
    return ""


def extract_parent_from_variant(variant_id: str) -> Optional[str]:
    if not variant_id:
        return None
    match = re.search(r"(parent_[a-zA-Z0-9]+)", variant_id)
    if match:
        return match.group(1)
    return None


def ensure_sheet(manager: SheetManager, folder_id: Optional[str], share_email: Optional[str]):
    sheet_id = manager.find_sheet_id(SHEET_PROGRESS)
    if not sheet_id:
        sheet_id = manager.create_sheet(SHEET_PROGRESS, folder_id=folder_id)
        manager.write_header(sheet_id, PROGRESS_HEADERS)
    else:
        result = manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="Sheet1!A1:I1"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            manager.write_header(sheet_id, PROGRESS_HEADERS)

    if sheet_id and share_email:
        manager.share_sheet(sheet_id, share_email, role="writer")


def main():
    parser = argparse.ArgumentParser(description="Import progress CSV into VDG_Progress")
    parser.add_argument("--csv", required=True, help="Path to progress CSV file")
    parser.add_argument("--status", default="tracking", help="Default status (tracking)")
    args = parser.parse_args()

    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    share_email = os.environ.get("KOMISSION_SHARE_EMAIL")
    folder_id = os.environ.get("KOMISSION_FOLDER_ID")

    manager = SheetManager()
    ensure_sheet(manager, folder_id, share_email)

    rows_to_add: List[List[object]] = []
    today = datetime.now().date().isoformat()

    with open(args.csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {k.strip().lower(): v for k, v in raw.items()}
            variant_id = resolve_field(row, "variant_id")
            if not variant_id:
                continue

            parent_id = resolve_field(row, "parent_id") or extract_parent_from_variant(variant_id) or ""
            variant_name = resolve_field(row, "variant_name") or ""
            date = resolve_field(row, "date") or today
            views = parse_number(resolve_field(row, "views"))
            engagement_rate = parse_number(resolve_field(row, "engagement_rate"))
            retention_rate = parse_number(resolve_field(row, "retention_rate"))
            confidence_score = parse_number(resolve_field(row, "confidence_score"))
            status = resolve_field(row, "status") or args.status

            rows_to_add.append([
                variant_id,
                date,
                int(views) if views is not None else "",
                engagement_rate if engagement_rate is not None else "",
                retention_rate if retention_rate is not None else "",
                confidence_score if confidence_score is not None else "",
                status,
                parent_id,
                variant_name
            ])

    if rows_to_add:
        manager.append_data(SHEET_PROGRESS, rows_to_add)
        print(f"Imported {len(rows_to_add)} progress rows into {SHEET_PROGRESS}")
    else:
        print("No progress rows to import.")


if __name__ == "__main__":
    main()
