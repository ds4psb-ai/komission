#!/usr/bin/env python3
"""
ingest_pattern_library.py (PEGL v1.0)

NotebookLM Pattern Engine 결과를 PatternLibrary에 저장

Usage:
  python backend/scripts/ingest_pattern_library.py --input patterns.json
  python backend/scripts/ingest_pattern_library.py --input patterns.json --dry-run

Input JSON 형식:
{
  "patterns": [
    {
      "pattern_id": "tiktok_beauty_hook2s_v1",
      "cluster_id": "hook-2s-textpunch",
      "temporal_phase": "T1",
      "platform": "tiktok",
      "category": "beauty",
      "invariant_rules": {
        "hook": {"type": "text_punch", "duration_sec": 2},
        "music": {"genre": "trending_kpop"}
      },
      "mutation_strategy": {
        "modifiable": ["background_color", "font_style"],
        "constrained": ["hook_duration"],
        "forbidden": ["remove_hook"]
      },
      "citations": [
        {"source_entry_id": "...", "context": "Top performer"}
      ],
      "source_pack_id": "optional-uuid"
    }
  ]
}
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import PatternLibrary, NotebookSourcePack
from app.utils.time import utcnow

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def ingest_patterns(
    db: AsyncSession,
    patterns: List[Dict[str, Any]],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    패턴 목록을 PatternLibrary에 저장
    
    Args:
        db: DB 세션
        patterns: 패턴 목록
        dry_run: True면 실제 저장 안 함
        
    Returns:
        결과 요약
    """
    inserted = 0
    updated = 0
    errors = []
    
    for pattern_data in patterns:
        try:
            pattern_id = pattern_data.get("pattern_id")
            if not pattern_id:
                errors.append({"error": "Missing pattern_id", "data": pattern_data})
                continue
            
            # 기존 패턴 확인
            existing_result = await db.execute(
                select(PatternLibrary).where(PatternLibrary.pattern_id == pattern_id)
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                if dry_run:
                    logger.info(f"[DRY-RUN] Would update: {pattern_id}")
                else:
                    # 새 리비전 생성
                    new_pattern = PatternLibrary(
                        pattern_id=f"{pattern_id}_r{existing.revision + 1}",
                        cluster_id=pattern_data.get("cluster_id", existing.cluster_id),
                        temporal_phase=pattern_data.get("temporal_phase", existing.temporal_phase),
                        platform=pattern_data.get("platform", existing.platform),
                        category=pattern_data.get("category", existing.category),
                        invariant_rules=pattern_data.get("invariant_rules", existing.invariant_rules),
                        mutation_strategy=pattern_data.get("mutation_strategy", existing.mutation_strategy),
                        citations=pattern_data.get("citations", existing.citations),
                        revision=existing.revision + 1,
                        previous_revision_id=existing.id,
                        sample_count=pattern_data.get("sample_count", 0),
                        confidence_score=pattern_data.get("confidence_score", 0.5),
                    )
                    
                    # Source Pack 연결
                    source_pack_id = pattern_data.get("source_pack_id")
                    if source_pack_id:
                        new_pattern.source_pack_id = UUID(source_pack_id)
                    
                    db.add(new_pattern)
                    logger.info(f"Updated pattern: {pattern_id} → revision {existing.revision + 1}")
                updated += 1
            else:
                if dry_run:
                    logger.info(f"[DRY-RUN] Would insert: {pattern_id}")
                else:
                    new_pattern = PatternLibrary(
                        pattern_id=pattern_id,
                        cluster_id=pattern_data["cluster_id"],
                        temporal_phase=pattern_data.get("temporal_phase", "T1"),
                        platform=pattern_data["platform"],
                        category=pattern_data["category"],
                        invariant_rules=pattern_data["invariant_rules"],
                        mutation_strategy=pattern_data["mutation_strategy"],
                        citations=pattern_data.get("citations"),
                        revision=1,
                        sample_count=pattern_data.get("sample_count", 0),
                        confidence_score=pattern_data.get("confidence_score", 0.5),
                    )
                    
                    # Source Pack 연결
                    source_pack_id = pattern_data.get("source_pack_id")
                    if source_pack_id:
                        new_pattern.source_pack_id = UUID(source_pack_id)
                    
                    db.add(new_pattern)
                    logger.info(f"Inserted pattern: {pattern_id}")
                inserted += 1
                
        except Exception as e:
            errors.append({"error": str(e), "pattern_id": pattern_data.get("pattern_id")})
            logger.error(f"Error processing pattern: {e}")
    
    if not dry_run:
        await db.commit()
    
    return {
        "inserted": inserted,
        "updated": updated,
        "errors": errors,
        "total": len(patterns),
    }


async def main_async(args: argparse.Namespace) -> None:
    # 입력 파일 로드
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    patterns = data.get("patterns", [])
    if not patterns:
        raise ValueError("No patterns found in input file")
    
    logger.info(f"Loaded {len(patterns)} patterns from {args.input}")
    
    # DB 연결
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            result = await ingest_patterns(db, patterns, dry_run=args.dry_run)
        
        print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Pattern Library Ingestion Complete")
        print(f"  Total patterns: {result['total']}")
        print(f"  Inserted: {result['inserted']}")
        print(f"  Updated: {result['updated']}")
        if result['errors']:
            print(f"  Errors: {len(result['errors'])}")
            for err in result['errors'][:5]:
                print(f"    - {err}")
                
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest NotebookLM patterns into PatternLibrary (PEGL v1.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/scripts/ingest_pattern_library.py --input patterns.json
  python backend/scripts/ingest_pattern_library.py --input patterns.json --dry-run
        """
    )
    parser.add_argument("--input", required=True, help="Input JSON file with patterns")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()
    
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
