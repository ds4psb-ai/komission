"""
build_notebook_source_pack.py (PEGL v1.0 + Ultra Mode)

Generate a NotebookLM Source Pack (Sheet) for a cluster.
Aggregates ALL entries in a cluster for comprehensive context.

PEGL v1.0 Updates:
- temporal_phase 인자 추가 (필수)
- NotebookSourcePack에 저장
- inputs_hash로 중복 방지
- 네이밍 규칙: NL_{platform}_{category}_{cluster_id}_{temporal_phase}_v{n}

Ultra Mode (v1.1):
- --mega-pack: 다중 클러스터를 단일 노트북에 통합 (최대 600개 소스)
- --cluster-ids: 쉼표로 구분된 다중 클러스터 ID
- cluster_id 컬럼 추가로 NotebookLM 내에서 필터링 가능

Usage:
  # Single cluster mode
  python backend/scripts/build_notebook_source_pack.py --cluster-id CLUSTER_ID --temporal-phase T1
  
  # Mega-pack mode (multiple clusters)
  python backend/scripts/build_notebook_source_pack.py --mega-pack --cluster-ids "cluster1,cluster2,cluster3" --temporal-phase all
"""
import argparse
import asyncio
import hashlib
import json
import csv
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import NotebookLibraryEntry, EvidenceSnapshot, PatternCluster, NotebookSourcePack
from app.services.sheet_manager import SheetManager
from app.utils.time import utcnow

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = ["section", "key", "value", "entry_idx"]
MEGA_PACK_HEADERS = ["section", "key", "value", "entry_idx", "cluster_id"]  # Ultra mode

# Valid temporal phases
TEMPORAL_PHASES = ["T0", "T1", "T2", "T3", "T4", "early", "growth", "mature", "decay"]

# Ultra mode limits
ULTRA_MAX_SOURCES = 600
MEGA_PACK_VERSION = "v1.1"


