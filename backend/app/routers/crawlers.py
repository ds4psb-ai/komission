"""
Crawlers API Router - Crawler Control & Status
Based on 14_OUTLIER_CRAWLER_INTEGRATION_DESIGN.md

Endpoints:
- POST /api/v1/crawlers/run - Trigger crawler execution
- GET /api/v1/crawlers/status - Get crawler status and last run info
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import OutlierSource, OutlierItem, OutlierItemStatus
from app.routers.auth import require_curator, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crawlers", tags=["Crawlers"])

# ==================
# SCHEMAS
# ==================

class Platform(str, Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    VIRLO = "virlo"
    ALL = "all"


class CrawlerRunRequest(BaseModel):
    platforms: List[Platform] = [Platform.ALL]
    limit: int = 50
    category: str = "trending"
    region: str = "KR"


class CrawlerRunResponse(BaseModel):
    status: str
    job_id: str
    platforms: List[str]
    message: str


class PlatformStatus(BaseModel):
    platform: str
    is_active: bool
    last_crawled: Optional[datetime]
    items_count: int
    last_24h_count: int


class CrawlerStatusResponse(BaseModel):
    status: str
    platforms: List[PlatformStatus]
    total_items: int
    pending_count: int
    promoted_count: int


# ==================
# JOB TRACKING (In-memory for MVP)
# ==================

_running_jobs = {}


async def _run_crawler_background(
    job_id: str,
    platforms: List[str],
    limit: int,
    category: str,
    region: str,
):
    """Background task to run crawlers"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import settings
    
    _running_jobs[job_id] = {
        "status": "running",
        "started_at": datetime.utcnow(),
        "platforms": platforms,
        "results": {}
    }
    
    try:
        # Dynamic import to avoid circular deps
        from app.crawlers.factory import CrawlerFactory
        from app.schemas.evidence import OutlierCrawlItem
        
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            for platform in platforms:
                try:
                    # Special handling for Virlo (async Playwright scraper)
                    if platform == "virlo":
                        from app.services.virlo_scraper import scrape_and_save_to_db
                        try:
                            result = await scrape_and_save_to_db(limit=limit)
                            _running_jobs[job_id]["results"][platform] = {
                                "collected": result.get("collected", 0),
                                "inserted": result.get("inserted", 0),
                                "s_tier_count": 0
                            }
                        except Exception as e:
                            logger.error(f"Virlo scraper failed: {e}")
                            _running_jobs[job_id]["results"][platform] = {"error": str(e)}
                        continue
                    
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
                    
                    # Insert items
                    inserted = 0
                    s_tier_count = 0
                    
                    # Import notification service
                    from app.services.notification_service import notify_s_tier
                    
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
                            await db.flush()  # Get the ID
                            inserted += 1
                            
                            # Send S-tier notification (score >= 500x)
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
                    
                    # Update source last_crawled
                    source.last_crawled = datetime.utcnow()
                    
                    _running_jobs[job_id]["results"][platform] = {
                        "collected": len(items),
                        "inserted": inserted,
                        "s_tier_count": s_tier_count
                    }
                    
                except Exception as e:
                    logger.error(f"Crawler {platform} failed: {e}")
                    _running_jobs[job_id]["results"][platform] = {"error": str(e)}
            
            await db.commit()
        
        await engine.dispose()
        _running_jobs[job_id]["status"] = "completed"
        _running_jobs[job_id]["completed_at"] = datetime.utcnow()
        
        # Send batch complete notification
        try:
            from app.services.notification_service import notification_service
            
            total_collected = sum(
                r.get("collected", 0) for r in _running_jobs[job_id]["results"].values()
                if isinstance(r, dict) and "collected" in r
            )
            total_inserted = sum(
                r.get("inserted", 0) for r in _running_jobs[job_id]["results"].values()
                if isinstance(r, dict) and "inserted" in r
            )
            total_s_tier = sum(
                r.get("s_tier_count", 0) for r in _running_jobs[job_id]["results"].values()
                if isinstance(r, dict) and "s_tier_count" in r
            )
            
            await notification_service.notify_batch_complete(
                job_id=job_id,
                platforms=platforms,
                total_collected=total_collected,
                total_inserted=total_inserted,
                s_tier_count=total_s_tier,
            )
        except Exception as e:
            logger.warning(f"Batch notification failed: {e}")
        
    except Exception as e:
        logger.error(f"Crawler job {job_id} failed: {e}")
        _running_jobs[job_id]["status"] = "failed"
        _running_jobs[job_id]["error"] = str(e)


# ==================
# ENDPOINTS
# ==================

