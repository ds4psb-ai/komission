#!/usr/bin/env python3
"""
Sheet Sync Scheduler
주기적으로 DB 데이터를 Google Sheets로 동기화

Usage:
    python scripts/run_sheet_sync.py

Cron (매일 오전 6시):
    0 6 * * * cd /path/to/backend && ./venv/bin/python scripts/run_sheet_sync.py
"""
import asyncio
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def sync_all_sheets():
    """모든 Sheet 동기화 실행"""
    from app.services.sheet_manager import SheetManager
    from app.database import AsyncSessionLocal
    
    logger.info("=" * 50)
    logger.info("Sheet Sync Started")
    logger.info(f"Time: {datetime.utcnow().isoformat()}")
    logger.info("=" * 50)
    
    results = {}
    
    try:
        sheet_manager = SheetManager()
        
        async with AsyncSessionLocal() as db:
            # 1. Outliers 시트 동기화
            logger.info("📊 Syncing Outliers...")
            try:
                from sqlalchemy import select
                from app.models import OutlierItem
                
                result = await db.execute(
                    select(OutlierItem).order_by(OutlierItem.crawled_at.desc()).limit(500)
                )
                items = result.scalars().all()
                
                rows = [[
                    str(i.id), i.title or "", i.video_url or "", i.platform or "",
                    i.category or "", str(i.view_count or 0), i.status.value, 
                    str(i.crawled_at) if i.crawled_at else ""
                ] for i in items]
                
                if rows:
                    await sheet_manager.upload_rows(
                        sheet_name="VDG_Outlier_Raw",
                        headers=["ID", "Title", "URL", "Platform", "Category", "Views", "Status", "CrawledAt"],
                        rows=rows
                    )
                    results["outliers"] = len(rows)
                    logger.info(f"  ✅ Synced {len(rows)} outliers")
            except Exception as e:
                logger.error(f"  ❌ Outliers sync failed: {e}")
                results["outliers_error"] = str(e)
            
            # 2. Notebook Library 시트 동기화
            logger.info("📚 Syncing Notebook Library...")
            try:
                from app.models import NotebookLibraryEntry
                
                result = await db.execute(
                    select(NotebookLibraryEntry).order_by(NotebookLibraryEntry.created_at.desc()).limit(200)
                )
                entries = result.scalars().all()
                
                rows = [[
                    str(e.id), e.cluster_id or "", e.short_summary or "",
                    str(e.created_at) if e.created_at else ""
                ] for e in entries]
                
                if rows:
                    await sheet_manager.upload_rows(
                        sheet_name="VDG_Notebook_Library",
                        headers=["ID", "ClusterID", "Summary", "CreatedAt"],
                        rows=rows
                    )
                    results["notebook_library"] = len(rows)
                    logger.info(f"  ✅ Synced {len(rows)} entries")
            except Exception as e:
                logger.error(f"  ❌ Notebook Library sync failed: {e}")
                results["notebook_library_error"] = str(e)
            
            # 3. Evidence Snapshots 시트 동기화
            logger.info("📈 Syncing Evidence Snapshots...")
            try:
                from app.models import EvidenceSnapshot
                
                result = await db.execute(
                    select(EvidenceSnapshot).order_by(EvidenceSnapshot.created_at.desc()).limit(100)
                )
                snapshots = result.scalars().all()
                
                rows = [[
                    str(s.id), str(s.parent_node_id), str(s.sample_count or 0),
                    s.top_mutation_type or "", s.period or "",
                    str(s.created_at) if s.created_at else ""
                ] for s in snapshots]
                
                if rows:
                    await sheet_manager.upload_rows(
                        sheet_name="VDG_Evidence",
                        headers=["ID", "ParentNodeID", "SampleCount", "TopMutation", "Period", "CreatedAt"],
                        rows=rows
                    )
                    results["evidence"] = len(rows)
                    logger.info(f"  ✅ Synced {len(rows)} snapshots")
            except Exception as e:
                logger.error(f"  ❌ Evidence sync failed: {e}")
                results["evidence_error"] = str(e)
    
    except Exception as e:
        logger.error(f"❌ Sheet sync initialization failed: {e}")
        results["init_error"] = str(e)
    
    logger.info("=" * 50)
    logger.info(f"Sync Complete: {results}")
    logger.info("=" * 50)
    
    return results


if __name__ == "__main__":
    result = asyncio.run(sync_all_sheets())
    print(f"\nSync Result: {result}")
