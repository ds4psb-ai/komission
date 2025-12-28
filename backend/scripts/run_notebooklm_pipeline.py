#!/usr/bin/env python3
"""
NotebookLM E2E Automation Pipeline (v2.0)

Complete automated workflow:
1. Fetch OutlierItems from DB (with VDG analysis)
2. Format as structured text sources
3. Create NotebookLM notebook via API
4. Add sources directly (bypasses Google Sheets)
5. Record NotebookSourcePack in DB

Usage:
    # Recent items (default: last 7 days, top 20 by score)
    python scripts/run_notebooklm_pipeline.py --recent --limit 20
    
    # Dry-run
    python scripts/run_notebooklm_pipeline.py --recent --dry-run
    
    # Specific category
    python scripts/run_notebooklm_pipeline.py --category food --limit 10

Environment:
    gcloud auth login ted.taeeun.kim@gmail.com
    gcloud config set project algebraic-envoy-456610-h8
"""
import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, ".env"))

from app.config import settings
from app.models import OutlierItem, NotebookSourcePack
from app.services.notebooklm_api import NotebookLMClient, get_client
from app.utils.time import utcnow

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Project configuration
PROJECT_ID = "algebraic-envoy-456610-h8"
PROJECT_NUMBER = "297976838198"


def format_outlier_as_source(item: OutlierItem) -> Dict[str, str]:
    """Format OutlierItem into structured text for NotebookLM source."""
    raw = item.raw_payload or {}
    vdg = raw.get("vdg_analysis", {})
    
    sections = []
    
    # Header
    title = item.title or "Untitled"
    sections.append(f"# Viral Content Analysis: {title}")
    sections.append("")
    
    # Basic Info
    sections.append("## Basic Information")
    sections.append(f"- **Platform**: {item.platform}")
    sections.append(f"- **Category**: {item.category}")
    sections.append(f"- **View Count**: {item.view_count:,}")
    sections.append(f"- **Outlier Score**: {item.outlier_score}")
    sections.append(f"- **Outlier Tier**: {item.outlier_tier}")
    if item.video_url:
        sections.append(f"- **URL**: {item.video_url}")
    sections.append("")
    
    # Hook Genome
    hook = vdg.get("hook_genome", {})
    if hook:
        sections.append("## Hook Pattern Analysis")
        sections.append(f"- **Pattern**: {hook.get('pattern', 'Unknown')}")
        sections.append(f"- **Delivery**: {hook.get('delivery', 'Unknown')}")
        sections.append(f"- **Strength**: {hook.get('strength', 'N/A')}/10")
        if hook.get("hook_summary"):
            sections.append(f"- **Summary**: {hook.get('hook_summary')}")
        
        # Microbeats (can be list or dict)
        microbeats = hook.get("microbeats", {})
        if microbeats:
            sections.append("")
            sections.append("### Microbeat Sequence")
            if isinstance(microbeats, dict):
                if microbeats.get("start"):
                    sections.append(f"- **Start (0-3s)**: {microbeats['start']}")
                if microbeats.get("build"):
                    sections.append(f"- **Build (3-6s)**: {microbeats['build']}")
                if microbeats.get("punch"):
                    sections.append(f"- **Punch (6-10s)**: {microbeats['punch']}")
            elif isinstance(microbeats, list):
                for i, beat in enumerate(microbeats[:5], 1):
                    if isinstance(beat, dict):
                        sections.append(f"- **Beat {i}**: {beat.get('description', beat)}")
                    else:
                        sections.append(f"- **Beat {i}**: {beat}")
        sections.append("")
    
    # Intent Layer
    intent = vdg.get("intent_layer", {})
    if intent:
        sections.append("## Psychological Intent")
        if intent.get("hook_trigger"):
            sections.append(f"- **Hook Trigger**: {intent['hook_trigger']}")
        if intent.get("retention_strategy"):
            sections.append(f"- **Retention Strategy**: {intent['retention_strategy']}")
        sections.append("")
    
    # Virality Analysis
    virality = hook.get("virality_analysis", {}) if hook else {}
    if virality:
        sections.append("## Virality Factors")
        for key, value in virality.items():
            if value:
                sections.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        sections.append("")
    
    # Capsule Brief
    capsule = vdg.get("capsule_brief", {})
    if capsule:
        sections.append("## Replication Guide")
        if capsule.get("hook_script"):
            sections.append(f"**Hook Script**: {capsule['hook_script']}")
        if capsule.get("do_not"):
            sections.append(f"**Avoid**: {', '.join(capsule['do_not'])}")
        sections.append("")
    
    # Full VDG JSON (truncated)
    if vdg:
        sections.append("## Full Analysis JSON")
        sections.append("```json")
        sections.append(json.dumps(vdg, ensure_ascii=False, indent=2)[:8000])
        sections.append("```")
    
    return {
        "sourceName": f"{item.platform}_{item.category}_{title[:40]}",
        "content": "\n".join(sections)
    }