def _safe_title(text: str, max_len: int = 50) -> str:
    """클러스터 ID를 시트 제목에 안전하게 사용할 수 있도록 정제 (50자 제한)"""
    cleaned = re.sub(r"[^\w\\-_ ]+", "-", text.strip())
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
    """개별 엔트리 정보 (VDG v3.3 Full Schema Extraction)"""
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
    
    # NotebookLM Summary (Legacy support)
    summary = entry.summary or {}
    if isinstance(summary, dict):
        for key in ["hook", "pattern", "viral_element", "main_insight", "view_count", "outlier_tier"]:
            if key in summary:
                rows.append(["entry_summary", key, _stringify(summary[key]), entry_idx])
    else:
        rows.append(["entry_summary", "summary", _stringify(summary), entry_idx])
    
    # === VDG v3.3 FULL SCHEMA EXTRACTION ===
    schema = entry.analysis_schema or {}
    if not schema:
        return rows

    rows.append(["entry_analysis", "schema_version", entry.schema_version or "v3.3", entry_idx])
    rows.append(["entry_analysis", "title", schema.get("title", ""), entry_idx])
    rows.append(["entry_analysis", "content_duration", str(schema.get("duration_sec", "")), entry_idx])
    rows.append(["entry_analysis", "upload_date", schema.get("upload_date", ""), entry_idx])

    # 0. Real Metrics (v3.3 - from OutlierItem)
    metrics = schema.get("metrics", {})
    if metrics:
        rows.append(["analysis_metrics", "view_count", str(metrics.get("view_count", 0)), entry_idx])
        rows.append(["analysis_metrics", "like_count", str(metrics.get("like_count", 0)), entry_idx])
        rows.append(["analysis_metrics", "share_count", str(metrics.get("share_count", "")), entry_idx])
        rows.append(["analysis_metrics", "outlier_tier", str(metrics.get("outlier_tier", "")), entry_idx])
        rows.append(["analysis_metrics", "outlier_score", str(metrics.get("outlier_score", "")), entry_idx])
        rows.append(["analysis_metrics", "creator_avg_views", str(metrics.get("creator_avg_views", "")), entry_idx])

    # 1. Hook Genome
    hook = schema.get("hook_genome", {})
    if hook:
        rows.append(["analysis_hook", "pattern", hook.get("pattern", ""), entry_idx])
        rows.append(["analysis_hook", "delivery", hook.get("delivery", ""), entry_idx])
        rows.append(["analysis_hook", "strength", str(hook.get("strength", "")), entry_idx])
        rows.append(["analysis_hook", "summary", hook.get("hook_summary", ""), entry_idx])
        
        # Microbeats (Start/Build/Punch)
        if "microbeats" in hook:
            rows.append(["analysis_hook", "microbeats_json", _stringify(hook["microbeats"]), entry_idx])
            
        # Virality Analysis
        viral = hook.get("virality_analysis", {})
        if viral:
            for k, v in viral.items():
                rows.append([f"analysis_hook_viral", k, _stringify(v), entry_idx])
    
    # 2. Intent Layer (Psychology)
    intent = schema.get("intent_layer", {})
    if intent:
        rows.append(["analysis_intent", "hook_trigger", intent.get("hook_trigger", ""), entry_idx])
        rows.append(["analysis_intent", "hook_trigger_reason", intent.get("hook_trigger_reason", ""), entry_idx])
        rows.append(["analysis_intent", "retention_strategy", intent.get("retention_strategy", ""), entry_idx])
        
        # Dopamine Radar & Irony
        rows.append(["analysis_intent", "dopamine_radar_json", _stringify(intent.get("dopamine_radar")), entry_idx])
        rows.append(["analysis_intent", "irony_analysis_json", _stringify(intent.get("irony_analysis")), entry_idx])
        
        # Sentiment Arc
        sentiment = intent.get("sentiment_arc", {})
        if sentiment:
            rows.append(["analysis_intent", "sentiment_trajectory", sentiment.get("trajectory", ""), entry_idx])
            rows.append(["analysis_intent", "sentiment_micro_shifts_json", _stringify(sentiment.get("micro_shifts")), entry_idx])

    # 3. Focus Windows (v3.3 - RL Reward Signals)
    focus_windows = schema.get("focus_windows", [])
    if focus_windows:
        for i, fw in enumerate(focus_windows[:5]):  # Top 5 windows
            window_id = fw.get("window_id", f"W{i}")
            t_window = fw.get("t_window", [])
            hotspot = fw.get("hotspot", {})
            scores = hotspot.get("scores", {})
            
            rows.append([f"focus_window_{i}", "window_id", window_id, entry_idx])
            rows.append([f"focus_window_{i}", "t_window", _stringify(t_window), entry_idx])
            rows.append([f"focus_window_{i}", "hotspot_scores", _stringify(scores), entry_idx])
            rows.append([f"focus_window_{i}", "hotspot_reasons", _stringify(hotspot.get("reasons", [])), entry_idx])
            rows.append([f"focus_window_{i}", "entities_json", _stringify(fw.get("entities", [])), entry_idx])
            rows.append([f"focus_window_{i}", "tags_json", _stringify(fw.get("tags", {})), entry_idx])

    # 4. Cross-Scene Analysis (v3.3 - Pattern Synthesis)
    cross = schema.get("cross_scene_analysis", {})
    if cross:
        rows.append(["cross_scene", "global_summary", cross.get("global_summary", ""), entry_idx])
        rows.append(["cross_scene", "consistent_elements_json", _stringify(cross.get("consistent_elements", [])), entry_idx])
        rows.append(["cross_scene", "evolving_elements_json", _stringify(cross.get("evolving_elements", [])), entry_idx])
        rows.append(["cross_scene", "director_intent_json", _stringify(cross.get("director_intent", [])), entry_idx])
        rows.append(["cross_scene", "entity_state_changes_json", _stringify(cross.get("entity_state_changes", [])), entry_idx])

    # 5. ASR/OCR (v3.3)
    asr = schema.get("asr_transcript", {})
    if asr:
        rows.append(["asr_ocr", "asr_lang", asr.get("lang", ""), entry_idx])
        rows.append(["asr_ocr", "asr_transcript", asr.get("transcript", ""), entry_idx])
        rows.append(["asr_ocr", "asr_translation_en", asr.get("translation_en", ""), entry_idx])
    
    ocr = schema.get("ocr_text", [])
    if ocr:
        rows.append(["asr_ocr", "ocr_text_json", _stringify(ocr), entry_idx])

    # 6. Narrative Structure (Scenes)
    scenes = schema.get("scenes", [])
    if scenes:
        # Provide a high-level summary of scenes structure
        scene_summaries = []
        for i, s in enumerate(scenes):
            narrative = s.get("narrative_unit", {})
            desc = narrative.get("summary", "")
            rhetoric = ",".join(narrative.get("rhetoric", []))
            scene_summaries.append(f"Scene {i+1} ({s.get('duration_sec')}s): {desc} [Rhetoric: {rhetoric}]")
        rows.append(["analysis_scenes", "structure_summary", "\n".join(scene_summaries), entry_idx])
        rows.append(["analysis_scenes", "full_scenes_json", _stringify(scenes), entry_idx])

    # 7. Capsule Brief (Replication Guide)
    capsule = schema.get("capsule_brief", {})
    if capsule:
        rows.append(["analysis_capsule", "hook_script", capsule.get("hook_script", ""), entry_idx])
        rows.append(["analysis_capsule", "constraints_json", _stringify(capsule.get("constraints")), entry_idx])
        rows.append(["analysis_capsule", "do_not_list", _stringify(capsule.get("do_not")), entry_idx])
        rows.append(["analysis_capsule", "shotlist_json", _stringify(capsule.get("shotlist")), entry_idx])

    # 8. Commerce & Audience
    if "commerce" in schema:
        rows.append(["analysis_commerce", "commerce_json", _stringify(schema["commerce"]), entry_idx])
    
    if "audience_reaction" in schema:
        reaction = schema["audience_reaction"]
        rows.append(["analysis_audience", "viral_signal", reaction.get("viral_signal", ""), entry_idx])
        rows.append(["analysis_audience", "analysis", reaction.get("analysis", ""), entry_idx])
        rows.append(["analysis_audience", "common_reactions", _stringify(reaction.get("common_reactions")), entry_idx])
        rows.append(["analysis_audience", "overall_sentiment", reaction.get("overall_sentiment", ""), entry_idx])
        rows.append(["analysis_audience", "best_comments_json", _stringify(reaction.get("best_comments")), entry_idx])
    
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


