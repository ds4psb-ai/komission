"""
build_notebook_source_pack.py

Generate a NotebookLM Source Pack (Sheet) for a cluster.
Aggregates ALL entries in a cluster for comprehensive context.

Usage:
  python backend/scripts/build_notebook_source_pack.py --cluster-id CLUSTER_ID
  python backend/scripts/build_notebook_source_pack.py --cluster-id CLUSTER_ID --dry-run
"""
import argparse
import asyncio
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import NotebookLibraryEntry, EvidenceSnapshot, PatternCluster
from app.services.sheet_manager import SheetManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = ["section", "key", "value", "entry_idx"]


def _safe_title(text: str, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^\w\-_ ]+", "-", text.strip())
    cleaned = cleaned.strip("-_ ")
    if not cleaned:
        cleaned = "cluster"
    return cleaned[:max_len]


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _append_dict_rows(rows: List[List[str]], section: str, data: Dict[str, Any], idx: str = "") -> None:
    for key, value in data.items():
        if value is None or value == "":
            continue
        rows.append([section, str(key), _stringify(value), idx])


def build_cluster_summary_rows(cluster: PatternCluster, entries: List[NotebookLibraryEntry]) -> List[List[str]]:
    """클러스터 요약 정보"""
    rows: List[List[str]] = []
    rows.append(["cluster", "cluster_id", cluster.cluster_id, ""])
    rows.append(["cluster", "cluster_name", cluster.cluster_name or "", ""])
    rows.append(["cluster", "pattern_type", cluster.pattern_type or "", ""])
    rows.append(["cluster", "member_count", str(cluster.member_count or len(entries)), ""])
    rows.append(["cluster", "avg_outlier_score", str(cluster.avg_outlier_score or "N/A"), ""])
    
    # 플랫폼 분포
    platforms = [e.platform for e in entries if e.platform]
    platform_dist = {p: platforms.count(p) for p in set(platforms)}
    rows.append(["cluster", "platform_distribution", _stringify(platform_dist), ""])
    
    # 카테고리 분포
    categories = [e.category for e in entries if e.category]
    category_dist = {c: categories.count(c) for c in set(categories)}
    rows.append(["cluster", "category_distribution", _stringify(category_dist), ""])

    # Temporal phase 분포
    temporal_phases = [e.temporal_phase for e in entries if e.temporal_phase]
    if temporal_phases:
        phase_dist = {p: temporal_phases.count(p) for p in set(temporal_phases)}
        rows.append(["cluster", "temporal_phase_distribution", _stringify(phase_dist), ""])

    age_values = [e.variant_age_days for e in entries if e.variant_age_days is not None]
    if age_values:
        avg_age = sum(age_values) / len(age_values)
        rows.append(["cluster", "avg_variant_age_days", f"{avg_age:.2f}", ""])

    decay_values = [e.novelty_decay_score for e in entries if e.novelty_decay_score is not None]
    if decay_values:
        avg_decay = sum(decay_values) / len(decay_values)
        rows.append(["cluster", "avg_novelty_decay_score", f"{avg_decay:.4f}", ""])

    burst_values = [e.burstiness_index for e in entries if e.burstiness_index is not None]
    if burst_values:
        avg_burst = sum(burst_values) / len(burst_values)
        rows.append(["cluster", "avg_burstiness_index", f"{avg_burst:.4f}", ""])
    
    return rows


