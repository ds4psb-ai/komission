"""
Cluster Service

P2 Roadmap: 클러스터 10개 수동 생성 지원
- Parent-Kids 구조 관리
- Distill 준비 상태 검증
- 클러스터 유사도 계산

SoR = In-memory (MVP), will migrate to DB
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.vdg_v4 import (
    ContentCluster, ClusterKid, ClusterSignature
)
from app.utils.time import iso_now, generate_short_id

logger = logging.getLogger(__name__)


# ====================
# P2 CLUSTER TEMPLATES
# ====================

P2_CLUSTER_TEMPLATES = {
    "question_hook": {
        "cluster_name": "질문형 훅 패턴",
        "signature": {
            "hook_pattern": "question_hook",
            "primary_intent": "curiosity",
            "audio_style": "direct_address",
            "key_elements": ["question", "pause", "reveal"]
        }
    },
    "reversal_hook": {
        "cluster_name": "반전 훅 패턴",
        "signature": {
            "hook_pattern": "reversal_hook",
            "primary_intent": "surprise",
            "audio_style": "buildup",
            "key_elements": ["setup", "misdirection", "reveal"]
        }
    },
    "visual_punch": {
        "cluster_name": "시각적 펀치 패턴",
        "signature": {
            "hook_pattern": "visual_punch",
            "primary_intent": "impact",
            "audio_style": "minimal",
            "key_elements": ["striking_visual", "quick_cut", "eye_catch"]
        }
    },
    "audio_trend": {
        "cluster_name": "오디오 트렌드 패턴",
        "signature": {
            "hook_pattern": "audio_trend",
            "primary_intent": "trend_riding",
            "audio_style": "trending_sound",
            "key_elements": ["popular_audio", "sync", "lip_sync"]
        }
    },
    "tutorial": {
        "cluster_name": "튜토리얼 구조 패턴",
        "signature": {
            "hook_pattern": "tutorial_structure",
            "primary_intent": "education",
            "audio_style": "voiceover",
            "key_elements": ["problem", "steps", "result"]
        }
    },
    "review": {
        "cluster_name": "리뷰 구조 패턴",
        "signature": {
            "hook_pattern": "review_structure",
            "primary_intent": "evaluation",
            "audio_style": "commentary",
            "key_elements": ["intro", "features", "verdict"]
        }
    },
    "vlog": {
        "cluster_name": "브이로그 구조 패턴",
        "signature": {
            "hook_pattern": "vlog_structure",
            "primary_intent": "lifestyle",
            "audio_style": "casual_narration",
            "key_elements": ["day_intro", "activities", "outro"]
        }
    },
    "unboxing": {
        "cluster_name": "제품 언박싱 패턴",
        "signature": {
            "hook_pattern": "unboxing",
            "primary_intent": "product_reveal",
            "audio_style": "asmr_commentary",
            "key_elements": ["package", "reveal", "first_impression"]
        }
    },
    "challenge": {
        "cluster_name": "챌린지형 패턴",
        "signature": {
            "hook_pattern": "challenge",
            "primary_intent": "participation",
            "audio_style": "challenge_sound",
            "key_elements": ["setup", "attempt", "result"]
        }
    },
    "comment_mise": {
        "cluster_name": "댓글 미장센 패턴",
        "signature": {
            "hook_pattern": "comment_mise",
            "primary_intent": "engagement",
            "audio_style": "reactive",
            "key_elements": ["bait_hook", "engagement_trigger", "cta"]
        }
    }
}


class ClusterService:
    """
    P2 Cluster Management Service.
    
    Usage:
        service = get_cluster_service()
        
        # Create from template
        cluster = service.create_from_template(
            template_key="question_hook",
            parent_vdg_id="vdg_xxx",
            parent_content_id="tiktok_abc123"
        )
        
        # Add kids
        service.add_kid(cluster.cluster_id, ClusterKid(...))
        
        # Check distill readiness
        if service.is_distill_ready(cluster.cluster_id):
            print("Ready for DistillRun!")
    """
    
    def __init__(self):
        """Initialize with in-memory storage (MVP)."""
        self._clusters: Dict[str, ContentCluster] = {}
    
    # ====================
    # CRUD OPERATIONS
    # ====================
    
    def create_cluster(
        self,
        cluster_name: str,
        parent_vdg_id: str,
        parent_content_id: str,
        signature: Optional[ClusterSignature] = None,
        parent_tier: str = "A",
        parent_merger_quality: str = "gold",
        created_by: str = "manual"
    ) -> ContentCluster:
        """Create a new cluster."""
        cluster_id = f"cluster_{generate_short_id()}"
        now = iso_now()
        
        cluster = ContentCluster(
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            parent_vdg_id=parent_vdg_id,
            parent_content_id=parent_content_id,
            parent_tier=parent_tier,
            parent_merger_quality=parent_merger_quality,
            signature=signature or ClusterSignature(),
            created_by=created_by,
            created_at=now,
            updated_at=now
        )
        
        self._clusters[cluster_id] = cluster
        logger.info(f"Created cluster: {cluster_id} ({cluster_name})")
        return cluster
    
    def create_from_template(
        self,
        template_key: str,
        parent_vdg_id: str,
        parent_content_id: str,
        parent_tier: str = "A",
        parent_merger_quality: str = "gold"
    ) -> ContentCluster:
        """Create cluster from P2 template."""
        if template_key not in P2_CLUSTER_TEMPLATES:
            raise ValueError(f"Unknown template: {template_key}. Available: {list(P2_CLUSTER_TEMPLATES.keys())}")
        
        template = P2_CLUSTER_TEMPLATES[template_key]
        signature = ClusterSignature(**template["signature"])
        
        return self.create_cluster(
            cluster_name=template["cluster_name"],
            parent_vdg_id=parent_vdg_id,
            parent_content_id=parent_content_id,
            signature=signature,
            parent_tier=parent_tier,
            parent_merger_quality=parent_merger_quality,
            created_by="template"
        )
    
    def get_cluster(self, cluster_id: str) -> Optional[ContentCluster]:
        """Get cluster by ID."""
        return self._clusters.get(cluster_id)
    
    def list_clusters(self, distill_ready_only: bool = False) -> List[ContentCluster]:
        """List all clusters, optionally filtered by distill readiness."""
        clusters = list(self._clusters.values())
        if distill_ready_only:
            clusters = [c for c in clusters if c.is_distill_ready()]
        return clusters
    
    def delete_cluster(self, cluster_id: str) -> bool:
        """Delete a cluster."""
        if cluster_id in self._clusters:
            del self._clusters[cluster_id]
            logger.info(f"Deleted cluster: {cluster_id}")
            return True
        return False
    
    # ====================
    # KIDS MANAGEMENT
    # ====================
    
    def add_kid(
        self,
        cluster_id: str,
        kid: ClusterKid
    ) -> bool:
        """Add a kid to a cluster."""
        cluster = self._clusters.get(cluster_id)
        if not cluster:
            return False
        
        # Check for duplicate
        existing_ids = [k.vdg_id for k in cluster.kids]
        if kid.vdg_id in existing_ids:
            logger.warning(f"Kid {kid.vdg_id} already in cluster {cluster_id}")
            return False
        
        # Add kid
        cluster.kids.append(kid)
        
        # Sync legacy fields
        if kid.vdg_id not in cluster.kid_vdg_ids:
            cluster.kid_vdg_ids.append(kid.vdg_id)
        if kid.content_id not in cluster.kid_content_ids:
            cluster.kid_content_ids.append(kid.content_id)
        
        # Update distill readiness
        cluster.distill_ready = cluster.is_distill_ready()
        cluster.updated_at = iso_now()
        
        logger.info(f"Added kid {kid.vdg_id} to cluster {cluster_id} (now {len(cluster.kids)} kids)")
        return True
    
    def remove_kid(
        self,
        cluster_id: str,
        kid_vdg_id: str
    ) -> bool:
        """Remove a kid from a cluster."""
        cluster = self._clusters.get(cluster_id)
        if not cluster:
            return False
        
        cluster.kids = [k for k in cluster.kids if k.vdg_id != kid_vdg_id]
        cluster.kid_vdg_ids = [v for v in cluster.kid_vdg_ids if v != kid_vdg_id]
        
        # Update distill readiness
        cluster.distill_ready = cluster.is_distill_ready()
        cluster.updated_at = iso_now()
        
        return True
    
    # ====================
    # DISTILL READINESS
    # ====================
    
    def is_distill_ready(self, cluster_id: str) -> bool:
        """Check if cluster is ready for DistillRun."""
        cluster = self._clusters.get(cluster_id)
        if not cluster:
            return False
        return cluster.is_distill_ready()
    
    def get_distill_readiness_report(self, cluster_id: str) -> Dict[str, Any]:
        """Get detailed distill readiness report."""
        cluster = self._clusters.get(cluster_id)
        if not cluster:
            return {"error": "Cluster not found"}
        
        checks = []
        
        # Check parent tier
        tier_ok = cluster.parent_tier in ["S", "A"]
        checks.append({
            "name": "parent_tier",
            "passed": tier_ok,
            "value": cluster.parent_tier,
            "required": "S or A"
        })
        
        # Check merger quality
        quality_ok = cluster.parent_merger_quality == "gold"
        checks.append({
            "name": "parent_merger_quality",
            "passed": quality_ok,
            "value": cluster.parent_merger_quality,
            "required": "gold"
        })
        
        # Check kids count
        kids_ok = len(cluster.kids) >= cluster.min_kids_required
        checks.append({
            "name": "kids_count",
            "passed": kids_ok,
            "value": len(cluster.kids),
            "required": f">= {cluster.min_kids_required}"
        })
        
        # Check success/failure contrast
        has_success = any(k.success for k in cluster.kids)
        has_failure = any(not k.success for k in cluster.kids)
        contrast_ok = has_success and has_failure
        checks.append({
            "name": "success_failure_contrast",
            "passed": contrast_ok,
            "value": f"success={has_success}, failure={has_failure}",
            "required": "both needed"
        })
        
        all_passed = all(c["passed"] for c in checks)
        
        return {
            "cluster_id": cluster_id,
            "cluster_name": cluster.cluster_name,
            "distill_ready": all_passed,
            "checks": checks,
            "recommendation": "Ready for DistillRun!" if all_passed else "Fix failing checks first"
        }
    
    # ====================
    # P2 PROGRESS TRACKING
    # ====================
    
    def get_p2_progress(self) -> Dict[str, Any]:
        """Get P2 roadmap progress (10 clusters goal)."""
        total = len(self._clusters)
        distill_ready = sum(1 for c in self._clusters.values() if c.is_distill_ready())
        
        # Template coverage
        template_coverage = {}
        for template_key in P2_CLUSTER_TEMPLATES:
            template_coverage[template_key] = sum(
                1 for c in self._clusters.values()
                if c.signature.hook_pattern == P2_CLUSTER_TEMPLATES[template_key]["signature"]["hook_pattern"]
            )
        
        return {
            "total_clusters": total,
            "distill_ready_clusters": distill_ready,
            "target": 10,
            "progress_percent": min(100, int(distill_ready / 10 * 100)),
            "template_coverage": template_coverage,
            "is_p2_complete": distill_ready >= 10
        }
    
    # ====================
    # SIMILARITY MATCHING
    # ====================
    
    def calculate_signature_similarity(
        self,
        sig1: ClusterSignature,
        sig2: ClusterSignature
    ) -> float:
        """Calculate similarity between two cluster signatures (0-1)."""
        score = 0.0
        total_weight = 0.0
        
        # Hook pattern (40%)
        if sig1.hook_pattern == sig2.hook_pattern:
            score += 0.40
        total_weight += 0.40
        
        # Primary intent (30%)
        if sig1.primary_intent == sig2.primary_intent:
            score += 0.30
        total_weight += 0.30
        
        # Audio style (20%)
        if sig1.audio_style == sig2.audio_style:
            score += 0.20
        total_weight += 0.20
        
        # Key elements overlap (10%)
        if sig1.key_elements and sig2.key_elements:
            overlap = len(set(sig1.key_elements) & set(sig2.key_elements))
            max_elems = max(len(sig1.key_elements), len(sig2.key_elements))
            score += 0.10 * (overlap / max_elems)
        total_weight += 0.10
        
        return score / total_weight if total_weight > 0 else 0.0


# Singleton
_cluster_service_instance = None


def get_cluster_service() -> ClusterService:
    """Get singleton ClusterService instance."""
    global _cluster_service_instance
    if _cluster_service_instance is None:
        _cluster_service_instance = ClusterService()
    return _cluster_service_instance
