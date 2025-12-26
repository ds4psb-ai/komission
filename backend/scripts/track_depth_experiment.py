"""
Depth Experiment Tracking Script
backend/scripts/track_depth_experiment.py

14-day tracking for Parent pilot experiments.
Based on Phase 4 requirements: Depth1 실험 실행 + 14일 추적

Usage:
    python scripts/track_depth_experiment.py --parent-id PARENT_ID
    python scripts/track_depth_experiment.py --all --days 14
"""
import sys
import os
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def track_parent_experiment(
    parent_id: str,
    days: int = 14,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Track a single parent's depth experiment progress.
    
    Args:
        parent_id: The parent node ID to track
        days: Number of days to look back (default 14)
        dry_run: If True, don't write to DB
    
    Returns:
        Tracking summary dict
    """
    from app.database import async_session_maker
    from app.models import RemixNode, EvidenceSnapshot
    from sqlalchemy import select, func, desc
    
    async with async_session_maker() as db:
        # Get parent node
        result = await db.execute(
            select(RemixNode).where(RemixNode.node_id == parent_id)
        )
        parent = result.scalar_one_or_none()
        
        if not parent:
            logger.error(f"Parent not found: {parent_id}")
            return {"error": f"Parent not found: {parent_id}"}
        
        logger.info(f"📊 Tracking: {parent.title}")
        
        # Get evidence snapshots for this parent
        cutoff = datetime.utcnow() - timedelta(days=days)
        evidence = await db.execute(
            select(EvidenceSnapshot)
            .where(EvidenceSnapshot.parent_node_id == parent.id)
            .where(EvidenceSnapshot.created_at >= cutoff)
            .order_by(desc(EvidenceSnapshot.created_at))
        )
        snapshots = evidence.scalars().all()
        
        if not snapshots:
            logger.warning(f"No evidence found in last {days} days")
            return {
                "parent_id": parent_id,
                "title": parent.title,
                "days_tracked": 0,
                "snapshots": 0,
                "status": "no_data"
            }
        
        # Calculate metrics
        first_date = min(s.created_at for s in snapshots)
        last_date = max(s.created_at for s in snapshots)
        days_tracked = (last_date - first_date).days + 1
        
        # Aggregate pattern performance
        patterns: Dict[str, List[float]] = {}
        for snap in snapshots:
            if snap.top_mutation_pattern:
                key = snap.top_mutation_pattern
                if key not in patterns:
                    patterns[key] = []
                if snap.confidence:
                    patterns[key].append(snap.confidence)
        
        # Find top pattern
        top_pattern = None
        top_score = 0.0
        for pattern, scores in patterns.items():
            avg = sum(scores) / len(scores) if scores else 0
            if avg > top_score:
                top_score = avg
                top_pattern = pattern
        
        # Determine experiment status
        avg_confidence = sum(s.confidence or 0 for s in snapshots) / len(snapshots)
        
        if days_tracked >= 14 and avg_confidence >= 0.8:
            status = "complete"
        elif days_tracked >= 14:
            status = "needs_decision"
        else:
            status = "tracking"
        
        summary = {
            "parent_id": parent_id,
            "title": parent.title,
            "days_tracked": days_tracked,
            "snapshots": len(snapshots),
            "top_pattern": top_pattern,
            "top_score": round(top_score, 3),
            "avg_confidence": round(avg_confidence, 3),
            "status": status,
            "first_date": first_date.isoformat(),
            "last_date": last_date.isoformat(),
        }
        
        logger.info(f"  Days: {days_tracked}")
        logger.info(f"  Snapshots: {len(snapshots)}")
        logger.info(f"  Top Pattern: {top_pattern} ({top_score:.2%})")
        logger.info(f"  Status: {status}")
        
        return summary


async def track_all_experiments(days: int = 14) -> List[Dict[str, Any]]:
    """Track all active parent experiments."""
    from app.database import async_session_maker
    from app.models import RemixNode
    from sqlalchemy import select
    
    async with async_session_maker() as db:
        # Get all master nodes
        result = await db.execute(
            select(RemixNode).where(RemixNode.layer == "master")
        )
        parents = result.scalars().all()
        
        logger.info(f"Found {len(parents)} parent nodes")
        
        summaries = []
        for parent in parents:
            summary = await track_parent_experiment(parent.node_id, days)
            summaries.append(summary)
        
        return summaries


def print_report(summaries: List[Dict[str, Any]]):
    """Print formatted tracking report."""
    print("\n" + "=" * 60)
    print("📊 DEPTH EXPERIMENT TRACKING REPORT")
    print("=" * 60)
    
    # Stats
    tracking = [s for s in summaries if s.get("status") == "tracking"]
    complete = [s for s in summaries if s.get("status") == "complete"]
    needs_decision = [s for s in summaries if s.get("status") == "needs_decision"]
    
    print(f"\n📈 Summary:")
    print(f"  Total Parents: {len(summaries)}")
    print(f"  🔄 Tracking: {len(tracking)}")
    print(f"  ✅ Complete: {len(complete)}")
    print(f"  ⚠️ Needs Decision: {len(needs_decision)}")
    
    # Details
    if complete:
        print(f"\n✅ COMPLETE ({len(complete)}):")
        for s in complete:
            print(f"  - {s['title'][:30]}... | {s['days_tracked']}d | {s['top_pattern']} ({s['top_score']:.0%})")
    
    if needs_decision:
        print(f"\n⚠️ NEEDS DECISION ({len(needs_decision)}):")
        for s in needs_decision:
            print(f"  - {s['title'][:30]}... | {s['days_tracked']}d | conf: {s['avg_confidence']:.0%}")
    
    if tracking:
        print(f"\n🔄 TRACKING ({len(tracking)}):")
        for s in tracking[:5]:  # Show first 5
            print(f"  - {s['title'][:30]}... | {s['days_tracked']}d remaining")
        if len(tracking) > 5:
            print(f"  ... and {len(tracking) - 5} more")
    
    print("\n" + "=" * 60)


async def main():
    parser = argparse.ArgumentParser(description="Track depth experiments")
    parser.add_argument("--parent-id", help="Specific parent to track")
    parser.add_argument("--all", action="store_true", help="Track all parents")
    parser.add_argument("--days", type=int, default=14, help="Days to look back")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if args.parent_id:
        summary = await track_parent_experiment(args.parent_id, args.days)
        if args.json:
            import json
            print(json.dumps(summary, indent=2))
        else:
            print_report([summary])
    
    elif args.all:
        summaries = await track_all_experiments(args.days)
        if args.json:
            import json
            print(json.dumps(summaries, indent=2))
        else:
            print_report(summaries)
    
    else:
        print("Usage: python track_depth_experiment.py --parent-id ID")
        print("       python track_depth_experiment.py --all")


if __name__ == "__main__":
    asyncio.run(main())
