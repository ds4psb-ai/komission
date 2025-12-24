"""
ingest_outlier_csv.py

Import outlier rows from a CSV into VDG_Outlier_Raw.

Usage:
  python scripts/ingest_outlier_csv.py --csv /path/to/outliers.csv --source-name "MyProvider"
"""
import argparse
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager

SHEET_OUTLIER = "VDG_Outlier_Raw"
OUTLIER_HEADERS = [
    "source_name", "source_url", "collected_at", "platform", "category",
    "title", "views", "growth_rate", "author", "posted_at", "status"
]

FIELD_ALIASES = {
    "source_url": ["source_url", "url", "link", "video_url", "post_url", "post_link"],
    "title": ["title", "caption", "name", "headline"],
    "platform": ["platform", "platform_name", "source_platform"],
    "category": ["category", "vertical", "genre", "topic"],
    "views": ["views", "view_count", "viewcount", "plays", "play_count"],
    "growth_rate": ["growth_rate", "growth", "velocity", "trend_score", "growth_pct"],
    "author": ["author", "creator", "username", "handle"],
    "posted_at": ["posted_at", "published_at", "post_date", "upload_date"],
    "collected_at": ["collected_at", "collected", "scraped_at"],
    "source_name": ["source_name", "source", "provider"],
}


def infer_platform(url: str) -> str:
    lowered = (url or "").lower()
    if "tiktok" in lowered:
        return "tiktok"
    if "instagram" in lowered or "insta" in lowered:
        return "instagram"
    if "youtu" in lowered:
        return "youtube"
    return "unknown"


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


def ensure_sheet(manager: SheetManager, folder_id: Optional[str], share_email: Optional[str]):
    sheet_id = manager.find_sheet_id(SHEET_OUTLIER)
    if not sheet_id:
        sheet_id = manager.create_sheet(SHEET_OUTLIER, folder_id=folder_id)
        manager.write_header(sheet_id, OUTLIER_HEADERS)
    else:
        # Ensure header exists
        result = manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="Sheet1!A1:K1"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            manager.write_header(sheet_id, OUTLIER_HEADERS)

    if sheet_id and share_email:
        manager.share_sheet(sheet_id, share_email, role="writer")
    return sheet_id


def load_existing_urls(manager: SheetManager) -> set:
    sheet_id = manager.find_sheet_id(SHEET_OUTLIER)
    if not sheet_id:
        return set()
    try:
        result = manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="Sheet1!B2:B2000"
        ).execute()
        rows = result.get("values", [])
        return {row[0] for row in rows if row}
    except Exception:
        return set()


def main():
    parser = argparse.ArgumentParser(description="Import outliers CSV into VDG_Outlier_Raw")
    parser.add_argument("--csv", required=True, help="Path to outlier CSV file")
    parser.add_argument("--source-name", default=None, help="Source name for rows")
    parser.add_argument("--status", default="new", help="Initial status (default: new)")
    parser.add_argument("--category", default=None, help="Fallback category")
    parser.add_argument("--platform", default=None, help="Fallback platform")
    args = parser.parse_args()

    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    share_email = os.environ.get("KOMISSION_SHARE_EMAIL")
    folder_id = os.environ.get("KOMISSION_FOLDER_ID")

    manager = SheetManager()
    ensure_sheet(manager, folder_id, share_email)

    existing_urls = load_existing_urls(manager)

    rows_to_add: List[List[object]] = []
    now_iso = datetime.now().isoformat()

    with open(args.csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = [h.strip().lower() for h in reader.fieldnames or []]
        for raw in reader:
            row = {k.strip().lower(): v for k, v in raw.items()}
            source_url = resolve_field(row, "source_url")
            if not source_url or source_url in existing_urls:
                continue

            title = resolve_field(row, "title")
            if not title:
                continue

            platform = resolve_field(row, "platform") or args.platform or infer_platform(source_url)
            category = resolve_field(row, "category") or args.category or "unknown"
            views = parse_number(resolve_field(row, "views"))
            growth_rate = parse_number(resolve_field(row, "growth_rate"))
            author = resolve_field(row, "author")
            posted_at = resolve_field(row, "posted_at")
            collected_at = resolve_field(row, "collected_at") or now_iso
            source_name = resolve_field(row, "source_name") or args.source_name or "external"

            rows_to_add.append([
                source_name,
                source_url,
                collected_at,
                platform,
                category,
                title,
                int(views) if views is not None else "",
                growth_rate if growth_rate is not None else "",
                author,
                posted_at,
                args.status,
            ])
            existing_urls.add(source_url)

    if rows_to_add:
        manager.append_data(SHEET_OUTLIER, rows_to_add)
        print(f"Imported {len(rows_to_add)} outlier rows into {SHEET_OUTLIER}")
    else:
        print("No new rows to import.")


if __name__ == "__main__":
    main()
