import logging
import re
import google.auth
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.auth.credentials import with_scopes_if_required

logger = logging.getLogger(__name__)

# Retry decorator for transient Google API errors
def _google_api_retry():
    """Decorator for retrying Google API calls with exponential backoff."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(HttpError),
        reraise=True
    )

class SheetManager:
    def __init__(self, credentials=None):
        try:
            # Scopes needed for Drive (create file) and Sheets (edit content)
            self.scopes = [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            self.folder_id = os.environ.get("KOMISSION_FOLDER_ID")
            
            if credentials:
                self.creds = credentials
                self.project_id = getattr(credentials, 'quota_project_id', 'unknown')
                logger.info("Using provided credentials.")
            else:
                # Try Service Account from Env first (for Server Automation)
                service_account_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                if service_account_path and os.path.exists(service_account_path):
                    try:
                        self.creds, self.project_id = google.auth.load_credentials_from_file(
                            service_account_path, scopes=self.scopes
                        )
                        self.creds = with_scopes_if_required(self.creds, scopes=self.scopes)
                        logger.info(f"Authenticated with Credentials File: {service_account_path}")
                        if not self.project_id:
                            self.project_id = getattr(self.creds, 'project_id', 'unknown')
                    except Exception as e:
                        logger.warning(f"Failed to load credentials file: {e}. Falling back to default auth.")
                        self.creds, self.project_id = google.auth.default(scopes=self.scopes)
                        logger.info(f"Authenticated with Default/Gcloud. Project ID: {self.project_id}")
                else:
                    # Fallback to gcloud default (for Local Dev)
                    self.creds, self.project_id = google.auth.default(scopes=self.scopes)
                    logger.info(f"Authenticated with Default/Gcloud. Project ID: {self.project_id}")

            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google: {e}")
            raise

    def _validate_sheet_title(self, title: str):
        """Validate sheet title to prevent injection or malformed names."""
        if not title or not isinstance(title, str):
            raise ValueError("Sheet title must be a non-empty string.")
        if len(title) > 100:
            raise ValueError(f"Sheet title too long ({len(title)} chars, max 100).")
        if not re.match(r'^[\w\-_ ]+$', title):
            raise ValueError(f"Invalid sheet title: '{title}'. Use only letters, numbers, spaces, underscores, hyphens.")


    @_google_api_retry()
    def create_sheet(self, title: str, folder_id: Optional[str] = None) -> str:
        """Create a new Google Sheet and return its ID."""
        self._validate_sheet_title(title)
        try:
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
            target_folder_id = folder_id or self.folder_id
            if target_folder_id:
                file_metadata['parents'] = [target_folder_id]

            file = self.drive_service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
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
                "rank", "winner", "generated_at", "data_source"
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
                "retention_rate", "confidence_score", "status", "parent_id", "variant_name"
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

    @_google_api_retry()
    def find_sheet_id(self, title: str) -> Optional[str]:
        """Find a Google Sheet ID by its name."""
        self._validate_sheet_title(title)
        try:
            query = f"name = '{title}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
            if self.folder_id:
                query = f"{query} and '{self.folder_id}' in parents"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            files = results.get('files', [])
            if not files:
                logger.warning(f"No sheet found with title: {title}")
                return None
            return files[0]['id']
        except HttpError as error:
            logger.error(f"An error occurred searching for sheet '{title}': {error}")
            return None

    @_google_api_retry()
    def append_data(self, sheet_title: str, rows: List[List[object]]):
        """Append data rows to the specified sheet."""
        sheet_id = self.find_sheet_id(sheet_title)
        if not sheet_id:
            logger.error(f"Cannot append data: Sheet '{sheet_title}' not found.")
            return

        try:
            body = {
                'values': rows
            }
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range='A1',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            logger.info(f"Appended {result.get('updates').get('updatedRows')} rows to {sheet_title} ({sheet_id})")
        except HttpError as error:
            logger.error(f"An error occurred appending data to {sheet_title}: {error}")
            raise

    def share_sheet(self, sheet_id: str, email_address: str, role: str = 'writer'):
        """Share a sheet with a specific email address."""
        try:
            user_permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email_address
            }
            self.drive_service.permissions().create(
                fileId=sheet_id,
                body=user_permission,
                fields='id',
                supportsAllDrives=True
            ).execute()
            logger.info(f"Shared sheet {sheet_id} with {email_address} as {role}")
        except HttpError as error:
            logger.error(f"An error occurred sharing sheet {sheet_id}: {error}")
            # Don't raise here to allow batch operations to continue even if one fails (e.g. already shared)
