"""
Patterns API Router - Hook Library
Aggregates VDG hook patterns for pattern confidence scoring
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/patterns", tags=["Patterns"])


class PatternStat(BaseModel):
    pattern: str
    count: int
    percentage: float
    avg_strength: float
    confidence: float


class PatternStatsResponse(BaseModel):
    total_analyzed: int
    patterns: List[PatternStat]
    top_pattern: Optional[str] = None


@router.get("/stats", response_model=PatternStatsResponse)
async def get_pattern_stats(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated hook pattern statistics from all analyzed videos.
    Supports both VDG v2.0 (global_context.hook_pattern) and v3.0 (hook_genome.pattern) schemas.
    """
    
    # Query to extract hook patterns from both v2 and v3 schemas
    query = text("""
        WITH pattern_data AS (
            SELECT 
                COALESCE(
                    gemini_analysis->'hook_genome'->>'pattern',
                    gemini_analysis->'global_context'->>'hook_pattern'
                ) as pattern,
                COALESCE(
                    (gemini_analysis->'hook_genome'->>'strength')::float,
                    (gemini_analysis->'global_context'->>'hook_strength_score')::float,
                    0.5
                ) as strength
            FROM remix_nodes
            WHERE gemini_analysis IS NOT NULL
        )
        SELECT 
            pattern,
            COUNT(*) as count,
            AVG(strength) as avg_strength
        FROM pattern_data
        WHERE pattern IS NOT NULL
        GROUP BY pattern
        ORDER BY count DESC
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Calculate totals and percentages
    total = sum(row[1] for row in rows)
    
    patterns = []
    for row in rows:
        pattern_name = row[0]
        count = row[1]
        avg_strength = row[2] or 0.5
        
        # Calculate confidence based on sample size and average strength
        # More samples + higher strength = higher confidence
        sample_factor = min(count / 10, 1.0)  # Cap at 10 samples for full confidence
        confidence = round(sample_factor * avg_strength, 2)
        
        patterns.append(PatternStat(
            pattern=pattern_name,
            count=count,
            percentage=round((count / total * 100) if total > 0 else 0, 1),
            avg_strength=round(avg_strength, 2),
            confidence=confidence
        ))
    
    return PatternStatsResponse(
        total_analyzed=total,
        patterns=patterns,
        top_pattern=patterns[0].pattern if patterns else None
    )


@router.get("/leaderboard")
async def get_pattern_leaderboard(
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """
    Get top performing patterns ranked by confidence score.
    Useful for Hook Library display.
    """
    stats = await get_pattern_stats(db)
    sorted_patterns = sorted(stats.patterns, key=lambda x: x.confidence, reverse=True)
    
    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "pattern": p.pattern,
                "confidence": p.confidence,
                "sample_size": p.count
            }
            for i, p in enumerate(sorted_patterns[:limit])
        ]
    }


# ==================
# Pattern Library CRUD (PEGL Output)
# ==================

from app.models import PatternLibrary
from sqlalchemy import select
from uuid import UUID


class PatternLibraryItem(BaseModel):
    id: str
    pattern_id: str
    cluster_id: str
    temporal_phase: str
    platform: str
    category: str
    invariant_rules: dict
    mutation_strategy: dict
    citations: Optional[list] = None
    revision: int
    created_at: str
    
    class Config:
        from_attributes = True


class PatternLibraryListResponse(BaseModel):
    total: int
    patterns: List[PatternLibraryItem]


@router.get("/library", response_model=PatternLibraryListResponse)
async def list_pattern_library(
    cluster_id: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List all patterns from PatternLibrary (PEGL output).
    These are the refined patterns promoted from NotebookLM Data Tables.
    """
    query = select(PatternLibrary).order_by(PatternLibrary.created_at.desc())
    
    if cluster_id:
        query = query.where(PatternLibrary.cluster_id == cluster_id)
    if platform:
        query = query.where(PatternLibrary.platform == platform)
    
    query = query.limit(limit)
    result = await db.execute(query)
    patterns = result.scalars().all()
    
    items = []
    for p in patterns:
        items.append(PatternLibraryItem(
            id=str(p.id),
            pattern_id=p.pattern_id,
            cluster_id=p.cluster_id,
            temporal_phase=p.temporal_phase,
            platform=p.platform,
            category=p.category,
            invariant_rules=p.invariant_rules or {},
            mutation_strategy=p.mutation_strategy or {},
            citations=p.citations,
            revision=p.revision,
            created_at=p.created_at.isoformat() if p.created_at else "",
        ))
    
    return PatternLibraryListResponse(total=len(items), patterns=items)


@router.get("/library/{pattern_id}")
async def get_pattern_library_item(
    pattern_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific pattern from PatternLibrary by pattern_id.
    """
    result = await db.execute(
        select(PatternLibrary).where(PatternLibrary.pattern_id == pattern_id)
    )
    pattern = result.scalar_one_or_none()
    
    if not pattern:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    return {
        "id": str(pattern.id),
        "pattern_id": pattern.pattern_id,
        "cluster_id": pattern.cluster_id,
        "temporal_phase": pattern.temporal_phase,
        "platform": pattern.platform,
        "category": pattern.category,
        "invariant_rules": pattern.invariant_rules or {},
        "mutation_strategy": pattern.mutation_strategy or {},
        "citations": pattern.citations,
        "revision": pattern.revision,
        "created_at": pattern.created_at.isoformat() if pattern.created_at else "",
    }
