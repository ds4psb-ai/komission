"""
Evidence Service - VDG (Variant Depth Genealogy) 계산 및 Evidence 생성
Phase 2: Evidence Loop 핵심 로직
"""
from typing import Dict, List, Optional, Any
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
import json

from app.utils.time import utcnow, days_ago

from app.models import RemixNode, EvidenceSnapshot
from app.schemas.evidence import (
    EvidenceRow,
    EvidenceTableResponse,
    EvidenceSnapshotCreate,
    MutationSummary,
)


class EvidenceService:
    """
    VDG 기반 Evidence 생성 서비스
    
    핵심 기능:
    1. Parent 노드의 Depth1/2 자식들 분석
    2. mutation_profile + performance_delta 집계
    3. EvidenceSnapshot 생성 및 저장
    4. Evidence Table (시트용) 변환
    """
    
    async def calculate_vdg_summary(
        self,
        db: AsyncSession,
        parent_node_id: str,
        period: str = "4w"
    ) -> Dict[str, Any]:
        """
        Parent 노드의 VDG 요약 계산
        
        Returns:
            {
                "depth1": { "audio": {...}, "visual": {...} },
                "depth2": { ... },
                "sample_count": 15,
                "top_mutation": {"type": "audio", "pattern": "KPOP", "rate": "+127%"}
            }
        """
        # 기간 필터 계산
        period_days = self._parse_period(period)
        cutoff_date = days_ago(period_days)
        
        # Depth 1 자식들 조회
        depth1_result = await db.execute(
            select(RemixNode).where(
                RemixNode.parent_node_id == UUID(parent_node_id) if isinstance(parent_node_id, str) else parent_node_id,
                RemixNode.created_at >= cutoff_date
            )
        )
        depth1_nodes = depth1_result.scalars().all()
        
        # Depth 2 자식들 조회
        depth1_ids = [n.id for n in depth1_nodes]
        depth2_nodes = []
        if depth1_ids:
            depth2_result = await db.execute(
                select(RemixNode).where(
                    RemixNode.parent_node_id.in_(depth1_ids),
                    RemixNode.created_at >= cutoff_date
                )
            )
            depth2_nodes = depth2_result.scalars().all()
        
        # Depth 1 mutation 집계
        depth1_summary = self._aggregate_mutations(depth1_nodes)
        
        # Depth 2 mutation 집계
        depth2_summary = self._aggregate_mutations(depth2_nodes) if depth2_nodes else None
        
        # Top mutation 결정
        top_mutation = self._find_top_mutation(depth1_summary)
        
        return {
            "depth1": depth1_summary,
            "depth2": depth2_summary,
            "sample_count": len(depth1_nodes) + len(depth2_nodes),
            "top_mutation": top_mutation,
        }
    
    def _aggregate_mutations(self, nodes: List[RemixNode]) -> Dict[str, Dict]:
        """노드 리스트에서 mutation 타입별 요약 생성"""
        aggregates: Dict[str, Dict[str, Dict]] = {
            "audio": {},
            "visual": {},
            "hook": {},
            "setting": {},
        }
        
        for node in nodes:
            if not node.mutation_profile:
                continue
            
            profile = node.mutation_profile
            delta = node.performance_delta or "+0%"
            is_success = delta.startswith("+") and self._parse_delta(delta) > 0
            
            # 각 mutation 타입 처리
            for mutation_type in ["audio", "visual", "hook", "setting"]:
                mutation_data = profile.get(mutation_type)
                if not mutation_data:
                    continue
                
                # 패턴 추출 (after 값 또는 summary)
                pattern = mutation_data.get("after") or mutation_data.get("summary", "unknown")
                if isinstance(pattern, dict):
                    pattern = str(pattern)
                
                if pattern not in aggregates[mutation_type]:
                    aggregates[mutation_type][pattern] = {
                        "success_count": 0,
                        "total_count": 0,
                        "delta_sum": 0,
                        "samples": [],
                    }
                
                agg = aggregates[mutation_type][pattern]
                agg["total_count"] += 1
                if is_success:
                    agg["success_count"] += 1
                agg["delta_sum"] += self._parse_delta(delta)
                agg["samples"].append(delta)
        
        # 요약 형태로 변환
        result = {}
        for mutation_type, patterns in aggregates.items():
            if not patterns:
                continue
            result[mutation_type] = {}
            for pattern, stats in patterns.items():
                if stats["total_count"] == 0:
                    continue
                avg_delta = stats["delta_sum"] / stats["total_count"]
                result[mutation_type][pattern] = {
                    "success_rate": stats["success_count"] / stats["total_count"],
                    "sample_count": stats["total_count"],
                    "avg_delta": f"+{avg_delta:.0f}%" if avg_delta >= 0 else f"{avg_delta:.0f}%",
                    "confidence": min(1.0, stats["total_count"] / 10),  # 10 샘플 이상이면 신뢰도 1.0
                }
        
        return result
    
    def _find_top_mutation(self, depth_summary: Dict) -> Optional[Dict]:
        """가장 성공적인 mutation 찾기"""
        best = None
        best_rate = -float("inf")
        
        for mutation_type, patterns in depth_summary.items():
            for pattern, stats in patterns.items():
                rate = self._parse_delta(stats.get("avg_delta", "0%"))
                if rate > best_rate and stats.get("sample_count", 0) >= 3:
                    best_rate = rate
                    best = {
                        "type": mutation_type,
                        "pattern": pattern,
                        "rate": stats["avg_delta"],
                        "confidence": stats["confidence"],
                    }
        
        return best
    
    async def create_evidence_snapshot(
        self,
        db: AsyncSession,
        parent_node_id: str,
        period: str = "4w"
    ) -> EvidenceSnapshot:
        """EvidenceSnapshot 생성 및 DB 저장"""
        vdg_summary = await self.calculate_vdg_summary(db, parent_node_id, period)
        
        top = vdg_summary.get("top_mutation")
        
        snapshot = EvidenceSnapshot(
            parent_node_id=UUID(parent_node_id) if isinstance(parent_node_id, str) else parent_node_id,
            period=period,
            depth1_summary=vdg_summary["depth1"],
            depth2_summary=vdg_summary.get("depth2"),
            top_mutation_type=top["type"] if top else None,
            top_mutation_pattern=top["pattern"] if top else None,
            top_mutation_rate=top["rate"] if top else None,
            sample_count=vdg_summary["sample_count"],
            confidence=top["confidence"] if top else 0.5,
        )
        
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        
        return snapshot
    
    async def generate_evidence_table(
        self,
        db: AsyncSession,
        parent_node_id: str,
        period: str = "4w"
    ) -> EvidenceTableResponse:
        """Evidence Table 생성 (시트 내보내기용)"""
        vdg_summary = await self.calculate_vdg_summary(db, parent_node_id, period)
        
        rows: List[EvidenceRow] = []
        
        # Depth 1 rows
        for mutation_type, patterns in vdg_summary.get("depth1", {}).items():
            for pattern, stats in patterns.items():
                rows.append(EvidenceRow(
                    parent_node_id=parent_node_id,
                    mutation_type=mutation_type,
                    before_pattern="original",
                    after_pattern=pattern,
                    success_rate=stats["success_rate"],
                    sample_count=stats["sample_count"],
                    avg_delta=stats["avg_delta"],
                    period=period,
                    depth=1,
                    confidence=stats["confidence"],
                    risk=self._assess_risk(stats),
                    updated_at=utcnow(),
                ))
        
        # Depth 2 rows
        depth2 = vdg_summary.get("depth2") or {}
        for mutation_type, patterns in depth2.items():
            for pattern, stats in patterns.items():
                rows.append(EvidenceRow(
                    parent_node_id=parent_node_id,
                    mutation_type=mutation_type,
                    before_pattern="depth1_variant",
                    after_pattern=pattern,
                    success_rate=stats["success_rate"],
                    sample_count=stats["sample_count"],
                    avg_delta=stats["avg_delta"],
                    period=period,
                    depth=2,
                    confidence=stats["confidence"],
                    risk=self._assess_risk(stats),
                    updated_at=utcnow(),
                ))
        
        # Sort by success rate
        rows.sort(key=lambda x: x.success_rate, reverse=True)
        
        top = vdg_summary.get("top_mutation")
        
        return EvidenceTableResponse(
            parent_node_id=parent_node_id,
            generated_at=utcnow(),
            period=period,
            rows=rows,
            total_samples=vdg_summary["sample_count"],
            top_recommendation=f"{top['type']}:{top['pattern']}" if top else None,
        )
    
    async def generate_evidence_csv(
        self,
        db: AsyncSession,
        parent_node_id: str,
        period: str = "4w"
    ) -> str:
        """Evidence Table을 CSV 문자열로 변환 (NotebookLM용)"""
        table = await self.generate_evidence_table(db, parent_node_id, period)
        
        # CSV Header
        csv_lines = [
            "parent_node_id,mutation_type,before,after,success_rate,sample_count,avg_delta,period,depth,confidence,risk,updated_at"
        ]
        
        for row in table.rows:
            line = f"{row.parent_node_id},{row.mutation_type},{row.before_pattern},{row.after_pattern},{row.success_rate:.2f},{row.sample_count},{row.avg_delta},{row.period},{row.depth},{row.confidence:.2f},{row.risk},{row.updated_at.isoformat()}"
            csv_lines.append(line)
            
        return "\n".join(csv_lines)

    def _parse_period(self, period: str) -> int:
        """기간 문자열을 일수로 변환"""
        if period.endswith("w"):
            return int(period[:-1]) * 7
        if period.endswith("m"):
            return int(period[:-1]) * 30
        if period.endswith("y"):
            return int(period[:-1]) * 365
        return 28  # default 4 weeks
    
    def _parse_delta(self, delta: str) -> float:
        """성과 델타 문자열을 숫자로 변환"""
        try:
            return float(delta.replace("%", "").replace("+", ""))
        except:
            return 0.0
    
    def _assess_risk(self, stats: Dict, novelty_decay_score: float = 1.0) -> str:
        """
        리스크 평가 (샘플 수 + 성공률 + novelty_decay 기반)
        
        novelty_decay_score: 0.2 ~ 1.0 (낮을수록 패턴이 오래됨)
        - 오래된 패턴(낮은 decay)은 리스크 상향
        """
        sample_count = stats.get("sample_count", 0)
        success_rate = stats.get("success_rate", 0)
        
        if sample_count < 5:
            return "high"  # 샘플 부족
        if success_rate < 0.3:
            return "high"  # 성공률 낮음
        
        # Novelty decay 리스크 조정 (Temporal Variation Theory)
        if novelty_decay_score < 0.5:
            # 패턴이 오래됨 - 창의성 필요
            if success_rate < 0.7:
                return "high"
            return "medium"
        
        if success_rate < 0.6:
            return "medium"
        return "low"


# Singleton
evidence_service = EvidenceService()
