#!/usr/bin/env python
"""
Export recent completed VDG analyses into golden fixtures.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models import OutlierItem, RemixNode  # noqa: E402
from app.services.curation_service import extract_features_from_vdg  # noqa: E402

DEFAULT_REQUIRED_VDG_KEYS = ["platform", "duration_ms", "hook_genome", "viral_kicks"]


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")


def _load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "description": "Golden set fixtures", "items": []}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def _build_checks(vdg: Dict[str, Any], comments: List[dict]) -> Dict[str, Any]:
    required_keys = [key for key in DEFAULT_REQUIRED_VDG_KEYS if key in vdg]
    features = extract_features_from_vdg(vdg)
    feature_ranges: Dict[str, List[float]] = {}
    if isinstance(features.get("hook_strength"), (int, float)):
        feature_ranges["hook_strength"] = [0.0, 1.0]
    if isinstance(features.get("duration_sec"), (int, float)):
        feature_ranges["duration_sec"] = [0.0, 300.0]

    return {
        "required_vdg_keys": required_keys,
        "min_comment_count": len(comments) if comments else 0,
        "feature_ranges": feature_ranges,
    }


async def _fetch_items(
    db: AsyncSession,
    limit: int,
    min_comments: int,
) -> List[Tuple[OutlierItem, RemixNode]]:
    query = (
        select(OutlierItem, RemixNode)
        .join(RemixNode, RemixNode.id == OutlierItem.promoted_to_node_id)
        .where(OutlierItem.analysis_status == "completed")
        .order_by(OutlierItem.updated_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()
    filtered: List[Tuple[OutlierItem, RemixNode]] = []
    for item, node in rows:
        comments = item.best_comments or []
        if len(comments) < min_comments:
            continue
        filtered.append((item, node))
    return filtered


async def export_golden(
    output_dir: Path,
    limit: int,
    min_comments: int,
    enabled: bool,
    overwrite: bool,
    database_url: str,
) -> int:
    manifest_path = output_dir / "manifest.json"
    manifest = _load_manifest(manifest_path)
    items = manifest.get("items", [])
    existing_ids = {entry.get("id") for entry in items if entry.get("id")}

    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    exported = 0
    skipped = 0
    async with async_session() as db:
        rows = await _fetch_items(db, limit=limit, min_comments=min_comments)

        for item, node in rows:
            vdg = node.gemini_analysis or None
            if not isinstance(vdg, dict):
                skipped += 1
                continue

            entry_id = _safe_id(node.node_id or str(item.id))
            if entry_id in existing_ids and not overwrite:
                skipped += 1
                continue

            outlier_payload = {
                "id": str(item.id),
                "video_url": item.video_url,
                "platform": item.platform,
                "category": item.category,
                "title": item.title,
                "thumbnail_url": item.thumbnail_url,
                "view_count": item.view_count or 0,
                "like_count": item.like_count or 0,
                "share_count": item.share_count or 0,
                "outlier_score": item.outlier_score,
                "outlier_tier": item.outlier_tier,
                "creator_avg_views": item.creator_avg_views,
                "engagement_rate": item.engagement_rate,
            }
            comments = item.best_comments or []

            outlier_path = Path("items") / f"{entry_id}.json"
            comments_path = Path("comments") / f"{entry_id}.json"
            vdg_path = Path("vdg") / f"{entry_id}.json"

            _write_json(output_dir / outlier_path, outlier_payload)
            _write_json(output_dir / comments_path, comments)
            _write_json(output_dir / vdg_path, vdg)

            entry = {
                "id": entry_id,
                "enabled": enabled,
                "outlier_item_path": str(outlier_path),
                "comments_path": str(comments_path),
                "vdg_path": str(vdg_path),
                "checks": _build_checks(vdg, comments),
            }

            existing_index = next(
                (idx for idx, existing in enumerate(items) if existing.get("id") == entry_id),
                None,
            )
            if existing_index is None:
                items.append(entry)
            else:
                items[existing_index] = entry

            existing_ids.add(entry_id)
            exported += 1

    await engine.dispose()

    manifest["items"] = items
    _write_json(manifest_path, manifest)
    print(f"Exported {exported} entries (skipped {skipped}).")
    return exported


def main() -> int:
    parser = argparse.ArgumentParser(description="Export VDG golden fixtures from DB")
    parser.add_argument("--limit", type=int, default=5, help="Number of items to export")
    parser.add_argument("--min-comments", type=int, default=0, help="Minimum comments required")
    parser.add_argument(
        "--output-dir",
        default=str(BACKEND_ROOT / "tests" / "fixtures" / "vdg_golden"),
        help="Output directory for fixtures",
    )
    parser.add_argument("--disable", action="store_true", help="Export fixtures as disabled")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing fixture files")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        from app.database import DATABASE_URL as DEFAULT_DB_URL  # noqa: E402

        database_url = DEFAULT_DB_URL

    output_dir = Path(args.output_dir).resolve()
    enabled = not args.disable

    exported = asyncio.run(
        export_golden(
            output_dir=output_dir,
            limit=args.limit,
            min_comments=args.min_comments,
            enabled=enabled,
            overwrite=args.overwrite,
            database_url=database_url,
        )
    )
    return 0 if exported > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
