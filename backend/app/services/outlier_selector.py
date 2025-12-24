import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OutlierItem, OutlierItemStatus, NotebookLibraryEntry
from app.services.sheet_manager import SheetManager

logger = logging.getLogger(__name__)


class OutlierSelector:
    """
    Selects promising outliers from DB and promotes them to VDG_Parent_Candidates (Sheet).
    Notebook Library 결과가 있는 Outlier만 후보로 승격한다.
    """

    def __init__(self, sheet_manager: SheetManager):
        self.sheet = sheet_manager
        self.primary_platforms = {
            p.strip().lower()
            for p in os.environ.get("KOMISSION_PRIMARY_PLATFORMS", "tiktok,instagram").split(",")
            if p.strip()
        }
        self.primary_view_threshold = float(os.environ.get("KOMISSION_PRIMARY_VIEW_THRESHOLD", "500000"))
        self.primary_growth_threshold = float(os.environ.get("KOMISSION_PRIMARY_GROWTH_THRESHOLD", "1.2"))
        self.secondary_view_threshold = float(os.environ.get("KOMISSION_SECONDARY_VIEW_THRESHOLD", "1000000"))
        self.secondary_growth_threshold = float(os.environ.get("KOMISSION_SECONDARY_GROWTH_THRESHOLD", "1.8"))

    async def process_pending_outliers(self, db: AsyncSession, limit: int = 200) -> int:
        candidates_sheet_id = self._ensure_candidates_sheet()
        existing_urls = self._load_existing_candidate_urls()

        result = await db.execute(
            select(OutlierItem, NotebookLibraryEntry)
            .outerjoin(NotebookLibraryEntry, NotebookLibraryEntry.source_url == OutlierItem.video_url)
            .where(OutlierItem.status == OutlierItemStatus.PENDING)
            .order_by(OutlierItem.crawled_at.desc())
            .limit(limit)
        )
        rows = result.all()

        if not rows:
            logger.info("No pending outliers found.")
            return 0

        candidates_to_add = []
        updated = 0

        for outlier, notebook_entry in rows:
            if not notebook_entry:
                continue

            view_threshold, growth_threshold = self._thresholds_for_platform(outlier.platform)
            views = outlier.view_count or 0
            growth = self._parse_growth(outlier.growth_rate)

            qualifies = views >= view_threshold or (growth is not None and growth >= growth_threshold)
            if qualifies:
                outlier.status = OutlierItemStatus.SELECTED
                updated += 1

                if outlier.video_url in existing_urls:
                    continue

                candidates_to_add.append([
                    str(uuid.uuid4()),
                    outlier.title or "Untitled",
                    outlier.platform or "unknown",
                    outlier.category or "unknown",
                    outlier.video_url,
                    views,
                    0.0,
                    "selector",
                    datetime.utcnow().isoformat(),
                    "planning",
                ])
                existing_urls.add(outlier.video_url)
            else:
                outlier.status = OutlierItemStatus.REJECTED
                updated += 1

        if candidates_to_add:
            self.sheet.append_data("VDG_Parent_Candidates", candidates_to_add)
            logger.info(f"Promoted {len(candidates_to_add)} candidates.")

        return updated

    def _thresholds_for_platform(self, platform: Optional[str]) -> Tuple[float, float]:
        if (platform or "").lower() in self.primary_platforms:
            return self.primary_view_threshold, self.primary_growth_threshold
        return self.secondary_view_threshold, self.secondary_growth_threshold

    def _parse_growth(self, value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        raw = str(value).strip().lower()
        raw = raw.replace("+", "")
        if raw.endswith("x"):
            raw = raw[:-1]
        if raw.endswith("%"):
            try:
                return float(raw[:-1]) / 100
            except ValueError:
                return None
        try:
            return float(raw)
        except ValueError:
            return None

    def _ensure_candidates_sheet(self) -> Optional[str]:
        sheet_id = self.sheet.find_sheet_id("VDG_Parent_Candidates")
        if not sheet_id:
            sheet_id = self.sheet.create_sheet("VDG_Parent_Candidates")
            self.sheet.write_header(sheet_id, [
                "parent_id", "title", "platform", "category", "source_url",
                "baseline_views", "baseline_engagement", "selected_by", "selected_at", "status"
            ])
        return sheet_id

    def _load_existing_candidate_urls(self) -> Set[str]:
        sheet_id = self.sheet.find_sheet_id("VDG_Parent_Candidates")
        if not sheet_id:
            return set()
        try:
            result = self.sheet.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="Sheet1!E2:E5000"
            ).execute()
            rows = result.get("values", [])
            return {row[0] for row in rows if row}
        except Exception:
            return set()
