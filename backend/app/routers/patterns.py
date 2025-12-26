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
