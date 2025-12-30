"""
Frame Extraction Utility (P0-2 + Flywheel Hardening)

Extracts frames from video based on AnalysisPlan t_windows.
Uses ffmpeg-python for efficient frame extraction.

Philosophy:
- Visual Pass should NOT receive full mp4
- Only plan-based frames → cost 1/5, better focus

Flywheel Hardening:
- Deterministic evidence_id for RL join keys
- Format: ev.frame.{content_id}.{ap_id}.{t_ms}.{sha8}
"""
import hashlib
import io
import logging
import tempfile
from typing import List, Tuple, Optional, NamedTuple
from pathlib import Path

logger = logging.getLogger(__name__)


class FrameEvidence(NamedTuple):
    """Frame with deterministic evidence ID for RL join."""
    evidence_id: str  # Structural ID (stable across extractor versions)
    t: float
    jpeg_bytes: bytes
    sha256: str  # Content hash for integrity/dedup (NOT in ID)


def generate_evidence_id(
    content_id: str,
    ap_id: str,
    t_ms: int,
    jpeg_bytes: bytes = None  # Optional - only used for sha256
) -> Tuple[str, str]:
    """
    Generate deterministic evidence_id for a frame.
    
    Phase 1 Refinement:
    - ID is STRUCTURAL only (stable across extractor versions)
    - sha256 is SEPARATE for integrity/dedup
    
    Format: ev.frame.{content_id}.{ap_id}.{t_ms:06d}
    
    Returns:
        (evidence_id, full_sha256)
    """
    # Calculate sha256 if bytes provided (for integrity/dedup)
    full_sha256 = hashlib.sha256(jpeg_bytes).hexdigest() if jpeg_bytes else ""
    
    # Sanitize IDs (remove special chars that might break joins)
    safe_content_id = content_id.replace(".", "_").replace("/", "_")[:32] if content_id else "unknown"
    safe_ap_id = ap_id.replace(".", "_")[:32] if ap_id else "noap"
    
    # STRUCTURAL ID ONLY - no sha in ID (extractor-version stable)
    evidence_id = f"ev.frame.{safe_content_id}.{safe_ap_id}.{t_ms:06d}"
    return evidence_id, full_sha256


def extract_frames_for_plan(
    video_bytes: bytes,
    t_windows: List[Tuple[float, float]],
    target_fps: float = 2.0,
    max_frames_per_window: int = 5,
    content_id: str = None,
    ap_ids: List[str] = None
) -> List[FrameEvidence]:
    """
    Extract frames from video based on AnalysisPlan t_windows.
    
    Args:
        video_bytes: Raw video bytes
        t_windows: List of (start_sec, end_sec) from plan.points
        target_fps: Frames per second to extract
        max_frames_per_window: Cap frames per window
        content_id: VDG content_id for evidence_id generation
        ap_ids: List of analysis_point_ids matching t_windows
        
    Returns:
        List of FrameEvidence (evidence_id, t, jpeg_bytes, sha256)
    """
    try:
        import ffmpeg
    except ImportError:
        logger.warning("⚠️ ffmpeg-python not installed, falling back to full video mode")
        return []
    
    frames: List[FrameEvidence] = []
    content_id = content_id or "unknown"
    
    # Create temp file for video
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_video:
        tmp_video.write(video_bytes)
        tmp_video_path = tmp_video.name
    
    try:
        for idx, (start_sec, end_sec) in enumerate(t_windows):
            duration = end_sec - start_sec
            num_frames = min(int(duration * target_fps) + 1, max_frames_per_window)
            
            if num_frames <= 0:
                continue
            
            # Get ap_id for this window
            ap_id = ap_ids[idx] if ap_ids and idx < len(ap_ids) else f"ap_{idx}"
            
            # Calculate frame timestamps
            step = duration / max(num_frames, 1)
            for i in range(num_frames):
                t = start_sec + (i * step)
                t_ms = int(t * 1000)
                
                try:
                    # Extract single frame as JPEG
                    out, _ = (
                        ffmpeg
                        .input(tmp_video_path, ss=t)
                        .output('pipe:', vframes=1, format='image2', vcodec='mjpeg', **{'q:v': 2})
                        .run(capture_stdout=True, capture_stderr=True, quiet=True)
                    )
                    
                    # Generate deterministic evidence_id
                    evidence_id, full_sha256 = generate_evidence_id(
                        content_id=content_id,
                        ap_id=ap_id,
                        t_ms=t_ms,
                        jpeg_bytes=out
                    )
                    
                    frames.append(FrameEvidence(
                        evidence_id=evidence_id,
                        t=t,
                        jpeg_bytes=out,
                        sha256=full_sha256
                    ))
                except Exception as e:
                    logger.warning(f"Failed to extract frame at t={t:.2f}s: {e}")
        
        logger.info(f"📷 Extracted {len(frames)} frames from {len(t_windows)} windows (with evidence IDs)")
        return frames
        
    finally:
        # Cleanup temp file
        Path(tmp_video_path).unlink(missing_ok=True)


