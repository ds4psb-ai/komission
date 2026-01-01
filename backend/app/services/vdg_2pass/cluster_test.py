"""
Cluster Test Service (P1-3)

Proof-ready 노드만을 대상으로 클러스터링 실테스트 수행

1. proof_ready=true인 kicks만 대상
2. mechanism 기반 signature 생성
3. 클러스터 할당 및 성과 추적

사용:
    from app.services.vdg_2pass.cluster_test import cluster_test_service
    clusters = await cluster_test_service.run_test(db)
"""
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class ClusterCandidate:
    """클러스터 후보 노드"""
    node_id: str
    kick_ids: List[str]
    mechanisms: List[str]
    avg_confidence: float
    evidence_score: float
    signature: str


@dataclass
class ClusterResult:
    """클러스터 결과"""
    cluster_id: str
    signature: str
    member_count: int
    members: List[ClusterCandidate]
    dominant_mechanisms: List[str]
    avg_confidence: float
    quality_score: float


class ClusterTestService:
    """
    Proof-Ready 노드 클러스터링 테스트 서비스
    
    1. DB에서 proof_ready kicks 조회
    2. mechanism 기반 signature 생성
    3. signature 유사도로 클러스터링
    4. 클러스터 품질 점수 계산
    """
    
    MIN_CONFIDENCE = 0.6  # 클러스터링 대상 최소 신뢰도
    MIN_CLUSTER_SIZE = 2  # 최소 클러스터 크기
    MECHANISM_WEIGHTS = {
        # 메커니즘 유형별 가중치
        "hook": 2.0,
        "반전": 1.5,
        "감정": 1.3,
        "미장센": 1.2,
        "default": 1.0,
    }
    
    async def run_test(
        self,
        db: AsyncSession,
        min_confidence: float = 0.6,
        limit: int = 500,
    ) -> Dict[str, Any]:
        """
        클러스터 테스트 실행
        
        Args:
            db: Database session
            min_confidence: 최소 신뢰도 필터
            limit: 최대 처리 노드 수
            
        Returns:
            {
                "total_candidates": int,
                "total_clusters": int,
                "clusters": List[ClusterResult],
                "unclustered": int,
                "quality_summary": dict,
            }
        """
        from app.models import ViralKick, RemixNode
        
        logger.info(f"🧪 Starting cluster test with min_confidence={min_confidence}")
        
        # 1. proof_ready kicks 조회
        query = (
            select(ViralKick)
            .where(ViralKick.proof_ready == True)
            .where(ViralKick.confidence >= min_confidence)
            .order_by(ViralKick.confidence.desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        kicks = result.scalars().all()
        
        if not kicks:
            logger.warning("No proof-ready kicks found")
            return {
                "total_candidates": 0,
                "total_clusters": 0,
                "clusters": [],
                "unclustered": 0,
                "quality_summary": {},
            }
        
        logger.info(f"📊 Found {len(kicks)} proof-ready kicks")
        
        # 2. 노드별 kicks 그룹화
        node_kicks = defaultdict(list)
        for kick in kicks:
            node_kicks[str(kick.node_id)].append(kick)
        
        # 3. 클러스터 후보 생성
        candidates = []
        for node_id, node_kick_list in node_kicks.items():
            candidate = self._create_candidate(node_id, node_kick_list)
            if candidate:
                candidates.append(candidate)
        
        logger.info(f"🎯 Created {len(candidates)} cluster candidates")
        
        # 4. Signature 기반 클러스터링
        clusters = self._cluster_by_signature(candidates)
        
        # 5. 결과 집계
        clustered_count = sum(c.member_count for c in clusters)
        unclustered_count = len(candidates) - clustered_count
        
        quality_summary = self._calculate_quality_summary(clusters)
        
        logger.info(f"✅ Cluster test complete: {len(clusters)} clusters, {unclustered_count} unclustered")
        
        return {
            "total_candidates": len(candidates),
            "total_clusters": len(clusters),
            "clusters": [self._cluster_to_dict(c) for c in clusters],
            "unclustered": unclustered_count,
            "quality_summary": quality_summary,
            "run_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _create_candidate(
        self, 
        node_id: str, 
        kicks: List[Any]
    ) -> Optional[ClusterCandidate]:
        """클러스터 후보 생성"""
        if not kicks:
            return None
        
        mechanisms = [k.mechanism for k in kicks if k.mechanism]
        if not mechanisms:
            return None
        
        # Signature 생성 (메커니즘 정규화 후 해시)
        normalized = sorted(set(self._normalize_mechanism(m) for m in mechanisms))
        signature = hashlib.md5("|".join(normalized).encode()).hexdigest()[:12]
        
        # 점수 계산
        avg_confidence = sum(k.confidence for k in kicks) / len(kicks)
        
        # Evidence score (comment + frame 증거 수)
        evidence_score = sum(
            len(k.comment_evidence_ids or []) + len(k.frame_evidence_ids or [])
            for k in kicks
        ) / len(kicks)
        
        return ClusterCandidate(
            node_id=node_id,
            kick_ids=[k.kick_id for k in kicks],
            mechanisms=normalized,
            avg_confidence=avg_confidence,
            evidence_score=evidence_score,
            signature=signature,
        )
    
    def _normalize_mechanism(self, mechanism: str) -> str:
        """메커니즘 정규화 (키워드 추출)"""
        # 핵심 키워드 추출
        keywords = []
        
        mechanism_lower = mechanism.lower()
        
        # 핵심 패턴 매칭
        patterns = [
            ("hook", ["hook", "훅", "첫"]),
            ("반전", ["반전", "twist", "전환"]),
            ("감정", ["감정", "emotion", "표정", "리액션"]),
            ("미장센", ["미장센", "앵글", "구도", "프레이밍"]),
            ("리듬", ["박자", "리듬", "비트", "타이밍"]),
            ("서사", ["스토리", "서사", "내러티브"]),
        ]
        
        for keyword, triggers in patterns:
            if any(t in mechanism_lower for t in triggers):
                keywords.append(keyword)
        
        if not keywords:
            # 첫 20자를 해시로 사용
            return hashlib.md5(mechanism[:20].encode()).hexdigest()[:8]
        
        return "_".join(sorted(set(keywords)))
    
    def _cluster_by_signature(
        self, 
        candidates: List[ClusterCandidate]
    ) -> List[ClusterResult]:
        """Signature 기반 클러스터링"""
        # Signature별 그룹화
        sig_groups = defaultdict(list)
        for c in candidates:
            sig_groups[c.signature].append(c)
        
        clusters = []
        for signature, members in sig_groups.items():
            if len(members) < self.MIN_CLUSTER_SIZE:
                continue
            
            # 지배적 메커니즘 찾기
            mechanism_counts = defaultdict(int)
            for m in members:
                for mech in m.mechanisms:
                    mechanism_counts[mech] += 1
            
            dominant = sorted(mechanism_counts.items(), key=lambda x: -x[1])[:3]
            dominant_mechanisms = [m[0] for m in dominant]
            
            # 클러스터 품질 점수
            avg_conf = sum(m.avg_confidence for m in members) / len(members)
            avg_evidence = sum(m.evidence_score for m in members) / len(members)
            quality_score = (avg_conf * 0.6 + min(avg_evidence / 5, 1) * 0.4)
            
            clusters.append(ClusterResult(
                cluster_id=f"cl_{signature}",
                signature=signature,
                member_count=len(members),
                members=members,
                dominant_mechanisms=dominant_mechanisms,
                avg_confidence=avg_conf,
                quality_score=quality_score,
            ))
        
        # 품질순 정렬
        clusters.sort(key=lambda c: -c.quality_score)
        
        return clusters
    
    def _calculate_quality_summary(
        self, 
        clusters: List[ClusterResult]
    ) -> Dict[str, Any]:
        """전체 품질 요약"""
        if not clusters:
            return {
                "avg_cluster_size": 0,
                "avg_quality_score": 0,
                "top_mechanisms": [],
            }
        
        total_members = sum(c.member_count for c in clusters)
        avg_size = total_members / len(clusters)
        avg_quality = sum(c.quality_score for c in clusters) / len(clusters)
        
        # Top mechanisms across all clusters
        mech_counts = defaultdict(int)
        for c in clusters:
            for m in c.dominant_mechanisms:
                mech_counts[m] += c.member_count
        
        top_mechanisms = sorted(mech_counts.items(), key=lambda x: -x[1])[:5]
        
        return {
            "avg_cluster_size": round(avg_size, 1),
            "avg_quality_score": round(avg_quality, 3),
            "top_mechanisms": [{"mechanism": m, "count": c} for m, c in top_mechanisms],
        }
    
    def _cluster_to_dict(self, cluster: ClusterResult) -> Dict[str, Any]:
        """ClusterResult를 dict로 변환"""
        return {
            "cluster_id": cluster.cluster_id,
            "signature": cluster.signature,
            "member_count": cluster.member_count,
            "dominant_mechanisms": cluster.dominant_mechanisms,
            "avg_confidence": round(cluster.avg_confidence, 3),
            "quality_score": round(cluster.quality_score, 3),
            "members": [
                {
                    "node_id": m.node_id,
                    "kick_ids": m.kick_ids,
                    "mechanisms": m.mechanisms,
                    "avg_confidence": round(m.avg_confidence, 3),
                    "evidence_score": round(m.evidence_score, 2),
                }
                for m in cluster.members
            ],
        }


# Singleton
cluster_test_service = ClusterTestService()