async def fetch_mega_pack_entries(
    db: AsyncSession, 
    cluster_ids: List[str], 
    temporal_phase: str = "all",
    limit: int = ULTRA_MAX_SOURCES
) -> List[NotebookLibraryEntry]:
    """
    Fetch entries from multiple clusters for Ultra Mega-Pack mode.
    
    Args:
        db: Database session
        cluster_ids: List of cluster IDs to include
        temporal_phase: Filter by phase or "all" for all phases
        limit: Maximum entries (default: 600 for Ultra)
    """
    query = select(NotebookLibraryEntry).where(
        NotebookLibraryEntry.cluster_id.in_(cluster_ids)
    )
    
    if temporal_phase != "all":
        query = query.where(NotebookLibraryEntry.temporal_phase == temporal_phase)
    
    query = query.order_by(
        NotebookLibraryEntry.cluster_id,
        NotebookLibraryEntry.created_at.desc()
    ).limit(limit)
    
    result = await db.execute(query)
    entries = list(result.scalars().all())
    
    logger.info(f"[MEGA-PACK] Fetched {len(entries)} entries from {len(cluster_ids)} clusters")
    return entries


async def fetch_multiple_clusters(db: AsyncSession, cluster_ids: List[str]) -> Dict[str, PatternCluster]:
    """Fetch cluster info for multiple cluster IDs."""
    result = await db.execute(
        select(PatternCluster).where(PatternCluster.cluster_id.in_(cluster_ids))
    )
    clusters = result.scalars().all()
    return {c.cluster_id: c for c in clusters}


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
        
        # Get actual first sheet name (handles locale: 'Sheet1' vs '시트1')
        spreadsheet_meta = manager.sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id, fields="sheets.properties.title"
        ).execute()
        first_sheet_name = spreadsheet_meta["sheets"][0]["properties"]["title"]
        
        body = {"values": [HEADERS] + rows}
        manager.sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{first_sheet_name}!A1",
            valueInputOption="RAW",
            body=body,
        ).execute()
        return sheet_id
    except Exception as e:
        logger.error(f"Failed to write sheet: {e}")
        raise


