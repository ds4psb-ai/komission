#!/usr/bin/env python3
"""
Backfill temporal fields for existing NotebookLibraryEntry records.

Usage:
    python backend/scripts/backfill_temporal_fields.py [--dry-run]
"""
import asyncio
import math
import os
import sys
from datetime import datetime
from typing import Optional

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import NotebookLibraryEntry, OutlierItem


def temporal_phase_for_age(age_days: int) -> str:
    """Map age to temporal phase (T0-T4)"""
    if age_days <= 7:
        return "T0"
    if age_days <= 14:
        return "T1"
    if age_days <= 28:
        return "T2"
    if age_days <= 42:
        return "T3"
    return "T4"


def novelty_decay(age_days: int) -> float:
    """Calculate novelty decay score using exponential decay with floor"""
    return round(max(0.2, math.exp(-age_days / 21)), 4)


def calculate_burstiness(views: int, creator_avg: int) -> float:
    """Calculate burstiness from view/avg ratio"""
    if creator_avg <= 0:
        creator_avg = 1
    ratio = views / creator_avg
    burst = min(1.0, math.log2(ratio + 1) / 3.32)
    return round(burst, 4)


async def backfill(dry_run: bool = False):
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get all entries without temporal_phase
        result = await db.execute(
            select(NotebookLibraryEntry).where(NotebookLibraryEntry.temporal_phase.is_(None))
        )
        entries = result.scalars().all()
        print(f"Found {len(entries)} entries to backfill")
        
        if not entries:
            print("Nothing to do")
            await engine.dispose()
            return
        
        # Preload cluster first_seen dates
        cluster_first_seen: dict[str, datetime] = {}
        cluster_ids = list(set(e.cluster_id for e in entries if e.cluster_id))
        
        for cid in cluster_ids:
            first_result = await db.execute(
                select(func.min(NotebookLibraryEntry.created_at))
                .where(NotebookLibraryEntry.cluster_id == cid)
            )
            first_seen = first_result.scalar_one_or_none()
            if first_seen:
                cluster_first_seen[cid] = first_seen
        
        # Preload related OutlierItems for burstiness
        source_urls = [e.source_url for e in entries if e.source_url]
        outlier_map: dict[str, OutlierItem] = {}
        if source_urls:
            outlier_result = await db.execute(
                select(OutlierItem).where(OutlierItem.video_url.in_(source_urls))
            )
            for item in outlier_result.scalars().all():
                outlier_map[item.video_url] = item
        
        updated = 0
        for entry in entries:
            reference_time = entry.created_at or datetime.utcnow()
            
            # Calculate age from cluster first seen
            if entry.cluster_id and entry.cluster_id in cluster_first_seen:
                first_seen = cluster_first_seen[entry.cluster_id]
                age_days = max(0, (reference_time - first_seen).days)
            else:
                age_days = 0
            
            # Calculate temporal fields
            entry.temporal_phase = temporal_phase_for_age(age_days)
            entry.variant_age_days = age_days
            entry.novelty_decay_score = novelty_decay(age_days)
            
            # Calculate burstiness from related outlier
            outlier = outlier_map.get(entry.source_url)
            if outlier:
                entry.burstiness_index = calculate_burstiness(
                    outlier.view_count or 0,
                    outlier.creator_avg_views or 1
                )
            else:
                # Use None for unknown burstiness (no matching Outlier)
                # to distinguish from 'actually low burst' (0.0)
                entry.burstiness_index = None
            
            updated += 1
            if updated % 50 == 0:
                print(f"  Processed {updated}/{len(entries)}...")
        
        if dry_run:
            print(f"\n[DRY RUN] Would update {updated} entries")
            print(f"Sample: {entries[0].source_url[:50] if entries else 'N/A'}...")
            print(f"  → phase={entries[0].temporal_phase}, age={entries[0].variant_age_days}, decay={entries[0].novelty_decay_score}")
        else:
            await db.commit()
            print(f"\n✅ Backfilled {updated} entries")
    
    await engine.dispose()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("Running in DRY RUN mode (no changes will be saved)\n")
    asyncio.run(backfill(dry_run=dry_run))
