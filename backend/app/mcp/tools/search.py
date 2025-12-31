"""
MCP Tools - 패턴 검색 도구
"""
from typing import Union

from sqlalchemy import select, or_, func
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import OutlierItem
from app.mcp.server import mcp, get_logger
from app.mcp.utils.validators import safe_format_number
from app.mcp.schemas.patterns import PatternResult, SearchFilters, SearchResponse

logger = get_logger()


@mcp.tool(
    tags=["search", "read-only", "auto-approve"],
)
async def search_patterns(
    query: str,
    category: str = None,
    platform: str = None,
    min_tier: str = "C",
    limit: int = 10,
    output_format: str = "markdown"
) -> Union[str, SearchResponse]:
    """
    L1/L2 패턴 검색 (읽기 전용, 자동 승인)
    
    Search for patterns by keyword, category, or platform.
    Returns a list of matching patterns with scores.
    
    Args:
        query: Search keyword (matches title, cluster_name)
        category: Filter by category (beauty, meme, food, etc.)
        platform: Filter by platform (tiktok, youtube, instagram)
        min_tier: Minimum tier to include (S, A, B, C)
        limit: Maximum number of results (default 10, max 50)
        output_format: markdown | json (structured Pydantic output)
    
    Returns:
        str (markdown) or SearchResponse (Pydantic model when json format)
    """
    logger.info(
        f"Tool call: search_patterns(query='{query}', platform='{platform}', limit={limit}, format={output_format})"
    )
    
    # Input validation
    TIER_PRIORITY = {"S": 1, "A": 2, "B": 3, "C": 4}
    if min_tier not in TIER_PRIORITY:
        min_tier = "C"
    
    # Limit bounds
    limit = max(1, min(limit, 50))
    
    # Sanitize query
    query = (query or "")[:100]
    output_format = (output_format or "markdown").lower()
    
    try:
        async with AsyncSessionLocal() as db:
            # Build query
            stmt = select(OutlierItem).where(
                OutlierItem.analysis_status == "completed",
                OutlierItem.outlier_tier.isnot(None),
            )
            
            # Apply text search
            if query:
                stmt = stmt.where(
                    or_(
                        OutlierItem.title.ilike(f"%{query}%"),
                        OutlierItem.category.ilike(f"%{query}%"),
                    )
                )
            
            # Apply filters
            if category:
                stmt = stmt.where(OutlierItem.category == category)
            if platform:
                stmt = stmt.where(OutlierItem.platform == platform)
            
            # Tier filter
            min_priority = TIER_PRIORITY.get(min_tier, 4)
            allowed_tiers = [t for t, p in TIER_PRIORITY.items() if p <= min_priority]
            stmt = stmt.where(OutlierItem.outlier_tier.in_(allowed_tiers))
            
            # Order by tier and score
            stmt = stmt.order_by(
                func.array_position(['S', 'A', 'B', 'C'], OutlierItem.outlier_tier),
                OutlierItem.outlier_score.desc(),
            ).limit(limit)
            
            result = await db.execute(stmt)
            patterns = result.scalars().all()
            
            # Build Pydantic models
            filters = SearchFilters(
                category=category,
                platform=platform,
                min_tier=min_tier,
                limit=limit
            )
            
            if not patterns:
                logger.info("No patterns found")
                if output_format in {"json", "structured"}:
                    return SearchResponse(
                        query=query or "",
                        filters=filters,
                        count=0,
                        results=[]
                    )
                return "❌ No patterns found matching your criteria."
            
            logger.info(f"Found {len(patterns)} patterns")
            
            # Build PatternResult list
            results = []
            for p in patterns:
                results.append(PatternResult(
                    id=str(p.id),
                    title=p.title or "Untitled",
                    tier=p.outlier_tier,
                    platform=p.platform,
                    category=p.category,
                    score=float(p.outlier_score) if p.outlier_score is not None else None,
                    views=p.view_count or 0,
                ))
            
            if output_format in {"json", "structured"}:
                return SearchResponse(
                    query=query or "",
                    filters=filters,
                    count=len(results),
                    results=results
                )
            
            # Format results (markdown)
            lines = [f"# Search Results for: '{query or 'all'}'\n"]
            lines.append(f"Found {len(results)} patterns:\n")
            
            for i, r in enumerate(results, 1):
                try:
                    score_display = f"{r.score:.0f}" if r.score is not None else "0"
                    lines.append(
                        f"{i}. **[{r.tier or 'N/A'}]** {r.title}\n"
                        f"   - Platform: {r.platform or 'N/A'} | Category: {r.category or 'N/A'}\n"
                        f"   - Score: {score_display} | Views: {safe_format_number(r.views)}\n"
                        f"   - ID: `{r.id}`\n"
                    )
                except Exception:
                    lines.append(f"{i}. [Error formatting result]\n")
            
            return "\n".join(lines)
            
    except SQLAlchemyError as e:
        logger.error(f"Database error in search_patterns: {e}")
        return f"❌ Database error: Unable to search patterns."
    except Exception as e:
        logger.error(f"Unexpected error in search_patterns: {e}")
        return f"❌ Error searching patterns: {str(e)[:100]}"
