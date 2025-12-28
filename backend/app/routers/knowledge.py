"""
Knowledge Center Router - Hook Library & Evidence Guides
Virlo Phase C: Knowledge Center 재해석
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from app.utils.time import utcnow

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    PatternConfidence, PatternCluster, EvidenceSnapshot,
    RemixNode, NotebookLibraryEntry
)
from app.routers.auth import get_current_user, User

router = APIRouter(prefix="/knowledge", tags=["Knowledge Center"])


# ==================
# SCHEMAS
# ==================

class HookPattern(BaseModel):
    pattern_code: str
    pattern_type: str  # visual, audio, semantic, hook
    confidence_score: float
    sample_count: int
    avg_retention: Optional[float] = None
    description: Optional[str] = None


class HookLibraryResponse(BaseModel):
    total_patterns: int
    top_hooks: List[HookPattern]
    categories: List[str]
    last_updated: datetime


class EvidenceGuide(BaseModel):
    id: str
    parent_title: str
    platform: str
    category: str
    top_mutation_type: Optional[str]
    top_mutation_pattern: Optional[str]
    success_rate: Optional[str]
    recommendation: str
    sample_count: int
    confidence: float


class EvidenceGuideResponse(BaseModel):
    total_guides: int
    guides: List[EvidenceGuide]


# ==================
# HOOK LIBRARY
# ==================

@router.get("/hooks", response_model=HookLibraryResponse)
async def get_hook_library(
    pattern_type: Optional[str] = Query(None, description="Filter by type: visual, audio, hook"),
    min_samples: int = Query(3, ge=1, description="Minimum verified samples"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Hook Library - 검증된 고성과 패턴 목록
    
    PatternConfidence 테이블에서 신뢰도가 높은 패턴을 반환.
    실제 성과 데이터가 쌓일수록 정확해짐.
    """
    query = select(PatternConfidence).where(
        PatternConfidence.sample_count >= min_samples
    )
    
    if pattern_type:
        query = query.where(PatternConfidence.pattern_type == pattern_type)
    
    query = query.order_by(desc(PatternConfidence.confidence_score)).limit(limit)
    
    result = await db.execute(query)
    patterns = result.scalars().all()
    
    if patterns:
        top_hooks = [
            HookPattern(
                pattern_code=p.pattern_code,
                pattern_type=p.pattern_type,
                confidence_score=p.confidence_score,
                sample_count=p.sample_count,
                avg_retention=None,  # Can be calculated from predictions
                description=_get_pattern_description(p.pattern_code),
            )
            for p in patterns
        ]
        last_updated = max(p.last_updated for p in patterns)
    else:
        # 기본 추천 (데이터 없을 때)
        top_hooks = _get_default_hooks()
        last_updated = utcnow()
    
    # Get unique categories
    categories = list(set(p.pattern_type for p in patterns)) if patterns else ["visual", "audio", "hook"]
    
    return HookLibraryResponse(
        total_patterns=len(top_hooks),
        top_hooks=top_hooks,
        categories=categories,
        last_updated=last_updated,
    )


