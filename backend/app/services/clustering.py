"""
Pattern Clustering Service (PEGL v1.0)
Based on 15_FINAL_ARCHITECTURE.md

핵심 원칙:
- 유사도 클러스터링(DB): Parent-Kids 변주를 데이터화
- 패턴 뎁스 구조를 축적
- 클러스터 ID를 기반으로 NotebookLM 폴더 분할

PEGL v1.0 Updates:
- VDGEdge candidate 자동 생성
- 유사도 기반 Parent-Child 관계 추론
"""
import logging
import re
import hashlib
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.time import utcnow

from app.schemas.analysis_schema import VideoAnalysisSchema
from app.models import PatternCluster, NotebookLibraryEntry, RemixNode, VDGEdgeType

logger = logging.getLogger(__name__)


class PatternClusteringService:
    """
    패턴 클러스터링 서비스
    영상 분석 스키마를 기반으로 유사도 계산 및 클러스터 할당
    """
    
    # 패턴 타입별 가중치 (VDG v3.2 기준)
    WEIGHTS = {
        "microbeat_sequence": 0.30,  # microbeats 순서 유사도
        "hook": 0.25,                # 훅 유형/길이
        "visual_pattern": 0.20,      # 시각 패턴
        "audio_pattern": 0.15,       # 오디오 패턴
        "timing": 0.10,              # 타이밍 프로필
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def calculate_similarity(
        self, 
        schema1: VideoAnalysisSchema, 
        schema2: VideoAnalysisSchema
    ) -> float:
        """
        두 스키마 간 유사도 계산 (0.0 ~ 1.0)
        
        Args:
            schema1: 첫 번째 분석 스키마
            schema2: 두 번째 분석 스키마
        
        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        total_score = 0.0
        weight_sum = 0.0

        normalized1 = self._normalize_schema(schema1)
        normalized2 = self._normalize_schema(schema2)

        # 1. Microbeat sequence 유사도
        seq1 = normalized1.get("microbeat_sequence")
        seq2 = normalized2.get("microbeat_sequence")
        if seq1 and seq2:
            sequence_score = self._sequence_similarity(seq1, seq2)
            total_score += sequence_score * self.WEIGHTS["microbeat_sequence"]
            weight_sum += self.WEIGHTS["microbeat_sequence"]

        # 2. 훅 유사도
        hook_score = self._compare_hooks(normalized1.get("hook"), normalized2.get("hook"))
        if hook_score is not None:
            total_score += hook_score * self.WEIGHTS["hook"]
            weight_sum += self.WEIGHTS["hook"]

        # 3. 시각 패턴 유사도
        visual_score = self._compare_visual_patterns(
            normalized1.get("visual_patterns"), 
            normalized2.get("visual_patterns")
        )
        if visual_score is not None:
            total_score += visual_score * self.WEIGHTS["visual_pattern"]
            weight_sum += self.WEIGHTS["visual_pattern"]

        # 4. 오디오 패턴 유사도
        audio_score = self._compare_audio_patterns(
            normalized1.get("audio_flags"),
            normalized2.get("audio_flags"),
            normalized1.get("audio_patterns"),
            normalized2.get("audio_patterns"),
        )
        if audio_score is not None:
            total_score += audio_score * self.WEIGHTS["audio_pattern"]
            weight_sum += self.WEIGHTS["audio_pattern"]

        # 5. 타이밍 유사도
        timing_score = self._compare_timing(
            normalized1.get("timing_profile"),
            normalized2.get("timing_profile"),
        )
        if timing_score is not None:
            total_score += timing_score * self.WEIGHTS["timing"]
            weight_sum += self.WEIGHTS["timing"]

        if weight_sum == 0:
            return 0.5
        return min(1.0, total_score / weight_sum)
    
    def _compare_hooks(self, hook1, hook2) -> Optional[float]:
        """훅 비교"""
        if not hook1 or not hook2:
            return None

        type1 = hook1.get("type")
        type2 = hook2.get("type")
        dur1 = hook1.get("duration_sec")
        dur2 = hook2.get("duration_sec")

        if type1 and type2 and type1 == type2:
            if dur1 is None or dur2 is None:
                return 0.9
            duration_diff = abs(dur1 - dur2)
            if duration_diff < 0.5:
                return 1.0
            if duration_diff < 1.0:
                return 0.8
            return 0.6
        return 0.3
    
    def _compare_visual_patterns(self, patterns1: Optional[List], patterns2: Optional[List]) -> Optional[float]:
        """시각 패턴 비교"""
        if not patterns1 or not patterns2:
            return None

        compare_count = min(3, len(patterns1), len(patterns2))
        matches = 0
        
        for i in range(compare_count):
            if patterns1[i] == patterns2[i]:
                matches += 1
        
        return matches / compare_count
    
    def _compare_timing(self, timing1: Optional[List[float]], timing2: Optional[List[float]]) -> Optional[float]:
        """타이밍 프로필 비교"""
        if not timing1 or not timing2:
            return None
        
        # 총 길이 비교
        total1 = sum(timing1)
        total2 = sum(timing2)
        
        if abs(total1 - total2) < 2.0:
            return 0.9
        elif abs(total1 - total2) < 5.0:
            return 0.6
        return 0.3

    def _compare_audio_patterns(
        self, 
        audio_flags1: Optional[dict],
        audio_flags2: Optional[dict],
        audio_patterns1: Optional[List[str]],
        audio_patterns2: Optional[List[str]],
    ) -> Optional[float]:
        """오디오 패턴 비교"""
        if audio_flags1 is None or audio_flags2 is None:
            if audio_patterns1 and audio_patterns2:
                compare_count = min(3, len(audio_patterns1), len(audio_patterns2))
                matches = 0
                for i in range(compare_count):
                    if audio_patterns1[i] == audio_patterns2[i]:
                        matches += 1
                return matches / compare_count
            return None

        trending1 = audio_flags1.get("is_trending")
        trending2 = audio_flags2.get("is_trending")
        if trending1 is None or trending2 is None:
            return 0.5
        return 1.0 if trending1 == trending2 else 0.5

    def _sequence_similarity(self, seq1: List[str], seq2: List[str]) -> float:
        """간단한 편집거리 기반 시퀀스 유사도"""
        if not seq1 or not seq2:
            return 0.5
        n, m = len(seq1), len(seq2)
        if n == 0 or m == 0:
            return 0.0
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = i
        for j in range(m + 1):
            dp[0][j] = j
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if seq1[i - 1] == seq2[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )
        dist = dp[n][m]
        max_len = max(n, m)
        return max(0.0, 1.0 - (dist / max_len))

    def _normalize_schema(self, schema) -> dict:
        """스키마 형태를 통일 (VideoAnalysisSchema / VDG / dict 지원)"""
        if hasattr(schema, "model_dump"):
            payload = schema.model_dump()
        elif isinstance(schema, dict):
            payload = schema
        else:
            payload = {}

        # VDG v3.x 형태
        if "hook_genome" in payload:
            hook_genome = payload.get("hook_genome") or {}
            microbeats = hook_genome.get("microbeats") or []
            sequence = [f"{b.get('role','')}:{b.get('cue','')}" for b in microbeats if b]
            hook_type = hook_genome.get("pattern") or hook_genome.get("delivery")
            hook_duration = None
            if hook_genome.get("start_sec") is not None and hook_genome.get("end_sec") is not None:
                hook_duration = max(0.0, hook_genome.get("end_sec") - hook_genome.get("start_sec"))

            visual_patterns: List[str] = []
            audio_patterns: List[str] = []
            timing_profile: List[float] = []
            scenes = payload.get("scenes") or []
            for scene in scenes:
                for shot in scene.get("shots") or []:
                    camera = shot.get("camera") or {}
                    move = camera.get("move") or camera.get("shot")
                    if move:
                        visual_patterns.append(str(move))
                    start = shot.get("start")
                    end = shot.get("end")
                    if start is not None and end is not None:
                        timing_profile.append(max(0.0, end - start))

            return {
                "microbeat_sequence": sequence,
                "hook": {"type": hook_type, "duration_sec": hook_duration},
                "visual_patterns": visual_patterns,
                "audio_patterns": audio_patterns,
                "audio_flags": None,
                "timing_profile": timing_profile,
                "primary_pattern": payload.get("summary") or payload.get("content_id"),
            }

        # VideoAnalysisSchema 형태
        hook = payload.get("hook") or {}
        shots = payload.get("shots") or []
        visual_patterns = [s.get("visual_pattern") for s in shots if s.get("visual_pattern")]
        audio_patterns = [s.get("audio_pattern") for s in shots if s.get("audio_pattern")]
        timing_profile = payload.get("timing_profile")
        if not timing_profile:
            timing_profile = [s.get("duration_sec") for s in shots if s.get("duration_sec") is not None]

        # Fallback: legacy schema에 microbeats가 없으면 shots로 pseudo-sequence 생성
        microbeat_sequence = payload.get("microbeats")
        if not microbeat_sequence and shots:
            microbeat_sequence = [
                f"{s.get('visual_pattern', 'unknown')}:{s.get('audio_pattern', 'none')}"
                for s in shots[:10]  # 최대 10개까지
            ]

        return {
            "microbeat_sequence": microbeat_sequence,
            "hook": {
                "type": hook.get("attention_technique"),
                "duration_sec": hook.get("hook_duration_sec"),
            },
            "visual_patterns": visual_patterns,
            "audio_patterns": audio_patterns,
            "audio_flags": {"is_trending": payload.get("audio_is_trending")},
            "timing_profile": timing_profile,
            "primary_pattern": payload.get("primary_pattern"),
        }

    def _sanitize_cluster_id(self, raw_id: str) -> str:
        """Normalize and cap cluster_id to fit DB constraints."""
        if not raw_id:
            return "pattern"
        slug = re.sub(r"[^a-z0-9-]+", "-", raw_id.lower()).strip("-")
        if not slug:
            return "pattern"
        if len(slug) <= 90:
            return slug
        digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:8]
        return f"{slug[:90]}-{digest}"
    
    async def get_or_create_cluster(
        self, 
        schema: VideoAnalysisSchema,
        similarity_threshold: float = 0.75
    ) -> Tuple[str, bool]:
        """
        스키마에 맞는 클러스터 찾기 또는 새로 생성
        
        Args:
            schema: 분석 스키마
            similarity_threshold: 동일 클러스터로 판정할 유사도 임계값
        
        Returns:
            (cluster_id, is_new) 튜플
        """
        # 기존 클러스터 조회
        result = await self.db.execute(select(PatternCluster))
        existing_clusters = result.scalars().all()

        normalized = self._normalize_schema(schema)
        proposed_cluster_id = self._sanitize_cluster_id(
            (normalized.get("primary_pattern") or "pattern")
        )

        # 최근 라이브러리 엔트리 기준 유사도 비교
        best_cluster_id = None
        best_score = 0.0
        entries_result = await self.db.execute(
            select(NotebookLibraryEntry)
            .where(NotebookLibraryEntry.cluster_id.isnot(None))
            .where(NotebookLibraryEntry.analysis_schema.isnot(None))
            .order_by(NotebookLibraryEntry.created_at.desc())
            .limit(200)
        )
        entries = entries_result.scalars().all()
        for entry in entries:
            score = self.calculate_similarity(schema, entry.analysis_schema)
            if score > best_score:
                best_score = score
                best_cluster_id = entry.cluster_id

        if best_cluster_id and best_score >= similarity_threshold:
            cluster = next((c for c in existing_clusters if c.cluster_id == best_cluster_id), None)
            if cluster:
                cluster.member_count += 1
                await self.db.commit()
                return cluster.cluster_id, False

        # 새 클러스터 생성 (ID 충돌 방지)
        pattern_type = self._infer_pattern_type(schema)
        candidate_id = proposed_cluster_id
        if any(c.cluster_id == candidate_id for c in existing_clusters):
            candidate_id = self._sanitize_cluster_id(
                f"{candidate_id}-{utcnow().strftime('%Y%m%d%H%M%S')}"
            )

        new_cluster = PatternCluster(
            cluster_id=candidate_id,
            cluster_name=normalized.get("primary_pattern") or candidate_id,
            pattern_type=pattern_type,
            member_count=1,
            avg_outlier_score=None,
        )

        self.db.add(new_cluster)
        await self.db.commit()

        logger.info(f"Created new cluster: {candidate_id}")
        return candidate_id, True
    
    def _infer_pattern_type(self, schema: VideoAnalysisSchema) -> str:
        """스키마에서 주요 패턴 타입 추론"""
        normalized = self._normalize_schema(schema)
        hook_type = (normalized.get("hook") or {}).get("type") or ""
        if hook_type in ["text_punch", "question"]:
            return "semantic"
        if hook_type in ["face_zoom", "zoom_in"]:
            return "visual"
        audio_flags = normalized.get("audio_flags") or {}
        if audio_flags.get("is_trending"):
            return "audio"
        return "visual"  # 기본값

    async def update_cluster_stats(self, cluster_id: str, outlier_score: Optional[float] = None):
        """
        클러스터 통계 업데이트
        
        Args:
            cluster_id: 클러스터 ID
            outlier_score: 새로 추가된 항목의 아웃라이어 점수
        """
        result = await self.db.execute(
            select(PatternCluster).where(PatternCluster.cluster_id == cluster_id)
        )
        cluster = result.scalar_one_or_none()
        
        if cluster and outlier_score is not None:
            # 이동 평균으로 avg_outlier_score 업데이트
            if cluster.avg_outlier_score is None:
                cluster.avg_outlier_score = outlier_score
            else:
                # 가중 평균
                n = cluster.member_count
                cluster.avg_outlier_score = (
                    (cluster.avg_outlier_score * (n - 1) + outlier_score) / n
                )
            await self.db.commit()


async def assign_cluster_to_entry(
    db: AsyncSession,
    entry: NotebookLibraryEntry,
    schema: VideoAnalysisSchema,
) -> str:
    """
    분석 스키마를 기반으로 Notebook Library 엔트리에 클러스터 할당
    
    Args:
        db: DB 세션
        entry: 대상 라이브러리 엔트리
        schema: 분석 스키마
    
    Returns:
        할당된 cluster_id
    """
    service = PatternClusteringService(db)
    cluster_id, is_new = await service.get_or_create_cluster(schema)
    
    # 엔트리 업데이트
    entry.cluster_id = cluster_id
    schema_payload = schema.model_dump() if hasattr(schema, "model_dump") else schema
    entry.analysis_schema = schema_payload
    entry.schema_version = "v3.2" if isinstance(schema_payload, dict) and "hook_genome" in schema_payload else "v1.0"
    
    await db.commit()
    
    logger.info(f"Assigned cluster {cluster_id} to entry {entry.id} (new={is_new})")
    return cluster_id


async def create_similarity_based_edges(
    db: AsyncSession,
    child_node_id,
    child_schema: VideoAnalysisSchema,
    similarity_threshold: float = 0.70,
    max_edges: int = 5,
) -> List[Tuple[str, float]]:
    """
    유사도 기반으로 VDGEdge candidate 생성 (PEGL v1.0)
    
    새로 분석된 콘텐츠와 기존 Parent 후보들 사이의 유사도를 계산하여
    임계값 이상인 경우 VDGEdge candidate를 생성합니다.
    
    Args:
        db: DB 세션
        child_node_id: 새로 분석된 노드의 ID
        child_schema: 새 노드의 분석 스키마
        similarity_threshold: Edge 생성 임계값 (기본 0.70)
        max_edges: 최대 생성할 Edge 수 (기본 5)
        
    Returns:
        [(parent_node_id, confidence), ...] 생성된 Edge 정보
    """
    from app.services.vdg_edge_service import VDGEdgeService
    from uuid import UUID
    
    service = PatternClusteringService(db)
    edge_service = VDGEdgeService(db)
    
    # Parent 후보 조회 (분석 스키마가 있는 RemixNode)
    result = await db.execute(
        select(RemixNode)
        .where(RemixNode.gemini_analysis.isnot(None))
        .where(RemixNode.id != child_node_id)  # 자기 자신 제외
        .order_by(RemixNode.created_at.desc())
        .limit(100)  # 최근 100개만 비교
    )
    parent_candidates = result.scalars().all()
    
    # 유사도 계산 및 정렬
    scored_parents = []
    for parent in parent_candidates:
        try:
            parent_schema = parent.gemini_analysis
            if not parent_schema:
                continue
            
            score = service.calculate_similarity(child_schema, parent_schema)
            if score >= similarity_threshold:
                scored_parents.append((parent, score))
        except Exception as e:
            logger.warning(f"Similarity calculation failed for {parent.id}: {e}")
            continue
    
    # 점수순 정렬
    scored_parents.sort(key=lambda x: x[1], reverse=True)
    scored_parents = scored_parents[:max_edges]
    
    # VDGEdge candidate 생성
    created_edges = []
    for parent, score in scored_parents:
        try:
            # Edge 타입 결정 (유사도 기준)
            if score >= 0.85:
                edge_type = VDGEdgeType.VARIATION
            elif score >= 0.75:
                edge_type = VDGEdgeType.INSPIRED_BY
            else:
                edge_type = VDGEdgeType.INSPIRED_BY
            
            edge = await edge_service.create_candidate_edge(
                parent_node_id=parent.id,
                child_node_id=UUID(str(child_node_id)) if not isinstance(child_node_id, UUID) else child_node_id,
                edge_type=edge_type,
                confidence=score,
                evidence_json={
                    "source": "similarity_based",
                    "similarity_score": score,
                    "threshold": similarity_threshold,
                }
            )
            created_edges.append((str(parent.id), score))
            logger.info(f"Created candidate edge: {parent.id} -> {child_node_id} (confidence={score:.2f})")
        except Exception as e:
            logger.warning(f"Failed to create edge for {parent.id}: {e}")
    
    await db.commit()
    
    logger.info(f"Created {len(created_edges)} similarity-based VDGEdge candidates for {child_node_id}")
    return created_edges
