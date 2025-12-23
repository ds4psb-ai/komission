import logging
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Optional

logger = logging.getLogger(__name__)

class SheetManager:
    def __init__(self, credentials=None):
        try:
            # Scopes needed for Drive (create file) and Sheets (edit content)
            self.scopes = [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            if credentials:
                self.creds = credentials
                self.project_id = getattr(credentials, 'quota_project_id', 'unknown')
                logger.info("Using provided credentials.")
            else:
                self.creds, self.project_id = google.auth.default(scopes=self.scopes)
                logger.info(f"Authenticated with Google. Project ID: {self.project_id}")

            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google: {e}")
            raise

    def create_sheet(self, title: str, folder_id: Optional[str] = None) -> str:
        """Create a new Google Sheet and return its ID."""
        try:
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]

            file = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            sheet_id = file.get('id')
            logger.info(f"Created sheet '{title}' with ID: {sheet_id}")
            return sheet_id
        except HttpError as error:
            logger.error(f"An error occurred creating sheet '{title}': {error}")
            raise

    def write_header(self, spreadsheet_id: str, headers: List[str]):
        """Write the header row to the first sheet."""
        try:
            body = {
                'values': [headers]
            }
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            logger.info(f"Updated headers for sheet {spreadsheet_id}: {result.get('updatedCells')} cells updated")
        except HttpError as error:
            logger.error(f"An error occurred writing headers to {spreadsheet_id}: {error}")
            raise

    def setup_evidence_loop(self, folder_id: Optional[str] = None):
        """Create all 9 Evidence Loop sheets with defined schemas."""
        
        # Schema definitions from docs/02_EVIDENCE_LOOP_CANVAS.md
        schemas = {
            "VDG_Outlier_Raw": [
                "source_name", "source_url", "collected_at", "platform", "category", 
                "title", "views", "growth_rate", "author", "posted_at", "status"
            ],
            "VDG_Parent_Candidates": [
                "parent_id", "title", "platform", "category", "source_url", 
                "baseline_views", "baseline_engagement", "selected_by", "selected_at", "status"
            ],
            "VDG_Evidence": [
                "evidence_id", "parent_id", "parent_title", "depth", "variant_id", "variant_name",
                "views", "engagement_rate", "retention_rate", "tracking_days", 
                "confidence_score", "confidence_ci_low", "confidence_ci_high", 
                "rank", "winner", "generated_at"
            ],
            "VDG_Decision": [
                "decision_id", "parent_id", "winner_variant_id", "winner_variant_name",
                "top_reasons", "risks", "next_experiment", "sample_size", 
                "tracking_days", "success_criteria", "status", "created_at"
            ],
            "VDG_Experiment": [
                "experiment_id", "parent_id", "variant_id", "assigned_creators", 
                "start_date", "end_date", "status", "notes"
            ],
            "VDG_Progress": [
                "variant_id", "date", "views", "engagement_rate", 
                "retention_rate", "confidence_score", "status"
            ],
            "VDG_O2O_Campaigns": [
                "campaign_id", "campaign_type", "title", "brand", "category", 
                "reward_points", "reward_product", "location_name", "address", 
                "status", "start_date", "end_date"
            ],
            "VDG_O2O_Applications": [
                "application_id", "campaign_id", "user_id", "status", 
                "applied_at", "updated_at", "shipment_tracking"
            ],
            "VDG_Insights": [
                "parent_id", "summary", "key_patterns", "risks", "created_at"
            ]
        }

        created_sheets = {}
        for title, headers in schemas.items():
            print(f"Creating {title}...")
            sheet_id = self.create_sheet(title, folder_id)
            self.write_header(sheet_id, headers)
            created_sheets[title] = sheet_id
        
        return created_sheets