@router.get("/hooks/{pattern_code}")
async def get_hook_detail(
    pattern_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 훅 패턴의 상세 정보
    """
    result = await db.execute(
        select(PatternConfidence).where(
            PatternConfidence.pattern_code == pattern_code
        )
    )
    pattern = result.scalar_one_or_none()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # Find example nodes using this pattern
    examples_result = await db.execute(
        select(NotebookLibraryEntry)
        .where(NotebookLibraryEntry.cluster_id.like(f"%{pattern_code.lower()}%"))
        .limit(5)
    )
    examples = examples_result.scalars().all()
    
    return {
        "pattern_code": pattern.pattern_code,
        "pattern_type": pattern.pattern_type,
        "confidence_score": pattern.confidence_score,
        "sample_count": pattern.sample_count,
        "avg_absolute_error": pattern.avg_absolute_error,
        "description": _get_pattern_description(pattern.pattern_code),
        "usage_tips": _get_pattern_tips(pattern.pattern_code),
        "examples": [
            {"source_url": e.source_url, "category": e.category}
            for e in examples
        ],
    }


# ==================
# EVIDENCE GUIDES
# ==================

@router.get("/guides", response_model=EvidenceGuideResponse)
async def get_evidence_guides(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Evidence 기반 실행 가이드 목록
    
    EvidenceSnapshot에서 검증된 변주 성공 패턴을 추출하여 가이드 생성.
    """
    query = (
        select(EvidenceSnapshot, RemixNode)
        .join(RemixNode, EvidenceSnapshot.parent_node_id == RemixNode.id)
        .where(EvidenceSnapshot.confidence >= min_confidence)
    )
    
    if category:
        # Try to filter by category from analysis
        pass  # RemixNode doesn't have direct category field
    
    if platform:
        query = query.where(RemixNode.platform == platform)
    
    query = query.order_by(desc(EvidenceSnapshot.confidence)).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    guides = []
    for snapshot, node in rows:
        # Generate recommendation based on top mutation
        recommendation = _generate_recommendation(
            snapshot.top_mutation_type,
            snapshot.top_mutation_pattern,
            snapshot.top_mutation_rate
        )
        
        guides.append(EvidenceGuide(
            id=str(snapshot.id),
            parent_title=node.title,
            platform=node.platform or "unknown",
            category=_infer_category(node),
            top_mutation_type=snapshot.top_mutation_type,
            top_mutation_pattern=snapshot.top_mutation_pattern,
            success_rate=snapshot.top_mutation_rate,
            recommendation=recommendation,
            sample_count=snapshot.sample_count,
            confidence=snapshot.confidence,
        ))
    
    return EvidenceGuideResponse(
        total_guides=len(guides),
        guides=guides,
    )


@router.get("/guides/{snapshot_id}")
async def get_guide_detail(
    snapshot_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 Evidence 가이드의 상세 정보
    """
    result = await db.execute(
        select(EvidenceSnapshot, RemixNode)
        .join(RemixNode, EvidenceSnapshot.parent_node_id == RemixNode.id)
        .where(EvidenceSnapshot.id == snapshot_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Guide not found")
    
    snapshot, node = row
    
    return {
        "id": str(snapshot.id),
        "parent_node": {
            "id": str(node.id),
            "node_id": node.node_id,
            "title": node.title,
            "platform": node.platform,
            "source_video_url": node.source_video_url,
        },
        "snapshot_date": snapshot.snapshot_date.isoformat(),
        "period": snapshot.period,
        "depth1_summary": snapshot.depth1_summary,
        "depth2_summary": snapshot.depth2_summary,
        "top_mutation": {
            "type": snapshot.top_mutation_type,
            "pattern": snapshot.top_mutation_pattern,
            "rate": snapshot.top_mutation_rate,
        },
        "sample_count": snapshot.sample_count,
        "confidence": snapshot.confidence,
        "recommendation": _generate_recommendation(
            snapshot.top_mutation_type,
            snapshot.top_mutation_pattern,
            snapshot.top_mutation_rate
        ),
        "execution_steps": _generate_execution_steps(snapshot),
    }


# ==================
# HELPER FUNCTIONS
# ==================

def _get_pattern_description(code: str) -> str:
    """Get human-readable description for pattern code."""
    descriptions = {
        "VIS_RAPID_CUT": "빠른 컷 전환 - 시선을 붙잡는 고속 편집",
        "VIS_ZOOM_TO_FACE": "얼굴 줌인 - 감정 강조를 위한 클로즈업",
        "VIS_TEXT_PUNCH": "텍스트 펀치 - 화면 위 텍스트로 임팩트 전달",
        "VIS_BEFORE_AFTER": "비포애프터 - 변화의 극적인 대비",
        "AUD_BASS_DROP": "베이스 드롭 - 음악 전환점에서 시각 동기화",
        "AUD_VIRAL_SOUND": "바이럴 사운드 - 트렌딩 오디오 활용",
        "AUD_VOICE_EFFECT": "음성 효과 - 변조된 보이스로 주목도 상승",
        "HOOK_QUESTION": "질문형 훅 - 궁금증 유발로 시작",
        "HOOK_SHOCK": "충격형 훅 - 예상 밖 장면으로 시선 확보",
        "HOOK_PROOF": "증거형 훅 - 결과를 먼저 보여주는 리버스",
    }
    return descriptions.get(code, f"패턴: {code}")


def _get_pattern_tips(code: str) -> List[str]:
    """Get usage tips for pattern code."""
    tips = {
        "VIS_RAPID_CUT": [
            "0.3-0.5초 단위로 컷 전환",
            "비트에 맞춰 편집",
            "첫 3초 안에 3-5개 컷 넣기",
        ],
        "VIS_ZOOM_TO_FACE": [
            "표정 변화 직전에 줌인",
            "말하는 순간 줌 사용",
            "감정 피크에서 가장 효과적",
        ],
        "AUD_BASS_DROP": [
            "드롭 직전 정적 만들기",
            "드롭과 동시에 비주얼 임팩트",
            "0.5초 선타이밍 효과적",
        ],
    }
    return tips.get(code, ["이 패턴을 영상 초반에 배치", "일관된 스타일 유지"])


def _get_default_hooks() -> List[HookPattern]:
    """Return default hooks when no data available."""
    return [
        HookPattern(pattern_code="VIS_RAPID_CUT", pattern_type="visual", confidence_score=0.75, sample_count=0),
        HookPattern(pattern_code="AUD_BASS_DROP", pattern_type="audio", confidence_score=0.72, sample_count=0),
        HookPattern(pattern_code="VIS_ZOOM_TO_FACE", pattern_type="visual", confidence_score=0.70, sample_count=0),
        HookPattern(pattern_code="HOOK_QUESTION", pattern_type="hook", confidence_score=0.68, sample_count=0),
        HookPattern(pattern_code="VIS_TEXT_PUNCH", pattern_type="visual", confidence_score=0.65, sample_count=0),
    ]


def _generate_recommendation(mutation_type: Optional[str], pattern: Optional[str], rate: Optional[str]) -> str:
    """Generate recommendation text based on mutation data."""
    if not mutation_type:
        return "이 Parent를 기반으로 변주를 시도해보세요."
    
    type_names = {
        "audio": "오디오",
        "visual": "비주얼",
        "hook": "훅",
        "setting": "세팅/로케이션",
        "timing": "타이밍",
    }
    type_name = type_names.get(mutation_type, mutation_type)
    
    if pattern and rate:
        return f"{type_name} 변주({pattern})가 {rate} 성과 향상을 보였습니다. 이 방향으로 시도해보세요."
    elif pattern:
        return f"{type_name} 요소를 {pattern} 방식으로 변경해보세요."
    else:
        return f"{type_name} 요소를 변주하는 것이 효과적입니다."


def _infer_category(node: RemixNode) -> str:
    """Infer category from node analysis."""
    if node.gemini_analysis and isinstance(node.gemini_analysis, dict):
        return node.gemini_analysis.get("category", "general")
    return "general"


def _generate_execution_steps(snapshot: EvidenceSnapshot) -> List[str]:
    """Generate step-by-step execution guide."""
    steps = [
        "1. 원본 Parent 영상을 시청하고 핵심 요소 파악",
        "2. 변주 포인트 결정 (위 추천 기반)",
    ]
    
    if snapshot.top_mutation_type == "audio":
        steps.append("3. 다른 트렌딩 오디오로 교체")
        steps.append("4. 음악 비트에 맞춰 영상 리타이밍")
    elif snapshot.top_mutation_type == "visual":
        steps.append("3. 촬영 구도/로케이션 변경")
        steps.append("4. 편집 스타일 차별화 (컷, 속도, 효과)")
    elif snapshot.top_mutation_type == "hook":
        steps.append("3. 오프닝 3초 완전히 새로 구성")
        steps.append("4. 더 강력한 훅 요소 추가")
    else:
        steps.append("3. 원본의 강점은 유지하며 약점 보완")
        steps.append("4. 타겟 오디언스에 맞게 조정")
    
    steps.append("5. 업로드 후 24-48시간 성과 모니터링")
    
    return steps