async def main_async(args: argparse.Namespace) -> None:
    is_mega_pack = getattr(args, 'mega_pack', False)
    
    if is_mega_pack:
        cluster_ids = [c.strip() for c in args.cluster_ids.split(",")]
        logger.info(f"[MEGA-PACK] Building Ultra Source Pack for {len(cluster_ids)} clusters, phase: {args.temporal_phase}")
    else:
        cluster_ids = [args.cluster_id]
        logger.info(f"Building Source Pack for cluster: {args.cluster_id}, phase: {args.temporal_phase}")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            if is_mega_pack:
                # Ultra Mega-Pack: Multi-cluster mode
                entries = await fetch_mega_pack_entries(
                    db, cluster_ids, args.temporal_phase, args.limit
                )
                clusters_dict = await fetch_multiple_clusters(db, cluster_ids)
                
                # Create virtual combined cluster for summary
                cluster = PatternCluster(
                    cluster_id="mega-pack-" + "-".join(cluster_ids[:3]),
                    cluster_name=f"Mega Pack ({len(cluster_ids)} clusters)",
                    member_count=len(entries),
                    pattern_type="combined"
                )
            else:
                # Single cluster mode (legacy)
                cluster = await fetch_cluster(db, args.cluster_id)
                if not cluster:
                    logger.warning(f"No PatternCluster found for {args.cluster_id}, continuing with entries only")
                    # 임시 클러스터 객체 생성
                    cluster = PatternCluster(
                        cluster_id=args.cluster_id,
                        cluster_name=args.cluster_id,
                        member_count=0
                    )
                
                # 모든 엔트리 조회 (temporal_phase 필터링) - only for single cluster mode
                entries = await fetch_all_entries(db, args.cluster_id, limit=args.limit)
                
                # PEGL v1.0: temporal_phase로 필터링
                if args.temporal_phase != "all":
                    entries = [e for e in entries if e.temporal_phase == args.temporal_phase]
            
            if not entries:
                cluster_desc = args.cluster_ids if is_mega_pack else args.cluster_id
                raise SystemExit(f"No notebook_library entries found for {cluster_desc}, phase={args.temporal_phase}")
            
            logger.info(f"Found {len(entries)} entries (phase: {args.temporal_phase})")
            
            # Evidence 조회
            parent_node_ids = [e.parent_node_id for e in entries if e.parent_node_id]
            evidences = await fetch_latest_evidence(db, parent_node_ids)
            logger.info(f"Found {len(evidences)} evidence snapshots")
            
            # PEGL v1.0: inputs_hash 계산 (중복 방지)
            cluster_id_for_pack = ",".join(cluster_ids) if is_mega_pack else args.cluster_id
            inputs_data = {
                "cluster_id": cluster_id_for_pack,
                "temporal_phase": args.temporal_phase,
                "entry_ids": sorted([str(e.id) for e in entries]),
                "mega_pack": is_mega_pack,
            }
            inputs_hash = hashlib.sha256(json.dumps(inputs_data, sort_keys=True).encode()).hexdigest()
            
            # Force overwrite check
            if getattr(args, 'force', False):
                 existing_any = await db.execute(
                    select(NotebookSourcePack).where(
                        NotebookSourcePack.cluster_id == cluster_id_for_pack,
                        NotebookSourcePack.temporal_phase == args.temporal_phase
                    )
                 )
                 existing_records = existing_any.scalars().all()
                 if existing_records:
                     logger.info(f"[FORCE] Deleting {len(existing_records)} existing Source Packs for {cluster_id_for_pack}/{args.temporal_phase}")
                     for r in existing_records:
                         await db.delete(r)
                     await db.commit()

            # 중복 체크
            existing_pack = await db.execute(
                select(NotebookSourcePack).where(
                    NotebookSourcePack.cluster_id == cluster_id_for_pack,
                    NotebookSourcePack.temporal_phase == args.temporal_phase,
                    NotebookSourcePack.inputs_hash == inputs_hash
                )
            )
            if existing_pack.scalar_one_or_none():
                logger.warning(f"Source Pack already exists with same inputs. Use --force to overwrite.")
                # 기존 Pack이 있어도 계속 진행 (덮어쓰기)
        
        # 행 생성
        all_rows: List[List[str]] = []
        
        # 1. 클러스터 요약
        all_rows.extend(build_cluster_summary_rows(cluster, entries))
        
        # 1.1 Studio Multi-Output 메타데이터 (Phase C)
        output_targets = getattr(args, 'output_targets', 'creator,business,ops')
        all_rows.append(["meta", "output_targets", output_targets, ""])
        all_rows.append(["meta", "schema_version", "v3.3", ""])
        all_rows.append(["meta", "pack_mode", "mega" if is_mega_pack else "standard", ""])
        
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
        
        # PEGL v1.0: 네이밍 규칙 적용
        # NL_{platform}_{category}_{cluster_id}_{temporal_phase}_v{n}
        platforms = list(set([e.platform for e in entries if e.platform]))
        categories = list(set([e.category for e in entries if e.category]))
        platform_str = platforms[0] if len(platforms) == 1 else "multi"
        category_str = categories[0] if len(categories) == 1 else "mixed"
        # Title generation (mega-pack uses combined ID)
        title_cluster = "mega" if is_mega_pack else _safe_title(args.cluster_id)
        title = f"NL_{platform_str}_{category_str}_{title_cluster}_{args.temporal_phase}_v1"
        
        # Sheet 작성 (실패 시 로컬 CSV)
        pack_type = "sheet"
        drive_file_id = ""
        drive_url = ""
        sheet_id = None
        
        try:
            if args.local:
                raise ValueError("Forcing local generation")

            manager = SheetManager()
            sheet_id = write_sheet(manager, title, all_rows, dry_run=args.dry_run)
            drive_file_id = sheet_id
            drive_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            
            # 공유 설정
            share_email = os.environ.get("KOMISSION_SHARE_EMAIL")
            if share_email and not args.dry_run:
                try:
                    manager.share_sheet(sheet_id, share_email, role="writer")
                    logger.info(f"Shared with: {share_email}")
                except Exception as e:
                    logger.warning(f"Failed to share sheet: {e}")
                    
        except Exception as e:
            if not args.local:
                logger.warning(f"Google Sheet generation failed: {e}")
            logger.info("Switching to Local CSV generation...")
            
            pack_type = "csv"
            filename = f"{title}.csv"
            output_dir = os.path.join(BASE_DIR, "data", "source_packs")
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            if not args.dry_run:
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerows(all_rows)
                logger.info(f"Saved local Source Pack: {filepath}")
            
            drive_file_id = "local"
            drive_url = f"file://{filepath}"
        
        # PEGL v1.0: NotebookSourcePack 저장
        async with async_session() as db:
            # Fix: Use naive datetime for DB compatibility
            now_naive = utcnow().replace(tzinfo=None)
            
            source_pack = NotebookSourcePack(
                cluster_id=cluster_id_for_pack,
                temporal_phase=args.temporal_phase,
                pack_type=pack_type,
                drive_file_id=drive_file_id,
                drive_url=drive_url,
                inputs_hash=inputs_hash,
                source_version=MEGA_PACK_VERSION if is_mega_pack else "v1.0",
                entry_count=len(entries),
                # Phase C: Multi-Output Protocol fields (SoR)
                output_targets=getattr(args, 'output_targets', 'creator,business,ops'),
                pack_mode="mega" if is_mega_pack else "standard",
                schema_version="v3.3",
                created_at=now_naive,
                updated_at=now_naive,
            )
            db.add(source_pack)
            await db.commit()
            logger.info(f"NotebookSourcePack saved: {source_pack.id}")
        
        print(f"✅ Source Pack created: {title}")
        print(f"   Pack Type: {pack_type}")
        print(f"   Location: {drive_url}")
        print(f"   Temporal Phase: {args.temporal_phase}")
        print(f"   Entries: {len(entries)}")
        print(f"   Evidence: {len(evidences)}")
        print(f"   Inputs Hash: {inputs_hash[:12]}...")
        
    except Exception as e:
        logger.error(f"Error building Source Pack: {e}")
        raise
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build NotebookLM Source Pack (Sheet) for a cluster (PEGL v1.0 + Ultra Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single cluster mode
  python backend/scripts/build_notebook_source_pack.py --cluster-id curiosity-hook --temporal-phase T1
  python backend/scripts/build_notebook_source_pack.py --cluster-id curiosity-hook --temporal-phase T1 --dry-run
  
  # Ultra Mega-Pack mode (multiple clusters, up to 600 sources)
  python backend/scripts/build_notebook_source_pack.py --mega-pack --cluster-ids "cluster1,cluster2,cluster3" --temporal-phase all
  python backend/scripts/build_notebook_source_pack.py --mega-pack --cluster-ids "hook-*" --temporal-phase T0 --limit 600
        """
    )
    
    # Single cluster mode (legacy)
    parser.add_argument("--cluster-id", help="Cluster ID to export (single cluster mode)")
    
    # Ultra mode
    parser.add_argument("--mega-pack", action="store_true", 
                        help="Enable Ultra Mega-Pack mode (multiple clusters, max 600 sources)")
    parser.add_argument("--cluster-ids", 
                        help="Comma-separated cluster IDs for mega-pack mode (supports wildcards like 'hook-*')")
    
    parser.add_argument("--temporal-phase", required=True, 
                        help=f"Temporal phase: {TEMPORAL_PHASES} or 'all' for all phases")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to Sheet")
    parser.add_argument("--limit", type=int, default=50, 
                        help=f"Max entries to include (default: 50, mega-pack max: {ULTRA_MAX_SOURCES})")
    parser.add_argument("--group-by-phase", action="store_true", 
                        help="Group entries by temporal phase (T0/T1/T2/T3/T4)")
    parser.add_argument("--local", action="store_true", help="Force local CSV generation instead of Google Sheets")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing source pack if it exists")
    
    # Output targets for Studio multi-output (Phase C preview)
    parser.add_argument("--output-targets", default="creator,business,ops",
                        help="Comma-separated output targets for Studio multi-output (default: creator,business,ops)")
    
    args = parser.parse_args()
    
    # Validate mode
    if args.mega_pack:
        if not args.cluster_ids:
            logger.error("--mega-pack requires --cluster-ids")
            sys.exit(1)
        if args.limit > ULTRA_MAX_SOURCES:
            logger.warning(f"Limit {args.limit} exceeds Ultra max ({ULTRA_MAX_SOURCES}), capping")
            args.limit = ULTRA_MAX_SOURCES
        args.cluster_id = None  # Clear single mode
    else:
        if not args.cluster_id:
            logger.error("Single cluster mode requires --cluster-id")
            sys.exit(1)
    
    # Validate temporal phase
    if args.temporal_phase != "all" and args.temporal_phase not in TEMPORAL_PHASES:
        logger.error(f"Invalid temporal phase: {args.temporal_phase}")
        logger.error(f"Valid phases: {TEMPORAL_PHASES}")
        sys.exit(1)
    
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
