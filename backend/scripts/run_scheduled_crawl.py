#!/usr/bin/env python3
"""
Scheduled Crawler Runner
Based on 13_PERIODIC_CRAWLING_SPEC.md (cron setup L177-194)

Usage:
    # Run all outlier crawlers
    python scripts/run_scheduled_crawl.py --type outliers --platform all
    
    # Run YouTube only
    python scripts/run_scheduled_crawl.py --type outliers --platform youtube
    
    # Run platform updates crawler
    python scripts/run_scheduled_crawl.py --type updates
    
    # With custom limit
    python scripts/run_scheduled_crawl.py --platform youtube --limit 100

Cron Examples (see crontab.example):
    0 0,6,12,18 * * * python run_scheduled_crawl.py --platform youtube
    0 0,4,8,12,16,20 * * * python run_scheduled_crawl.py --platform tiktok
    0 9 * * * python run_scheduled_crawl.py --type updates
"""
import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


PLATFORMS = ["youtube", "tiktok", "instagram", "virlo"]
CRAWL_TYPES = ["outliers", "updates"]


async def run_outlier_crawlers(
    platforms: list[str],
    limit: int = 50,
    category: str = "trending",
    region: str = "KR",
    db: AsyncSession = None
) -> dict:
    """
    Run outlier crawlers for specified platforms.
    
    Args:
        platforms: List of platform names
        limit: Max items per platform
        category: Content category
        region: Region code
        db: Database session
        
    Returns:
        Dict with results per platform
    """
    from app.crawlers.factory import CrawlerFactory
    from app.models import OutlierSource, OutlierItem, OutlierItemStatus
    from app.services.notification_service import notify_s_tier, notification_service
    
    results = {}
    total_inserted = 0
    total_collected = 0
    total_s_tier = 0
    
    for platform in platforms:
        logger.info(f"Starting crawler for: {platform}")
        platform_result = {"status": "pending"}
        
        try:
            # Special handling for Virlo (async scraper)
            if platform == "virlo":
                from app.services.virlo_scraper import scrape_and_save_to_db
                result = await scrape_and_save_to_db(limit=limit)
                platform_result = {
                    "status": "success",
                    "collected": result.get("collected", 0),
                    "inserted": result.get("inserted", 0),
                }
                total_collected += result.get("collected", 0)
                total_inserted += result.get("inserted", 0)
            else:
                # Standard crawler
                crawler = CrawlerFactory.create(platform)
                items = crawler.crawl(
                    limit=limit,
                    category=category,
                    region_code=region if platform == "youtube" else None,
                    region=region if platform != "youtube" else None,
                )
                
                if hasattr(crawler, 'close'):
                    crawler.close()
                
                # Get or create source
                source_name = f"{platform}_auto"
                source_result = await db.execute(
                    select(OutlierSource).where(OutlierSource.name == source_name)
                )
                source = source_result.scalar_one_or_none()
                
                if not source:
                    source = OutlierSource(
                        name=source_name,
                        base_url=f"https://crawler.{platform}.auto",
                        auth_type="api_key",
                        is_active=True,
                    )
                    db.add(source)
                    await db.flush()
                
                # Insert items
                inserted = 0
                s_tier_count = 0
                
                for item in items:
                    existing = await db.execute(
                        select(OutlierItem).where(
                            OutlierItem.external_id == item.external_id
                        )
                    )
                    if not existing.scalar_one_or_none():
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
                            outlier_score=item.outlier_score,
                            outlier_tier=item.outlier_tier,
                            status=OutlierItemStatus.PENDING,
                            crawled_at=datetime.utcnow(),
                        )
                        db.add(outlier)
                        await db.flush()
                        inserted += 1
                        
                        # S-tier notification
                        if item.outlier_score and item.outlier_score >= 500:
                            s_tier_count += 1
                            try:
                                await notify_s_tier(
                                    outlier_id=str(outlier.id),
                                    title=item.title or "Untitled",
                                    platform=platform,
                                    video_url=item.video_url,
                                    outlier_score=item.outlier_score,
                                    view_count=item.view_count or 0,
                                )
                            except Exception as e:
                                logger.warning(f"S-tier notification failed: {e}")
                
                # Update source timestamp
                source.last_crawled = datetime.utcnow()
                
                platform_result = {
                    "status": "success",
                    "collected": len(items),
                    "inserted": inserted,
                    "s_tier_count": s_tier_count,
                }
                total_collected += len(items)
                total_inserted += inserted
                total_s_tier += s_tier_count
                
        except Exception as e:
            logger.error(f"Crawler {platform} failed: {e}")
            platform_result = {"status": "failed", "error": str(e)}
        
        results[platform] = platform_result
        logger.info(f"Completed {platform}: {platform_result}")
    
    await db.commit()
    
    # Send batch complete notification
    try:
        await notification_service.notify_batch_complete(
            job_id=f"scheduled_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            platforms=platforms,
            total_collected=total_collected,
            total_inserted=total_inserted,
            s_tier_count=total_s_tier,
        )
    except Exception as e:
        logger.warning(f"Batch notification failed: {e}")
    
    return results


