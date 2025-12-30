"""
Evidence ID Generators for Non-Frame Evidence Types

H-Final-2: Deterministic evidence IDs for comments, ASR, OCR.
Enables RL join and deduplication across evidence types.

Format patterns:
- ev.comment.{content_id}.{hash12}
- ev.asr.{content_id}.{t0_ms}.{t1_ms}.{sha8}
- ev.ocr.{content_id}.{t_ms}.{sha8}
- ev.metric.{content_id}.{ap_id}.{metric_id}
"""
import hashlib
from typing import Tuple


def generate_comment_evidence_id(
    content_id: str,
    comment_id: str,
    platform: str = "unknown"
) -> Tuple[str, str]:
    """
    Generate deterministic evidence ID for a comment.
    
    Returns:
        (evidence_id, full_sha256)
    """
    safe_content_id = content_id.replace(".", "_")[:32]
    full_sha = hashlib.sha256(comment_id.encode()).hexdigest()
    hash12 = full_sha[:12]
    
    evidence_id = f"ev.comment.{platform}.{safe_content_id}.{hash12}"
    return evidence_id, full_sha


def generate_asr_evidence_id(
    content_id: str,
    t0_ms: int,
    t1_ms: int,
    text: str
) -> Tuple[str, str]:
    """
    Generate deterministic evidence ID for ASR (speech) span.
    
    Returns:
        (evidence_id, full_sha256)
    """
    safe_content_id = content_id.replace(".", "_")[:32]
    full_sha = hashlib.sha256(text.encode()).hexdigest()
    sha8 = full_sha[:8]
    
    evidence_id = f"ev.asr.{safe_content_id}.{t0_ms}.{t1_ms}.{sha8}"
    return evidence_id, full_sha


def generate_ocr_evidence_id(
    content_id: str,
    t_ms: int,
    text: str
) -> Tuple[str, str]:
    """
    Generate deterministic evidence ID for OCR (on-screen text) span.
    
    Returns:
        (evidence_id, full_sha256)
    """
    safe_content_id = content_id.replace(".", "_")[:32]
    full_sha = hashlib.sha256(text.encode()).hexdigest()
    sha8 = full_sha[:8]
    
    evidence_id = f"ev.ocr.{safe_content_id}.{t_ms}.{sha8}"
    return evidence_id, full_sha


def generate_metric_evidence_id(
    content_id: str,
    ap_id: str,
    metric_id: str
) -> str:
    """
    Generate deterministic evidence ID for a metric measurement.
    
    Note: No sha needed since metric_id is already structured.
    """
    safe_content_id = content_id.replace(".", "_")[:32]
    safe_ap_id = ap_id.replace(".", "_")[:48]
    safe_metric_id = metric_id.replace(".", "_")[:32]
    
    return f"ev.metric.{safe_content_id}.{safe_ap_id}.{safe_metric_id}"
