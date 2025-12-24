"""
ingest_outlier_csv_db.py

Import outlier rows from a CSV into DB (outlier_items).

Usage:
  python backend/scripts/ingest_outlier_csv_db.py --csv /path/to/outliers.csv --source-name "ProviderName"
"""
import argparse
import asyncio
import csv
import hashlib
import os
import sys
from typing import Dict, Optional

from dotenv import load_dotenv
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import OutlierItem, OutlierSource, OutlierItemStatus

FIELD_ALIASES = {
    "external_id": ["external_id", "id", "content_id", "video_id"],
    "source_url": ["source_url", "url", "link", "video_url", "post_url", "post_link"],
    "title": ["title", "caption", "name", "headline"],
    "platform": ["platform", "platform_name", "source_platform"],
    "category": ["category", "vertical", "genre", "topic"],
    "views": ["views", "view_count", "viewcount", "plays", "play_count"],
    "growth_rate": ["growth_rate", "growth", "velocity", "trend_score", "growth_pct"],
    "source_name": ["source_name", "source", "provider"],
}


def resolve_field(row: Dict[str, str], key: str) -> str:
    for alias in FIELD_ALIASES.get(key, []):
        if alias in row and row[alias]:
            return row[alias]
    return ""


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


def normalize_external_id(source_name: str, external_id: str, video_url: str) -> str:
    safe_source = (source_name or "external").strip().lower()
    raw_id = (external_id or "").strip()
    if not raw_id:
        raw_id = hashlib.sha256(video_url.encode("utf-8")).hexdigest()
    if raw_id.startswith(f"{safe_source}:"):
        return raw_id
    return f"{safe_source}:{raw_id}"


async def get_or_create_source(db: AsyncSession, source_name: str) -> OutlierSource:
    result = await db.execute(select(OutlierSource).where(OutlierSource.name == source_name))
    source = result.scalar_one_or_none()
    if source:
        return source
    source = OutlierSource(
        name=source_name,
        base_url="provider://",
        auth_type="none",
        crawl_interval_hours=24,
    )
    db.add(source)
    await db.flush()
    return source


async def outlier_exists(db: AsyncSession, external_id: str, video_url: str) -> bool:
    result = await db.execute(
        select(OutlierItem.id).where(
            or_(OutlierItem.external_id == external_id, OutlierItem.video_url == video_url)
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def main_async(args: argparse.Namespace) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    inserted = 0
    async with async_session() as db:
        with open(args.csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                row = {k.strip().lower(): v for k, v in raw.items()}
                source_url = resolve_field(row, "source_url")
                if not source_url:
                    continue

                title = resolve_field(row, "title")
                if not title:
                    continue

                platform = resolve_field(row, "platform") or args.platform or infer_platform(source_url)
                category = resolve_field(row, "category") or args.category or "unknown"
                views = parse_number(resolve_field(row, "views"))
                growth_rate = parse_number(resolve_field(row, "growth_rate"))

                source_name = resolve_field(row, "source_name") or args.source_name or "external"
                source = await get_or_create_source(db, source_name)

                external_id = normalize_external_id(
                    source_name,
                    resolve_field(row, "external_id"),
                    source_url,
                )

                if await outlier_exists(db, external_id, source_url):
                    continue

                item = OutlierItem(
                    source_id=source.id,
                    external_id=external_id,
                    video_url=source_url,
                    title=title,
                    platform=platform,
                    category=category,
                    view_count=int(views) if views is not None else 0,
                    growth_rate=str(growth_rate) if growth_rate is not None else None,
                    status=OutlierItemStatus.PENDING,
                )
                db.add(item)
                inserted += 1

        await db.commit()

    await engine.dispose()
    print(f"Inserted {inserted} outliers into DB.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import outliers CSV into DB")
    parser.add_argument("--csv", required=True, help="Path to outlier CSV file")
    parser.add_argument("--source-name", default=None, help="Source name for rows")
    parser.add_argument("--category", default=None, help="Fallback category")
    parser.add_argument("--platform", default=None, help="Fallback platform")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