@router.post("/run", response_model=CrawlerRunResponse)
async def run_crawlers(
    request: CrawlerRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_curator),
):
    """
    크롤러 실행 트리거 (관리자 전용)
    
    백그라운드에서 크롤러를 실행하고 job_id를 반환합니다.
    /crawlers/status/{job_id}로 진행 상황을 확인할 수 있습니다.
    """
    job_id = f"crawl_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Resolve platforms
    if Platform.ALL in request.platforms:
        platforms = ["youtube", "tiktok", "instagram"]
    else:
        platforms = [p.value for p in request.platforms]
    
    # Start background job
    background_tasks.add_task(
        _run_crawler_background,
        job_id=job_id,
        platforms=platforms,
        limit=request.limit,
        category=request.category,
        region=request.region,
    )
    
    return CrawlerRunResponse(
        status="started",
        job_id=job_id,
        platforms=platforms,
        message=f"Crawler job started. Check status with GET /crawlers/jobs/{job_id}"
    )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """크롤러 작업 상태 조회"""
    if job_id not in _running_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _running_jobs[job_id]


@router.get("/status", response_model=CrawlerStatusResponse)
async def get_crawler_status(
    db: AsyncSession = Depends(get_db)
):
    """
    크롤러 전체 상태 조회
    
    각 플랫폼별 마지막 크롤 시각, 수집 건수 등을 반환합니다.
    """
    from datetime import timedelta
    
    # Get sources
    result = await db.execute(select(OutlierSource))
    sources = result.scalars().all()
    
    platform_statuses = []
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    
    for source in sources:
        # Count items for this source
        count_result = await db.execute(
            select(func.count(OutlierItem.id)).where(
                OutlierItem.source_id == source.id
            )
        )
        total_count = count_result.scalar() or 0
        
        # Count last 24h
        recent_result = await db.execute(
            select(func.count(OutlierItem.id)).where(
                OutlierItem.source_id == source.id,
                OutlierItem.crawled_at >= day_ago
            )
        )
        recent_count = recent_result.scalar() or 0
        
        # Infer platform from source name
        platform = source.name.replace("_auto", "").replace("_manual", "")
        
        platform_statuses.append(PlatformStatus(
            platform=platform,
            is_active=source.is_active,
            last_crawled=source.last_crawled,
            items_count=total_count,
            last_24h_count=recent_count,
        ))
    
    # Total counts
    total_result = await db.execute(select(func.count(OutlierItem.id)))
    total = total_result.scalar() or 0
    
    pending_result = await db.execute(
        select(func.count(OutlierItem.id)).where(
            OutlierItem.status == OutlierItemStatus.PENDING
        )
    )
    pending = pending_result.scalar() or 0
    
    promoted_result = await db.execute(
        select(func.count(OutlierItem.id)).where(
            OutlierItem.status == OutlierItemStatus.PROMOTED
        )
    )
    promoted = promoted_result.scalar() or 0
    
    return CrawlerStatusResponse(
        status="healthy",
        platforms=platform_statuses,
        total_items=total,
        pending_count=pending,
        promoted_count=promoted,
    )


@router.get("/health")
async def crawler_health(
    db: AsyncSession = Depends(get_db)
):
    """
    크롤러 헬스 체크 (13_PERIODIC_CRAWLING_SPEC.md)
    
    모니터링 시스템에서 호출하여 크롤러 상태를 확인합니다.
    """
    from datetime import timedelta
    
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    
    # Check each platform
    platform_health = {}
    platforms = ["youtube", "tiktok", "instagram"]
    
    for platform in platforms:
        result = await db.execute(
            select(OutlierSource).where(
                OutlierSource.name == f"{platform}_auto"
            )
        )
        source = result.scalar_one_or_none()
        
        if source:
            # Check if crawled in last 24h
            is_stale = source.last_crawled is None or source.last_crawled < day_ago
            platform_health[platform] = {
                "status": "warning" if is_stale else "healthy",
                "last_crawled": source.last_crawled.isoformat() if source.last_crawled else None,
                "stale": is_stale,
            }
        else:
            platform_health[platform] = {
                "status": "not_configured",
                "last_crawled": None,
                "stale": True,
            }
    
    # Get running jobs count
    running_count = sum(1 for j in _running_jobs.values() if j.get("status") == "running")
    
    # Overall status
    all_healthy = all(
        p.get("status") == "healthy" 
        for p in platform_health.values()
    )
    
    # Get quota information
    try:
        from app.services.quota_manager import get_quota_manager
        quota_mgr = get_quota_manager()
        quotas = {
            "youtube": quota_mgr.sync_get_remaining("youtube"),
            "tiktok": quota_mgr.sync_get_remaining("tiktok"),
            "instagram": quota_mgr.sync_get_remaining("instagram"),
        }
    except Exception as e:
        logger.warning(f"Quota info unavailable: {e}")
        quotas = {}
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": now.isoformat(),
        "crawlers": platform_health,
        "quotas": quotas,
        "running_jobs": running_count,
        "total_jobs_tracked": len(_running_jobs),
    }
