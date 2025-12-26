#!/usr/bin/env python3
"""
Evidence Batch Scheduler
Based on 16_PDR.md FR-004: Evidence 자동 생성 주기 (주 1회)

이 스크립트는 모든 MASTER 노드에 대해 Evidence 스냅샷을 생성합니다.
cron이나 Cloud Scheduler로 주 1회 실행을 권장합니다.

사용법:
    python scripts/run_evidence_batch.py

Cron 예시 (매주 월요일 오전 3시):
    0 3 * * 1 cd /path/to/backend && ./venv/bin/python scripts/run_evidence_batch.py
"""
import asyncio
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_evidence_batch():
    """모든 MASTER 노드에 대해 Evidence 스냅샷 생성"""
    from app.database import get_db, engine
    from app.models import RemixNode, NodeLayer
    from app.services.evidence_service import evidence_service
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    
    logger.info("=" * 50)
    logger.info("Evidence Batch Scheduler Started")
    logger.info(f"Time: {datetime.utcnow().isoformat()}")
    logger.info("=" * 50)
    
    async with AsyncSession(engine) as db:
        # 1. MASTER 노드 조회
        result = await db.execute(
            select(RemixNode).where(RemixNode.layer == NodeLayer.MASTER)
        )
        master_nodes = result.scalars().all()
        
        logger.info(f"Found {len(master_nodes)} MASTER nodes")
        
        success_count = 0
        error_count = 0
        
        for node in master_nodes:
            try:
                # 2. Evidence 스냅샷 생성
                snapshot = await evidence_service.create_evidence_snapshot(
                    db=db,
                    parent_node_id=node.node_id,
                    period="4w"  # 기본 4주
                )
                
                if snapshot:
                    logger.info(f"✅ Created evidence for {node.node_id}: {snapshot.sample_count} samples")
                    success_count += 1
                else:
                    logger.warning(f"⚠️ No children for {node.node_id}, skipped")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {node.node_id}: {e}")
                error_count += 1
        
        logger.info("=" * 50)
        logger.info(f"Batch Complete: {success_count} success, {error_count} errors")
        logger.info("=" * 50)
        
        return {"success": success_count, "errors": error_count}


if __name__ == "__main__":
    result = asyncio.run(run_evidence_batch())
    print(f"\nBatch Result: {result}")
