"""
Google Cloud Podcast API Client (Standalone)

독립형 Podcast API - NotebookLM 노트북 없이 직접 팟캐스트 생성

Features:
- 텍스트/이미지/오디오/비디오 컨텍스트 입력
- 커스텀 Focus 프롬프트
- 한국어 포함 다국어 지원
- SHORT (4-5분) / STANDARD (10분) 길이 선택
- MP3 직접 다운로드

Reference: 
- https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-podcasts
- discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/podcasts

Usage:
    client = PodcastAPIClient(project_id="your-project-id")
    
    # Create podcast
    operation = await client.create_podcast(
        contexts=[{"text": "VDG 분석 결과..."}],
        focus="촬영 가이드로 설명해줘",
        length="SHORT",
        language_code="ko",
        title="훅 패턴 촬영 가이드",
    )
    
    # Wait and download
    mp3_bytes = await client.wait_and_download(operation["operation_name"])
"""
import asyncio
import logging
import os
import subprocess
from typing import Any, Dict, List, Literal, Optional

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discovery Engine API v1 (Podcast API - NOT v1alpha)
PODCAST_API_BASE = "https://discoveryengine.googleapis.com/v1"


class PodcastAPIClient:
    """
    Google Cloud Podcast API Client (Standalone)
    
    NotebookLM 없이 직접 팟캐스트 생성 가능.
    VDG 분석 결과를 입력하면 촬영 가이드/바이럴 가이드 오디오 생성.
    """
    
    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize Podcast API client.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON (optional, uses gcloud if not set)
        """
        self.project_id = project_id
        self.base_url = f"{PODCAST_API_BASE}/projects/{project_id}/locations/global"
        
        self._access_token: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self.credentials_path = credentials_path
        
        logger.info(f"Podcast API client initialized for project: {project_id}")
    
    def _get_access_token(self) -> str:
        """Get access token using gcloud CLI."""
        if self._access_token:
            return self._access_token
        
        try:
            # Try specific account first
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                self._access_token = result.stdout.strip()
                logger.info("Using gcloud CLI access token")
                return self._access_token
        except Exception as e:
            logger.warning(f"gcloud CLI token not available: {e}")
        
        raise RuntimeError(
            "Failed to get access token. Run 'gcloud auth login' first."
        )
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get authorization header."""
        token = self._get_access_token()
        return {"Authorization": f"Bearer {token}"}
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    # ==================
    # Podcast Generation
    # ==================
    
    async def create_podcast(
        self,
        contexts: List[Dict[str, Any]],
        focus: str,
        length: Literal["SHORT", "STANDARD"] = "SHORT",
        language_code: str = "ko",
        title: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a podcast from contexts.
        
        Args:
            contexts: List of content dicts. Each dict should have one of:
                - {"text": "plain text content"}
                - {"blob": {"mimeType": "image/png", "data": "base64..."}}
            focus: Focus prompt for the podcast content
            length: "SHORT" (4-5min) or "STANDARD" (~10min)
            language_code: BCP47 language code (e.g., "ko", "en", "ja")
            title: Podcast title
            description: Podcast description
            
        Returns:
            Operation info with operation_name for status polling and download
        """
        client = await self._get_client()
        
        payload = {
            "podcastConfig": {
                "focus": focus,
                "length": length,
                "languageCode": language_code,
            },
            "contexts": contexts,
            "title": title,
            "description": description,
        }
        
        response = await client.post(
            f"{self.base_url}/podcasts",
            headers={
                **self._get_auth_header(),
                "Content-Type": "application/json",
            },
            json=payload,
        )
        
        if not response.is_success:
            error_detail = response.text
            logger.error(f"Podcast creation failed: {response.status_code} - {error_detail}")
            raise RuntimeError(f"Podcast creation failed: {response.status_code} - {error_detail}")
        
        result = response.json()
        operation_name = result.get("name", "")
        
        logger.info(f"Podcast creation started: {operation_name}")
        
        return {
            "operation_name": operation_name,
            "status": "in_progress",
            "raw_response": result,
        }
    
    async def get_operation_status(self, operation_name: str) -> Dict[str, Any]:
        """
        Get operation status.
        
        Args:
            operation_name: Operation name from create_podcast response
            
        Returns:
            Operation status info
        """
        client = await self._get_client()
        
        # Operation status endpoint
        response = await client.get(
            f"{PODCAST_API_BASE}/{operation_name}",
            headers=self._get_auth_header(),
        )
        
        if not response.is_success:
            logger.error(f"Status check failed: {response.status_code}")
            raise RuntimeError(f"Status check failed: {response.status_code}")
        
        result = response.json()
        done = result.get("done", False)
        
        return {
            "operation_name": operation_name,
            "done": done,
            "status": "completed" if done else "in_progress",
            "raw_response": result,
        }
    
    async def download_podcast(self, operation_name: str) -> bytes:
        """
        Download completed podcast as MP3.
        
        Args:
            operation_name: Operation name from create_podcast response
            
        Returns:
            MP3 audio bytes
        """
        client = await self._get_client()
        
        # Download endpoint with alt=media
        response = await client.get(
            f"{PODCAST_API_BASE}/{operation_name}:download",
            params={"alt": "media"},
            headers=self._get_auth_header(),
            follow_redirects=True,
        )
        
        if not response.is_success:
            logger.error(f"Download failed: {response.status_code}")
            raise RuntimeError(f"Download failed: {response.status_code}")
        
        logger.info(f"Downloaded podcast: {len(response.content)} bytes")
        return response.content
    
    async def wait_and_download(
        self,
        operation_name: str,
        poll_interval: float = 5.0,
        max_wait: float = 600.0,  # 10 minutes max
    ) -> bytes:
        """
        Wait for podcast generation and download.
        
        Args:
            operation_name: Operation name from create_podcast response
            poll_interval: Seconds between status checks
            max_wait: Maximum wait time in seconds
            
        Returns:
            MP3 audio bytes
        """
        elapsed = 0.0
        
        while elapsed < max_wait:
            status = await self.get_operation_status(operation_name)
            
            if status["done"]:
                logger.info(f"Podcast ready after {elapsed:.1f}s")
                return await self.download_podcast(operation_name)
            
            logger.info(f"Waiting for podcast... ({elapsed:.0f}s)")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise TimeoutError(f"Podcast generation timed out after {max_wait}s")


# ==================
# Focus Prompt Templates
# ==================

FOCUS_TEMPLATES = {
    "shooting_guide": """
이 분석 결과를 바탕으로 숏폼 촬영 가이드를 만들어줘.

촬영자가 이어폰으로 들으면서 바로 따라할 수 있도록:
1. 장면별 카메라 워크 (롱샷, 클로즈업 등)
2. 정확한 타이밍 (몇 초에 무엇을)
3. 오디오 포인트 (어디서 음악 드롭, 효과음)
4. 핵심적으로 지켜야 할 것
5. 절대 하지 말아야 할 것

마치 영화 감독이 현장에서 지시하듯이 명확하고 간결하게.
""",
    
    "viral_guide": """
이 아웃라이어 콘텐츠가 왜 바이럴되었는지 분석해줘.

크리에이터가 이해하기 쉽게:
1. 훅이 왜 강력한지
2. 어떤 감정을 자극하는지
3. 댓글 반응에서 알 수 있는 핵심 포인트
4. 이 패턴을 응용할 때 주의할 점
5. 비슷하게 만들려면 꼭 지켜야 할 것

친근하지만 프로페셔널한 톤으로.
""",
    
    "pattern_overview": """
이 패턴 클러스터에 속한 영상들의 공통점을 설명해줘.

패턴을 처음 접하는 크리에이터를 위해:
1. 패턴 이름의 의미
2. 왜 이 패턴이 효과적인지
3. 성공 사례에서 공통적으로 나타나는 요소
4. 이 패턴의 best practice
5. 흔한 실수와 피해야 할 것

마치 선배 크리에이터가 후배에게 알려주듯이.
""",
}


def get_focus_template(template_type: str) -> str:
    """Get focus prompt template by type."""
    return FOCUS_TEMPLATES.get(template_type, FOCUS_TEMPLATES["shooting_guide"])


# ==================
# Helper Functions
# ==================

def get_client(project_id: Optional[str] = None) -> PodcastAPIClient:
    """
    Get Podcast API client with defaults from environment.
    
    Environment variables:
    - PODCAST_API_PROJECT_ID: GCP project ID
    """
    project = project_id or os.environ.get("PODCAST_API_PROJECT_ID")
    if not project:
        # Fallback to NotebookLM project ID
        project = os.environ.get("NOTEBOOKLM_PROJECT_ID")
    if not project:
        raise ValueError("project_id required (or set PODCAST_API_PROJECT_ID)")
    
    return PodcastAPIClient(project_id=project)


def build_vdg_context(vdg_analysis: Dict[str, Any], best_comments: List[str] = None) -> str:
    """
    Build context text from VDG analysis for podcast generation.
    
    Args:
        vdg_analysis: VDG analysis result dict
        best_comments: Optional list of best comments
        
    Returns:
        Formatted context text
    """
    parts = []
    
    # Title
    if vdg_analysis.get("title"):
        parts.append(f"# 영상 제목: {vdg_analysis['title']}")
    
    # Hook info
    if vdg_analysis.get("hook_genome"):
        hook = vdg_analysis["hook_genome"]
        parts.append(f"\n## 훅 분석")
        parts.append(f"- 패턴: {hook.get('pattern', 'N/A')}")
        parts.append(f"- 강도: {hook.get('strength', 'N/A')}")
        parts.append(f"- 지속시간: {hook.get('duration_sec', 'N/A')}초")
    
    # Scenes
    if vdg_analysis.get("scenes"):
        parts.append(f"\n## 장면 분석")
        for i, scene in enumerate(vdg_analysis["scenes"][:5]):  # Limit to 5 scenes
            narrative = scene.get("narrative_unit", {})
            parts.append(f"\n### 장면 {i+1}")
            parts.append(f"- 역할: {narrative.get('role', 'N/A')}")
            parts.append(f"- 요약: {narrative.get('summary', 'N/A')}")
            if narrative.get("dialogue"):
                parts.append(f"- 대사: {narrative['dialogue']}")
            
            # Camera info
            shots = scene.get("shots", [])
            if shots:
                cam = shots[0].get("camera", {})
                parts.append(f"- 카메라: {cam.get('shot', '')} / {cam.get('move', '')} / {cam.get('angle', '')}")
            
            # Timing
            if "duration_sec" in scene:
                parts.append(f"- 길이: {scene['duration_sec']}초")
    
    # Best comments
    if best_comments:
        parts.append(f"\n## 베스트 댓글 반응")
        for comment in best_comments[:5]:
            parts.append(f"- {comment}")
    
    return "\n".join(parts)
