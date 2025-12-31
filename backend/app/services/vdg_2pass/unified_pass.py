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
    - Zoom Windows: 5fps (scene cuts + audio peaks)
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
        # Zoom Windows 설정
        enable_zoom_windows: bool = True,
        zoom_window_fps: float = 5.0,
        zoom_window_duration: float = 2.0,  # 각 zoom window ±1초
        max_zoom_windows: int = 4,
    ):
        self.model_id = model_id or os.getenv("VDG_PRO_MODEL", DEFAULT_MODEL_PRO)
        self.media_resolution = media_resolution or os.getenv("VDG_MEDIA_RESOLUTION", "low")
        self.hook_clip_seconds = hook_clip_seconds
        self.hook_clip_fps = hook_clip_fps
        self.full_video_fps = full_video_fps
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        # Zoom Windows
        self.enable_zoom_windows = enable_zoom_windows
        self.zoom_window_fps = zoom_window_fps
        self.zoom_window_duration = zoom_window_duration
        self.max_zoom_windows = max_zoom_windows

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

        # 2. Video parts in ONE request (추가 호출 없이 심층 해석):
        #    - Hook clip: 0~hook_clip_seconds with higher fps for precise microbeats
        #    - Zoom Windows: scene cuts + audio peaks with medium fps
        #    - Full video: low fps for global causality
        
        video_parts = []
        
        # Hook part (항상 포함)
        hook_part = types.Part.from_uri(
            file_uri=video_file.uri,
            mime_type=video_file.mime_type,
            video_metadata=types.VideoMetadata(
                start_offset="0s",
                end_offset=f"{self.hook_clip_seconds}s",
                fps=self.hook_clip_fps,
            ),
        )
        video_parts.append(hook_part)
        
        # Zoom Windows (scene cuts + audio peaks)
        zoom_windows = []
        if self.enable_zoom_windows:
            zoom_windows = self._detect_zoom_windows(
                video_path,
                duration_ms,
                max_windows=self.max_zoom_windows
            )
            for i, (start_sec, end_sec) in enumerate(zoom_windows):
                zoom_part = types.Part.from_uri(
                    file_uri=video_file.uri,
                    mime_type=video_file.mime_type,
                    video_metadata=types.VideoMetadata(
                        start_offset=f"{start_sec:.1f}s",
                        end_offset=f"{end_sec:.1f}s",
                        fps=self.zoom_window_fps,
                    ),
                )
                video_parts.append(zoom_part)
            logger.info(f"🔍 Added {len(zoom_windows)} zoom windows")
        
        # Full video part
        full_part = types.Part.from_uri(
            file_uri=video_file.uri,
            mime_type=video_file.mime_type,
            video_metadata=types.VideoMetadata(
                fps=self.full_video_fps,
            ),
        )
        video_parts.append(full_part)

        # 3. 프롬프트 빌드 (Metric Registry SSoT에서 allow-list 주입)
        prompt = build_unified_prompt(
            duration_ms=duration_ms,
            platform=platform,
            caption=caption,
            hashtags=hashtags,
            top_comments=top_comments,
            metric_definitions=METRIC_DEFINITIONS,
        )
        
        # Zoom Windows 정보를 프롬프트에 추가
        if zoom_windows:
            zoom_info = "\n\nZOOM WINDOWS (high-FPS clips for precise analysis):\n"
            for i, (start_sec, end_sec) in enumerate(zoom_windows):
                zoom_info += f"- Z{i+1}: {start_sec:.1f}s ~ {end_sec:.1f}s\n"
            zoom_info += "Use these to localize viral_kicks precisely within these windows.\n"
            prompt += zoom_info

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=prompt),
                    *video_parts,
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

    def _detect_zoom_windows(
        self,
        video_path: str,
        duration_ms: int,
        max_windows: int = 4,
    ) -> List[Tuple[float, float]]:
        """
        결정론적 Zoom Windows 감지
        
        ffmpeg scene detection으로 scene cuts 위치 탐지
        각 cut 주변 ±1초 구간을 zoom window로 설정
        
        Returns:
            List of (start_sec, end_sec) tuples
        """
        import subprocess
        
        duration_sec = duration_ms / 1000.0
        half_window = self.zoom_window_duration / 2.0
        
        zoom_points = []
        
        # 1. ffmpeg scene detection (scene cuts)
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "frame=pts_time",
                    "-of", "csv=p=0",
                    "-f", "lavfi",
                    f"movie={video_path},select=gt(scene\\,0.3)"
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    try:
                        t = float(line.strip())
                        if t > self.hook_clip_seconds and t < duration_sec - 1:
                            zoom_points.append(("scene_cut", t))
                    except ValueError:
                        continue
        except Exception as e:
            logger.warning(f"Scene detection failed: {e}")
        
        # 2. 중간 지점 (전환이 많은 곳)
        if len(zoom_points) < max_windows:
            mid_points = [
                duration_sec * 0.25,
                duration_sec * 0.5,
                duration_sec * 0.75,
            ]
            for t in mid_points:
                if t > self.hook_clip_seconds and t < duration_sec - 1:
                    # 이미 추가된 scene cut과 겹치지 않으면 추가
                    is_duplicate = any(
                        abs(existing_t - t) < self.zoom_window_duration
                        for _, existing_t in zoom_points
                    )
                    if not is_duplicate:
                        zoom_points.append(("fallback", t))
        
        # 3. 시간순 정렬 후 상위 max_windows개 선택
        zoom_points.sort(key=lambda x: x[1])
        selected = zoom_points[:max_windows]
        
        # 4. (start, end) 튜플로 변환
        windows = []
        for _, t in selected:
            start = max(0, t - half_window)
            end = min(duration_sec, t + half_window)
            windows.append((start, end))
        
        return windows

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
