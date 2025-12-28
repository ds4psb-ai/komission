"""
Run/Artifact/Idempotency 관리 유틸리티 (PEGL Phase 0)

사용법:
    from app.utils.run_manager import RunManager, generate_idempotency_key

    # Run 생성 및 실행
    async with RunManager(db, RunType.CRAWLER, inputs={"source": "virlo"}) as run:
        result = await crawl_virlo()
        run.add_artifact("raw_data", result)
"""
import hashlib
import json
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Run, Artifact, RunStatus, RunType, ArtifactType
from app.utils.time import utcnow


def generate_idempotency_key(inputs: Dict[str, Any]) -> str:
    """
    입력값으로부터 idempotency key 생성
    
    동일한 입력은 항상 동일한 key를 생성하여 중복 실행 방지
    """
    # JSON 직렬화 시 키 정렬하여 일관성 보장
    canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def generate_run_id(run_type: RunType) -> str:
    """사람 친화적인 run_id 생성"""
    timestamp = utcnow().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid4())[:8]
    return f"{run_type.value}_{timestamp}_{short_uuid}"


def generate_artifact_id(artifact_type: ArtifactType, run_id: str) -> str:
    """사람 친화적인 artifact_id 생성"""
    short_uuid = str(uuid4())[:8]
    return f"{run_id}_{artifact_type.value}_{short_uuid}"


async def get_existing_run(
    db: AsyncSession,
    run_type: RunType,
    idempotency_key: str
) -> Optional[Run]:
    """동일 idempotency_key로 완료된 Run이 있으면 반환"""
    result = await db.execute(
        select(Run).where(
            Run.run_type == run_type,
            Run.idempotency_key == idempotency_key,
            Run.status == RunStatus.COMPLETED
        )
    )
    return result.scalar_one_or_none()


class RunManager:
    """
    Run 생명주기 관리자
    
    Context manager로 사용하면 자동으로 상태 추적 및 에러 핸들링
    """
    
    def __init__(
        self,
        db: AsyncSession,
        run_type: RunType,
        inputs: Dict[str, Any],
        triggered_by: str = "api",
        parent_run_id: Optional[str] = None,
        skip_if_exists: bool = True
    ):
        self.db = db
        self.run_type = run_type
        self.inputs = inputs
        self.triggered_by = triggered_by
        self.parent_run_id = parent_run_id
        self.skip_if_exists = skip_if_exists
        
        self.idempotency_key = generate_idempotency_key(inputs)
        self.run: Optional[Run] = None
        self.skipped = False
        self._artifacts: list = []
    
    async def __aenter__(self) -> "RunManager":
        # 기존 완료된 Run 확인
        if self.skip_if_exists:
            existing = await get_existing_run(self.db, self.run_type, self.idempotency_key)
            if existing:
                self.run = existing
                self.skipped = True
                return self
        
        # 새 Run 생성
        self.run = Run(
            run_id=generate_run_id(self.run_type),
            run_type=self.run_type,
            status=RunStatus.RUNNING,
            idempotency_key=self.idempotency_key,
            inputs_hash=self.idempotency_key,
            inputs_json=self.inputs,
            triggered_by=self.triggered_by,
            started_at=utcnow()
        )
        
        self.db.add(self.run)
        await self.db.flush()  # ID 할당
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.skipped:
            return False
        
        if exc_type is not None:
            # 에러 발생
            self.run.status = RunStatus.FAILED
            self.run.error_message = str(exc_val)
            self.run.error_traceback = "".join(traceback.format_tb(exc_tb))
        else:
            # 정상 완료
            self.run.status = RunStatus.COMPLETED
        
        self.run.ended_at = utcnow()
        if self.run.started_at:
            delta = self.run.ended_at - self.run.started_at
            self.run.duration_ms = int(delta.total_seconds() * 1000)
        
        await self.db.commit()
        return False  # 예외 전파
    
    def add_artifact(
        self,
        artifact_type: ArtifactType,
        name: str,
        data: Optional[Dict] = None,
        storage_type: str = "db",
        storage_path: Optional[str] = None,
        schema_version: str = "v1.0"
    ) -> Artifact:
        """Run에 아티팩트 추가"""
        if self.skipped:
            return None
        
        artifact = Artifact(
            artifact_id=generate_artifact_id(artifact_type, self.run.run_id),
            run_id=self.run.id,
            artifact_type=artifact_type,
            name=name,
            storage_type=storage_type,
            storage_path=storage_path,
            schema_version=schema_version,
            data_json=data,
            content_hash=generate_idempotency_key(data) if data else None
        )
        
        self.db.add(artifact)
        self._artifacts.append(artifact)
        return artifact
    
    def set_result_summary(self, summary: Dict[str, Any]):
        """실행 결과 요약 설정"""
        if self.run and not self.skipped:
            self.run.result_summary = summary
    
    @property
    def is_skipped(self) -> bool:
        """중복으로 스킵되었는지"""
        return self.skipped
    
    @property
    def artifacts(self) -> list:
        """생성된 아티팩트 목록"""
        return self._artifacts


# 편의 함수들
async def create_run(
    db: AsyncSession,
    run_type: RunType,
    inputs: Dict[str, Any],
    triggered_by: str = "api"
) -> Run:
    """단순 Run 생성"""
    run = Run(
        run_id=generate_run_id(run_type),
        run_type=run_type,
        status=RunStatus.QUEUED,
        idempotency_key=generate_idempotency_key(inputs),
        inputs_hash=generate_idempotency_key(inputs),
        inputs_json=inputs,
        triggered_by=triggered_by
    )
    db.add(run)
    await db.flush()
    return run


async def mark_run_started(db: AsyncSession, run: Run):
    """Run 시작 마킹"""
    run.status = RunStatus.RUNNING
    run.started_at = utcnow()
    await db.flush()


async def mark_run_completed(db: AsyncSession, run: Run, result_summary: Optional[Dict] = None):
    """Run 완료 마킹"""
    run.status = RunStatus.COMPLETED
    run.ended_at = utcnow()
    if result_summary:
        run.result_summary = result_summary
    if run.started_at:
        delta = run.ended_at - run.started_at
        run.duration_ms = int(delta.total_seconds() * 1000)
    await db.commit()


async def mark_run_failed(db: AsyncSession, run: Run, error: Exception):
    """Run 실패 마킹"""
    run.status = RunStatus.FAILED
    run.ended_at = utcnow()
    run.error_message = str(error)
    run.error_traceback = traceback.format_exc()
    if run.started_at:
        delta = run.ended_at - run.started_at
        run.duration_ms = int(delta.total_seconds() * 1000)
    await db.commit()