def build_entry_rows(entry: NotebookLibraryEntry, idx: int) -> List[List[str]]:
    """개별 엔트리 정보"""
    rows: List[List[str]] = []
    entry_idx = str(idx + 1)
    
    rows.append(["entry", "platform", entry.platform, entry_idx])
    rows.append(["entry", "category", entry.category, entry_idx])
    rows.append(["entry", "source_url", entry.source_url, entry_idx])
    rows.append(["entry", "created_at", entry.created_at.isoformat() if entry.created_at else "", entry_idx])
    rows.append(["entry_temporal", "temporal_phase", entry.temporal_phase or "", entry_idx])
    rows.append([
        "entry_temporal",
        "variant_age_days",
        str(entry.variant_age_days) if entry.variant_age_days is not None else "",
        entry_idx,
    ])
    rows.append([
        "entry_temporal",
        "novelty_decay_score",
        str(entry.novelty_decay_score) if entry.novelty_decay_score is not None else "",
        entry_idx,
    ])
    rows.append([
        "entry_temporal",
        "burstiness_index",
        str(entry.burstiness_index) if entry.burstiness_index is not None else "",
        entry_idx,
    ])
    
    summary = entry.summary or {}
    if isinstance(summary, dict):
        # 주요 요약 필드만 추출
        for key in ["hook", "pattern", "viral_element", "main_insight"]:
            if key in summary:
                rows.append(["entry_summary", key, _stringify(summary[key]), entry_idx])
    else:
        rows.append(["entry_summary", "summary", _stringify(summary), entry_idx])
    
    # 분석 스키마의 핵심 필드만 추출
    schema = entry.analysis_schema or {}
    if schema:
        rows.append(["entry_analysis", "schema_version", entry.schema_version or "", entry_idx])
        # VDG v3.x에서 핵심 필드 추출
        if "hook_genome" in schema:
            hook = schema.get("hook_genome", {})
            rows.append(["entry_analysis", "hook_pattern", hook.get("pattern", ""), entry_idx])
            rows.append(["entry_analysis", "hook_delivery", hook.get("delivery", ""), entry_idx])
            rows.append(["entry_analysis", "hook_strength", str(hook.get("strength", "")), entry_idx])
        if "intent_layer" in schema:
            intent = schema.get("intent_layer", {})
            rows.append(["entry_analysis", "hook_trigger", intent.get("hook_trigger", ""), entry_idx])
    
    return rows


def build_evidence_rows(evidence: EvidenceSnapshot) -> List[List[str]]:
    """Evidence 정보"""
    rows: List[List[str]] = []
    rows.append(["evidence", "snapshot_date", evidence.snapshot_date.isoformat(), ""])
    rows.append(["evidence", "period", evidence.period, ""])
    rows.append(["evidence", "top_mutation_type", evidence.top_mutation_type or "", ""])
    rows.append(["evidence", "top_mutation_pattern", evidence.top_mutation_pattern or "", ""])
    rows.append(["evidence", "top_mutation_rate", str(evidence.top_mutation_rate or ""), ""])
    rows.append(["evidence", "sample_count", str(evidence.sample_count), ""])
    rows.append(["evidence", "confidence", str(evidence.confidence), ""])
    
    if evidence.depth1_summary:
        rows.append(["evidence", "depth1_summary", _stringify(evidence.depth1_summary), ""])
    if evidence.depth2_summary:
        rows.append(["evidence", "depth2_summary", _stringify(evidence.depth2_summary), ""])
    
    return rows


async def fetch_cluster(db: AsyncSession, cluster_id: str) -> Optional[PatternCluster]:
    result = await db.execute(
        select(PatternCluster).where(PatternCluster.cluster_id == cluster_id)
    )
    return result.scalar_one_or_none()