async def fetch_outliers(
    db: AsyncSession,
    category: Optional[str] = None,
    limit: int = 20,
    days: int = 7,
    min_score: float = 0.0,
) -> List[OutlierItem]:
    """Fetch OutlierItems from database."""
    query = select(OutlierItem)
    
    # Time filter
    cutoff = datetime.now() - timedelta(days=days)
    query = query.where(OutlierItem.crawled_at >= cutoff)
    
    # Category filter
    if category:
        query = query.where(OutlierItem.category == category)
    
    # Score filter
    if min_score > 0:
        query = query.where(OutlierItem.outlier_score >= min_score)
    
    # Order by score and limit
    query = query.order_by(OutlierItem.outlier_score.desc()).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def save_source_pack(
    db: AsyncSession,
    notebook_id: str,
    entry_count: int,
    category: str = "mixed",
) -> NotebookSourcePack:
    """Save NotebookSourcePack to database."""
    now = utcnow().replace(tzinfo=None)
    
    inputs_hash = hashlib.sha256(
        f"{notebook_id}:{entry_count}:{now.isoformat()}".encode()
    ).hexdigest()
    
    pack = NotebookSourcePack(
        cluster_id=f"auto_{category}_{now.strftime('%Y%m%d')}",
        temporal_phase="auto",
        pack_type="notebooklm_api_v2",
        drive_file_id=notebook_id,
        drive_url=f"https://notebooklm.google.com/notebook/{notebook_id}?project={PROJECT_NUMBER}",
        inputs_hash=inputs_hash,
        source_version="v2.0-api",
        entry_count=entry_count,
        pack_mode="auto",
        schema_version="v3.3",
        notebook_id=notebook_id,  # Phase D: NotebookLM Integration linkage
        created_at=now,
        updated_at=now,
    )
    
    db.add(pack)
    await db.commit()
    await db.refresh(pack)
    
    return pack


async def run_pipeline(args: argparse.Namespace) -> None:
    """Execute the E2E pipeline."""
    logger.info("🚀 NotebookLM Automation Pipeline v2.0")
    
    # Database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Step 1: Fetch OutlierItems
            logger.info(f"Fetching items (category={args.category}, limit={args.limit}, days={args.days})")
            items = await fetch_outliers(
                db,
                category=args.category,
                limit=args.limit,
                days=args.days,
            )
            
            if not items:
                logger.warning("No OutlierItems found")
                return
            
            logger.info(f"📊 Found {len(items)} OutlierItems")
            
            # Step 2: Format as sources
            sources = []
            for item in items:
                try:
                    source = format_outlier_as_source(item)
                    sources.append(source)
                except Exception as e:
                    logger.warning(f"Failed to format item {item.id}: {e}")
            
            logger.info(f"📝 Formatted {len(sources)} sources")
            
            if args.dry_run:
                logger.info("[DRY-RUN] Preview:")
                for s in sources[:3]:
                    logger.info(f"  - {s['sourceName']}: {len(s['content'])} chars")
                return
            
            # Step 3: Create NotebookLM notebook and add sources
            client = get_client(
                project_id=PROJECT_ID,
                project_number=PROJECT_NUMBER,
            )
            
            try:
                date_str = datetime.now().strftime("%Y-%m-%d")
                cat_str = args.category or "mixed"
                title = f"Komission Auto - {cat_str} - {date_str}"
                
                notebook = await client.create_notebook(title=title)
                notebook_id = notebook.get("notebookId")
                logger.info(f"✅ Created notebook: {notebook_id}")
                
                # Add sources in batches
                batch_size = 10
                total_added = 0
                
                for i in range(0, len(sources), batch_size):
                    batch = sources[i:i + batch_size]
                    result = await client.add_sources(
                        notebook_id=notebook_id,
                        source_urls=[],
                        source_contents=[{
                            "displayName": s["sourceName"],
                            "content": s["content"]
                        } for s in batch]
                    )
                    added = len(result.get("sources", []))
                    total_added += added
                    logger.info(f"  Batch {i // batch_size + 1}: {added} sources")
                
                logger.info(f"✅ Total sources: {total_added}")
                
                # Step 4: Save to database
                if not args.no_db:
                    pack = await save_source_pack(
                        db,
                        notebook_id=notebook_id,
                        entry_count=total_added,
                        category=cat_str,
                    )
                    logger.info(f"✅ Saved NotebookSourcePack: {pack.id}")
                
                # Summary
                notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}?project={PROJECT_NUMBER}"
                print("\n" + "=" * 60)
                print("🎉 PIPELINE COMPLETE!")
                print("=" * 60)
                print(f"📓 Notebook: {title}")
                print(f"🔗 URL: {notebook_url}")
                print(f"📊 Sources: {total_added} items")
                print("=" * 60)
                
            finally:
                await client.close()
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="NotebookLM E2E Automation Pipeline v2.0")
    parser.add_argument("--category", help="Filter by category (food, beauty, etc.)")
    parser.add_argument("--limit", type=int, default=20, help="Max items (default: 20)")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--recent", action="store_true", help="Get recent items (alias for --days 7)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--no-db", action="store_true", help="Skip database recording")
    
    args = parser.parse_args()
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
