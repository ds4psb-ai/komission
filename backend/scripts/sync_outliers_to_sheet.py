"""
sync_outliers_to_sheet.py

Export outlier_items from DB into VDG_Outlier_Raw for the Evidence Loop.

Usage:
  python scripts/sync_outliers_to_sheet.py --limit 200 --status pending,selected
  python scripts/sync_outliers_to_sheet.py --since 2026-01-01
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.models import OutlierItem, OutlierSource, OutlierItemStatus
from app.services.sheet_manager import SheetManager


SHEET_OUTLIER = "VDG_Outlier_Raw"
OUTLIER_HEADERS = [
    "source_name", "source_url", "collected_at", "platform", "category",
    "title", "views", "growth_rate", "author", "posted_at", "status",
]


def ensure_sheet(manager: SheetManager, folder_id: Optional[str], share_email: Optional[str]) -> str:
    sheet_id = manager.find_sheet_id(SHEET_OUTLIER)
    if not sheet_id:
        sheet_id = manager.create_sheet(SHEET_OUTLIER, folder_id=folder_id)
        manager.write_header(sheet_id, OUTLIER_HEADERS)
    else:
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
            spreadsheetId=sheet_id, range="Sheet1!B2:B5000"
        ).execute()
        rows = result.get("values", [])
        return {row[0] for row in rows if row}
    except Exception:
        return set()


def parse_statuses(raw: Optional[str]) -> Optional[List[OutlierItemStatus]]:
    if not raw:
        return None
    statuses = []
    for token in raw.split(","):
        value = token.strip().lower()
        if not value:
            continue
        try:
            statuses.append(OutlierItemStatus(value))
        except ValueError:
            raise SystemExit(f"Unknown status: {value}")
    return statuses or None


def status_to_sheet(status: OutlierItemStatus) -> str:
    if status == OutlierItemStatus.PENDING:
        return "new"
    if status == OutlierItemStatus.SELECTED:
        return "candidate"
    if status == OutlierItemStatus.REJECTED:
        return "ignored"
    if status == OutlierItemStatus.PROMOTED:
        return "promoted"
    return "new"


def parse_since(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        raise SystemExit("--since expects ISO date (YYYY-MM-DD) or datetime")


async def fetch_outliers(
    db: AsyncSession,
    statuses: Optional[List[OutlierItemStatus]],
    since: Optional[datetime],
    limit: int,
):
    query = select(OutlierItem, OutlierSource).join(OutlierSource, OutlierItem.source_id == OutlierSource.id)
    if statuses:
        query = query.where(OutlierItem.status.in_(statuses))
    if since:
        query = query.where(OutlierItem.crawled_at >= since)
    query = query.order_by(OutlierItem.crawled_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.all()


async def main_async(args):
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    share_email = os.environ.get("KOMISSION_SHARE_EMAIL")
    folder_id = os.environ.get("KOMISSION_FOLDER_ID")

    manager = SheetManager()
    ensure_sheet(manager, folder_id, share_email)
    existing_urls = load_existing_urls(manager)

    database_url = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    statuses = parse_statuses(args.status)
    since = parse_since(args.since)

    async with async_session() as db:
        rows = await fetch_outliers(db, statuses, since, args.limit)

    rows_to_add: List[List[object]] = []
    for item, source in rows:
        if not item.video_url or item.video_url in existing_urls:
            continue
        rows_to_add.append([
            source.name,
            item.video_url,
            item.crawled_at.isoformat() if item.crawled_at else "",
            item.platform,
            item.category,
            item.title or "",
            item.view_count or 0,
            item.growth_rate or "",
            "",
            "",
            status_to_sheet(OutlierItemStatus(item.status)),
        ])
        existing_urls.add(item.video_url)

    if rows_to_add:
        manager.append_data(SHEET_OUTLIER, rows_to_add)
        print(f"Exported {len(rows_to_add)} outlier rows into {SHEET_OUTLIER}")
    else:
        print("No new outlier rows to export.")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Export DB outliers to VDG_Outlier_Raw sheet")
    parser.add_argument("--limit", type=int, default=200, help="Max rows to export")
    parser.add_argument("--status", default=None, help="Filter by status (comma-separated)")
    parser.add_argument("--since", default=None, help="ISO date/datetime filter (YYYY-MM-DD)")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
