"""
Cluster Determinism Utilities v1.0

Provides deterministic ID generation and signature hashing for ContentCluster.

Requirements (from consultant feedback):
1. cluster_id must be deterministic (same input → same ID)
2. signature hash must be normalized (key sorting, float rounding)
3. kid_vdg_ids must be deduplicated and sorted

Usage:
    from app.utils.cluster_determinism import (
        generate_cluster_id, normalize_signature_hash, 
        dedupe_sort_kids
    )
    
    cluster_id = generate_cluster_id(
        pattern_slug="hook_subversion",
        niche="beauty",
        parent_vdg_id="vdg_abc123"
    )
"""
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


# ====================
# CLUSTER ID GENERATION
# ====================

def generate_cluster_id(
    pattern_slug: str,
    niche: str,
    parent_vdg_id: str,
    week: Optional[str] = None  # Format: "202452" (year+week)
) -> str:
    """
    Generate deterministic cluster ID.
    
    Format: cl.{pattern_slug}.{niche}.{yyyyww}.{hash8}
    
    The hash is derived from parent_vdg_id for uniqueness while
    allowing the same parent to always produce the same cluster_id.
    
    Args:
        pattern_slug: Pattern identifier (e.g., "hook_subversion")
        niche: Content niche (e.g., "beauty", "food")
        parent_vdg_id: Parent VDG ID (determines uniqueness)
        week: Optional week override (defaults to current week)
    
    Returns:
        Deterministic cluster ID like "cl.hook_subversion.beauty.202452.a8f3d2e1"
    """
    # Normalize inputs
    pattern_slug = pattern_slug.lower().strip().replace(" ", "_")
    niche = niche.lower().strip()
    
    # Get week if not provided
    if not week:
        now = datetime.utcnow()
        week = f"{now.year}{now.isocalendar()[1]:02d}"
    
    # Generate deterministic hash from parent
    hash_input = f"{pattern_slug}:{niche}:{parent_vdg_id}"
    hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    
    return f"cl.{pattern_slug}.{niche}.{week}.{hash_digest}"


def validate_cluster_id(cluster_id: str) -> bool:
    """Validate cluster ID format."""
    parts = cluster_id.split(".")
    if len(parts) != 5:
        return False
    if parts[0] != "cl":
        return False
    # Check week format (6 digits)
    try:
        week = parts[3]
        if len(week) != 6 or not week.isdigit():
            return False
    except (ValueError, IndexError):
        return False
    # Check hash (8 hex chars)
    if len(parts[4]) != 8:
        return False
    return True


# ====================
# SIGNATURE NORMALIZATION
# ====================

def normalize_signature_dict(signature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize signature dict for deterministic hashing.
    
    Rules:
    1. Sort all keys recursively
    2. Round floats to 6 decimal places
    3. Sort list items if they're strings
    4. Convert None to empty string for consistency
    """
    def normalize_value(v: Any) -> Any:
        if v is None:
            return ""
        if isinstance(v, float):
            return round(v, 6)
        if isinstance(v, dict):
            return {k: normalize_value(v2) for k, v2 in sorted(v.items())}
        if isinstance(v, list):
            normalized = [normalize_value(item) for item in v]
            # Sort if all items are strings
            if all(isinstance(x, str) for x in normalized):
                return sorted(normalized)
            return normalized
        return v
    
    return {k: normalize_value(v) for k, v in sorted(signature.items())}


def compute_signature_hash(signature: Dict[str, Any]) -> str:
    """
    Compute deterministic hash of signature.
    
    Returns hash in format: sig.{hash12}
    """
    normalized = normalize_signature_dict(signature)
    json_str = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    hash_digest = hashlib.sha256(json_str.encode()).hexdigest()[:12]
    return f"sig.{hash_digest}"


class SignatureHasher:
    """
    Utility class for signature normalization and hashing.
    
    Usage:
        hasher = SignatureHasher()
        hash1 = hasher.hash(sig_dict)
        hash2 = hasher.hash(sig_dict)  # Same as hash1
    """
    
    def normalize(self, signature: Dict[str, Any]) -> Dict[str, Any]:
        return normalize_signature_dict(signature)
    
    def hash(self, signature: Dict[str, Any]) -> str:
        return compute_signature_hash(signature)
    
    def verify_determinism(self, sig1: Dict[str, Any], sig2: Dict[str, Any]) -> bool:
        """Check if two signatures produce the same hash."""
        return self.hash(sig1) == self.hash(sig2)


# ====================
# KIDS DEDUPLICATION
# ====================

def dedupe_sort_kids(kid_vdg_ids: List[str]) -> List[str]:
    """
    Deduplicate and sort kid VDG IDs.
    
    Ensures deterministic ordering for cluster operations.
    """
    return sorted(set(kid_vdg_ids))


def dedupe_sort_content_ids(content_ids: List[str]) -> List[str]:
    """Deduplicate and sort content IDs."""
    return sorted(set(content_ids))


# ====================
# CLUSTER VALIDATION
# ====================

class ClusterValidationResult(BaseModel):
    """Validation result for cluster quality checks."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


def validate_cluster_for_distill(
    parent_vdg_id: str,
    kid_vdg_ids: List[str],
    parent_tier: str = "A",
    parent_merger_quality: str = "gold",
    min_kids: int = 6,
    min_unique_creators: int = 3
) -> ClusterValidationResult:
    """
    Validate cluster meets distill requirements.
    
    Requirements (from consultant):
    - Parent tier: S or A
    - Parent merger quality: gold
    - Kids >= 6 (10개 빨리 만들려면 6~8이 현실적)
    - Unique creators >= 3
    """
    errors = []
    warnings = []
    
    # Check parent tier
    if parent_tier not in ["S", "A"]:
        errors.append(f"Parent tier must be S or A, got: {parent_tier}")
    
    # Check merger quality
    if parent_merger_quality != "gold":
        if parent_merger_quality == "silver":
            warnings.append("Silver merger quality may produce lower-quality distill")
        else:
            errors.append(f"Parent merger quality must be gold, got: {parent_merger_quality}")
    
    # Check kids count
    unique_kids = dedupe_sort_kids(kid_vdg_ids)
    if len(unique_kids) < min_kids:
        errors.append(f"Need >= {min_kids} kids, got: {len(unique_kids)}")
    
    # Future: check unique creators (requires VDG metadata)
    # For now, just warn if we can't verify
    if min_unique_creators > 1:
        warnings.append(f"Cannot verify {min_unique_creators} unique creators without VDG metadata")
    
    return ClusterValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


# ====================
# PR CHECKLIST GENERATOR
# ====================

def generate_schema_checklist(model_cls: type) -> str:
    """
    Generate PR checklist from Pydantic model.
    
    Auto-generates 1:1 field/type mapping from current code.
    """
    lines = [
        f"## {model_cls.__name__} (Schema Fields)",
        f"- Canonical: `{model_cls.__module__}.{model_cls.__name__}`",
        ""
    ]
    
    # Get fields (Pydantic v2)
    if hasattr(model_cls, "model_fields"):
        for name, field in model_cls.model_fields.items():
            ann = getattr(field, "annotation", None) or model_cls.__annotations__.get(name)
            required = field.is_required()
            req_str = "required" if required else "optional"
            lines.append(f"- [ ] `{name}`: `{ann}` — {req_str}")
    
    return "\n".join(lines)
