# backend/app/services/vdg_2pass/unified_pass.py
"""
VDG Unified Pass (Pass 1: Gemini 3.0 Pro 1회 호출)

핵심 설계:
- Pass 1: LLM이 의미/인과/Plan Seed 생성
- Pass 2: CV가 결정론적 수치 측정

API 특징:
- VideoMetadata: hook clip (10fps) + full video (1fps) 분리
- media_resolution: low/high로 토큰 비용 제어
- response_schema: structured output
"""
from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from google.genai import types

from app.services.genai_client import get_genai_client, DEFAULT_MODEL_PRO
from app.schemas.metric_registry import METRIC_DEFINITIONS, validate_metric_id
from app.schemas.vdg_unified_pass import UnifiedPassLLMOutput
from app.services.vdg_2pass.prompts.unified_prompt import (
    build_unified_prompt,
    PROMPT_VERSION_UNIFIED,
)

logger = logging.getLogger(__name__)


# ============================================
# Provenance
# ============================================

@dataclass(frozen=True)
class UnifiedPassProvenance:
    """Pass 1 실행 메타데이터"""
    prompt_version: str
    model_id: str
    run_at: str
    media_resolution: str
    hook_clip_fps: float
    full_video_fps: float
    hook_clip_window: str  # e.g. "0s-4s"
    latency_ms: int = 0
    usage: Optional[Dict[str, Any]] = None


# ============================================
# Exceptions
# ============================================

class UnifiedPassError(RuntimeError):
    """Unified Pass 실행 오류"""
    pass


# ============================================
# Main Class
# ============================================

