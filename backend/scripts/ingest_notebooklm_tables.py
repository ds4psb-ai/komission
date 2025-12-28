"""
ingest_notebooklm_tables.py (Phase B: Data Tables → DB Pipeline)

Ingest NotebookLM Data Tables export (Google Sheets) into PatternSynthesis table.

WORKFLOW:
1. NotebookLM creates Data Tables from pattern synthesis
2. Export to Google Sheets
3. This script reads Sheets and upserts to PatternSynthesis

Usage:
  python backend/scripts/ingest_notebooklm_tables.py --sheet-url "https://docs.google.com/spreadsheets/d/..."
  python backend/scripts/ingest_notebooklm_tables.py --sheet-url "..." --cluster-id "hook-2s" --dry-run
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
sys.path.append(BASE_DIR)

from app.config import settings
from app.models import PatternSynthesis, SynthesisType, NotebookSourcePack, PatternLibrary, EvidenceSnapshot
from app.services.sheet_manager import SheetManager
from app.utils.time import utcnow

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def promote_to_pattern_library(
    db: AsyncSession,
    syntheses: List[PatternSynthesis],
    dry_run: bool = False,
) -> int:
    """
    Promote PatternSynthesis entries to PatternLibrary.
    
    Combines invariant_rules and mutation_strategy from syntheses
    into final PatternLibrary entries.
    
    Groups by (cluster_id, temporal_phase) to prevent phase mixing.
    """
    promoted = 0
    
    # Group by (cluster_id, temporal_phase) to prevent mixing
    by_cluster_phase: Dict[tuple, List[PatternSynthesis]] = {}
    for s in syntheses:
        key = (s.cluster_id, s.temporal_phase or "T1")
        if key not in by_cluster_phase:
            by_cluster_phase[key] = []
        by_cluster_phase[key].append(s)
    
    for (cluster_id, temporal_phase), cluster_syntheses in by_cluster_phase.items():
        # Extract invariant_rules and mutation_strategy
        invariant_rules = {}
        mutation_strategy = {}
        citations_all = []
        platform = None
        category = None
        
        for s in cluster_syntheses:
            if s.synthesis_type == SynthesisType.INVARIANT_RULES:
                invariant_rules = s.synthesis_data
                # Extract platform/category from synthesis data if available
                platform = s.synthesis_data.get("platform") or platform
                category = s.synthesis_data.get("category") or category
            elif s.synthesis_type == SynthesisType.MUTATION_STRATEGY:
                mutation_strategy = s.synthesis_data
            
            if s.citations:
                citations_all.extend(s.citations if isinstance(s.citations, list) else [s.citations])
        
        if not invariant_rules:
            logger.warning(f"No invariant_rules for cluster {cluster_id}/{temporal_phase}, skipping promotion")
            continue
        
        # Fallback: try to extract from row metadata if not in synthesis_data
        if not platform:
            for s in cluster_syntheses:
                platform = s.synthesis_data.get("platform") or s.synthesis_data.get("플랫폼")
                if platform:
                    break
        if not category:
            for s in cluster_syntheses:
                category = s.synthesis_data.get("category") or s.synthesis_data.get("카테고리")
                if category:
                    break
        
        # Final fallback with warning
        if not platform:
            platform = "unknown"
            logger.warning(f"Platform not found for {cluster_id}, using 'unknown'")
        if not category:
            category = "unknown"
            logger.warning(f"Category not found for {cluster_id}, using 'unknown'")
        
        pattern_id = f"{cluster_id}_{temporal_phase}_v1"
        
        if dry_run:
            logger.info(f"[DRY-RUN] Would promote cluster {cluster_id}/{temporal_phase} to PatternLibrary")
            promoted += 1
            continue
        
        # Check existing
        from sqlalchemy import select, and_
        existing = await db.execute(
            select(PatternLibrary).where(
                and_(
                    PatternLibrary.cluster_id == cluster_id,
                    PatternLibrary.temporal_phase == temporal_phase
                )
            )
        )
        existing_pattern = existing.scalar_one_or_none()
        
        if existing_pattern:
            # Create new revision
            pattern_id = f"{cluster_id}_{temporal_phase}_r{existing_pattern.revision + 1}"
            new_pattern = PatternLibrary(
                pattern_id=pattern_id,
                cluster_id=cluster_id,
                temporal_phase=temporal_phase,
                platform=platform,
                category=category,
                invariant_rules=invariant_rules,
                mutation_strategy=mutation_strategy or {},
                citations=citations_all or None,
                revision=existing_pattern.revision + 1,
                previous_revision_id=existing_pattern.id,
            )
        else:
            new_pattern = PatternLibrary(
                pattern_id=pattern_id,
                cluster_id=cluster_id,
                temporal_phase=temporal_phase,
                platform=platform,
                category=category,
                invariant_rules=invariant_rules,
                mutation_strategy=mutation_strategy or {},
                citations=citations_all or None,
                revision=1,
            )
        
        db.add(new_pattern)
        logger.info(f"Promoted cluster {cluster_id}/{temporal_phase} to PatternLibrary: {pattern_id}")
        promoted += 1
    
    if not dry_run:
        await db.commit()
    
    return promoted


async def link_citations_to_evidence(
    db: AsyncSession,
    syntheses: List[PatternSynthesis],
    dry_run: bool = False,
) -> int:
    """
    Phase E: Link PatternSynthesis citations to EvidenceSnapshot.
    
    For each PatternSynthesis with citations, find related EvidenceSnapshot
    entries (matching cluster_id AND temporal_phase) and populate:
    - notebooklm_citation: ALL citations as JSON string
    - synthesis_source: source type with synthesis_type
    - synthesis_id: link to PatternSynthesis
    """
    from datetime import timedelta
    from sqlalchemy import select, and_, func
    from app.models import RemixNode
    
    linked = 0
    
    # Helper: calculate date range for temporal phase
    def phase_date_range(phase: str, base_date):
        """
        Calculate date range for temporal phase.
        Based on 17_TEMPORAL_VARIATION_THEORY.md:
        - T0: 0-7 days (100% homage)
        - T1: 8-14 days (95% homage)
        - T2: 15-28 days (90% homage)
        - T3: 29+ days (85% homage)
        """
        phase_windows = {
            "T0": (0, 7),
            "T1": (8, 14),
            "T2": (15, 28),
            "T3": (29, 365),  # Upper bound for practical purposes
        }
        days_range = phase_windows.get(phase, (0, 365))
        start = base_date + timedelta(days=days_range[0])
        end = base_date + timedelta(days=days_range[1])
        return start, end
    
    for synthesis in syntheses:
        if not synthesis.citations:
            continue
        
        # Build query conditions
        conditions = [RemixNode.cluster_id == synthesis.cluster_id]
        
        if synthesis.temporal_phase:
            # Get cluster's first appearance date from RemixNode created_at
            first_node_result = await db.execute(
                select(func.min(RemixNode.created_at)).where(
                    RemixNode.cluster_id == synthesis.cluster_id
                )
            )
            cluster_first_date = first_node_result.scalar_one_or_none()
            
            if cluster_first_date:
                phase_start, phase_end = phase_date_range(synthesis.temporal_phase, cluster_first_date)
                conditions.append(RemixNode.created_at >= phase_start)
                conditions.append(RemixNode.created_at <= phase_end)
                logger.debug(f"Matching {synthesis.cluster_id}/{synthesis.temporal_phase}: "
                           f"{phase_start.date()} to {phase_end.date()}")
        
        result = await db.execute(
            select(RemixNode).where(
                and_(*conditions) if len(conditions) > 1 else conditions[0]
            )
        )
        parent_nodes = result.scalars().all()
        
        if not parent_nodes:
            logger.debug(f"No parent nodes found for cluster {synthesis.cluster_id}/{synthesis.temporal_phase or 'any'}")
            continue
        
        for node in parent_nodes:
            # Find evidence snapshots for this parent
            evidence_result = await db.execute(
                select(EvidenceSnapshot).where(
                    EvidenceSnapshot.parent_node_id == node.id
                )
            )
            snapshots = evidence_result.scalars().all()
            
            for snapshot in snapshots:
                if dry_run:
                    logger.info(f"[DRY-RUN] Would link synthesis {synthesis.id} to evidence {snapshot.id}")
                    linked += 1
                    continue
                
                # Store ALL citations as JSON, not just first one
                import json
                if isinstance(synthesis.citations, list):
                    citation_text = json.dumps(synthesis.citations, ensure_ascii=False)
                elif isinstance(synthesis.citations, dict):
                    citation_text = json.dumps(synthesis.citations, ensure_ascii=False)
                else:
                    citation_text = str(synthesis.citations)
                
                # Include synthesis_type in source field for tracking
                synthesis_source = f"notebooklm_data_table:{synthesis.synthesis_type.value}"
                
                snapshot.notebooklm_citation = citation_text
                snapshot.synthesis_source = synthesis_source
                snapshot.synthesis_id = synthesis.id
                
                logger.info(f"Linked synthesis {synthesis.id} ({synthesis.synthesis_type.value}) to evidence {snapshot.id}")
                linked += 1
    
    if not dry_run:
        await db.commit()
    
    return linked


# Expected column mappings for Data Tables export
COLUMN_MAPPINGS = {
    "synthesis_type": ["type", "synthesis_type", "pattern_type"],
    "cluster_id": ["cluster", "cluster_id", "pattern_cluster"],
    "rules": ["rules", "invariant_rules", "불변규칙"],
    "must_keep": ["must_keep", "유지필수"],
    "citations": ["citations", "sources", "인용"],
    "confidence": ["confidence", "신뢰도"],
}


def extract_sheet_id(url: str) -> str:
    """Extract Google Sheets ID from URL."""
    if "/d/" in url:
        parts = url.split("/d/")[1].split("/")
        return parts[0]
    return url


def parse_synthesis_type(value: str) -> SynthesisType:
    """Parse synthesis type from various formats."""
    value_lower = value.lower().replace(" ", "_").replace("-", "_")
    
    mapping = {
        "invariant": SynthesisType.INVARIANT_RULES,
        "invariant_rules": SynthesisType.INVARIANT_RULES,
        "불변규칙": SynthesisType.INVARIANT_RULES,
        "mutation": SynthesisType.MUTATION_STRATEGY,
        "mutation_strategy": SynthesisType.MUTATION_STRATEGY,
        "변주전략": SynthesisType.MUTATION_STRATEGY,
        "failure": SynthesisType.FAILURE_MODES,
        "failure_modes": SynthesisType.FAILURE_MODES,
        "실패패턴": SynthesisType.FAILURE_MODES,
        "audience": SynthesisType.AUDIENCE_SIGNAL,
        "audience_signal": SynthesisType.AUDIENCE_SIGNAL,
        "오디언스": SynthesisType.AUDIENCE_SIGNAL,
        "hook": SynthesisType.HOOK_PATTERN,
        "hook_pattern": SynthesisType.HOOK_PATTERN,
        "훅패턴": SynthesisType.HOOK_PATTERN,
        "director": SynthesisType.DIRECTOR_INTENT,
        "director_intent": SynthesisType.DIRECTOR_INTENT,
        "연출의도": SynthesisType.DIRECTOR_INTENT,
    }
    
    for key, syn_type in mapping.items():
        if key in value_lower:
            return syn_type
    
    return SynthesisType.INVARIANT_RULES  # Default


def find_column(headers: List[str], candidates: List[str]) -> Optional[int]:
    """Find column index by matching candidate names."""
    headers_lower = [h.lower().strip() for h in headers]
    for candidate in candidates:
        if candidate.lower() in headers_lower:
            return headers_lower.index(candidate.lower())
    return None


def parse_json_cell(value: str) -> Any:
    """Parse JSON from cell value, or return as-is."""
    if not value or not isinstance(value, str):
        return value
    
    value = value.strip()
    if value.startswith("{") or value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    
    # Try parsing comma-separated values as list
    if "," in value and not value.startswith("["):
        return [v.strip() for v in value.split(",")]
    
    return value


async def fetch_sheet_data(sheet_url: str) -> List[Dict[str, Any]]:
    """Fetch and parse sheet data."""
    sheet_id = extract_sheet_id(sheet_url)
    
    try:
        manager = SheetManager()
        result = manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range="A:Z"  # Fetch all columns
        ).execute()
        
        values = result.get("values", [])
        if not values:
            raise ValueError("Sheet is empty")
        
        headers = values[0]
        rows = []
        
        for row in values[1:]:
            if not row or not any(row):
                continue
            
            # Pad row to match headers
            padded_row = row + [""] * (len(headers) - len(row))
            row_dict = {headers[i]: padded_row[i] for i in range(len(headers))}
            rows.append(row_dict)
        
        logger.info(f"Fetched {len(rows)} rows from sheet")
        return rows
        
    except Exception as e:
        logger.error(f"Failed to fetch sheet: {e}")
        raise


async def ingest_rows(
    db: AsyncSession,
    rows: List[Dict[str, Any]],
    sheet_url: str,
    cluster_id: Optional[str],
    notebook_id: Optional[str],
    output_format: str,
    language: str,
    dry_run: bool = False
) -> int:
    """Ingest parsed rows into PatternSynthesis table."""
    ingested = 0
    
    for row in rows:
        # Determine synthesis type
        type_value = row.get("type") or row.get("synthesis_type") or row.get("pattern_type") or "invariant"
        synthesis_type = parse_synthesis_type(str(type_value))
        
        # Get cluster_id from row or argument
        row_cluster = row.get("cluster") or row.get("cluster_id") or row.get("pattern_cluster") or cluster_id
        if not row_cluster:
            logger.warning(f"Skipping row without cluster_id: {row}")
            continue
        
        # Build synthesis_data
        synthesis_data = {}
        
        # Extract rules/invariants
        rules = row.get("rules") or row.get("invariant_rules") or row.get("불변규칙")
        if rules:
            synthesis_data["rules"] = parse_json_cell(str(rules))
        
        # Extract must_keep
        must_keep = row.get("must_keep") or row.get("유지필수")
        if must_keep:
            synthesis_data["must_keep"] = parse_json_cell(str(must_keep))
        
        # Extract confidence
        confidence = row.get("confidence") or row.get("신뢰도")
        if confidence:
            try:
                synthesis_data["confidence"] = float(confidence)
            except (ValueError, TypeError):
                pass
        
        # Copy all other fields
        for key, value in row.items():
            if key not in ["type", "synthesis_type", "cluster", "cluster_id", "rules", "citations", "confidence"]:
                if value and str(value).strip():
                    synthesis_data[key] = parse_json_cell(str(value))
        
        # Extract citations
        citations_raw = row.get("citations") or row.get("sources") or row.get("인용")
        citations = None
        if citations_raw:
            citations = parse_json_cell(str(citations_raw))
            if isinstance(citations, str):
                citations = [{"source": citations}]
        
        if dry_run:
            logger.info(f"[DRY-RUN] Would ingest: type={synthesis_type.value}, cluster={row_cluster}")
            ingested += 1
            continue
        
        # Create PatternSynthesis
        synthesis = PatternSynthesis(
            notebook_id=notebook_id,
            source_sheet_url=sheet_url,
            cluster_id=row_cluster,
            synthesis_type=synthesis_type,
            synthesis_data=synthesis_data,
            citations=citations,
            output_format=output_format,
            language=language,
        )
        db.add(synthesis)
        ingested += 1
    
    if not dry_run:
        await db.commit()
    
    return ingested


async def main_async(args: argparse.Namespace) -> None:
    logger.info(f"Ingesting NotebookLM Data Tables from: {args.sheet_url}")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    syntheses_created = []
    
    try:
        # Fetch sheet data
        rows = await fetch_sheet_data(args.sheet_url)
        
        if not rows:
            logger.warning("No rows to ingest")
            return
        
        async with async_session() as db:
            ingested = await ingest_rows(
                db=db,
                rows=rows,
                sheet_url=args.sheet_url,
                cluster_id=args.cluster_id,
                notebook_id=args.notebook_id,
                output_format=args.output_format,
                language=args.language,
                dry_run=args.dry_run,
            )
            
            print(f"✅ Ingested {ingested} pattern syntheses")
            if args.dry_run:
                print("   (dry-run mode, no changes saved)")
            
            # Promotion to PatternLibrary
            if args.promote:
                # Fetch recently created syntheses for promotion
                if not args.dry_run:
                    from sqlalchemy import select
                    result = await db.execute(
                        select(PatternSynthesis).where(
                            PatternSynthesis.source_sheet_url == args.sheet_url
                        )
                    )
                    syntheses_created = result.scalars().all()
                    
                    if syntheses_created:
                        promoted = await promote_to_pattern_library(
                            db=db,
                            syntheses=syntheses_created,
                            dry_run=args.dry_run,
                        )
                        print(f"✅ Promoted {promoted} clusters to PatternLibrary")
                    else:
                        logger.warning("No syntheses found for promotion")
                else:
                    # In dry-run, just simulate promotion
                    logger.info("[DRY-RUN] Would promote syntheses to PatternLibrary")
            
            # Phase E: Link citations to EvidenceSnapshot
            if getattr(args, 'link_evidence', False):
                if not args.dry_run:
                    if not syntheses_created:
                        # Fetch if not already fetched
                        from sqlalchemy import select
                        result = await db.execute(
                            select(PatternSynthesis).where(
                                PatternSynthesis.source_sheet_url == args.sheet_url
                            )
                        )
                        syntheses_created = result.scalars().all()
                    
                    if syntheses_created:
                        linked = await link_citations_to_evidence(
                            db=db,
                            syntheses=syntheses_created,
                            dry_run=args.dry_run,
                        )
                        print(f"✅ Linked {linked} evidence snapshots to syntheses")
                    else:
                        logger.warning("No syntheses found for evidence linking")
                else:
                    logger.info("[DRY-RUN] Would link citations to EvidenceSnapshot")
            
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest NotebookLM Data Tables export into PatternSynthesis table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic ingestion
  python backend/scripts/ingest_notebooklm_tables.py --sheet-url "https://docs.google.com/spreadsheets/d/..."
  
  # With cluster and output format
  python backend/scripts/ingest_notebooklm_tables.py --sheet-url "..." --cluster-id "hook-2s" --output-format creator
  
  # Full pipeline: ingest + promote to PatternLibrary + link to Evidence
  python backend/scripts/ingest_notebooklm_tables.py --sheet-url "..." --promote --link-evidence
  
  # Dry run (preview only)
  python backend/scripts/ingest_notebooklm_tables.py --sheet-url "..." --promote --link-evidence --dry-run
        """
    )
    parser.add_argument("--sheet-url", required=True, help="Google Sheets URL of Data Tables export")
    parser.add_argument("--cluster-id", help="Default cluster_id if not in sheet")
    parser.add_argument("--notebook-id", help="NotebookLM notebook ID")
    parser.add_argument("--output-format", default="creator", 
                        choices=["creator", "business", "ops"],
                        help="Output format type (default: creator)")
    parser.add_argument("--language", default="ko", help="Language code (default: ko)")
    parser.add_argument("--promote", action="store_true", 
                        help="Also promote to PatternLibrary after ingestion")
    parser.add_argument("--link-evidence", action="store_true",
                        help="Link citations to EvidenceSnapshot (Phase E)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()


