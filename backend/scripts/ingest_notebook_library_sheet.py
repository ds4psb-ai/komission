"""
ingest_notebook_library_sheet.py

Ingest NotebookLM outputs from a Google Sheet into notebook_library (DB SoR).

Usage:
  python backend/scripts/ingest_notebook_library_sheet.py --sheet VDG_Insights
"""
import argparse
import asyncio
import json
import os
import sys
import uuid
from typing import Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import NotebookLibraryEntry
from app.services.sheet_manager import SheetManager


def parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None


def parse_int(value: str) -> Optional[int]:
    if value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def parse_float(value: str) -> Optional[float]:
    if value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def normalize_summary(summary: str, key_patterns: str, risks: str) -> Dict[str, object]:
    payload: Dict[str, object] = {"summary": summary}
    if key_patterns:
        try:
            payload["key_patterns"] = json.loads(key_patterns)
        except json.JSONDecodeError:
            payload["key_patterns"] = key_patterns
    if risks:
        try:
            payload["risks"] = json.loads(risks)
        except json.JSONDecodeError:
            payload["risks"] = risks
    return payload


async def entry_exists(db: AsyncSession, source_url: str) -> bool:
    result = await db.execute(
        select(NotebookLibraryEntry.id).where(NotebookLibraryEntry.source_url == source_url).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def main_async(args: argparse.Namespace) -> None:
    manager = SheetManager()
    sheet_id = manager.find_sheet_id(args.sheet)
    if not sheet_id:
        raise SystemExit(f"Sheet not found: {args.sheet}")

    result = manager.sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range="Sheet1!A1:Z"
    ).execute()
    rows = result.get("values", [])
    if len(rows) < 2:
        print("No rows to ingest.")
        return

    headers = [h.strip().lower() for h in rows[0]]
    header_map = {name: idx for idx, name in enumerate(headers)}

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    inserted = 0
    async with async_session() as db:
        for row in rows[1:]:
            def get(name: str) -> str:
                idx = header_map.get(name)
                if idx is None or idx >= len(row):
                    return ""
                return str(row[idx]).strip()

            summary = get("summary")
            if not summary:
                continue

            parent_id_raw = get("parent_id")
            parent_node_id = parse_uuid(parent_id_raw)
            key_patterns = get("key_patterns")
            risks = get("risks")
            source_url = get("source_url") or (
                f"parent://{parent_id_raw}" if parent_id_raw else f"sheet://{args.sheet}/{inserted + 1}"
            )
            cluster_id = get("cluster_id") or key_patterns or None
            platform = get("platform") or args.platform
            category = get("category") or args.category
            temporal_phase = get("temporal_phase") or None
            variant_age_days = parse_int(get("variant_age_days"))
            novelty_decay_score = parse_float(get("novelty_decay_score"))
            burstiness_index = parse_float(get("burstiness_index"))

            if await entry_exists(db, source_url):
                continue

            entry = NotebookLibraryEntry(
                source_url=source_url,
                platform=platform,
                category=category,
                summary=normalize_summary(summary, key_patterns, risks),
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
    print(f"Inserted {inserted} notebook entries from sheet '{args.sheet}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest NotebookLM outputs from a Sheet")
    parser.add_argument("--sheet", default="VDG_Insights", help="Sheet name (default: VDG_Insights)")
    parser.add_argument("--platform", default="unknown", help="Fallback platform")
    parser.add_argument("--category", default="unknown", help="Fallback category")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
