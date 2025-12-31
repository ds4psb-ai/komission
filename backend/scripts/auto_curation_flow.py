#!/usr/bin/env python
"""
Auto curation flow (non-VDG):
- select pending outliers
- promote or reject based on simple rules
- record curation decisions

Defaults to dry-run. Use --commit to apply.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models import (  # noqa: E402
    CurationDecisionType,
    NodeGovernance,
    NodeLayer,
    NodePermission,
    OutlierItem,
    OutlierItemStatus,
    RemixNode,
    User,
)
from app.services.curation_service import record_curation_decision  # noqa: E402
from app.services.remix_nodes import generate_remix_node_id  # noqa: E402


async def _get_or_create_curator(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(
        email=email,
        firebase_uid=f"script_{uuid.uuid4().hex}",
        name="Curation Script",
        role="user",
        is_active=True,
        is_curator=True,
    )
    db.add(user)
    await db.flush()
    return user


def _should_promote(item: OutlierItem, promote_tiers: List[str]) -> bool:
    if item.outlier_tier and item.outlier_tier.upper() in promote_tiers:
        return True
    return False


def _is_campaign(item: OutlierItem, campaign_tiers: List[str], campaign_score: float) -> bool:
    if item.outlier_tier and item.outlier_tier.upper() in campaign_tiers:
        return True
    if item.outlier_score is not None and item.outlier_score >= campaign_score:
        return True
    return False


async def _promote_item(
    db: AsyncSession,
    *,
    item: OutlierItem,
    curator: User,
    campaign_eligible: bool,
) -> None:
    node_id = await generate_remix_node_id(db)
    node = RemixNode(
        node_id=node_id,
        title=item.title or "Untitled Outlier",
        source_video_url=item.video_url,
        platform=item.platform,
        layer=NodeLayer.MASTER,
        permission=NodePermission.READ_ONLY,
        governed_by=NodeGovernance.OPEN_COMMUNITY,
        view_count=item.view_count or 0,
        created_by=curator.id,
        owner_type=curator.role,
    )
    db.add(node)
    await db.flush()

    item.status = OutlierItemStatus.PROMOTED
    item.promoted_to_node_id = node.id
    item.campaign_eligible = campaign_eligible

    decision_type = (
        CurationDecisionType.CAMPAIGN if campaign_eligible else CurationDecisionType.NORMAL
    )
    await record_curation_decision(
        db,
        outlier_item_id=item.id,
        remix_node_id=node.id,
        curator_id=curator.id,
        decision_type=decision_type,
    )


async def _reject_item(
    db: AsyncSession,
    *,
    item: OutlierItem,
    curator: User,
) -> None:
    item.status = OutlierItemStatus.REJECTED
    await record_curation_decision(
        db,
        outlier_item_id=item.id,
        remix_node_id=None,
        curator_id=curator.id,
        decision_type=CurationDecisionType.REJECTED,
    )


async def run(
    database_url: str,
    *,
    limit: int,
    platform: Optional[str],
    category: Optional[str],
    promote_tiers: List[str],
    campaign_tiers: List[str],
    campaign_score: float,
    mode: str,
    curator_email: str,
    commit: bool,
) -> int:
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    promoted = 0
    rejected = 0
    skipped = 0

    async with async_session() as db:
        curator = await _get_or_create_curator(db, curator_email)

        query = select(OutlierItem).where(OutlierItem.status == OutlierItemStatus.PENDING)
        if platform:
            query = query.where(OutlierItem.platform == platform)
        if category:
            query = query.where(OutlierItem.category == category)
        query = query.order_by(OutlierItem.outlier_score.desc().nullslast())
        query = query.limit(limit)

        result = await db.execute(query)
        items = result.scalars().all()

        if not items:
            print("No pending outliers found.")
            await engine.dispose()
            return 0

        for item in items:
            decision = "skip"
            campaign_eligible = False

            if mode == "promote":
                decision = "promote"
            elif mode == "reject":
                decision = "reject"
            else:
                if _should_promote(item, promote_tiers):
                    decision = "promote"
                    campaign_eligible = _is_campaign(item, campaign_tiers, campaign_score)
                else:
                    decision = "reject"

            print(
                f"[{decision.upper()}] {item.id} | tier={item.outlier_tier} "
                f"score={item.outlier_score} url={item.video_url}"
            )

            if not commit:
                skipped += 1
                continue

            if decision == "promote":
                await _promote_item(db, item=item, curator=curator, campaign_eligible=campaign_eligible)
                promoted += 1
            elif decision == "reject":
                await _reject_item(db, item=item, curator=curator)
                rejected += 1
            else:
                skipped += 1

        if commit:
            await db.commit()

    await engine.dispose()
    print(f"\nSummary: promoted={promoted}, rejected={rejected}, skipped={skipped}")
    return promoted + rejected


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto curation flow (non-VDG)")
    parser.add_argument("--limit", type=int, default=10, help="Max items to process")
    parser.add_argument("--platform", type=str, default=None, help="Filter by platform")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument("--mode", choices=["auto", "promote", "reject"], default="auto")
    parser.add_argument("--promote-tiers", default="S,A", help="Comma-separated tiers to promote")
    parser.add_argument("--campaign-tiers", default="S", help="Comma-separated tiers to mark campaign")
    parser.add_argument("--campaign-score", type=float, default=100.0, help="Score threshold for campaign")
    parser.add_argument("--curator-email", default="demo@komission.ai", help="Curator email")
    parser.add_argument("--commit", action="store_true", help="Apply changes (default dry-run)")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        from app.database import DATABASE_URL as DEFAULT_DB_URL  # noqa: E402

        database_url = DEFAULT_DB_URL

    promote_tiers = [t.strip().upper() for t in args.promote_tiers.split(",") if t.strip()]
    campaign_tiers = [t.strip().upper() for t in args.campaign_tiers.split(",") if t.strip()]

    processed = asyncio.run(
        run(
            database_url,
            limit=args.limit,
            platform=args.platform,
            category=args.category,
            promote_tiers=promote_tiers,
            campaign_tiers=campaign_tiers,
            campaign_score=args.campaign_score,
            mode=args.mode,
            curator_email=args.curator_email,
            commit=args.commit,
        )
    )
    return 0 if processed >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