def frames_to_model_parts(
    frames: List[FrameEvidence],
    include_timestamp: bool = True,
    include_evidence_id: bool = False
) -> List:
    """
    Convert extracted frames to Gemini model input parts.
    
    Args:
        frames: List of FrameEvidence
        include_timestamp: Add timestamp text before each frame
        include_evidence_id: Add evidence_id for traceability
        
    Returns:
        List of Part objects for model input
    """
    try:
        from google.generativeai import types
    except ImportError:
        logger.error("google.generativeai not available")
        return []
    
    parts = []
    for frame in frames:
        if include_timestamp:
            label = f"[Frame at t={frame.t:.2f}s"
            if include_evidence_id:
                label += f" | {frame.evidence_id}"
            label += "]"
            parts.append(label)
        
        parts.append(types.Part(
            inline_data=types.Blob(
                data=frame.jpeg_bytes,
                mime_type="image/jpeg"
            )
        ))
    
    return parts


class FrameExtractor:
    """
    P0-2 + Flywheel: Plan-based frame extraction for Visual Pass.
    
    Instead of sending full mp4, extracts only frames
    from AnalysisPlan t_windows.
    
    Benefits:
    - Cost reduction: ~1/5 of full video tokens
    - Better focus: Model sees only relevant frames
    - Evidence: Each frame has deterministic evidence_id for RL join
    
    Flywheel Hardening:
    - evidence_id format: ev.frame.{content_id}.{ap_id}.{t_ms}.{sha8}
    - Same input → same ID → dedup/join possible
    """
    
    @staticmethod
    def extract_for_plan(
        video_bytes: bytes,
        plan,  # AnalysisPlan
        target_fps: float = 2.0,
        content_id: str = None
    ) -> List[FrameEvidence]:
        """
        Extract frames based on AnalysisPlan's t_windows.
        
        Returns FrameEvidence with deterministic evidence_id.
        """
        t_windows = [
            (p.t_window[0], p.t_window[1]) 
            for p in plan.points 
            if p.t_window
        ]
        ap_ids = [p.id for p in plan.points if p.t_window]
        
        return extract_frames_for_plan(
            video_bytes, 
            t_windows, 
            target_fps,
            content_id=content_id,
            ap_ids=ap_ids
        )
    
    @staticmethod
    def to_model_parts(frames: List[FrameEvidence]) -> List:
        """Convert frames to model input parts."""
        return frames_to_model_parts(frames)
    
    @staticmethod
    def get_evidence_ids(frames: List[FrameEvidence]) -> List[str]:
        """Get list of evidence_ids for storing in VDG."""
        return [f.evidence_id for f in frames]
    
    @staticmethod
    def is_available() -> bool:
        """Check if ffmpeg-python is installed."""
        try:
            import ffmpeg
            return True
        except ImportError:
            return False