async def fetch_all_entries(db: AsyncSession, cluster_id: str, limit: int = 50) -> List[NotebookLibraryEntry]:
    result = await db.execute(
        select(NotebookLibraryEntry)
        .where(NotebookLibraryEntry.cluster_id == cluster_id)
        .order_by(NotebookLibraryEntry.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def fetch_latest_evidence(db: AsyncSession, parent_node_ids: List[str]) -> List[EvidenceSnapshot]:
    if not parent_node_ids:
        return []
    result = await db.execute(
        select(EvidenceSnapshot)
        .where(EvidenceSnapshot.parent_node_id.in_(parent_node_ids))
        .order_by(EvidenceSnapshot.snapshot_date.desc())
        .limit(5)
    )
    return list(result.scalars().all())


def write_sheet(manager: SheetManager, title: str, rows: List[List[str]], dry_run: bool = False) -> str:
    if dry_run:
        logger.info(f"[DRY-RUN] Would create/update sheet: {title}")
        logger.info(f"[DRY-RUN] Total rows: {len(rows)}")
        return "DRY_RUN_SHEET_ID"
    
    try:
        sheet_id = manager.find_sheet_id(title)
        if not sheet_id:
            folder_id = os.environ.get("KOMISSION_FOLDER_ID")
            sheet_id = manager.create_sheet(title, folder_id=folder_id)
            logger.info(f"Created new sheet: {title}")
        else:
            logger.info(f"Updating existing sheet: {title}")
        
        body = {"values": [HEADERS] + rows}
        manager.sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body,
        ).execute()
        return sheet_id
    except Exception as e:
        logger.error(f"Failed to write sheet: {e}")
        raise


async def main_async(args: argparse.Namespace) -> None:
    logger.info(f"Building Source Pack for cluster: {args.cluster_id}")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # 클러스터 정보 조회
            cluster = await fetch_cluster(db, args.cluster_id)
            if not cluster:
                logger.warning(f"No PatternCluster found for {args.cluster_id}, continuing with entries only")
                # 임시 클러스터 객체 생성
                cluster = PatternCluster(
                    cluster_id=args.cluster_id,
                    cluster_name=args.cluster_id,
                    member_count=0
                )
            
            # 모든 엔트리 조회
            entries = await fetch_all_entries(db, args.cluster_id, limit=args.limit)
            if not entries:
                raise SystemExit(f"No notebook_library entries found for cluster_id={args.cluster_id}")
            
            logger.info(f"Found {len(entries)} entries in cluster")
            
            # Evidence 조회
            parent_node_ids = [e.parent_node_id for e in entries if e.parent_node_id]
            evidences = await fetch_latest_evidence(db, parent_node_ids)
            logger.info(f"Found {len(evidences)} evidence snapshots")
        
        # 행 생성
        all_rows: List[List[str]] = []
        
        # 1. 클러스터 요약
        all_rows.extend(build_cluster_summary_rows(cluster, entries))
        
        # 2. Phase별 그룹핑 (Temporal Variation Theory Section 8.3)
        if getattr(args, 'group_by_phase', False):
            # Phase 순서: T0 (fresh) -> T4 (stale)
            phases = ['T0', 'T1', 'T2', 'T3', 'T4']
            for phase in phases:
                phase_entries = [e for e in entries if e.temporal_phase == phase]
                if not phase_entries:
                    continue
                
                # Phase 헤더
                all_rows.append([f"phase_{phase}", "phase", phase, ""])
                all_rows.append([f"phase_{phase}", "count", str(len(phase_entries)), ""])
                
                # Phase별 통계
                decay_vals = [e.novelty_decay_score for e in phase_entries if e.novelty_decay_score]
                burst_vals = [e.burstiness_index for e in phase_entries if e.burstiness_index]
                if decay_vals:
                    avg_decay = sum(decay_vals) / len(decay_vals)
                    all_rows.append([f"phase_{phase}", "avg_novelty_decay", f"{avg_decay:.4f}", ""])
                if burst_vals:
                    avg_burst = sum(burst_vals) / len(burst_vals)
                    all_rows.append([f"phase_{phase}", "avg_burstiness", f"{avg_burst:.4f}", ""])
                
                # Phase별 엔트리
                for idx, entry in enumerate(phase_entries):
                    all_rows.extend(build_entry_rows(entry, idx))
            
            logger.info(f"Grouped entries by phase: {phases}")
        else:
            # 기존 로직: 모든 엔트리 순차적 출력
            for idx, entry in enumerate(entries):
                all_rows.extend(build_entry_rows(entry, idx))
        
        # 3. Evidence
        for evidence in evidences:
            all_rows.extend(build_evidence_rows(evidence))
        
        logger.info(f"Total rows to write: {len(all_rows)}")
        
        if args.dry_run:
            logger.info("[DRY-RUN] Preview of first 20 rows:")
            for row in all_rows[:20]:
                logger.info(f"  {row}")
            return
        
        # Sheet 작성
        manager = SheetManager()
        title = f"NL_Pack_{_safe_title(args.cluster_id)}"
        sheet_id = write_sheet(manager, title, all_rows, dry_run=args.dry_run)
        
        # 공유 설정
        share_email = os.environ.get("KOMISSION_SHARE_EMAIL")
        if share_email and not args.dry_run:
            try:
                manager.share_sheet(sheet_id, share_email, role="writer")
                logger.info(f"Shared with: {share_email}")
            except Exception as e:
                logger.warning(f"Failed to share sheet: {e}")
        
        print(f"✅ Source Pack created: {title}")
        print(f"   Sheet ID: {sheet_id}")
        print(f"   Entries: {len(entries)}")
        print(f"   Evidence: {len(evidences)}")
        
    except Exception as e:
        logger.error(f"Error building Source Pack: {e}")
        raise
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build NotebookLM Source Pack (Sheet) for a cluster",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/scripts/build_notebook_source_pack.py --cluster-id curiosity-hook
  python backend/scripts/build_notebook_source_pack.py --cluster-id curiosity-hook --dry-run
  python backend/scripts/build_notebook_source_pack.py --cluster-id curiosity-hook --limit 20
        """
    )
    parser.add_argument("--cluster-id", required=True, help="Cluster ID to export")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to Sheet")
    parser.add_argument("--limit", type=int, default=50, help="Max entries to include (default: 50)")
    parser.add_argument("--group-by-phase", action="store_true", 
                        help="Group entries by temporal phase (T0/T1/T2/T3/T4)")
    args = parser.parse_args()
    
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
