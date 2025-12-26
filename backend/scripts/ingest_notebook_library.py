"""
ingest_notebook_library.py

Import NotebookLM outputs into notebook_library (DB SoR).

Usage:
  python backend/scripts/ingest_notebook_library.py --json /path/to/notebooklm.json
  python backend/scripts/ingest_notebook_library.py --json /path/to/notebooklm.jsonl --platform tiktok --category beauty
"""
import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional
import uuid

from dotenv import load_dotenv
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import NotebookLibraryEntry


def load_records(path: str) -> List[Dict[str, Any]]:
    if path.endswith(".jsonl"):
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        return payload
    return [payload]


def normalize_summary(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"summary": str(value)}


def parse_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def parse_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


async def entry_exists(
    db: AsyncSession,
    source_url: str,
    parent_node_id: Optional[uuid.UUID],
) -> bool:
    query = select(NotebookLibraryEntry.id).where(NotebookLibraryEntry.source_url == source_url)
    if parent_node_id:
        query = query.where(NotebookLibraryEntry.parent_node_id == parent_node_id)
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none() is not None


def parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except ValueError:
        raise SystemExit(f"Invalid UUID: {value}")


async def main_async(args: argparse.Namespace) -> None:
    records = load_records(args.json)
    if not records:
        print("No notebook records found.")
        return

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    inserted = 0
    async with async_session() as db:
        for record in records:
            source_url = record.get("source_url") or record.get("url")
            if not source_url:
                continue

            platform = record.get("platform") or args.platform or "unknown"
            category = record.get("category") or args.category or "unknown"
            summary = normalize_summary(record.get("summary") or record.get("notes"))
            cluster_id = record.get("cluster_id") or args.cluster_id
            parent_node_id = parse_uuid(record.get("parent_node_id") or args.parent_node_id)
            temporal_phase = record.get("temporal_phase")
            variant_age_days = parse_int(record.get("variant_age_days"))
            novelty_decay_score = parse_float(record.get("novelty_decay_score"))
            burstiness_index = parse_float(record.get("burstiness_index"))

            if await entry_exists(db, source_url, parent_node_id):
                continue

            entry = NotebookLibraryEntry(
                source_url=source_url,
                platform=platform,
                category=category,
                summary=summary,
                cluster_id=cluster_id,
                parent_node_id=parent_node_id,
                temporal_phase=temporal_phase,
                variant_age_days=variant_age_days,
                novelty_decay_score=novelty_decay_score,
                burstiness_index=burstiness_index,
            )
            db.add(entry)
            inserted += 1

        await db.commit()

    await engine.dispose()
    print(f"Inserted {inserted} notebook entries into notebook_library.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import NotebookLM outputs into notebook_library")
    parser.add_argument("--json", required=True, help="Path to NotebookLM output (json/jsonl)")
    parser.add_argument("--platform", default=None, help="Fallback platform")
    parser.add_argument("--category", default=None, help="Fallback category")
    parser.add_argument("--cluster-id", default=None, help="Fallback cluster_id")
    parser.add_argument("--parent-node-id", default=None, help="Optional parent node ID")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
