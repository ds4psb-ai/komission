"""
VDG Edge Service (PEGL v1.0)

VDG Parent-Child Edge 관리 서비스
- candidate / confirmed / rejected 상태 관리
- confidence 점수 및 evidence 추적

사용 예:
    from app.services.vdg_edge_service import VDGEdgeService
    
    service = VDGEdgeService(db)
    edge = await service.create_candidate_edge(parent_id, child_id, VDGEdgeType.FORK, 0.75)
    edge = await service.confirm_edge(edge.id, user_id, "manual_review")
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import (
    VDGEdge, VDGEdgeStatus, VDGEdgeType,
    RemixNode
)
from app.utils.time import utcnow

import logging

logger = logging.getLogger(__name__)


class VDGEdgeService:
    """
    VDG Edge 관리 서비스
    
    Parent-Child 관계를 추적하고 증거 기반으로 확정합니다.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================
    # Edge Creation
    # ==================
    
    async def create_candidate_edge(
        self,
        parent_node_id: uuid.UUID,
        child_node_id: uuid.UUID,
        edge_type: VDGEdgeType,
        confidence: float,
        evidence_json: Optional[Dict[str, Any]] = None,
        run_id: Optional[uuid.UUID] = None,
    ) -> VDGEdge:
        """
        새 candidate edge 생성
        
        Args:
            parent_node_id: Parent 노드 ID
            child_node_id: Child 노드 ID
            edge_type: FORK / VARIATION / INSPIRED_BY
            confidence: 신뢰도 (0.0 ~ 1.0)
            evidence_json: 증거 데이터 (옵션)
            run_id: 연결할 Run ID (옵션)
            
        Returns:
            생성된 VDGEdge (CANDIDATE 상태)
        """
        # 노드 존재 확인
        parent = await self._get_node(parent_node_id)
        child = await self._get_node(child_node_id)
        
        if not parent:
            raise ValueError(f"Parent node not found: {parent_node_id}")
        if not child:
            raise ValueError(f"Child node not found: {child_node_id}")
        
        # 중복 확인
        existing = await self._get_existing_edge(parent_node_id, child_node_id)
        if existing:
            logger.warning(f"Edge already exists: {existing.id}")
            return existing
        
        edge = VDGEdge(
            parent_node_id=parent_node_id,
            child_node_id=child_node_id,
            edge_type=edge_type,
            edge_status=VDGEdgeStatus.CANDIDATE,
            confidence=confidence,
            evidence_json=evidence_json or {},
            run_id=run_id,
        )
        
        self.db.add(edge)
        await self.db.flush()
        
        logger.info(f"Candidate edge created: {parent_node_id} → {child_node_id} ({edge_type.value})")
        return edge
    
    async def create_batch_candidate_edges(
        self,
        parent_node_id: uuid.UUID,
        children: List[Dict[str, Any]],
        run_id: Optional[uuid.UUID] = None,
    ) -> List[VDGEdge]:
        """
        여러 child에 대한 candidate edge 일괄 생성
        
        Args:
            parent_node_id: Parent 노드 ID
            children: [{"child_id": UUID, "edge_type": VDGEdgeType, "confidence": float}, ...]
            run_id: 연결할 Run ID (옵션)
            
        Returns:
            생성된 VDGEdge 리스트
        """
        edges = []
        for child_data in children:
            try:
                edge = await self.create_candidate_edge(
                    parent_node_id=parent_node_id,
                    child_node_id=child_data["child_id"],
                    edge_type=child_data.get("edge_type", VDGEdgeType.VARIATION),
                    confidence=child_data.get("confidence", 0.5),
                    evidence_json=child_data.get("evidence_json"),
                    run_id=run_id,
                )
                edges.append(edge)
            except Exception as e:
                logger.error(f"Failed to create edge for {child_data}: {e}")
        
        return edges
    
    # ==================
    # Edge Status Management
    # ==================
    
    async def confirm_edge(
        self,
        edge_id: uuid.UUID,
        confirmed_by: uuid.UUID,
        confirmation_method: str = "manual_review",
        updated_evidence: Optional[Dict[str, Any]] = None,
    ) -> VDGEdge:
        """
        Edge를 CONFIRMED 상태로 변경
        
        Args:
            edge_id: Edge ID
            confirmed_by: 확정자 User ID
            confirmation_method: 확정 방법 (manual_review, auto_threshold, etc.)
            updated_evidence: 추가 증거 데이터 (옵션)
        """
        edge = await self._get_edge(edge_id)
        if not edge:
            raise ValueError(f"Edge not found: {edge_id}")
        
        if edge.edge_status != VDGEdgeStatus.CANDIDATE:
            raise ValueError(f"Edge is not in CANDIDATE status: {edge.edge_status}")
        
        edge.edge_status = VDGEdgeStatus.CONFIRMED
        edge.confirmed_by = confirmed_by
        edge.confirmed_at = utcnow()
        edge.confirmation_method = confirmation_method
        edge.updated_at = utcnow()
        
        if updated_evidence:
            edge.evidence_json = {**edge.evidence_json, **updated_evidence}
        
        await self.db.flush()
        logger.info(f"Edge confirmed: {edge_id} by {confirmed_by}")
        return edge
    
    async def reject_edge(
        self,
        edge_id: uuid.UUID,
        rejected_by: uuid.UUID,
        reason: str,
    ) -> VDGEdge:
        """
        Edge를 REJECTED 상태로 변경
        
        Args:
            edge_id: Edge ID
            rejected_by: 거부자 User ID
            reason: 거부 사유
        """
        edge = await self._get_edge(edge_id)
        if not edge:
            raise ValueError(f"Edge not found: {edge_id}")
        
        if edge.edge_status != VDGEdgeStatus.CANDIDATE:
            raise ValueError(f"Edge is not in CANDIDATE status: {edge.edge_status}")
        
        edge.edge_status = VDGEdgeStatus.REJECTED
        edge.confirmed_by = rejected_by  # 거부자 기록
        edge.confirmed_at = utcnow()
        edge.confirmation_method = "rejected"
        edge.updated_at = utcnow()
        edge.evidence_json = {**edge.evidence_json, "rejection_reason": reason}
        
        await self.db.flush()
        logger.info(f"Edge rejected: {edge_id} by {rejected_by}")
        return edge
    
    async def update_confidence(
        self,
        edge_id: uuid.UUID,
        new_confidence: float,
        evidence_update: Optional[Dict[str, Any]] = None,
    ) -> VDGEdge:
        """
        Edge confidence 업데이트
        
        Args:
            edge_id: Edge ID
            new_confidence: 새 신뢰도
            evidence_update: 추가 증거 데이터
        """
        edge = await self._get_edge(edge_id)
        if not edge:
            raise ValueError(f"Edge not found: {edge_id}")
        
        edge.confidence = new_confidence
        edge.updated_at = utcnow()
        
        if evidence_update:
            edge.evidence_json = {**edge.evidence_json, **evidence_update}
        
        await self.db.flush()
        logger.info(f"Edge confidence updated: {edge_id} → {new_confidence}")
        return edge
    
    # ==================
    # Auto Confirmation
    # ==================
    
    async def auto_confirm_high_confidence(
        self,
        threshold: float = 0.85,
        confirmed_by: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> List[VDGEdge]:
        """
        높은 confidence를 가진 candidate edge 자동 확정
        
        Args:
            threshold: 자동 확정 임계값 (기본 0.85)
            confirmed_by: 시스템 User ID (옵션)
            limit: 최대 처리 수
            
        Returns:
            확정된 VDGEdge 리스트
        """
        result = await self.db.execute(
            select(VDGEdge)
            .where(
                and_(
                    VDGEdge.edge_status == VDGEdgeStatus.CANDIDATE,
                    VDGEdge.confidence >= threshold
                )
            )
            .limit(limit)
        )
        candidates = list(result.scalars().all())
        
        confirmed_edges = []
        for edge in candidates:
            edge.edge_status = VDGEdgeStatus.CONFIRMED
            edge.confirmed_by = confirmed_by
            edge.confirmed_at = utcnow()
            edge.confirmation_method = f"auto_threshold_{threshold}"
            edge.updated_at = utcnow()
            confirmed_edges.append(edge)
        
        await self.db.flush()
        logger.info(f"Auto-confirmed {len(confirmed_edges)} edges with confidence >= {threshold}")
        return confirmed_edges
    
    # ==================
    # Query Methods
    # ==================
    
    async def get_children(
        self,
        parent_node_id: uuid.UUID,
        status: Optional[VDGEdgeStatus] = None,
    ) -> List[VDGEdge]:
        """
        Parent의 모든 children edge 조회
        """
        query = select(VDGEdge).where(VDGEdge.parent_node_id == parent_node_id)
        if status:
            query = query.where(VDGEdge.edge_status == status)
        query = query.order_by(VDGEdge.confidence.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_parents(
        self,
        child_node_id: uuid.UUID,
        status: Optional[VDGEdgeStatus] = None,
    ) -> List[VDGEdge]:
        """
        Child의 모든 parents edge 조회
        """
        query = select(VDGEdge).where(VDGEdge.child_node_id == child_node_id)
        if status:
            query = query.where(VDGEdge.edge_status == status)
        query = query.order_by(VDGEdge.confidence.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_confirmed_children(
        self,
        parent_node_id: uuid.UUID,
    ) -> List[VDGEdge]:
        """
        Parent의 확정된 children만 조회
        """
        return await self.get_children(parent_node_id, VDGEdgeStatus.CONFIRMED)
    
    async def get_candidate_count(self) -> int:
        """
        전체 candidate edge 수 조회
        """
        result = await self.db.execute(
            select(VDGEdge).where(VDGEdge.edge_status == VDGEdgeStatus.CANDIDATE)
        )
        return len(list(result.scalars().all()))
    
    # ==================
    # Private Methods
    # ==================
    
    async def _get_node(self, node_id: uuid.UUID) -> Optional[RemixNode]:
        result = await self.db.execute(
            select(RemixNode).where(RemixNode.id == node_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_edge(self, edge_id: uuid.UUID) -> Optional[VDGEdge]:
        result = await self.db.execute(
            select(VDGEdge).where(VDGEdge.id == edge_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_existing_edge(
        self,
        parent_node_id: uuid.UUID,
        child_node_id: uuid.UUID,
    ) -> Optional[VDGEdge]:
        result = await self.db.execute(
            select(VDGEdge).where(
                and_(
                    VDGEdge.parent_node_id == parent_node_id,
                    VDGEdge.child_node_id == child_node_id
                )
            )
        )
        return result.scalar_one_or_none()
