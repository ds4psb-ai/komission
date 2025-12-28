#!/usr/bin/env python3
"""
Phase D: NotebookLM Source Pack Upload Automation

This script automates the ingestion of Source Packs into NotebookLM.
It connects the "Source Pack" (Phase B/C) to the "Pattern Engine" (Phase D).

Features:
- Scans NotebookSourcePack table for entries without notebook_id
- Creates a new NotebookLM notebook for each cluster/phase
- Uploads the Source Pack (Sheet URL) as a source
- Updates database with created notebook_id

Usage:
    python backend/scripts/upload_source_pack_to_notebook.py [--dry-run]
"""

import sys
import os
import asyncio
import argparse
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core import settings
from app.models import NotebookSourcePack
from app.services.notebooklm_api import get_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def upload_pending_packs(dry_run: bool = False):
    """
    Find pending source packs and upload them to NotebookLM.
    """
    # 1. Database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 2. NotebookLM Client
    try:
        # Use simple project ID from settings or env
        client = get_client()
    except Exception as e:
        logger.error(f"Failed to initialize NotebookLM client: {e}")
        logger.error("Please set NOTEBOOKLM_PROJECT_ID and credentials.")
        return

    processed_count = 0
    
    try:
        async with async_session() as db:
            # 3. Find pending packs (no notebook_id)
            # Only process 'sheet' type packs (Google Sheets) as they are URL-based
            stmt = select(NotebookSourcePack).where(
                and_(
                    NotebookSourcePack.notebook_id.is_(None),
                    NotebookSourcePack.pack_type == "sheet"
                )
            ).order_by(NotebookSourcePack.created_at.desc())
            
            result = await db.execute(stmt)
            pending_packs = result.scalars().all()
            
            if not pending_packs:
                logger.info("No pending source packs found.")
                return

            logger.info(f"Found {len(pending_packs)} pending source packs.")
            
            for pack in pending_packs:
                # Construct title: [VDG] {cluster_id} - Phase {temporal_phase}
                # Use cluster_id and phase for naming
                cluster_label = pack.cluster_id
                phase_label = pack.temporal_phase
                title = f"[VDG] {cluster_label} - {phase_label}"
                
                # Sheet URL
                source_url = pack.drive_url
                if not source_url:
                    logger.warning(f"Pack {pack.id} has no drive_url, skipping.")
                    continue
                
                if dry_run:
                    logger.info(f"[DRY-RUN] Would create notebook '{title}' and add source: {source_url}")
                    processed_count += 1
                    continue
                
                try:
                    # 4. Create Notebook
                    logger.info(f"Creating notebook: {title}")
                    notebook = await client.create_notebook(
                        title=title,
                        description=f"VDG Source Pack for {pack.cluster_id} ({pack.temporal_phase})",
                        sources=[source_url]
                    )
                    
                    # 5. Extract Notebook ID
                    # Response format depends on API version, assume 'name' field contains resource path
                    # name: "projects/{project}/locations/{location}/notebooks/{notebook_id}"
                    notebook_name = notebook.get("name", "")
                    notebook_id = notebook_name.split("/")[-1]
                    
                    if not notebook_id:
                        logger.error(f"Failed to extract notebook ID from response: {notebook}")
                        continue
                        
                    # 6. Update DB
                    pack.notebook_id = notebook_id
                    db.add(pack)
                    await db.commit()
                    
                    logger.info(f"✅ Created notebook {notebook_id} for pack {pack.id}")
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process pack {pack.id}: {e}")
                    # Continue to next pack even if one fails
                    continue
                    
    finally:
        await client.close()
        await engine.dispose()
        
    logger.info(f"Complete. Processed {processed_count} packs.")


def main():
    parser = argparse.ArgumentParser(description="Upload pending Source Packs to NotebookLM")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    
    args = parser.parse_args()
    
    asyncio.run(upload_pending_packs(args.dry_run))


if __name__ == "__main__":
    main()
