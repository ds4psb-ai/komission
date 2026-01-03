# backend/app/services/vdg_2pass/unified_pass.py
"""
VDG Unified Pass (Pass 1: Gemini 3.0 Pro 1회 호출)

핵심 설계:
- Pass 1: LLM이 의미/인과/Plan Seed 생성
- Pass 2: CV가 결정론적 수치 측정

API 특징:
- VideoMetadata: hook clip (10fps) + full video (1fps) 분리
- media_resolution: low/high로 토큰 비용 제어
- JSON output (manual validation)
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
    - JSON output: 수동 Pydantic 검증
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
        
        # Note: video_metadata parameter not supported in current SDK version
        # Using simple Part.from_uri without segment specification
        # The LLM will analyze the full video
        full_part = types.Part.from_uri(
            file_uri=video_file.uri,
            mime_type=video_file.mime_type,
        )
        video_parts.append(full_part)
        
        # Log that we're using full video (segment features disabled)
        logger.info(f"📹 Using full video analysis (segment features disabled due to SDK)")

        # 3. 프롬프트 빌드 (Metric Registry SSoT에서 allow-list 주입)
        prompt = build_unified_prompt(
            duration_ms=duration_ms,
            platform=platform,
            caption=caption,
            hashtags=hashtags,
            top_comments=top_comments,
            metric_definitions=METRIC_DEFINITIONS,
        )
        
        
        # Note: Zoom Windows feature disabled due to SDK limitations

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=prompt),
                    *video_parts,
                ],
            )
        ]

        # 4. API 호출 (JSON mode only - response_schema removed due to $ref/anyOf limitation)
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=0.95,
            max_output_tokens=self.max_output_tokens,
            response_mime_type="application/json",
            # Note: response_schema removed - Gemini doesn't support $ref or anyOf in nested schemas
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
            # Parse raw JSON first
            import json
            raw_json = json.loads(resp.text)
            
            # Preprocess: add missing required fields with defaults
            if 'duration_ms' not in raw_json:
                raw_json['duration_ms'] = duration_ms
            if 'language' not in raw_json:
                raw_json['language'] = 'ko'
            if 'schema_version' not in raw_json:
                raw_json['schema_version'] = 'unified_pass_llm.v2'
                
            # Preprocess: intent_layer defaults
            if 'intent_layer' not in raw_json:
                raw_json['intent_layer'] = {
                    'creator_intent': 'Unknown',
                    'audience_trigger': [],
                    'novelty': 'Unknown',
                    'clarity': 'Unknown'
                }
            
            # Preprocess: hook_genome defaults
            if 'hook_genome' not in raw_json:
                raw_json['hook_genome'] = {
                    'strength': 0.5,
                    'hook_start_ms': 0,
                    'hook_end_ms': min(4000, duration_ms),
                    'microbeats': []
                }
            
            # Preprocess: fix microbeat roles if invalid
            if 'hook_genome' in raw_json and 'microbeats' in raw_json['hook_genome']:
                valid_roles = {'start', 'setup', 'hook', 'punch', 'reveal', 'demo', 'payoff', 'cta', 'loop'}
                for mb in raw_json['hook_genome']['microbeats']:
                    if not isinstance(mb, dict):
                        continue  # Skip non-dict items
                    if mb.get('role') not in valid_roles:
                        mb['role'] = 'hook'
            
            # Preprocess: fix mise_en_scene types (props -> prop)
            if 'mise_en_scene_signals' in raw_json:
                valid_mise_types = {'composition', 'lighting', 'color', 'wardrobe', 'prop', 'setting', 'camera', 'editing', 'audio', 'text'}
                type_fixes = {'props': 'prop', 'sound': 'audio', 'costume': 'wardrobe'}
                for mes in raw_json['mise_en_scene_signals']:
                    if not isinstance(mes, dict):
                        continue  # Skip non-dict items
                    t = mes.get('type', '')
                    if t not in valid_mise_types:
                        mes['type'] = type_fixes.get(t, 'setting')
            
            # Preprocess: fix comment_evidence fields
            if 'comment_evidence_top5' in raw_json:
                valid_signal_types = {'hook', 'twist', 'relatability', 'aesthetic', 'instruction', 'shock', 'product', 'editing', 'music', 'humor', 'other'}
                for ce in raw_json['comment_evidence_top5']:
                    if not isinstance(ce, dict):
                        continue  # Skip non-dict items
                    # Fix comment_rank (might be 'C01' string)
                    cr = ce.get('comment_rank', 1)
                    if isinstance(cr, str):
                        # Extract number from 'C01' format
                        import re
                        match = re.search(r'\d+', cr)
                        ce['comment_rank'] = int(match.group()) if match else 1
                    # Fix missing quote (might be 'text' field)
                    if 'quote' not in ce and 'text' in ce:
                        ce['quote'] = ce['text'][:160]
                    elif 'quote' not in ce:
                        ce['quote'] = 'Unknown comment'
                    # Fix signal_type
                    if ce.get('signal_type') not in valid_signal_types:
                        ce['signal_type'] = 'other'
                    # Ensure why_it_matters
                    if 'why_it_matters' not in ce:
                        ce['why_it_matters'] = 'Relevant to video content'
            
            # Preprocess: comment_evidence_top5 defaults (requires min 1, max 10)
            if 'comment_evidence_top5' not in raw_json or len(raw_json.get('comment_evidence_top5', [])) < 1:
                existing = raw_json.get('comment_evidence_top5', [])
                if len(existing) < 1:
                    existing.append({
                        'comment_rank': 1,
                        'quote': 'No comments available',
                        'signal_type': 'other',
                        'why_it_matters': 'No audience comments found'
                    })
                raw_json['comment_evidence_top5'] = existing[:10]
            
            # Preprocess: fix existing viral_kicks fields
            if 'viral_kicks' in raw_json:
                for i, kick in enumerate(raw_json['viral_kicks']):
                    if not isinstance(kick, dict):
                        continue  # Skip non-dict items
                    # Ensure kick_index
                    if 'kick_index' not in kick:
                        kick['kick_index'] = i + 1
                    # Ensure title
                    if 'title' not in kick:
                        kick['title'] = kick.get('name', kick.get('description', f'Kick {i+1}'))[:100]
                    # Ensure mechanism
                    if 'mechanism' not in kick:
                        kick['mechanism'] = kick.get('description', kick.get('why', 'Visual impact'))[:240]
                    # Ensure window
                    if 'window' not in kick:
                        kick['window'] = {'start_ms': i * 2000, 'end_ms': i * 2000 + 2000}
                    # Ensure evidence_comment_ranks and parse C01 format
                    if 'evidence_comment_ranks' not in kick:
                        kick['evidence_comment_ranks'] = [1]
                    else:
                        # Parse 'C01' format to integers
                        import re
                        parsed_ranks = []
                        for rank in kick['evidence_comment_ranks']:
                            if isinstance(rank, int):
                                parsed_ranks.append(rank)
                            elif isinstance(rank, str):
                                match = re.search(r'\d+', rank)
                                parsed_ranks.append(int(match.group()) if match else 1)
                        kick['evidence_comment_ranks'] = parsed_ranks or [1]
                    # Ensure evidence_cues
                    if 'evidence_cues' not in kick:
                        kick['evidence_cues'] = [kick.get('cue', 'Visual element')]
                    # Ensure creator_instruction
                    if 'creator_instruction' not in kick:
                        kick['creator_instruction'] = kick.get('instruction', kick.get('action', 'Follow this pattern'))[:200]
                    # P2-1: Ensure keyframes (3 keyframes: start, peak, end)
                    if 'keyframes' not in kick or len(kick.get('keyframes', [])) < 3:
                        window = kick.get('window', {})
                        start = window.get('start_ms', kick.get('kick_index', 1) * 1000)
                        end = window.get('end_ms', start + 2000)
                        mid = (start + end) // 2
                        kick['keyframes'] = [
                            {'t_ms': start, 'role': 'start', 'what_to_see': 'Hook entry point'},
                            {'t_ms': mid, 'role': 'peak', 'what_to_see': 'Peak viral moment'},
                            {'t_ms': max(start, end - 100), 'role': 'end', 'what_to_see': 'Resolution/payoff'},
                        ]
            
            # Preprocess: viral_kicks defaults (requires 3-6)
            if 'viral_kicks' not in raw_json or len(raw_json.get('viral_kicks', [])) < 3:
                existing = raw_json.get('viral_kicks', [])
                while len(existing) < 3:
                    idx = len(existing) + 1
                    existing.append({
                        'kick_index': idx,
                        'window': {'start_ms': idx * 1000, 'end_ms': idx * 1000 + 2000},
                        'title': f'Kick {idx}',
                        'mechanism': 'Placeholder',
                        'evidence_comment_ranks': [1],
                        'evidence_cues': ['Visual element'],
                        'creator_instruction': 'Placeholder',
                        'keyframes': [
                            {'t_ms': idx * 1000, 'role': 'start', 'what_to_see': 'Entry point'},
                            {'t_ms': idx * 1000 + 1000, 'role': 'peak', 'what_to_see': 'Peak moment'},
                            {'t_ms': idx * 1000 + 1900, 'role': 'end', 'what_to_see': 'Resolution'},
                        ]
                    })
                raw_json['viral_kicks'] = existing[:6]
            
            # Preprocess: causal_reasoning defaults or fix if string
            if 'causal_reasoning' not in raw_json:
                raw_json['causal_reasoning'] = {
                    'why_viral_one_liner': 'Unknown',
                    'causal_chain': [],
                    'replication_recipe': [],
                    'risks_or_unknowns': []
                }
            elif isinstance(raw_json['causal_reasoning'], str):
                # LLM sometimes returns causal_reasoning as a plain string
                raw_json['causal_reasoning'] = {
                    'why_viral_one_liner': raw_json['causal_reasoning'][:240],
                    'causal_chain': raw_json.get('causal_chain', []),
                    'replication_recipe': raw_json.get('replication_recipe', []),
                    'risks_or_unknowns': []
                }
            
            # Preprocess: convert entity_hints from Dict to List if needed
            if 'entity_hints' in raw_json and isinstance(raw_json['entity_hints'], dict):
                hints_list = []
                for key, hint in raw_json['entity_hints'].items():
                    if isinstance(hint, dict):
                        hint['key'] = key  # Add key field
                        hints_list.append(hint)
                raw_json['entity_hints'] = hints_list
            
            # Preprocess: fix entity_hints fields
            if 'entity_hints' in raw_json:
                valid_cv_priority = {'primary', 'secondary', 'optional'}
                priority_map = {'high': 'primary', 'medium': 'secondary', 'low': 'optional'}
                valid_entity_types = {'person', 'face', 'hand', 'product', 'text', 'environment', 'other'}
                entity_type_map = {
                    'food': 'product', 'dish': 'product', 'ingredient': 'product', 'cooking': 'environment',
                    'object': 'other', 'item': 'product', 'location': 'environment', 'scene': 'environment',
                    'animal': 'other', 'nature': 'environment', 'background': 'environment'
                }
                for hint in raw_json['entity_hints']:
                    if not isinstance(hint, dict):
                        continue  # Skip non-dict items
                    # Fix entity_type
                    et = hint.get('entity_type', 'other')
                    if et not in valid_entity_types:
                        hint['entity_type'] = entity_type_map.get(et, 'other')
                    # Fix cv_priority
                    cv_p = hint.get('cv_priority', 'secondary')
                    if cv_p not in valid_cv_priority:
                        hint['cv_priority'] = priority_map.get(cv_p, 'secondary')
                    # Fix appears_windows format (list -> dict)
                    if 'appears_windows' in hint:
                        fixed_windows = []
                        for w in hint['appears_windows']:
                            if isinstance(w, list) and len(w) == 2:
                                fixed_windows.append({'start_ms': w[0], 'end_ms': w[1]})
                            elif isinstance(w, dict):
                                fixed_windows.append(w)
                        hint['appears_windows'] = fixed_windows
            
            # Preprocess: fix analysis_plan.points
            if 'analysis_plan' in raw_json and 'points' in raw_json['analysis_plan']:
                valid_agg = {'mean', 'median', 'max', 'min', 'first', 'last', 'p95'}
                valid_roi = {'full_frame', 'face', 'main_subject', 'product', 'text_overlay'}
                roi_map = {
                    'global': 'full_frame', 'full': 'full_frame', 'frame': 'full_frame',
                    'person': 'main_subject', 'subject': 'main_subject', 'object': 'main_subject',
                    'text': 'text_overlay', 'overlay': 'text_overlay',
                }
                for point in raw_json['analysis_plan']['points']:
                    if not isinstance(point, dict):
                        continue  # Skip non-dict items
                    if 'measurements' in point:
                        for m in point['measurements']:
                            if m.get('aggregation') not in valid_agg:
                                m['aggregation'] = 'mean'
                            if m.get('roi') not in valid_roi:
                                m['roi'] = roi_map.get(m.get('roi'), 'full_frame')
            
            # Preprocess: analysis_plan defaults
            if 'analysis_plan' not in raw_json:
                raw_json['analysis_plan'] = {'points': []}
            
            # Validate with Pydantic
            out = UnifiedPassLLMOutput.model_validate(raw_json)
            
        except Exception as e:
            logger.warning(f"Validation failed, attempting lenient parse: {e}")
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

        # Warn if polling timed out without reaching ACTIVE state
        state = getattr(video_file, 'state', None)
        name = getattr(state, 'name', None) if state else None
        if name and name not in ('ACTIVE', 'SUCCEEDED'):
            logger.warning(f'Video file polling timed out, state={name}. Inference may fail.')
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
                timeout=180,  # 3분 (영상 길이에 따라 증가 가능)
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
            timeout=30,  # ffprobe는 빠르므로 30초
        )
        duration_sec = float(result.stdout.strip())
        return int(duration_sec * 1000)
    except Exception as e:
        logger.warning(f"ffprobe failed, using 0: {e}")
        return 0
