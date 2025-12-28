"""
run_outlier_analysis_batch.py

Batch executes the Gemini Analysis Pipeline for pending OutlierItems.
Updates the database with VDG analysis results.
"""
import asyncio
import os
import sys
import argparse
from typing import List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

from app.config import settings
from app.models import OutlierItem, OutlierItemStatus
from app.services.gemini_pipeline import gemini_pipeline

async def process_batch(limit: int = 10, dry_run: bool = False):
    """
    Process a batch of pending outlier items.
    """
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 1. Fetch pending items
        # Criteria: analysis_status is pending/null AND status is not rejected
        stmt = select(OutlierItem).where(
            or_(
                OutlierItem.analysis_status == 'pending',
                OutlierItem.analysis_status == None,
            ),
            OutlierItem.status != OutlierItemStatus.REJECTED
        ).limit(limit)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        if not items:
            print("No pending items found.")
            return

        print(f"Found {len(items)} pending items. Starting analysis...")
        
        success_count = 0
        failure_count = 0

        for item in items:
            print(f"Analyzing {item.id} - {item.title} ({item.video_url})")
            
            if dry_run:
                print("  [Dry Run] Skipping API call.")
                continue

            try:
                # Update status to 'analyzing'
                item.analysis_status = 'analyzing'
                await db.commit()

                # Call Gemini Pipeline
                # We use the item ID as the node_id for tracking
                vdg_result = await gemini_pipeline.analyze_video(
                    video_url=item.video_url,
                    node_id=str(item.id)
                )

                # Store result
                if not item.raw_payload:
                    item.raw_payload = {}
                
                # Convert VDG model to dict
                item.raw_payload['vdg_analysis'] = vdg_result.model_dump()
                item.analysis_status = 'completed'
                
                # Update outlier score from VDG if available
                if vdg_result.hook_genome and vdg_result.hook_genome.strength:
                    item.outlier_score = vdg_result.hook_genome.strength

                await db.commit()
                print(f"  ✅ Success. Hook Score: {item.outlier_score}")
                success_count += 1

            except Exception as e:
                print(f"  ❌ Failed: {e}")
                
                # Reset status to failed so we can retry or investigate
                await db.rollback() # Rollback the 'analyzing' state if needed, but we want to capture failure
                
                # Start fresh transaction for error update
                item.analysis_status = 'failed'
                # Optionally store error in raw_payload or a separate field
                if not item.raw_payload:
                    item.raw_payload = {}
                item.raw_payload['last_error'] = str(e)
                
                await db.commit()
                failure_count += 1
                
    await engine.dispose()
    print("\nBatch Complete.")
    print(f"Success: {success_count}")
    print(f"Failed: {failure_count}")

def main():
    parser = argparse.ArgumentParser(description="Run Outlier Analysis Batch")
    parser.add_argument("--limit", type=int, default=10, help="Number of items to process")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without calling API")
    args = parser.parse_args()

    asyncio.run(process_batch(limit=args.limit, dry_run=args.dry_run))

if __name__ == "__main__":
    main()
