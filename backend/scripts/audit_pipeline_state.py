#!/usr/bin/env python
"""
Pipeline State Audit (read-only)

Validates non-VDG invariants:
- promoted/rejected items must have curation decisions
- promoted items must have promoted_to_node_id
- analysis_status should not advance without promotion
- rule_followed/matched_rule_id consistency
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from sqlalchemy import exists, func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models import CurationDecision, OutlierItem, OutlierItemStatus  # noqa: E402

NON_PENDING_ANALYSIS_STATUS = [
    "approved",
    "analyzing",
    "completed",
    "comments_pending_review",
    "comments_failed",
    "comments_ready",
    "skipped",
]


async def _count_and_sample(
    db: AsyncSession,
    query,
    limit: int,
) -> Tuple[int, List[Tuple]]:
    count = await db.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await db.execute(query.limit(limit))).all()
    return int(count or 0), rows


def _print_section(title: str, count: int, rows: Sequence[Tuple]) -> None:
    print(f"\n== {title} ==")
    print(f"- count: {count}")
    if rows:
        print("- samples:")
        for row in rows:
            print(f"  - {row}")
    else:
        print("- samples: none")


async def audit(database_url: str, limit: int) -> int:
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    issues = 0
    async with async_session() as db:
        # 1) Promoted items missing promoted_to_node_id
        query = select(OutlierItem.id, OutlierItem.video_url).where(
            OutlierItem.status == OutlierItemStatus.PROMOTED,
            OutlierItem.promoted_to_node_id.is_(None),
        )
        count, rows = await _count_and_sample(db, query, limit)
        _print_section("PROMOTED without promoted_to_node_id", count, rows)
        issues += count

        # 2) Analysis status advanced without promotion
        query = select(
            OutlierItem.id,
            OutlierItem.analysis_status,
            OutlierItem.status,
        ).where(
            OutlierItem.analysis_status.in_(NON_PENDING_ANALYSIS_STATUS),
            OutlierItem.promoted_to_node_id.is_(None),
        )
        count, rows = await _count_and_sample(db, query, limit)
        _print_section("analysis_status advanced without promotion", count, rows)
        issues += count

        # 3) Promoted items without normal/campaign decision
        promoted_missing_decision = select(
            OutlierItem.id,
            OutlierItem.video_url,
        ).where(
            OutlierItem.status == OutlierItemStatus.PROMOTED,
            ~exists(
                select(CurationDecision.id).where(
                    CurationDecision.outlier_item_id == OutlierItem.id,
                    CurationDecision.decision_type.in_(["normal", "campaign"]),
                )
            ),
        )
        count, rows = await _count_and_sample(db, promoted_missing_decision, limit)
        _print_section("PROMOTED without normal/campaign decision", count, rows)
        issues += count

        # 4) Rejected items without rejected decision
        rejected_missing_decision = select(
            OutlierItem.id,
            OutlierItem.video_url,
        ).where(
            OutlierItem.status == OutlierItemStatus.REJECTED,
            ~exists(
                select(CurationDecision.id).where(
                    CurationDecision.outlier_item_id == OutlierItem.id,
                    CurationDecision.decision_type == "rejected",
                )
            ),
        )
        count, rows = await _count_and_sample(db, rejected_missing_decision, limit)
        _print_section("REJECTED without rejected decision", count, rows)
        issues += count

        # 5) rule_followed / matched_rule_id mismatch
        mismatch_query = select(
            CurationDecision.id,
            CurationDecision.matched_rule_id,
            CurationDecision.rule_followed,
        ).where(
            (CurationDecision.matched_rule_id.isnot(None) & CurationDecision.rule_followed.is_(None))
            | (CurationDecision.matched_rule_id.is_(None) & CurationDecision.rule_followed.isnot(None))
        )
        count, rows = await _count_and_sample(db, mismatch_query, limit)
        _print_section("Decision rule_followed mismatch", count, rows)
        issues += count

        # 6) vdg_snapshot without extracted_features (should be updated together)
        vdg_mismatch_query = select(
            CurationDecision.id,
            CurationDecision.outlier_item_id,
        ).where(
            CurationDecision.vdg_snapshot.isnot(None),
            CurationDecision.extracted_features.is_(None),
        )
        count, rows = await _count_and_sample(db, vdg_mismatch_query, limit)
        _print_section("Decision has vdg_snapshot but no extracted_features", count, rows)
        issues += count

    await engine.dispose()
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit non-VDG pipeline state")
    parser.add_argument("--limit", type=int, default=20, help="Max samples per check")
    parser.add_argument("--fail-on-issue", action="store_true", help="Exit non-zero on issues")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        from app.database import DATABASE_URL as DEFAULT_DB_URL  # noqa: E402

        database_url = DEFAULT_DB_URL

    issues = asyncio.run(audit(database_url, limit=args.limit))
    print(f"\nTotal issues: {issues}")
    if args.fail_on_issue and issues > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
