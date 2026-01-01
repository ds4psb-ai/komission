"""
Evidence-Guided Clip Generator (P0-5)

댓글/CV 신호 기반으로 고밀도 분석이 필요한 구간을 식별

2-Pass "딥다이브"의 핵심을 1회 호출로 복원:
- 댓글에서 timestamp 힌트 추출 ("0:05", "1분 20초")
- Scene boundary 감지 (ffmpeg scene detect)
- 기본 훅 윈도우 (0-5s)

사용:
    from app.services.vdg_2pass.evidence_clip_generator import evidence_clip_generator
    clips = evidence_clip_generator.generate_clips(video_path, comments, duration_sec)
"""
import re
import logging
import subprocess
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EvidenceClip:
    """Evidence 기반 클립 정보"""
    clip_id: str
    start_ms: int
    end_ms: int
    fps: float = 10.0  # High density
    reason: str = ""
    source: str = ""  # "hook_window" | "comment_hint" | "scene_cut"
    priority: int = 1  # 1=highest


class EvidenceGuidedClipGenerator:
    """댓글/CV 신호 기반 고밀도 클립 생성기"""
    
    DEFAULT_HOOK_WINDOW_MS = 5000  # 0-5초
    DEFAULT_CLIP_DURATION_MS = 4000  # ±2초 = 4초
    DEFAULT_HIGH_DENSITY_FPS = 10.0
    MAX_CLIPS = 6
    
    # 한국어 timestamp 패턴
    TIMESTAMP_PATTERNS = [
        # MM:SS format
        (r'(\d{1,2}):(\d{2})', lambda m: (int(m.group(1)) * 60 + int(m.group(2))) * 1000),
        # "N초" format
        (r'(\d+)초', lambda m: int(m.group(1)) * 1000),
        # "N분 M초" format
        (r'(\d+)분\s*(\d+)?초?', lambda m: (int(m.group(1)) * 60 + int(m.group(2) or 0)) * 1000),
        # "0:05" style quotes
        (r'"(\d{1,2}):(\d{2})"', lambda m: (int(m.group(1)) * 60 + int(m.group(2))) * 1000),
    ]
    
    def generate_clips(
        self,
        video_path: str,
        comments: List[Dict[str, Any]],
        duration_sec: float,
        include_scene_cuts: bool = True
    ) -> List[EvidenceClip]:
        """
        고밀도 분석이 필요한 클립 목록 생성
        
        Args:
            video_path: 비디오 파일 경로
            comments: 댓글 리스트 [{"text": str, "likes": int}, ...]
            duration_sec: 비디오 길이 (초)
            include_scene_cuts: Scene cut 감지 포함 여부
            
        Returns:
            List[EvidenceClip] (priority 순 정렬)
        """
        duration_ms = int(duration_sec * 1000)
        clips: List[EvidenceClip] = []
        used_windows: List[Tuple[int, int]] = []
        
        # 1. 기본 훅 윈도우 (항상 포함, priority 1)
        hook_end = min(self.DEFAULT_HOOK_WINDOW_MS, duration_ms)
        clips.append(EvidenceClip(
            clip_id="clip.hook_0_5",
            start_ms=0,
            end_ms=hook_end,
            fps=self.DEFAULT_HIGH_DENSITY_FPS,
            reason="default_hook_window",
            source="hook_window",
            priority=1
        ))
        used_windows.append((0, hook_end))
        
        # 2. 댓글에서 timestamp 힌트 추출
        timestamp_hints = self._extract_timestamp_hints(comments)
        for i, hint in enumerate(timestamp_hints[:3]):  # 최대 3개
            t_ms = hint['t_ms']
            
            # 범위 체크
            if t_ms < 0 or t_ms > duration_ms:
                continue
            
            # 중복 체크
            if self._overlaps_existing(t_ms, used_windows, margin_ms=2000):
                continue
            
            start_ms = max(0, t_ms - 2000)
            end_ms = min(duration_ms, t_ms + 2000)
            
            clips.append(EvidenceClip(
                clip_id=f"clip.comment_{t_ms}",
                start_ms=start_ms,
                end_ms=end_ms,
                fps=self.DEFAULT_HIGH_DENSITY_FPS,
                reason=f"comment_timestamp_hint: {hint['source']}",
                source="comment_hint",
                priority=2
            ))
            used_windows.append((start_ms, end_ms))
        
        # 3. Scene cuts (ffmpeg 기반)
        if include_scene_cuts and len(clips) < self.MAX_CLIPS:
            scene_cuts = self._detect_scene_cuts(video_path, duration_ms)
            for cut_ms in scene_cuts[:2]:  # 최대 2개
                if self._overlaps_existing(cut_ms, used_windows, margin_ms=2000):
                    continue
                
                start_ms = max(0, cut_ms - 1500)
                end_ms = min(duration_ms, cut_ms + 1500)
                
                clips.append(EvidenceClip(
                    clip_id=f"clip.scene_{cut_ms}",
                    start_ms=start_ms,
                    end_ms=end_ms,
                    fps=self.DEFAULT_HIGH_DENSITY_FPS,
                    reason=f"scene_cut_at_{cut_ms}ms",
                    source="scene_cut",
                    priority=3
                ))
                used_windows.append((start_ms, end_ms))
        
        # Priority 정렬
        clips.sort(key=lambda c: c.priority)
        
        logger.info(f"📹 Generated {len(clips)} evidence clips: {[c.clip_id for c in clips]}")
        
        return clips[:self.MAX_CLIPS]
    
    def _extract_timestamp_hints(
        self, 
        comments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        댓글에서 timestamp 힌트 추출
        
        예: "0:05 부분 미쳤다" → {"t_ms": 5000, "source": "MM:SS"}
        """
        hints = []
        seen_timestamps = set()
        
        for c in comments:
            text = c.get('text', '') or ''
            
            for pattern, converter in self.TIMESTAMP_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    try:
                        t_ms = converter(match)
                        
                        # Dedup (±1초 범위)
                        rounded = (t_ms // 1000) * 1000
                        if rounded not in seen_timestamps:
                            seen_timestamps.add(rounded)
                            hints.append({
                                't_ms': t_ms,
                                'source': pattern[:10],
                                'comment_text': text[:50],
                                'likes': c.get('likes', 0)
                            })
                            break  # 하나만 추출
                    except (ValueError, TypeError):
                        continue
        
        # 좋아요 순 정렬
        hints.sort(key=lambda h: h.get('likes', 0), reverse=True)
        
        return hints
    
    def _detect_scene_cuts(
        self, 
        video_path: str, 
        duration_ms: int
    ) -> List[int]:
        """
        ffmpeg scene detection으로 scene cut 위치 탐지
        
        Returns:
            List of timestamps in milliseconds
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'packet=pts_time,flags',
                '-select_streams', 'v:0',
                '-of', 'json',
                video_path
            ]
            
            # Alternative: use scene detection filter
            scene_cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', 'select=gt(scene\\,0.3),showinfo',
                '-f', 'null', '-'
            ]
            
            # Run with timeout
            result = subprocess.run(
                scene_cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3분 (긴 영상 지원)
            )
            
            # Parse scene changes from stderr
            scene_times = []
            for line in result.stderr.split('\n'):
                if 'pts_time:' in line:
                    match = re.search(r'pts_time:([\d.]+)', line)
                    if match:
                        t_sec = float(match.group(1))
                        t_ms = int(t_sec * 1000)
                        if 1000 < t_ms < duration_ms - 1000:  # Skip very start/end
                            scene_times.append(t_ms)
            
            return sorted(set(scene_times))[:4]  # Max 4 scene cuts
            
        except subprocess.TimeoutExpired:
            logger.warning("Scene detection timed out")
            return []
        except FileNotFoundError:
            logger.warning("ffmpeg not found for scene detection")
            return []
        except Exception as e:
            logger.warning(f"Scene detection failed: {e}")
            return []
    
    def _overlaps_existing(
        self, 
        t_ms: int, 
        used_windows: List[Tuple[int, int]],
        margin_ms: int = 2000
    ) -> bool:
        """기존 윈도우와 겹치는지 확인"""
        for start, end in used_windows:
            if start - margin_ms <= t_ms <= end + margin_ms:
                return True
        return False
    
    def format_for_prompt(self, clips: List[EvidenceClip]) -> str:
        """클립 정보를 프롬프트용 문자열로 포맷"""
        lines = ["=== EVIDENCE-GUIDED FOCUS WINDOWS ==="]
        lines.append("다음 구간에서 특히 증거를 찾으세요:\n")
        
        for clip in clips:
            start_sec = clip.start_ms / 1000
            end_sec = clip.end_ms / 1000
            lines.append(f"- [{clip.clip_id}] {start_sec:.1f}s - {end_sec:.1f}s ({clip.reason})")
        
        lines.append("\n각 viral_kick은 위 focus window 중 하나를 반드시 커버해야 합니다.")
        
        return "\n".join(lines)


# Singleton instance
evidence_clip_generator = EvidenceGuidedClipGenerator()
