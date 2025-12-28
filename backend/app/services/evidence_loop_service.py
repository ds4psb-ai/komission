"""
Evidence Loop Service (PEGL v1.0)

상태머신 기반 Evidence Loop 관리 서비스
- EvidenceEvent 생성 및 상태 전이
- DecisionObject 생성 및 저장

상태 전이:
QUEUED → RUNNING → EVIDENCE_READY → DECIDED → EXECUTED → MEASURED
         ↓
       FAILED (어느 단계에서든 발생 가능)

사용 예:
    from app.services.evidence_loop_service import EvidenceLoopService
    
    service = EvidenceLoopService(db)
    event = await service.start_event(parent_node_id)
    # ... evidence 수집 ...
    event = await service.mark_evidence_ready(event, snapshot_id)
    # ... decision 생성 ...
    event = await service.create_decision(event, DecisionType.GO, {...})
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    EvidenceEvent, EvidenceEventStatus,
    DecisionObject, DecisionType,
    EvidenceSnapshot, RemixNode
)
from app.utils.time import utcnow
from app.utils.run_manager import generate_run_id, RunType

import logging

logger = logging.getLogger(__name__)


class EvidenceLoopService:
    """
    Evidence Loop 상태머신 서비스
    
    모든 Evidence Loop 작업은 이 서비스를 통해 수행하여
    상태 추적 및 감사 로그를 보장합니다.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================
    # Event Lifecycle
    # ==================
    
    async def start_event(
        self,
        parent_node_id: uuid.UUID,
        run_id: Optional[uuid.UUID] = None,
    ) -> EvidenceEvent:
        """
        새 Evidence Loop 이벤트 시작
        
        Args:
            parent_node_id: 대상 Parent 노드 ID
            run_id: 연결할 Run ID (옵션)
            
        Returns:
            생성된 EvidenceEvent (QUEUED 상태)
        """
        # Parent 존재 확인
        parent_result = await self.db.execute(
            select(RemixNode).where(RemixNode.id == parent_node_id)
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise ValueError(f"Parent node not found: {parent_node_id}")
        
        # 이벤트 ID 생성
        event_id = f"evt_{utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        event = EvidenceEvent(
            event_id=event_id,
            parent_node_id=parent_node_id,
            run_id=run_id,
            status=EvidenceEventStatus.QUEUED,
            queued_at=utcnow(),
        )
        
        self.db.add(event)
        await self.db.flush()
        
        logger.info(f"Evidence event started: {event_id} for parent {parent_node_id}")
        return event
    
    async def mark_running(self, event: EvidenceEvent) -> EvidenceEvent:
        """
        이벤트를 RUNNING 상태로 전이
        """
        self._validate_transition(event, EvidenceEventStatus.RUNNING)
        event.status = EvidenceEventStatus.RUNNING
        event.updated_at = utcnow()
        
        await self.db.flush()
        logger.info(f"Evidence event running: {event.event_id}")
        return event
    
    async def mark_evidence_ready(
        self,
        event: EvidenceEvent,
        snapshot_id: uuid.UUID,
    ) -> EvidenceEvent:
        """
        Evidence 수집 완료 - EVIDENCE_READY 상태로 전이
        
        Args:
            event: 대상 이벤트
            snapshot_id: 수집된 EvidenceSnapshot ID
        """
        self._validate_transition(event, EvidenceEventStatus.EVIDENCE_READY)
        
        event.status = EvidenceEventStatus.EVIDENCE_READY
        event.evidence_snapshot_id = snapshot_id
        event.evidence_ready_at = utcnow()
        event.updated_at = utcnow()
        
        await self.db.flush()
        logger.info(f"Evidence ready: {event.event_id} with snapshot {snapshot_id}")
        return event
    
    async def create_decision(
        self,
        event: EvidenceEvent,
        decision_type: DecisionType,
        decision_json: Dict[str, Any],
        evidence_summary: Optional[Dict[str, Any]] = None,
        decided_by: Optional[uuid.UUID] = None,
        decision_method: str = "auto",
        transcript_artifact_id: Optional[uuid.UUID] = None,
    ) -> tuple[EvidenceEvent, DecisionObject]:
        """
        Decision 생성 및 DECIDED 상태로 전이
        
        Args:
            event: 대상 이벤트
            decision_type: GO / STOP / PIVOT
            decision_json: 구조화된 결정 내용
            evidence_summary: 증거 요약 (옵션)
            decided_by: 결정자 User ID (null이면 자동)
            decision_method: "auto", "manual", "hybrid"
            transcript_artifact_id: Debate 기록 ID (옵션)
            
        Returns:
            (업데이트된 event, 생성된 DecisionObject)
        """
        self._validate_transition(event, EvidenceEventStatus.DECIDED)
        
        # Decision ID 생성
        decision_id = f"dec_{utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        decision = DecisionObject(
            decision_id=decision_id,
            evidence_event_id=event.id,
            decision_type=decision_type,
            decision_json=decision_json,
            evidence_summary=evidence_summary,
            transcript_artifact_id=transcript_artifact_id,
            decided_by=decided_by,
            decision_method=decision_method,
            decided_at=utcnow(),
        )
        
        self.db.add(decision)
        await self.db.flush()
        
        # Event 업데이트
        event.status = EvidenceEventStatus.DECIDED
        event.decision_object_id = decision.id
        event.decided_at = utcnow()
        event.updated_at = utcnow()
        
        await self.db.flush()
        logger.info(f"Decision created: {decision_id} ({decision_type.value})")
        return event, decision
    
    async def mark_executed(self, event: EvidenceEvent) -> EvidenceEvent:
        """
        Decision 실행 완료 - EXECUTED 상태로 전이
        """
        self._validate_transition(event, EvidenceEventStatus.EXECUTED)
        
        event.status = EvidenceEventStatus.EXECUTED
        event.executed_at = utcnow()
        event.updated_at = utcnow()
        
        await self.db.flush()
        logger.info(f"Evidence event executed: {event.event_id}")
        return event
    
    async def mark_measured(self, event: EvidenceEvent) -> EvidenceEvent:
        """
        측정 완료 - MEASURED 상태로 전이 (루프 종료)
        """
        self._validate_transition(event, EvidenceEventStatus.MEASURED)
        
        event.status = EvidenceEventStatus.MEASURED
        event.measured_at = utcnow()
        event.updated_at = utcnow()
        
        await self.db.flush()
        logger.info(f"Evidence event measured: {event.event_id} (loop complete)")
        return event
    
    async def mark_failed(
        self,
        event: EvidenceEvent,
        error_message: str,
    ) -> EvidenceEvent:
        """
        실패 처리 - 어느 단계에서든 FAILED 상태로 전이 가능
        """
        event.status = EvidenceEventStatus.FAILED
        event.error_message = error_message
        event.updated_at = utcnow()
        
        await self.db.flush()
        logger.error(f"Evidence event failed: {event.event_id} - {error_message}")
        return event
    
    # ==================
    # Query Methods
    # ==================
    
    async def get_pending_events(
        self,
        parent_node_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> list[EvidenceEvent]:
        """
        처리 대기 중인 이벤트 조회 (QUEUED 상태)
        """
        query = select(EvidenceEvent).where(
            EvidenceEvent.status == EvidenceEventStatus.QUEUED
        )
        if parent_node_id:
            query = query.where(EvidenceEvent.parent_node_id == parent_node_id)
        query = query.order_by(EvidenceEvent.queued_at).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_event_by_id(self, event_id: str) -> Optional[EvidenceEvent]:
        """
        이벤트 ID로 조회
        """
        result = await self.db.execute(
            select(EvidenceEvent).where(EvidenceEvent.event_id == event_id)
        )
        return result.scalar_one_or_none()
    
    async def get_latest_event_for_parent(
        self,
        parent_node_id: uuid.UUID,
    ) -> Optional[EvidenceEvent]:
        """
        Parent에 대한 최신 이벤트 조회
        """
        result = await self.db.execute(
            select(EvidenceEvent)
            .where(EvidenceEvent.parent_node_id == parent_node_id)
            .order_by(EvidenceEvent.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    # ==================
    # Validation
    # ==================
    
    def _validate_transition(
        self,
        event: EvidenceEvent,
        target_status: EvidenceEventStatus,
    ) -> None:
        """
        상태 전이 유효성 검사
        
        유효한 전이:
        - QUEUED → RUNNING
        - RUNNING → EVIDENCE_READY
        - EVIDENCE_READY → DECIDED
        - DECIDED → EXECUTED
        - EXECUTED → MEASURED
        """
        valid_transitions = {
            EvidenceEventStatus.QUEUED: [EvidenceEventStatus.RUNNING, EvidenceEventStatus.FAILED],
            EvidenceEventStatus.RUNNING: [EvidenceEventStatus.EVIDENCE_READY, EvidenceEventStatus.FAILED],
            EvidenceEventStatus.EVIDENCE_READY: [EvidenceEventStatus.DECIDED, EvidenceEventStatus.FAILED],
            EvidenceEventStatus.DECIDED: [EvidenceEventStatus.EXECUTED, EvidenceEventStatus.FAILED],
            EvidenceEventStatus.EXECUTED: [EvidenceEventStatus.MEASURED, EvidenceEventStatus.FAILED],
            EvidenceEventStatus.MEASURED: [],  # 종료 상태
            EvidenceEventStatus.FAILED: [],  # 종료 상태
        }
        
        if target_status not in valid_transitions.get(event.status, []):
            raise ValueError(
                f"Invalid state transition: {event.status.value} → {target_status.value}"
            )
