import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from app.services.sheet_manager import SheetManager

logger = logging.getLogger(__name__)

class OutlierSelector:
    """
    Selects promising outliers from VDG_Outlier_Raw and promotes them to VDG_Parent_Candidates.
    """

    def __init__(self, sheet_manager: SheetManager):
        self.sheet = sheet_manager

    def process_new_outliers(self):
        """
        Reads 'new' rows from VDG_Outlier_Raw, scores them, and updates status.
        Qualified outliers are added to VDG_Parent_Candidates.
        """
        # 1. Read Raw Outliers (Simulating read - in real app, we'd query the sheet)
        # Since Sheets API doesn't support SQL-like querying easily without pulling data,
        # we will fetch all and filter in memory for this MVP script.
        # OPTIMIZATION NOTE: In production, read only 'new' rows or use a DB.
        
        raw_sheet_id = self.sheet.find_sheet_id("VDG_Outlier_Raw")
        if not raw_sheet_id:
            logger.error("VDG_Outlier_Raw sheet not found.")
            return

        try:
            # Fetch all values
            result = self.sheet.sheets_service.spreadsheets().values().get(
                spreadsheetId=raw_sheet_id,
                range="A:K" # Columns A to K
            ).execute()
            rows = result.get('values', [])
            
            if not rows or len(rows) < 2:
                logger.info("No data found in VDG_Outlier_Raw.")
                return

            headers = rows[0]
            data_rows = rows[1:]
            
            # Map headers to indices
            header_map = {h: i for i, h in enumerate(headers)}
            
            candidates_to_add = []
            updates = [] # List of (row_index, new_status)

            for i, row in enumerate(data_rows):
                # Safe get
                def get_col(name):
                    idx = header_map.get(name)
                    if idx is not None and idx < len(row):
                        return row[idx]
                    return None

                status = get_col("status")
                
                if status == "new":
                    title = get_col("title")
                    views = self._parse_int(get_col("views"))
                    growth_rate = self._parse_float(get_col("growth_rate"))
                    platform = get_col("platform")
                    category = get_col("category")
                    source_url = get_col("source_url")

                    # --- SELECTION LOGIC (Mock AI/Heuristic) ---
                    # Criteria: Views > 500k OR Growth Rate > 1.2
                    is_qualified = False
                    reason = "Low metrics"

                    if views and views > 500000:
                        is_qualified = True
                        reason = "High viral velocity (Views > 500k)"
                    elif growth_rate and growth_rate > 1.2:
                        is_qualified = True
                        reason = f"High growth rate ({growth_rate}x)"

                    new_status = "candidate" if is_qualified else "ignored"
                    
                    # Update status in Raw sheet
                    # Row index is i + 2 (1-based, +1 for header)
                    updates.append((i + 2, new_status))

                    if is_qualified:
                        # Prepare Candidate Row
                        # | parent_id | title | platform | category | source_url | baseline_views | baseline_engagement | selected_by | selected_at | status |
                        candidates_to_add.append([
                            str(uuid.uuid4()),
                            title,
                            platform or "unknown",
                            category or "unknown",
                            source_url or "",
                            views or 0,
                            0.0, # baseline_engagement (placeholder)
                            "AI_Selector", # selected_by
                            datetime.now().isoformat(),
                            "planning" # Initial status for parent
                        ])
                        logger.info(f" Selected '{title}' as candidate. Reason: {reason}")
                    else:
                         logger.info(f" Ignored '{title}'. Reason: {reason}")

            # 2. Batch Update Status in Raw Sheet
            for row_idx, new_status in updates:
                 # TODO: Batch this properly for performance
                 # For MVP, single cell updates are acceptable but slow
                 self.sheet.sheets_service.spreadsheets().values().update(
                    spreadsheetId=raw_sheet_id,
                    range=f"K{row_idx}", # Assuming 'status' is column K (11th)
                    valueInputOption="RAW",
                    body={'values': [[new_status]]}
                ).execute()
            
            # 3. Append to Candidates Sheet
            if candidates_to_add:
                self.sheet.append_data("VDG_Parent_Candidates", candidates_to_add)
                logger.info(f"Promoted {len(candidates_to_add)} candidates.")

        except Exception as e:
            logger.error(f"Error filtering outliers: {e}")

    def _parse_int(self, val):
        try:
            return int(str(val).replace(',', ''))
        except:
            return 0
            
    def _parse_float(self, val):
        try:
            return float(str(val).replace(',', ''))
        except:
            return 0.0
