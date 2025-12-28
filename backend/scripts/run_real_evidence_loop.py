"""
run_real_evidence_loop.py (PEGL v1.0)

REAL DATA PIPELINE for NotebookLM
=================================

This script acts as the "Time & Experience Simulator" for the content engine.
It moves data between sheets to simulate the passage of time and evidence collection.

PEGL v1.0 Updates:
- EvidenceEvent 상태머신 통합 (선택적)
- RunManager 지원 (선택적)

Flow:
1. READ `VDG_Parent_Candidates` (Source of Truth)
   - Gets pending candidates.
2. WRITE `VDG_Evidence` (Data Generation)
   - Generates 'virtual' performance data for depth experiments.
   - This becomes the INPUT for Opal and NotebookLM.
3. RUN Opal (Decision)
   - Reads `VDG_Evidence`.
   - Writes to `VDG_Decision`.

This ensures NotebookLM always has 'fresh' data tables to analyze, grounded in Sheet IDs.
"""
import sys
import os
import asyncio
import uuid
import random
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import logging
# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


from app.services.sheet_manager import SheetManager
from app.services.opal_engine import OpalEngine

# PEGL v1.0: Optional DB integration
USE_DB_TRACKING = os.environ.get("EVIDENCE_LOOP_USE_DB", "false").lower() == "true"

# --- Configuration (from Environment Variables) ---
SHEET_OUTLIER = "VDG_Outlier_Raw"
SHEET_PARENT = "VDG_Parent_Candidates"
SHEET_EVIDENCE = "VDG_Evidence"
SHEET_DECISION = "VDG_Decision"
SHEET_PROGRESS = "VDG_Progress"

# Required: User email for sharing sheets
USER_EMAIL = os.environ.get("KOMISSION_SHARE_EMAIL")
# Optional: Folder ID to create sheets in (bypasses SA quota issues)
FOLDER_ID = os.environ.get("KOMISSION_FOLDER_ID")
PRIMARY_PLATFORMS = {
    p.strip().lower()
    for p in os.environ.get("KOMISSION_PRIMARY_PLATFORMS", "tiktok,instagram").split(",")
    if p.strip()
}
PRIMARY_VIEW_THRESHOLD = float(os.environ.get("KOMISSION_PRIMARY_VIEW_THRESHOLD", "500000"))
PRIMARY_GROWTH_THRESHOLD = float(os.environ.get("KOMISSION_PRIMARY_GROWTH_THRESHOLD", "1.2"))
SECONDARY_VIEW_THRESHOLD = float(os.environ.get("KOMISSION_SECONDARY_VIEW_THRESHOLD", "1000000"))
SECONDARY_GROWTH_THRESHOLD = float(os.environ.get("KOMISSION_SECONDARY_GROWTH_THRESHOLD", "1.8"))

REQUIRED_HEADERS = {
    SHEET_OUTLIER: [
        "source_name", "source_url", "collected_at", "platform", "category",
        "title", "views", "growth_rate", "author", "posted_at", "status"
    ],
    SHEET_PARENT: [
        "parent_id", "title", "platform", "category", "source_url",
        "baseline_views", "baseline_engagement", "selected_by", "selected_at", "status"
    ],
    SHEET_EVIDENCE: [
        "evidence_id", "parent_id", "parent_title", "depth", "variant_id", "variant_name",
        "views", "engagement_rate", "retention_rate", "tracking_days",
        "confidence_score", "confidence_ci_low", "confidence_ci_high", "rank", "winner",
        "generated_at", "data_source"
    ],
    SHEET_DECISION: [
        "decision_id", "parent_id", "winner_variant_id", "winner_variant_name",
        "top_reasons", "risks", "next_experiment", "sample_size",
        "tracking_days", "success_criteria", "status", "created_at"
    ],
    SHEET_PROGRESS: [
        "variant_id", "date", "views", "engagement_rate",
        "retention_rate", "confidence_score", "status",
        "parent_id", "variant_name"
    ],
}

LEGACY_EVIDENCE_HEADERS = [
    "evidence_id", "parent_id", "parent_title", "depth", "variant_id", "variant_name",
    "views", "engagement_rate", "retention_rate", "tracking_days",
    "confidence_score", "confidence_ci_low", "confidence_ci_high", "rank", "winner",
    "generated_at"
]

PROGRESS_STATUS_ALLOW = {"tracking", "complete", "completed", "done", ""}

# Validate required config at import time
if not USER_EMAIL:
    raise EnvironmentError(
        "KOMISSION_SHARE_EMAIL env var is required. "
        "Example: export KOMISSION_SHARE_EMAIL=your@email.com"
    )

