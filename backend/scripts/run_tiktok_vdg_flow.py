#!/usr/bin/env python3
"""
End-to-end TikTok VDG flow (DB → comments → Gemini → DB).

Creates:
- OutlierSource (if missing)
- User (if missing)
- RemixNode
- OutlierItem (promoted)
Then runs the VDG analysis pipeline with comment extraction.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import select


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.database import async_session_maker
from app.models import (
    User,
    OutlierSource,
    OutlierItem,
    OutlierItemStatus,
    RemixNode,
)
from app.routers.outliers import _run_vdg_analysis_with_comments


VIDEO_URL = os.getenv("TIKTOK_TEST_URL", "https://vt.tiktok.com/ZSPKdL6gv/")
SOURCE_NAME = os.getenv("TIKTOK_TEST_SOURCE", "ManualTikTokTest")
CATEGORY = os.getenv("TIKTOK_TEST_CATEGORY", "meme")
TEST_EMAIL = os.getenv("TIKTOK_TEST_EMAIL", "ted.taeeun.kim@gmail.com")


async def ensure_user(db) -> User:
    result = await db.execute(select(User).where(User.email == TEST_EMAIL))
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(
        firebase_uid=f"local-{uuid.uuid4()}",
        email=TEST_EMAIL,
        name="Local Test User",
        role="admin",
        is_curator=True,
        curator_since=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def ensure_source(db) -> OutlierSource:
    result = await db.execute(select(OutlierSource).where(OutlierSource.name == SOURCE_NAME))
    source = result.scalar_one_or_none()
    if source:
        return source

    source = OutlierSource(
        name=SOURCE_NAME,
        base_url="https://www.tiktok.com",
        auth_type="session",
        auth_config={"note": "manual test source"},
        crawl_interval_hours=24,
        is_active=True,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def main() -> None:
    async with async_session_maker() as db:
        user = await ensure_user(db)
        source = await ensure_source(db)

        node_id = f"tiktok_test_{int(time.time())}"
        node = RemixNode(
            node_id=node_id,
            title="TikTok Test Node",
            created_by=user.id,
            owner_type="admin",
            platform="tiktok",
            source_video_url=VIDEO_URL,
        )
        db.add(node)
        await db.commit()
        await db.refresh(node)

        item = OutlierItem(
            source_id=source.id,
            external_id=f"tiktok-test-{uuid.uuid4()}",
            video_url=VIDEO_URL,
            title="TikTok Test Outlier",
            platform="tiktok",
            category=CATEGORY,
            view_count=1,
            status=OutlierItemStatus.PROMOTED,
            promoted_to_node_id=node.id,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)

        print(f"Running VDG analysis for {node.node_id} / item {item.id}")

    # Run analysis in background-style task
    await _run_vdg_analysis_with_comments(
        item_id=str(item.id),
        node_id=node.node_id,
        video_url=VIDEO_URL,
        platform="tiktok",
    )

    # Verify results
    async with async_session_maker() as db:
        item_result = await db.execute(select(OutlierItem).where(OutlierItem.id == item.id))
        item = item_result.scalar_one_or_none()
        node_result = await db.execute(select(RemixNode).where(RemixNode.id == node.id))
        node = node_result.scalar_one_or_none()

        print("\n✅ Results")
        print(f"- OutlierItem.analysis_status: {item.analysis_status if item else 'missing'}")
        print(f"- OutlierItem.best_comments: {len(item.best_comments or []) if item else 0}")
        print(f"- RemixNode.gemini_analysis: {'set' if node and node.gemini_analysis else 'missing'}")


if __name__ == "__main__":
    asyncio.run(main())
