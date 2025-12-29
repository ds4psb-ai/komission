"""
Frame Extraction Utility (P0-2 Hardening)

Extracts frames from video based on AnalysisPlan t_windows.
Uses ffmpeg-python for efficient frame extraction.

Philosophy:
- Visual Pass should NOT receive full mp4
- Only plan-based frames → cost 1/5, better focus
"""
import io
import logging
import tempfile
from typing import List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_frames_for_plan(
    video_bytes: bytes,
    t_windows: List[Tuple[float, float]],
    target_fps: float = 2.0,
    max_frames_per_window: int = 5
) -> List[Tuple[float, bytes]]:
    """
    Extract frames from video based on AnalysisPlan t_windows.
    
    Args:
        video_bytes: Raw video bytes
        t_windows: List of (start_sec, end_sec) from plan.points
        target_fps: Frames per second to extract
        max_frames_per_window: Cap frames per window
        
    Returns:
        List of (timestamp, jpeg_bytes) tuples
    """
    try:
        import ffmpeg
    except ImportError:
        logger.warning("⚠️ ffmpeg-python not installed, falling back to full video mode")
        return []
    
    frames: List[Tuple[float, bytes]] = []
    
    # Create temp file for video
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_video:
        tmp_video.write(video_bytes)
        tmp_video_path = tmp_video.name
    
    try:
        for start_sec, end_sec in t_windows:
            duration = end_sec - start_sec
            num_frames = min(int(duration * target_fps) + 1, max_frames_per_window)
            
            if num_frames <= 0:
                continue
            
            # Calculate frame timestamps
            step = duration / max(num_frames, 1)
            for i in range(num_frames):
                t = start_sec + (i * step)
                
                try:
                    # Extract single frame as JPEG
                    out, _ = (
                        ffmpeg
                        .input(tmp_video_path, ss=t)
                        .output('pipe:', vframes=1, format='image2', vcodec='mjpeg', **{'q:v': 2})
                        .run(capture_stdout=True, capture_stderr=True, quiet=True)
                    )
                    frames.append((t, out))
                except Exception as e:
                    logger.warning(f"Failed to extract frame at t={t:.2f}s: {e}")
        
        logger.info(f"📷 Extracted {len(frames)} frames from {len(t_windows)} windows")
        return frames
        
    finally:
        # Cleanup temp file
        Path(tmp_video_path).unlink(missing_ok=True)


def frames_to_model_parts(
    frames: List[Tuple[float, bytes]],
    include_timestamp: bool = True
) -> List:
    """
    Convert extracted frames to Gemini model input parts.
    
    Args:
        frames: List of (timestamp, jpeg_bytes)
        include_timestamp: Add timestamp text before each frame
        
    Returns:
        List of Part objects for model input
    """
    try:
        from google.generativeai import types
    except ImportError:
        logger.error("google.generativeai not available")
        return []
    
    parts = []
    for t, jpeg_bytes in frames:
        if include_timestamp:
            parts.append(f"[Frame at t={t:.2f}s]")
        
        parts.append(types.Part(
            inline_data=types.Blob(
                data=jpeg_bytes,
                mime_type="image/jpeg"
            )
        ))
    
    return parts


class FrameExtractor:
    """
    P0-2: Plan-based frame extraction for Visual Pass.
    
    Instead of sending full mp4, extracts only frames
    from AnalysisPlan t_windows.
    
    Benefits:
    - Cost reduction: ~1/5 of full video tokens
    - Better focus: Model sees only relevant frames
    - Evidence: Each frame is traceable to a plan point
    """
    
    @staticmethod
    def extract_for_plan(
        video_bytes: bytes,
        plan,  # AnalysisPlan
        target_fps: float = 2.0
    ) -> List[Tuple[float, bytes]]:
        """Extract frames based on AnalysisPlan's t_windows."""
        t_windows = [
            (p.t_window[0], p.t_window[1]) 
            for p in plan.points 
            if p.t_window
        ]
        return extract_frames_for_plan(video_bytes, t_windows, target_fps)
    
    @staticmethod
    def to_model_parts(frames: List[Tuple[float, bytes]]) -> List:
        """Convert frames to model input parts."""
        return frames_to_model_parts(frames)
    
    @staticmethod
    def is_available() -> bool:
        """Check if ffmpeg-python is installed."""
        try:
            import ffmpeg
            return True
        except ImportError:
            return False