class RealDataPipeline:
    def __init__(self):
        # Prefer existing credentials; fall back to repo credential file if present.
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cred_path = os.path.join(base_dir, 'backend', 'credentials.json')
        if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(cred_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
        elif not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            raise FileNotFoundError(
                "GOOGLE_APPLICATION_CREDENTIALS not set and fallback credentials.json not found."
            )

        self.manager = SheetManager()
        self.opal = OpalEngine(self.manager)
        
        # Log Service Account Email for User
        if hasattr(self.manager.creds, 'service_account_email'):
            logger.info(f"Service Account: {self.manager.creds.service_account_email}")
            logger.info("Share your Google Drive Folder with this email if you hit Quota errors.")

    async def run(self):
        logger.info("Starting Real Data Pipeline...")

        
        # 0. Ensure Sheets Exist & Are Shared
        self._ensure_sheets_exist()

        # 0.5 Promote Outlier Raw → Parent Candidates
        promoted = self._promote_outliers_to_candidates()
        if promoted:
            logger.info(f"Promoted {promoted} outlier rows into parent candidates.")

        # 1. Fetch Candidates from Sheet
        candidates = self._fetch_candidates()
        if not candidates:
            logger.warning("No candidates found. Seeding Mock Candidate for Demo.")
            self._seed_mock_candidate()
            candidates = self._fetch_candidates()

        logger.info(f"Found {len(candidates)} candidates.")
        
        # 2. Generate Evidence for active candidates
        new_evidence_count = 0
        for parent in candidates:
            # Only process if status is relevant (e.g., 'depth1', 'planning')
            # For this runner, we process ALL to ensure data flow.
            logger.info(f"Processing: {parent['title']}")
            
            progress_rows = self._fetch_progress_rows(parent["parent_id"])
            if progress_rows:
                logger.info(f"Using {len(progress_rows)} progress rows for {parent['parent_id']}")
                evidence_rows = self._generate_evidence_from_progress(parent, progress_rows)
            else:
                evidence_rows = self._generate_evidence_data(parent)
            if evidence_rows:
                # Append to Sheet
                self.manager.append_data(SHEET_EVIDENCE, evidence_rows)
                new_evidence_count += len(evidence_rows)
                
                # 3. Trigger Opal Decision immediately for this parent
                # (Reading back raw dict for efficiency context pass)
                evidence_group = {
                    "parent_id": parent["parent_id"],
                    "parent_title": parent["title"],
                    "variants": [
                        {
                            "variant_name": row[5],
                            "views": row[6],
                            "retention_rate": row[8],
                            "confidence_score": row[10]
                        } for row in evidence_rows
                    ]
                }
                
                logger.info(f"Requesting Opal Decision for {parent['title']}")
                try:
                    await self.opal.generate_and_save_decision(evidence_group)
                except Exception as err:
                    logger.error(f"Opal decision failed for {parent['parent_id']}: {err}")
                    raise

        logger.info(f"Pipeline Finished. Added {new_evidence_count} evidence rows.")

    def _fetch_candidates(self) -> List[Dict[str, Any]]:
        """
        Reads VDG_Parent_Candidates sheet to get source data.
        Returns minimal dict list: [{parent_id, title, category, ...}]
        """
        sheet_id = self.manager.find_sheet_id(SHEET_PARENT)
        if not sheet_id:
            return []
            
        # Read all values (using basic get)
        try:
            result = self.manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="Sheet1!A1:J200"
            ).execute()
            rows = result.get('values', [])
            stats = []
            for idx, row in enumerate(rows):
                if len(row) < 2:
                    continue
                # Skip header row if present
                if idx == 0 and row[0] == "parent_id":
                    continue
                # Parse based on schema index (0:id, 1:title, 3:category)
                stats.append({
                    "parent_id": row[0],
                    "title": row[1],
                    "category": row[3] if len(row) > 3 else "general",
                    "baseline_views": self._parse_number(row[5]) if len(row) > 5 else None,
                })
            return stats
        except Exception as e:
            logger.error(f"Read Failed: {e}")
            return []

    def _fetch_progress_rows(self, parent_id: str) -> List[Dict[str, Any]]:
        sheet_id = self.manager.find_sheet_id(SHEET_PROGRESS)
        if not sheet_id:
            return []

        try:
            result = self.manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="Sheet1!A1:I2000"
            ).execute()
            rows = result.get('values', [])
            if not rows:
                return []

            headers = rows[0]
            header_map = {h: i for i, h in enumerate(headers)}
            progress_rows: List[Dict[str, Any]] = []

            for row in rows[1:]:
                if len(row) < 2:
                    continue
                status = (self._get_cell(row, header_map, "status") or "").strip().lower()
                if status not in PROGRESS_STATUS_ALLOW:
                    continue

                row_parent_id = (self._get_cell(row, header_map, "parent_id") or "").strip()
                variant_id = (self._get_cell(row, header_map, "variant_id") or "").strip()
                if not row_parent_id and variant_id:
                    row_parent_id = self._extract_parent_from_variant(variant_id) or ""

                if row_parent_id != parent_id:
                    continue

                progress_rows.append({
                    "variant_id": variant_id,
                    "variant_name": self._get_cell(row, header_map, "variant_name"),
                    "date": self._get_cell(row, header_map, "date"),
                    "views": self._get_cell(row, header_map, "views"),
                    "engagement_rate": self._get_cell(row, header_map, "engagement_rate"),
                    "retention_rate": self._get_cell(row, header_map, "retention_rate"),
                    "confidence_score": self._get_cell(row, header_map, "confidence_score"),
                })

            return progress_rows
        except Exception as e:
            logger.error(f"Progress read failed: {e}")
            return []

    def _get_cell(self, row: List[Any], header_map: Dict[str, int], key: str) -> Any:
        idx = header_map.get(key)
        if idx is None or idx >= len(row):
            return ""
        return row[idx]

    def _extract_parent_from_variant(self, variant_id: str) -> Optional[str]:
        if not variant_id:
            return None
        match = re.search(r"(parent_[a-zA-Z0-9]+)", variant_id)
        if match:
            return match.group(1)
        return None

    def _fetch_outliers(self) -> List[Dict[str, Any]]:
        sheet_id = self.manager.find_sheet_id(SHEET_OUTLIER)
        if not sheet_id:
            return []

        try:
            result = self.manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="Sheet1!A1:K500"
            ).execute()
            rows = result.get('values', [])
            if not rows:
                return []
            headers = rows[0]
            header_map = {h: i for i, h in enumerate(headers)}
            outliers: List[Dict[str, Any]] = []
            for idx, row in enumerate(rows[1:], start=2):
                if len(row) < 2:
                    continue
                outliers.append({
                    "source_name": self._get_cell(row, header_map, "source_name"),
                    "source_url": self._get_cell(row, header_map, "source_url"),
                    "collected_at": self._get_cell(row, header_map, "collected_at"),
                    "platform": self._get_cell(row, header_map, "platform"),
                    "category": self._get_cell(row, header_map, "category"),
                    "title": self._get_cell(row, header_map, "title"),
                    "views": self._get_cell(row, header_map, "views"),
                    "growth_rate": self._get_cell(row, header_map, "growth_rate"),
                    "author": self._get_cell(row, header_map, "author"),
                    "posted_at": self._get_cell(row, header_map, "posted_at"),
                    "status": self._get_cell(row, header_map, "status"),
                    "_row_index": idx,
                    "_status_col": header_map.get("status", 10),
                })
            return outliers
        except Exception as e:
            logger.error(f"Outlier read failed: {e}")
            return []

    def _load_candidate_keys(self):
        sheet_id = self.manager.find_sheet_id(SHEET_PARENT)
        if not sheet_id:
            return set(), set()

        try:
            result = self.manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="Sheet1!A1:J500"
            ).execute()
            rows = result.get('values', [])
            urls = set()
            titles = set()
            for idx, row in enumerate(rows):
                if len(row) < 2:
                    continue
                if idx == 0 and row[0] == "parent_id":
                    continue
                if len(row) > 4 and row[4]:
                    urls.add(row[4])
                if row[1]:
                    titles.add(row[1])
            return urls, titles
        except Exception as e:
            logger.error(f"Candidate lookup failed: {e}")
            return set(), set()

    def _parse_number(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", "")
        if not text:
            return None
        if text.endswith("%"):
            try:
                return float(text.rstrip("%")) / 100
            except ValueError:
                return None
        match = re.search(r"[-+]?\d*\.?\d+", text)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def _promote_outliers_to_candidates(self) -> int:
        outliers = self._fetch_outliers()
        if not outliers:
            return 0

        existing_urls, existing_titles = self._load_candidate_keys()
        rows: List[List[Any]] = []
        updates: List[Dict[str, Any]] = []
        for outlier in outliers:
            status = (outlier.get("status") or "").strip().lower()
            if status and status not in {"new", "pending"}:
                continue

            title = outlier.get("title") or ""
            source_url = outlier.get("source_url") or ""
            if not title or not source_url:
                updates.append({
                    "row_index": outlier.get("_row_index"),
                    "status_col": outlier.get("_status_col", 10),
                    "status": "ignored"
                })
                continue

            if source_url in existing_urls or title in existing_titles:
                updates.append({
                    "row_index": outlier.get("_row_index"),
                    "status_col": outlier.get("_status_col", 10),
                    "status": "ignored"
                })
                continue

            views = self._parse_number(outlier.get("views"))
            growth_rate = self._parse_number(outlier.get("growth_rate"))
            platform = (outlier.get("platform") or "").strip().lower()
            is_primary = platform in PRIMARY_PLATFORMS

            view_threshold = PRIMARY_VIEW_THRESHOLD if is_primary else SECONDARY_VIEW_THRESHOLD
            growth_threshold = PRIMARY_GROWTH_THRESHOLD if is_primary else SECONDARY_GROWTH_THRESHOLD

            qualified = False
            if views is not None and views >= view_threshold:
                qualified = True
            if growth_rate is not None and growth_rate >= growth_threshold:
                qualified = True

            new_status = "candidate" if qualified else "ignored"
            updates.append({
                "row_index": outlier.get("_row_index"),
                "status_col": outlier.get("_status_col", 10),
                "status": new_status
            })

            if qualified:
                rows.append([
                    f"parent_{uuid.uuid4().hex[:10]}",
                    title,
                    outlier.get("platform") or "",
                    outlier.get("category") or "general",
                    source_url,
                    int(views) if views is not None else "",
                    growth_rate if growth_rate is not None else "",
                    "auto-import",
                    datetime.now().isoformat(),
                    "candidate"
                ])

        if rows:
            self.manager.append_data(SHEET_PARENT, rows)

        for update in updates:
            row_index = update.get("row_index")
            status_col = update.get("status_col")
            if not row_index:
                continue
            col_letter = self._column_letter((status_col or 10) + 1)
            self.manager.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.manager.find_sheet_id(SHEET_OUTLIER),
                range=f"{col_letter}{row_index}",
                valueInputOption="RAW",
                body={'values': [[update["status"]]]}
            ).execute()
        return len(rows)

    def _column_letter(self, index: int) -> str:
        """Convert 1-based column index to A1 letter."""
        letters = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            letters = chr(65 + remainder) + letters
        return letters

    def _ensure_sheets_exist(self):
        """
        Checks if required sheets exist. If not, creates and SHARES them.
        """
        for sheet_name, headers in REQUIRED_HEADERS.items():
            sheet_id = self.manager.find_sheet_id(sheet_name)
            if not sheet_id:
                logger.warning(f"{sheet_name} not found. Creating...")
                # Create via Setup Loop or simplified Create
                sheet_id = self.manager.create_sheet(sheet_name, folder_id=FOLDER_ID)

            if sheet_id:
                self._ensure_sheet_header(sheet_id, sheet_name, headers)
            
            # SHARE with User
            if sheet_id:
                logger.info(f"Sharing {sheet_name} with {USER_EMAIL}")
                self.manager.share_sheet(sheet_id, USER_EMAIL, role='writer')

    def _ensure_sheet_header(self, sheet_id: str, sheet_name: str, headers: List[str]):
        try:
            result = self.manager.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="Sheet1!A1:Q1"
            ).execute()
            rows = result.get('values', [])
            current = rows[0] if rows else []
            if not current:
                self.manager.write_header(sheet_id, headers)
                return

            if sheet_name == SHEET_EVIDENCE and current == LEGACY_EVIDENCE_HEADERS:
                logger.info(f"Upgrading legacy header for {sheet_name}")
                self.manager.write_header(sheet_id, headers)
                return

            if current != headers:
                logger.warning(f"{sheet_name} header mismatch; keeping existing header.")
        except Exception as e:
            logger.error(f"Header check failed for {sheet_name}: {e}")

    def _generate_evidence_from_progress(
        self,
        parent: Dict[str, Any],
        progress_rows: List[Dict[str, Any]]
    ) -> List[List[Any]]:
        grouped: Dict[str, Dict[str, Any]] = {}
        for row in progress_rows:
            variant_id = row.get("variant_id") or ""
            if not variant_id:
                continue
            entry = grouped.setdefault(variant_id, {
                "variant_name": row.get("variant_name") or variant_id,
                "views": [],
                "engagement": [],
                "retention": [],
                "confidence": [],
                "dates": set(),
            })
            views = self._parse_number(row.get("views"))
            if views is not None:
                entry["views"].append(views)
            engagement = self._parse_number(row.get("engagement_rate"))
            if engagement is not None:
                entry["engagement"].append(engagement)
            retention = self._parse_number(row.get("retention_rate"))
            if retention is not None:
                entry["retention"].append(retention)
            confidence = self._parse_number(row.get("confidence_score"))
            if confidence is not None:
                entry["confidence"].append(confidence)
            date = row.get("date")
            if date:
                entry["dates"].add(date)

        scored = []
        for variant_id, entry in grouped.items():
            views_total = sum(entry["views"]) if entry["views"] else 0
            engagement_avg = sum(entry["engagement"]) / len(entry["engagement"]) if entry["engagement"] else ""
            retention_avg = sum(entry["retention"]) / len(entry["retention"]) if entry["retention"] else ""
            confidence_avg = sum(entry["confidence"]) / len(entry["confidence"]) if entry["confidence"] else ""
            tracking_days = len(entry["dates"]) if entry["dates"] else max(1, len(entry["views"]))

            if confidence_avg == "" and tracking_days:
                confidence_avg = min(0.95, 0.5 + 0.05 * tracking_days)

            score = views_total
            if isinstance(retention_avg, (int, float)):
                score *= (0.5 + retention_avg)

            scored.append({
                "variant_id": variant_id,
                "variant_name": entry["variant_name"],
                "views_total": int(views_total),
                "engagement_avg": engagement_avg,
                "retention_avg": retention_avg,
                "confidence_avg": confidence_avg,
                "tracking_days": tracking_days,
                "score": score,
            })

        scored.sort(key=lambda item: item["score"], reverse=True)
        rows: List[List[Any]] = []
        for idx, item in enumerate(scored, start=1):
            confidence = item["confidence_avg"]
            if isinstance(confidence, (int, float)):
                ci_low = max(0.0, confidence - 0.05)
                ci_high = min(1.0, confidence + 0.05)
            else:
                ci_low = ""
                ci_high = ""

            rows.append([
                str(uuid.uuid4()),
                parent["parent_id"],
                parent["title"],
                1,
                item["variant_id"],
                item["variant_name"],
                item["views_total"],
                item["engagement_avg"],
                item["retention_avg"],
                item["tracking_days"],
                confidence,
                ci_low,
                ci_high,
                idx,
                idx == 1,
                datetime.now().isoformat(),
                "progress"
            ])

        return rows

    def _generate_evidence_data(self, parent: Dict[str, str]) -> List[List[Any]]:
        """
        Generates 2 variant rows (Original vs Remix) for Evidence Sheet.
        Simulates data NotebookLM would analyze.
        """
        # Logic: Randomize stats based on category
        is_beauty = "beauty" in parent["category"].lower()
        baseline_views = parent.get("baseline_views")
        if isinstance(baseline_views, (int, float)) and baseline_views > 0:
            base_views = int(baseline_views)
        else:
            base_views = 50000 if is_beauty else 150000
        
        # Row Schema:
        # [0:evidence_id, 1:parent_id, 2:parent_title, 3:depth, 4:variant_id, 5:variant_name,
        #  6:views, 7:engagement, 8:retention, 9:tracking_days, 
        #  10:conf_score, 11:ci_l, 12:ci_h, 13:rank, 14:winner, 15:generated_at, 16:data_source]
        
        rows = []
        
        # Variant A (Control)
        rows.append([
            str(uuid.uuid4()), parent["parent_id"], parent["title"], 1, 
            str(uuid.uuid4()), "Original Mix",
            random.randint(base_views, base_views * 2), 0.05, 0.45, 7,
            0.82, 0.80, 0.84, 1, True, datetime.now().isoformat(),
            "simulated"
        ])
        
        # Variant B (Test)
        rows.append([
            str(uuid.uuid4()), parent["parent_id"], parent["title"], 1, 
            str(uuid.uuid4()), "Faster Hook V1",
            random.randint(int(base_views * 0.5), int(base_views * 1.5)), 0.03, 0.25, 3,
            0.45, 0.30, 0.60, 2, False, datetime.now().isoformat(),
            "simulated"
        ])
        
        return rows

    def _seed_mock_candidate(self):
        """
        Seeds a mock parent candidate if the sheet is empty to verify the loop.
        """
        row = [
            str(uuid.uuid4()), "Glass Skin Challenge (Mock)", "tiktok", "beauty", 
            "http://tiktok.com/mock", 150000, 0.12, "auto-seed", 
            datetime.now().isoformat(), "candidate"
        ]
        self.manager.append_data(SHEET_PARENT, [row])
        logger.info("Seeded mock candidate to VDG_Parent_Candidates.")

if __name__ == "__main__":
    try:
        pipeline = RealDataPipeline()
        asyncio.run(pipeline.run())
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
