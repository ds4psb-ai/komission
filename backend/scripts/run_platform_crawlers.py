"""
run_platform_crawlers.py

Unified runner for all platform crawlers (YouTube, TikTok, Instagram).
Fetches trending/viral content and ingests into outlier_items DB.

Usage:
  python backend/scripts/run_platform_crawlers.py --platforms youtube,tiktok,instagram --limit 50
  python backend/scripts/run_platform_crawlers.py --platforms youtube --category entertainment
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import OutlierItem, OutlierSource
from app.schemas.evidence import OutlierCrawlItem
from app.crawlers.factory import CrawlerFactory

logger = logging.getLogger(__name__)


async def get_or_create_source(
    db: AsyncSession, 
    source_name: str, 
    platform: str
) -> OutlierSource:
    """Get existing source or create new one."""
    result = await db.execute(
        select(OutlierSource).where(OutlierSource.name == source_name)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        source = OutlierSource(
            name=source_name,
            base_url=f"https://crawler.{platform}.auto",
            auth_type="api_key",
            is_active=True,
        )
        db.add(source)
        await db.flush()
        logger.info(f"Created source: {source_name}")
    
    return source


async def save_crawl_items(
    db: AsyncSession,
    items: List[OutlierCrawlItem],
    source: OutlierSource,
) -> int:
    """Save crawled items to database, skipping duplicates."""
    inserted = 0
    
    for item in items:
        # Check for duplicate
        result = await db.execute(
            select(OutlierItem).where(
                OutlierItem.external_id == item.external_id,
                OutlierItem.source_id == source.id,
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            continue
        
        outlier = OutlierItem(
            source_id=source.id,
            external_id=item.external_id,
            video_url=item.video_url,
            platform=item.platform,
            category=item.category,
            title=item.title,
            thumbnail_url=item.thumbnail_url,
            view_count=item.view_count,
            like_count=item.like_count,
            share_count=item.share_count,
            growth_rate=item.growth_rate,
            # Extended metrics
            outlier_score=item.outlier_score,
            outlier_tier=item.outlier_tier,
            creator_avg_views=item.creator_avg_views,
            engagement_rate=item.engagement_rate,
            
            status="pending",
            crawled_at=datetime.utcnow(),
        )
        db.add(outlier)
        inserted += 1
    
    return inserted


async def run_crawler(
    platform: str,
    limit: int = 50,
    category: str = "trending",
    region: str = "KR",
    **kwargs
) -> List[OutlierCrawlItem]:
    """Run a single platform crawler."""
    try:
        crawler = CrawlerFactory.create(platform)
        
        logger.info(f"Running {platform} crawler...")
        items = crawler.crawl(
            limit=limit,
            category=category,
            region_code=region if platform == "youtube" else region,
            region=region if platform != "youtube" else None,
            **kwargs
        )
        
        if hasattr(crawler, 'close'):
            crawler.close()
        
        return items
        
    except ValueError as e:
        logger.error(f"Failed to create {platform} crawler: {e}")
        return []
    except Exception as e:
        logger.error(f"{platform} crawler failed: {e}")
        return []


async def main_async(args: argparse.Namespace) -> None:
    """Main async entry point."""
    platforms = [p.strip().lower() for p in args.platforms.split(",")]
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    total_inserted = 0
    
    async with async_session() as db:
        for platform in platforms:
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing platform: {platform}")
            logger.info(f"{'='*50}")
            
            # Get or create source
            source_name = f"{platform}_auto"
            source = await get_or_create_source(db, source_name, platform)
            
            # Run crawler
            items = await run_crawler(
                platform=platform,
                limit=args.limit,
                category=args.category,
                region=args.region,
            )
            
            if not items:
                logger.warning(f"No items collected from {platform}")
                continue
            
            logger.info(f"Collected {len(items)} items from {platform}")
            
            # Save to database
            inserted = await save_crawl_items(db, items, source)
            total_inserted += inserted
            
            logger.info(f"Inserted {inserted} new items (skipped {len(items) - inserted} duplicates)")
        
        await db.commit()
    
    await engine.dispose()
    
    logger.info(f"\n{'='*50}")
    logger.info(f"CRAWL COMPLETE: Total {total_inserted} new items inserted")
    logger.info(f"{'='*50}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run platform crawlers")
    parser.add_argument(
        "--platforms", 
        default="youtube,tiktok,instagram",
        help="Comma-separated list of platforms to crawl"
    )
    parser.add_argument("--limit", type=int, default=50, help="Max items per platform")
    parser.add_argument("--category", default="trending", help="Content category")
    parser.add_argument("--region", default="KR", help="Region code")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