async def run_platform_updates(limit: int = 10, db: AsyncSession = None) -> dict:
    """
    Run platform updates crawler.
    
    Args:
        limit: Max items per source
        db: Database session
        
    Returns:
        Dict with crawl results
    """
    from app.crawlers.platform_updates import PlatformUpdatesCrawler
    
    crawler = PlatformUpdatesCrawler()
    
    try:
        updates = await crawler.crawl_all(limit=limit)
        logger.info(f"Fetched {len(updates)} platform updates")
        
        # TODO: Save to database when PlatformUpdate model is added
        # For now, just log the results
        for update in updates:
            logger.info(f"  [{update.platform}] {update.title}")
        
        return {
            "status": "success",
            "total_updates": len(updates),
            "updates": [
                {
                    "platform": u.platform,
                    "title": u.title,
                    "source_url": u.source_url,
                }
                for u in updates
            ]
        }
    except Exception as e:
        logger.error(f"Platform updates crawler failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        await crawler.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Run scheduled crawler jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scheduled_crawl.py --platform youtube
  python run_scheduled_crawl.py --platform all --limit 100
  python run_scheduled_crawl.py --type updates
        """
    )
    parser.add_argument(
        "--type",
        choices=CRAWL_TYPES,
        default="outliers",
        help="Type of crawl: outliers or updates"
    )
    parser.add_argument(
        "--platform",
        choices=PLATFORMS + ["all"],
        default="all",
        help="Platform to crawl (for outliers type)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max items per platform"
    )
    parser.add_argument(
        "--category",
        default="trending",
        help="Content category"
    )
    parser.add_argument(
        "--region",
        default="KR",
        help="Region code"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without executing"
    )
    
    args = parser.parse_args()
    
    # Resolve platforms
    if args.type == "outliers":
        platforms = PLATFORMS if args.platform == "all" else [args.platform]
    else:
        platforms = []
    
    logger.info(f"Starting scheduled crawl: type={args.type}, platforms={platforms}")
    
    if args.dry_run:
        print(f"[DRY RUN] Would run {args.type} crawl")
        if args.type == "outliers":
            print(f"  Platforms: {platforms}")
            print(f"  Limit: {args.limit}")
        return
    
    # Database setup
    from app.config import settings
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        if args.type == "outliers":
            results = await run_outlier_crawlers(
                platforms=platforms,
                limit=args.limit,
                category=args.category,
                region=args.region,
                db=db
            )
        else:
            results = await run_platform_updates(limit=args.limit, db=db)
    
    await engine.dispose()
    
    logger.info(f"Crawl completed: {results}")
    
    # Exit with error code if any failures
    if args.type == "outliers":
        failures = [p for p, r in results.items() if r.get("status") == "failed"]
        if failures:
            logger.error(f"Failed platforms: {failures}")
            sys.exit(1)
    elif results.get("status") == "failed":
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
