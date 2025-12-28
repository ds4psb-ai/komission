"""
run_youtube_analysis_local.py

Local-only YouTube VDG analysis script.
Uses YouTube Data API for comments + yt-dlp with browser cookies for video download.
Outputs to production DB with the same schema as TikTok.

Usage:
    # Single URL
    python scripts/run_youtube_analysis_local.py --url "https://www.youtube.com/shorts/xxx"
    
    # By OutlierItem ID
    python scripts/run_youtube_analysis_local.py --item-id "uuid-here"
    
    # Batch pending YouTube items
    python scripts/run_youtube_analysis_local.py --batch --limit 5
"""
import asyncio
import os
import sys
import argparse
import uuid
from typing import Optional, List, Dict, Any

# Add backend directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import OutlierItem, OutlierItemStatus, OutlierSource, RemixNode, NotebookLibraryEntry, EvidenceSnapshot
from app.services.gemini_pipeline import gemini_pipeline
from app.services.comment_extractor import extract_best_comments
from app.utils.time import utcnow


async def get_or_create_youtube_source(db: AsyncSession) -> uuid.UUID:
    """Get or create YouTube outlier source."""
    stmt = select(OutlierSource).where(OutlierSource.name == "youtube_local")
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        source = OutlierSource(
            name="youtube_local",
            base_url="https://www.youtube.com",
            auth_type="api_key",
            is_active=True
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
    
    return source.id


async def create_outlier_item_from_url(
    db: AsyncSession,
    video_url: str,
    source_id: uuid.UUID
) -> OutlierItem:
    """Create OutlierItem from YouTube URL."""
    import re
    
    # Extract video ID
    patterns = [
        r'youtube\.com/shorts/([a-zA-Z0-9_-]+)',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)',
    ]
    
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, video_url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {video_url}")
    
    # Check if already exists
    stmt = select(OutlierItem).where(OutlierItem.external_id == video_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        print(f"♻️ Using existing OutlierItem: {existing.id}")
        return existing
    
    # Normalize URL to shorts format
    normalized_url = f"https://www.youtube.com/shorts/{video_id}"
    
    item = OutlierItem(
        source_id=source_id,
        external_id=video_id,
        video_url=normalized_url,
        platform="youtube",
        category="shorts",
        status=OutlierItemStatus.PENDING,
        analysis_status="pending"
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    print(f"✅ Created OutlierItem: {item.id}")
    return item


async def analyze_youtube_item(
    db: AsyncSession,
    item: OutlierItem,
    dry_run: bool = False
) -> bool:
    """
    Analyze a single YouTube item.
    
    Steps:
    1. Extract comments via YouTube Data API
    2. Download video via yt-dlp with browser cookies
    3. Run Gemini VDG analysis
    4. Save results to DB
    """
    print(f"\n{'='*60}")
    print(f"📹 Analyzing: {item.video_url}")
    print(f"   ID: {item.id}")
    print(f"{'='*60}")
    
    try:
        # 1. Extract comments if not already present
        comments = []
        if item.best_comments:
            print(f"✅ Using existing comments: {len(item.best_comments)}")
            comments = item.best_comments
        else:
            print("📝 Extracting comments via YouTube Data API...")
            comments = await extract_best_comments(item.video_url, "youtube", limit=10)
            if comments:
                item.best_comments = comments
                await db.commit()
                print(f"✅ Extracted {len(comments)} comments")
            else:
                print("⚠️ No comments extracted (continuing anyway)")
        
        if dry_run:
            print("[Dry Run] Skipping VDG analysis")
            return True
        
        # 2. Update status to analyzing
        item.analysis_status = "analyzing"
        await db.commit()
        
        # 3. Generate node_id for tracking
        from datetime import datetime
        node_id = f"youtube_local_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 4. Run Gemini VDG analysis
        print(f"🚀 Starting VDG analysis with {len(comments)} comments...")
        vdg_result = await gemini_pipeline.analyze_video(
            video_url=item.video_url,
            node_id=node_id,
            audience_comments=comments
        )
        
        # 5. Save VDG result
        if not item.raw_payload:
            item.raw_payload = {}
        item.raw_payload['vdg_analysis'] = vdg_result.model_dump()
        item.analysis_status = "completed"
        
        # Update outlier score from VDG
        if vdg_result.hook_genome and vdg_result.hook_genome.strength:
            item.outlier_score = vdg_result.hook_genome.strength
        
        # 6. Run VDG quality validation
        from app.validators.vdg_quality_validator import validate_vdg_quality
        quality_result = validate_vdg_quality(vdg_result.model_dump())
        item.vdg_quality_score = quality_result.score
        item.vdg_quality_valid = quality_result.is_valid
        item.vdg_quality_issues = quality_result.issues
        
        print(f"📊 VDG quality: score={item.vdg_quality_score}, valid={item.vdg_quality_valid}")
        
        await db.commit()
        
        # 7. Create RemixNode if promoted
        if item.status == OutlierItemStatus.PROMOTED and item.promoted_to_node_id:
            stmt = select(RemixNode).where(RemixNode.id == item.promoted_to_node_id)
            result = await db.execute(stmt)
            remix_node = result.scalar_one_or_none()
            if remix_node:
                remix_node.gemini_analysis = vdg_result.model_dump()
                await db.commit()
                print(f"✅ Updated RemixNode: {remix_node.node_id}")
        
        # 8. Create NotebookLibraryEntry
        cluster_id = f"youtube-local-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        notebook_entry = NotebookLibraryEntry(
            source_url=item.video_url,
            platform="youtube",
            category=item.category or "shorts",
            summary={"hook": vdg_result.hook_genome.model_dump() if vdg_result.hook_genome else {}},
            cluster_id=cluster_id,
            analysis_schema=vdg_result.model_dump(),
            schema_version="v3.3"
        )
        db.add(notebook_entry)
        await db.commit()
        print(f"📚 Created NotebookLibraryEntry: {cluster_id}")
        
        # 9. Create EvidenceSnapshot (minimal)
        if item.promoted_to_node_id:
            snapshot = EvidenceSnapshot(
                parent_node_id=item.promoted_to_node_id,
                period="4w",
                depth1_summary={
                    "youtube_local": {
                        "vdg_score": item.vdg_quality_score,
                        "hook_strength": item.outlier_score
                    }
                },
                sample_count=1,
                confidence=item.vdg_quality_score or 0.5
            )
            db.add(snapshot)
            await db.commit()
            print(f"📊 Created EvidenceSnapshot for {item.promoted_to_node_id}")
        
        print(f"\n✅ Analysis complete!")
        print(f"   analysis_status: {item.analysis_status}")
        print(f"   vdg_quality_score: {item.vdg_quality_score}")
        print(f"   outlier_score: {item.outlier_score}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Update status to failed
        item.analysis_status = "failed"
        if not item.raw_payload:
            item.raw_payload = {}
        item.raw_payload['last_error'] = str(e)
        await db.commit()
        
        return False


async def run_batch(limit: int = 5, dry_run: bool = False):
    """Process pending YouTube items in batch."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Fetch pending YouTube items
        stmt = select(OutlierItem).where(
            OutlierItem.platform == "youtube",
            or_(
                OutlierItem.analysis_status == "pending",
                OutlierItem.analysis_status == None
            ),
            OutlierItem.status != OutlierItemStatus.REJECTED
        ).limit(limit)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        if not items:
            print("No pending YouTube items found.")
            return
        
        print(f"Found {len(items)} pending YouTube items.")
        
        success = 0
        failed = 0
        
        for item in items:
            if await analyze_youtube_item(db, item, dry_run):
                success += 1
            else:
                failed += 1
        
        print(f"\n{'='*60}")
        print(f"Batch Complete: {success} success, {failed} failed")
        print(f"{'='*60}")
    
    await engine.dispose()


async def run_single(url: str = None, item_id: str = None, dry_run: bool = False):
    """Process a single YouTube URL or item."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        item = None
        
        if item_id:
            stmt = select(OutlierItem).where(OutlierItem.id == uuid.UUID(item_id))
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()
            if not item:
                print(f"❌ Item not found: {item_id}")
                return
        elif url:
            source_id = await get_or_create_youtube_source(db)
            item = await create_outlier_item_from_url(db, url, source_id)
        else:
            print("❌ Must provide --url or --item-id")
            return
        
        await analyze_youtube_item(db, item, dry_run)
    
    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Local YouTube VDG Analysis")
    parser.add_argument("--url", help="YouTube URL to analyze")
    parser.add_argument("--item-id", help="OutlierItem ID to analyze")
    parser.add_argument("--batch", action="store_true", help="Process pending YouTube items in batch")
    parser.add_argument("--limit", type=int, default=5, help="Batch limit")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without VDG analysis")
    args = parser.parse_args()
    
    if args.batch:
        asyncio.run(run_batch(limit=args.limit, dry_run=args.dry_run))
    elif args.url or args.item_id:
        asyncio.run(run_single(url=args.url, item_id=args.item_id, dry_run=args.dry_run))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
