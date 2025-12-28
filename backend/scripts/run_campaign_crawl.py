#!/usr/bin/env python3
"""
run_campaign_crawl.py

Experience campaign-aligned outlier crawling.
Fetches viral shorts in categories: beauty, food, living, product, meme

Campaign Types:
- visit (방문형): O2O, 맛집, 카페, 네일샵
- shipment (배송형): 화장품, 식품, 가전
- instant (즉석형): 현장 추첨, 이벤트

Usage:
  python scripts/run_campaign_crawl.py --category beauty --limit 20
  python scripts/run_campaign_crawl.py --all --limit 10
"""
import argparse
import asyncio
import logging
import os
import sys
from typing import Dict, List

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.crawlers.youtube import YouTubeCrawler
from app.models import OutlierItem, OutlierSource, OutlierItemStatus
from app.utils.time import utcnow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Campaign_Crawl")

# Category → Search Keywords mapping
CAMPAIGN_SEARCH_QUERIES: Dict[str, List[str]] = {
    "beauty": ["뷰티", "화장품 리뷰", "스킨케어"],
    "food": ["맛집", "먹방", "요리 레시피"],
    "living": ["리빙", "인테리어", "청소 꿀팁"],
    "product": ["리뷰", "언박싱", "제품리뷰"],
    "meme": ["밈", "웃긴영상", "코미디"],
}

# Category → Campaign Type mapping (for downstream assignment)
CATEGORY_TO_CAMPAIGN_TYPE: Dict[str, str] = {
    "beauty": "shipment",    # 화장품 배송
    "food": "visit",         # 맛집 방문
    "living": "shipment",    # 가구/생활용품 배송
    "product": "shipment",   # 제품 배송
    "meme": "instant",       # 즉석 이벤트/콜라보
}


def normalize_external_id(source_name: str, external_id: str, video_url: str) -> str:
    import hashlib
    safe_source = (source_name or "unknown").strip().lower()
    raw_id = (external_id or "").strip()
    if not raw_id:
        raw_id = hashlib.sha256(video_url.encode("utf-8")).hexdigest()
    if raw_id.startswith(f"{safe_source}:"):
        return raw_id
    return f"{safe_source}:{raw_id}"


async def get_or_create_source(db: AsyncSession, source_name: str) -> OutlierSource:
    # Try to reuse existing youtube_auto source
    result = await db.execute(select(OutlierSource).where(OutlierSource.name == "youtube_auto"))
    source = result.scalar_one_or_none()
    if source:
        return source
    
    # Fallback: check for exact match
    result = await db.execute(select(OutlierSource).where(OutlierSource.name == source_name))
    source = result.scalar_one_or_none()
    if source:
        return source
    
    # Create new with naive datetime
    from datetime import datetime
    source = OutlierSource(
        name=source_name,
        base_url="crawler://youtube_campaign",
        auth_type="none",
        crawl_interval_hours=6,
    )
    source.created_at = datetime.utcnow()
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


async def crawl_category(category: str, limit_per_query: int = 10, dry_run: bool = False) -> dict:
    """Crawl a single category with multiple keywords."""
    queries = CAMPAIGN_SEARCH_QUERIES.get(category, [])
    if not queries:
        logger.warning(f"No queries defined for category: {category}")
        return {"category": category, "collected": 0, "inserted": 0}

    campaign_type = CATEGORY_TO_CAMPAIGN_TYPE.get(category, "shipment")
    logger.info(f"Category '{category}' → campaign_type '{campaign_type}'")

    all_items = []
    total_quota = 0

    with YouTubeCrawler() as crawler:
        for query in queries:
            logger.info(f"[{category}] Searching: '{query}'")
            try:
                items = crawler.search_shorts_by_keyword(query, limit=limit_per_query)
                for item in items:
                    item.category = category
                all_items.extend(items)
                total_quota = crawler.quota_used
                logger.info(f"  → Got {len(items)} items (quota: {total_quota})")
            except Exception as e:
                logger.error(f"  → Failed: {e}")
                continue

    if dry_run:
        logger.info(f"[DRY RUN] Would insert {len(all_items)} items for {category} ({campaign_type})")
        return {"category": category, "campaign_type": campaign_type, "collected": len(all_items), "inserted": 0, "quota": total_quota}

    # Save to DB
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    inserted = 0
    from datetime import datetime
    now = datetime.utcnow()

    async with async_session() as db:
        source = await get_or_create_source(db, f"youtube_campaign_{category}")

        for item in all_items:
            if not item.video_url:
                continue

            external_id = normalize_external_id("youtube", item.external_id, item.video_url)
            if await outlier_exists(db, external_id, item.video_url):
                continue

            new_item = OutlierItem(
                source_id=source.id,
                external_id=external_id,
                video_url=item.video_url,
                title=item.title,
                thumbnail_url=item.thumbnail_url,
                platform="youtube",
                category=category,
                view_count=item.view_count,
                like_count=item.like_count,
                growth_rate=item.growth_rate,
                outlier_score=item.outlier_score,
                outlier_tier=item.outlier_tier,
                status=OutlierItemStatus.PENDING,
                crawled_at=now,
            )
            db.add(new_item)
            inserted += 1

        source.last_crawled = now
        await db.commit()

    await engine.dispose()

    logger.info(f"[{category}] Inserted {inserted}/{len(all_items)} new items (campaign_type: {campaign_type})")
    return {"category": category, "campaign_type": campaign_type, "collected": len(all_items), "inserted": inserted, "quota": total_quota}


async def main_async(args) -> None:
    results = []

    if args.all:
        categories = list(CAMPAIGN_SEARCH_QUERIES.keys())
    else:
        categories = [args.category]

    for category in categories:
        result = await crawl_category(
            category=category,
            limit_per_query=args.limit,
            dry_run=args.dry_run,
        )
        results.append(result)

    # Summary
    total_collected = sum(r["collected"] for r in results)
    total_inserted = sum(r["inserted"] for r in results)
    total_quota = sum(r.get("quota", 0) for r in results)

    logger.info("=" * 50)
    logger.info(f"Campaign Crawl Complete")
    logger.info(f"  Categories: {len(results)}")
    logger.info(f"  Collected: {total_collected}")
    logger.info(f"  Inserted: {total_inserted}")
    logger.info(f"  Quota used: {total_quota} units")
    logger.info("")
    logger.info("Campaign Type Mapping:")
    for r in results:
        logger.info(f"  {r['category']} → {r.get('campaign_type', 'unknown')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Experience Campaign Outlier Crawler")
    parser.add_argument("--category", default="beauty", choices=list(CAMPAIGN_SEARCH_QUERIES.keys()),
                        help="Category to crawl")
    parser.add_argument("--all", action="store_true", help="Crawl all categories")
    parser.add_argument("--limit", type=int, default=10, help="Limit per search query")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to DB")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
