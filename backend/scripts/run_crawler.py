"""
run_crawler.py

CLI to run outlier crawlers and ingest data into DB (SoR).

Usage:
  python backend/scripts/run_crawler.py --source mock --limit 5
"""
import argparse
import asyncio
import hashlib
import logging
import os
import sys
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# Add backend to path
sys.path.append(BASE_DIR)

from app.config import settings
from app.crawlers.factory import CrawlerFactory
from app.models import OutlierItem, OutlierSource, OutlierItemStatus

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("OutlierCrawler")


def normalize_external_id(source_name: str, external_id: str, video_url: str) -> str:
    safe_source = (source_name or "unknown").strip().lower()
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
        base_url="crawler://",
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


async def main_async(args) -> None:
    crawler = CrawlerFactory.create(args.source)
    items = crawler.crawl(limit=args.limit)
    if not items:
        logger.info("No items found.")
        return

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    new_count = 0
    source_cache: Dict[str, OutlierSource] = {}
    now = datetime.utcnow()

    async with async_session() as db:
        for item in items:
            if not item.video_url:
                continue
            source_name = (item.source_name or args.source).strip()
            source = source_cache.get(source_name)
            if not source:
                source = await get_or_create_source(db, source_name)
                source_cache[source_name] = source

            external_id = normalize_external_id(source_name, item.external_id, item.video_url)
            if await outlier_exists(db, external_id, item.video_url):
                continue

            new_item = OutlierItem(
                source_id=source.id,
                external_id=external_id,
                video_url=item.video_url,
                title=item.title,
                thumbnail_url=item.thumbnail_url,
                platform=item.platform,
                category=item.category,
                view_count=item.view_count,
                like_count=item.like_count,
                share_count=item.share_count,
                growth_rate=item.growth_rate,
                status=OutlierItemStatus.PENDING,
                crawled_at=now,
            )
            db.add(new_item)
            new_count += 1

        for source in source_cache.values():
            source.last_crawled = now

        await db.commit()

    await engine.dispose()

    if new_count:
        logger.info(f"Inserted {new_count} outliers into DB (outlier_items).")
        logger.info("Next: run sync_outliers_to_sheet.py to export to VDG_Outlier_Raw.")
    else:
        logger.info("No new unique outliers inserted.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Outlier Crawler")
    parser.add_argument("--source", required=True, help="Crawler source (mock, tiktok, etc.)")
    parser.add_argument("--limit", type=int, default=10, help="Number of items to fetch")
    args = parser.parse_args()

    try:
        asyncio.run(main_async(args))
    except Exception as exc:
        logger.error(f"Run failed: {exc}")


if __name__ == "__main__":
    main()
