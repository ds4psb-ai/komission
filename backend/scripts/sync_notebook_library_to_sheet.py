"""
sync_notebook_library_to_sheet.py

Export notebook_library (DB SoR) into VDG_Insights sheet (ops/share bus).

Usage:
  python backend/scripts/sync_notebook_library_to_sheet.py --limit 200
"""
import argparse
import asyncio
import json
import os
import sys
from typing import List, Optional, Set

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import NotebookLibraryEntry
from app.services.sheet_manager import SheetManager

SHEET_INSIGHTS = "VDG_Insights"
INSIGHTS_HEADERS = ["parent_id", "summary", "key_patterns", "risks", "created_at"]


def ensure_sheet(manager: SheetManager, folder_id: Optional[str], share_email: Optional[str]) -> str:
    sheet_id = manager.find_sheet_id(SHEET_INSIGHTS)
    if not sheet_id:
        sheet_id = manager.create_sheet(SHEET_INSIGHTS, folder_id=folder_id)
        manager.write_header(sheet_id, INSIGHTS_HEADERS)
    else:
        result = manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="Sheet1!A1:E1"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            manager.write_header(sheet_id, INSIGHTS_HEADERS)

    if sheet_id and share_email:
        manager.share_sheet(sheet_id, share_email, role="writer")
    return sheet_id


def load_existing_summaries(manager: SheetManager) -> Set[str]:
    sheet_id = manager.find_sheet_id(SHEET_INSIGHTS)
    if not sheet_id:
        return set()
    try:
        result = manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="Sheet1!B2:B5000"
        ).execute()
        rows = result.get("values", [])
        return {row[0] for row in rows if row}
    except Exception:
        return set()


def summarize(entry: NotebookLibraryEntry) -> str:
    summary = entry.summary or {}
    if isinstance(summary, dict):
        for key in ("summary", "overview", "brief"):
            if key in summary and summary[key]:
                return str(summary[key])
        return json.dumps(summary, ensure_ascii=False)
    return str(summary)


def extract_key_patterns(entry: NotebookLibraryEntry) -> str:
    summary = entry.summary or {}
    if isinstance(summary, dict):
        for key in ("key_patterns", "patterns", "hooks"):
            if key in summary and summary[key]:
                return json.dumps(summary[key], ensure_ascii=False)
    return entry.cluster_id or ""


def extract_risks(entry: NotebookLibraryEntry) -> str:
    summary = entry.summary or {}
    if isinstance(summary, dict):
        for key in ("risks", "risk"):
            if key in summary and summary[key]:
                return json.dumps(summary[key], ensure_ascii=False)
    return ""


async def fetch_entries(db: AsyncSession, limit: int) -> List[NotebookLibraryEntry]:
    result = await db.execute(
        select(NotebookLibraryEntry).order_by(NotebookLibraryEntry.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


async def main_async(args: argparse.Namespace) -> None:
    share_email = os.environ.get("KOMISSION_SHARE_EMAIL")
    folder_id = os.environ.get("KOMISSION_FOLDER_ID")

    manager = SheetManager()
    ensure_sheet(manager, folder_id, share_email)
    existing_summaries = load_existing_summaries(manager)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        entries = await fetch_entries(db, args.limit)

    rows_to_add: List[List[str]] = []
    for entry in entries:
        summary_text = summarize(entry)
        if summary_text in existing_summaries:
            continue
        rows_to_add.append([
            str(entry.parent_node_id) if entry.parent_node_id else "",
            summary_text,
            extract_key_patterns(entry),
            extract_risks(entry),
            entry.created_at.isoformat(),
        ])
        existing_summaries.add(summary_text)

    if rows_to_add:
        manager.append_data(SHEET_INSIGHTS, rows_to_add)
        print(f"Exported {len(rows_to_add)} rows to {SHEET_INSIGHTS}")
    else:
        print("No new insights rows to export.")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export notebook_library to VDG_Insights sheet")
    parser.add_argument("--limit", type=int, default=200, help="Max rows to export")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