class UnifiedPass:
    """
    Pass 1: Gemini 3.0 Pro 1회 호출 (의미/인과/Plan seed)
    
    설계 원칙:
    - Hook clip (0~4s): 10fps (정밀 microbeat 분석)
    - Full video: 1fps (전체 인과관계)
    - Structured output: response_schema 사용
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        media_resolution: Optional[str] = None,  # "low" or "high"
        hook_clip_seconds: float = 4.0,
        hook_clip_fps: float = 10.0,
        full_video_fps: float = 1.0,
        max_output_tokens: int = 8192,
        temperature: float = 0.2,
    ):
        self.model_id = model_id or os.getenv("VDG_PRO_MODEL", DEFAULT_MODEL_PRO)
        self.media_resolution = media_resolution or os.getenv("VDG_MEDIA_RESOLUTION", "low")
        self.hook_clip_seconds = hook_clip_seconds
        self.hook_clip_fps = hook_clip_fps
        self.full_video_fps = full_video_fps
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature

    def run(
        self,
        *,
        video_path: str,
        duration_ms: int,
        platform: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        top_comments: Optional[List[str]] = None,
    ) -> Tuple[UnifiedPassLLMOutput, UnifiedPassProvenance]:
        """
        Unified Pass 실행
        
        Args:
            video_path: 비디오 파일 경로
            duration_ms: 비디오 길이 (밀리초)
            platform: 플랫폼 (tiktok/youtube/instagram)
            caption: 영상 캡션
            hashtags: 해시태그 목록
            top_comments: 상위 댓글 목록
        
        Returns:
            (UnifiedPassLLMOutput, UnifiedPassProvenance)
        """
        start_time = time.time()
        client = get_genai_client()
        top_comments = top_comments or []

        # 1. 비디오 업로드
        video_file = self._upload_video(client, video_path)
        logger.info(f"📹 Video uploaded: {video_file.name}")

        # 2. Two video parts in ONE request:
        #    - Hook clip: 0~hook_clip_seconds with higher fps for precise microbeats
        #    - Full video: low fps for global causality
        hook_part = types.Part.from_uri(
            file_uri=video_file.uri,
            mime_type=video_file.mime_type,
            video_metadata=types.VideoMetadata(
                start_offset="0s",
                end_offset=f"{self.hook_clip_seconds}s",
                fps=self.hook_clip_fps,
            ),
        )
        full_part = types.Part.from_uri(
            file_uri=video_file.uri,
            mime_type=video_file.mime_type,
            video_metadata=types.VideoMetadata(
                fps=self.full_video_fps,
            ),
        )

        # 3. 프롬프트 빌드 (Metric Registry SSoT에서 allow-list 주입)
        prompt = build_unified_prompt(
            duration_ms=duration_ms,
            platform=platform,
            caption=caption,
            hashtags=hashtags,
            top_comments=top_comments,
            metric_definitions=METRIC_DEFINITIONS,
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=prompt),
                    hook_part,
                    full_part,
                ],
            )
        ]

        # 4. API 호출 (Structured output)
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=0.95,
            max_output_tokens=self.max_output_tokens,
            response_mime_type="application/json",
            response_schema=UnifiedPassLLMOutput,
        )

        try:
            resp = client.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=config,
            )
        except Exception as e:
            raise UnifiedPassError(f"UnifiedPass API call failed: {e}") from e

        latency_ms = int((time.time() - start_time) * 1000)

        # 5. Parse response
        if not resp.text:
            raise UnifiedPassError("UnifiedPass returned empty response")

        try:
            # SDK의 parsed 속성 사용 시도
            if hasattr(resp, 'parsed') and resp.parsed is not None:
                out: UnifiedPassLLMOutput = resp.parsed
            else:
                # Fallback: JSON 직접 파싱
                out = UnifiedPassLLMOutput.model_validate_json(resp.text)
        except Exception as e:
            raise UnifiedPassError(
                f"UnifiedPass JSON parse failed: {e}\nRaw: {resp.text[:800]}"
            ) from e

        # 6. Metric ID 정규화/검증
        out = self._normalize_and_validate_metrics(out)

        # 7. Usage 추출
        usage = None
        if hasattr(resp, 'usage_metadata'):
            usage = {
                "prompt_tokens": getattr(resp.usage_metadata, 'prompt_token_count', 0),
                "completion_tokens": getattr(resp.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(resp.usage_metadata, 'total_token_count', 0),
            }

        # 8. Provenance 생성
        prov = UnifiedPassProvenance(
            prompt_version=PROMPT_VERSION_UNIFIED,
            model_id=self.model_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            media_resolution=self.media_resolution,
            hook_clip_fps=self.hook_clip_fps,
            full_video_fps=self.full_video_fps,
            hook_clip_window=f"0s-{self.hook_clip_seconds}s",
            latency_ms=latency_ms,
            usage=usage,
        )

        logger.info(
            f"✅ UnifiedPass completed: latency={latency_ms}ms, "
            f"analysis_points={len(out.analysis_plan.points)}"
        )

        return out, prov

    # ============================================
    # Helpers
    # ============================================

    def _upload_video(self, client, video_path: str):
        """비디오 파일 업로드 및 처리 대기"""
        p = Path(video_path)
        if not p.exists():
            raise UnifiedPassError(f"video_path not found: {video_path}")

        video_file = client.files.upload(file=p)

        # Poll until ACTIVE (일부 모델은 처리 시간 필요)
        for _ in range(60):
            state = getattr(video_file, "state", None)
            name = getattr(state, "name", None) if state else None
            if name in (None, "ACTIVE", "SUCCEEDED"):
                return video_file
            if name in ("FAILED", "ERROR"):
                raise UnifiedPassError(f"video file processing failed: state={name}")
            time.sleep(1.0)
            try:
                video_file = client.files.get(name=video_file.name)
            except Exception:
                pass

        return video_file

    def _normalize_and_validate_metrics(
        self, out: UnifiedPassLLMOutput
    ) -> UnifiedPassLLMOutput:
        """Metric ID 정규화 및 allow-list 검증"""
        allowed = set(METRIC_DEFINITIONS.keys())

        for p in out.analysis_plan.points:
            for m in p.measurements:
                canonical = validate_metric_id(m.metric_id)
                m.metric_id = canonical
                if canonical not in allowed:
                    raise UnifiedPassError(
                        f"LLM returned unknown metric_id: {canonical}"
                    )

        return out


# ============================================
# ffprobe duration helper
# ============================================

def get_video_duration_ms(video_path: str) -> int:
    """ffprobe로 비디오 길이 추출 (밀리초)"""
    import subprocess
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        duration_sec = float(result.stdout.strip())
        return int(duration_sec * 1000)
    except Exception as e:
        logger.warning(f"ffprobe failed, using 0: {e}")
        return 0
