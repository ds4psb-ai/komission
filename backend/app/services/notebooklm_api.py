"""
NotebookLM Enterprise API Client (Phase D)

Provides automation for NotebookLM notebook lifecycle:
- Create notebooks with sources
- Add/sync sources
- Fetch Data Tables outputs
- Share/archive notebooks

Reference: docs/18_NOTEBOOKLM_ENTERPRISE_INTEGRATION.md

Usage:
    client = NotebookLMClient(
        project_id="algebraic-envoy-456610-h8",
        project_number="297976838198"
    )
    notebook_id = await client.create_notebook("My Notebook", sources=["..."])
"""
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discovery Engine API v1alpha (NotebookLM Enterprise)
NOTEBOOKLM_API_BASE = "https://discoveryengine.googleapis.com/v1alpha"


class NotebookLMClient:
    """
    NotebookLM Enterprise API Client
    
    Enables programmatic control of NotebookLM notebooks:
    - create_notebook: Create new notebook with title and sources
    - get_notebook: Get notebook metadata
    - add_sources: Add sources to existing notebook
    - share_notebook: Share with users/service accounts
    - archive_notebook: Archive/delete notebook
    - get_data_tables: Fetch Data Tables output for DB ingestion
    
    Reference: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks
    """
    
    def __init__(
        self,
        project_id: str,
        project_number: Optional[str] = None,
        location: str = "global",
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize NotebookLM client.
        
        Args:
            project_id: GCP project ID (e.g., 'algebraic-envoy-456610-h8')
            project_number: GCP project NUMBER (e.g., '297976838198') - required for Discovery Engine
            location: API location (global, us, eu)
            credentials_path: Path to service account JSON (optional, uses ADC if not set)
        """
        self.project_id = project_id
        self.project_number = project_number or os.environ.get("NOTEBOOKLM_PROJECT_NUMBER")
        self.location = location
        
        # Discovery Engine requires project NUMBER in the path
        if not self.project_number:
            raise ValueError(
                "project_number is required for Discovery Engine API. "
                "Set via parameter or NOTEBOOKLM_PROJECT_NUMBER env var."
            )
        
        # Discovery Engine API requires location prefix in hostname
        # Format: {location}-discoveryengine.googleapis.com
        location_prefix = f"{location}-" if location != "global" else "global-"
        self.base_url = f"https://{location_prefix}discoveryengine.googleapis.com/v1alpha/projects/{self.project_number}/locations/{location}"
        logger.info(f"NotebookLM API base URL: {self.base_url}")
        
        # Load credentials
        self.credentials = self._load_credentials(credentials_path)
        self._http_client: Optional[httpx.AsyncClient] = None
    
    def _load_credentials(self, credentials_path: Optional[str] = None):
        """Load GCP credentials with gcloud fallback."""
        import subprocess
        
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        
        # Option 1: Explicit service account file
        if credentials_path:
            return service_account.Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )
        
        # Option 2: Environment variable (skip if it's the wrong project)
        env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_path and os.path.exists(env_path):
            try:
                import json
                with open(env_path) as f:
                    sa_info = json.load(f)
                # Only use if it matches our project
                if sa_info.get("project_id") == self.project_id:
                    return service_account.Credentials.from_service_account_file(
                        env_path, scopes=scopes
                    )
                else:
                    logger.info(f"Skipping SA file (project mismatch): {sa_info.get('project_id')} != {self.project_id}")
            except Exception as e:
                logger.warning(f"Failed to read SA file: {e}")
        
        # Option 3: gcloud CLI token (PRIORITY - uses ted.taeeun.kim@gmail.com)
        try:
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token", "--account=ted.taeeun.kim@gmail.com"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
                logger.info("Using gcloud CLI token for ted.taeeun.kim@gmail.com")
                # Return a simple object that holds the token
                return type('GcloudToken', (), {'token': token, 'expired': False})()
        except Exception as e:
            logger.info(f"gcloud CLI token not available: {e}")
        
        # Option 4: ADC (fallback)
        try:
            from google.auth import default
            credentials, project = default(scopes=scopes)
            logger.info(f"Using ADC credentials (project: {project})")
            return credentials
        except Exception as e:
            logger.warning(f"ADC not available: {e}")
        
        return None
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get authorization header with refreshed token."""
        if not self.credentials:
            raise RuntimeError("No credentials available")
        
        # Handle gcloud token (simple object)
        if hasattr(self.credentials, 'token') and not hasattr(self.credentials, 'refresh'):
            return {"Authorization": f"Bearer {self.credentials.token}"}
        
        # Handle standard Google credentials
        if self.credentials.expired or not self.credentials.token:
            self.credentials.refresh(Request())
        
        return {"Authorization": f"Bearer {self.credentials.token}"}
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    # ==================
    # Notebook Operations
    # ==================
    
    async def create_notebook(
        self,
        title: str,
        sources: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new NotebookLM notebook.
        
        Args:
            title: Notebook title
            sources: Optional list of source URLs to add
            description: Optional description
            
        Returns:
            Created notebook metadata including notebook_id
        """
        client = await self._get_client()
        
        payload = {
            "title": title,
        }
        # Note: description field is not supported by the API
        
        response = await client.post(
            f"{self.base_url}/notebooks",
            headers={
                **self._get_auth_header(),
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        
        notebook = response.json()
        notebook_id = notebook.get("name", "").split("/")[-1]
        
        logger.info(f"Created notebook: {notebook_id}")
        
        # Add sources if provided
        if sources:
            await self.add_sources(notebook_id, sources)
        
        return notebook
    
    async def get_notebook(self, notebook_id: str) -> Dict[str, Any]:
        """
        Get notebook metadata.
        
        Args:
            notebook_id: Notebook ID
            
        Returns:
            Notebook metadata
        """
        client = await self._get_client()
        
        response = await client.get(
            f"{self.base_url}/notebooks/{notebook_id}",
            headers=self._get_auth_header(),
        )
        response.raise_for_status()
        
        return response.json()
    
    async def add_sources(
        self,
        notebook_id: str,
        source_urls: List[str],
        source_contents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Add sources to an existing notebook using batchCreate.
        
        Args:
            notebook_id: Notebook ID
            source_urls: List of source URLs (Drive, Sheets, YouTube, etc.)
            source_contents: Optional list of raw content dicts with 'content' and 'mimeType'
            
        Returns:
            Operation result
        """
        client = await self._get_client()
        
        # Build userContents array - supports text, web URLs, YouTube, and Google Drive
        # Ref: https://cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources
        user_contents = []
        
        for url in source_urls:
            if "youtube.com" in url or "youtu.be" in url:
                # YouTube video content
                user_contents.append({"videoContent": {"url": url}})
            elif url.startswith(("http://", "https://")):
                # Web content
                user_contents.append({"webContent": {"url": url, "sourceName": url}})
            else:
                # Treat as Google Drive document ID
                user_contents.append({"googleDriveContent": {
                    "documentId": url,
                    "mimeType": "application/vnd.google-apps.document",
                    "sourceName": url
                }})
        
        # Add raw text content
        if source_contents:
            for content in source_contents:
                user_contents.append({"textContent": {
                    "sourceName": content.get("displayName", "Untitled"),
                    "content": content.get("content", ""),
                }})
        
        if not user_contents:
            return {"sources": []}
        
        response = await client.post(
            f"{self.base_url}/notebooks/{notebook_id}/sources:batchCreate",
            headers={
                **self._get_auth_header(),
                "Content-Type": "application/json",
            },
            json={"userContents": user_contents},
        )
        response.raise_for_status()
        
        result = response.json()
        sources_added = len(result.get("sources", []))
        logger.info(f"Added {sources_added} sources to notebook {notebook_id}")
        return result
    
    async def share_notebook(
        self,
        notebook_id: str,
        email: str,
        role: str = "reader",
    ) -> Dict[str, Any]:
        """
        Share notebook with a user.
        
        Args:
            notebook_id: Notebook ID
            email: Email to share with
            role: Permission role (reader, writer, owner)
            
        Returns:
            Share result
        """
        client = await self._get_client()
        
        response = await client.post(
            f"{self.base_url}/notebooks/{notebook_id}:share",
            headers={
                **self._get_auth_header(),
                "Content-Type": "application/json",
            },
            json={
                "email": email,
                "role": role,
            },
        )
        response.raise_for_status()
        
        logger.info(f"Shared notebook {notebook_id} with {email} as {role}")
        return response.json()
    
    async def archive_notebook(self, notebook_id: str) -> bool:
        """
        Archive (soft delete) a notebook.
        
        Args:
            notebook_id: Notebook ID
            
        Returns:
            True if successful
        """
        client = await self._get_client()
        
        response = await client.delete(
            f"{self.base_url}/notebooks/{notebook_id}",
            headers=self._get_auth_header(),
        )
        response.raise_for_status()
        
        logger.info(f"Archived notebook {notebook_id}")
        return True
    
    async def list_notebooks(
        self,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List notebooks in the project.
        
        Args:
            page_size: Number of notebooks per page
            page_token: Pagination token
            
        Returns:
            List of notebooks with pagination info
        """
        client = await self._get_client()
        
        params = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
        
        response = await client.get(
            f"{self.base_url}/notebooks",
            headers=self._get_auth_header(),
            params=params,
        )
        response.raise_for_status()
        
        return response.json()
    
    # ==================
    # Data Tables (Phase B Integration)
    # ==================
    
    async def get_data_tables(
        self,
        notebook_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch Data Tables output from a notebook.
        
        This is used for Phase B integration: Data Tables → DB
        
        Args:
            notebook_id: Notebook ID
            
        Returns:
            List of data tables with structured content
        """
        client = await self._get_client()
        
        response = await client.get(
            f"{self.base_url}/notebooks/{notebook_id}/dataTables",
            headers=self._get_auth_header(),
        )
        response.raise_for_status()
        
        data = response.json()
        tables = data.get("dataTables", [])
        
        logger.info(f"Fetched {len(tables)} data tables from notebook {notebook_id}")
        return tables
    
    async def export_data_table_to_sheets(
        self,
        notebook_id: str,
        table_id: str,
    ) -> str:
        """
        Export a Data Table to Google Sheets.
        
        Args:
            notebook_id: Notebook ID
            table_id: Data Table ID
            
        Returns:
            Google Sheets URL
        """
        client = await self._get_client()
        
        response = await client.post(
            f"{self.base_url}/notebooks/{notebook_id}/dataTables/{table_id}:exportToSheets",
            headers={
                **self._get_auth_header(),
                "Content-Type": "application/json",
            },
            json={},
        )
        response.raise_for_status()
        
        result = response.json()
        sheets_url = result.get("sheetsUrl", "")
        
        logger.info(f"Exported data table to: {sheets_url}")
        return sheets_url


# ==================
# Helper Functions
# ==================

def get_client(
    project_id: Optional[str] = None,
    project_number: Optional[str] = None,
    credentials_path: Optional[str] = None,
) -> NotebookLMClient:
    """
    Get NotebookLM client with defaults from environment.
    
    Environment variables:
    - NOTEBOOKLM_PROJECT_ID: GCP project ID
    - NOTEBOOKLM_PROJECT_NUMBER: GCP project NUMBER (required for Discovery Engine)
    
    Note: GOOGLE_APPLICATION_CREDENTIALS is handled internally by NotebookLMClient
    with project mismatch checking and gcloud token fallback.
    """
    project = project_id or os.environ.get("NOTEBOOKLM_PROJECT_ID")
    if not project:
        raise ValueError("project_id required (or set NOTEBOOKLM_PROJECT_ID)")
    
    number = project_number or os.environ.get("NOTEBOOKLM_PROJECT_NUMBER")
    
    # Only pass credentials_path if explicitly provided
    # Let NotebookLMClient handle the project mismatch and gcloud fallback
    return NotebookLMClient(
        project_id=project,
        project_number=number,
        credentials_path=credentials_path,  # Only use if explicitly passed
    )
