"""
MCP Resources - 패턴 관련 리소스
"""
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import PatternCluster, PatternRecurrenceLink
from app.mcp.server import mcp, get_logger

logger = get_logger()


@mcp.resource("komission://patterns/{cluster_id}")
async def get_pattern(cluster_id: str) -> str:
    """
    Pattern Library 항목 조회
    
    Returns pattern cluster information including:
    - Name and type
    - Member count and average score
    - Recurrence information
    """
    logger.info(f"Resource request: patterns/{cluster_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PatternCluster).where(PatternCluster.cluster_id == cluster_id)
            )
            cluster = result.scalar_one_or_none()
            
            if not cluster:
                logger.warning(f"Pattern cluster not found: {cluster_id}")
                return f"❌ Pattern cluster '{cluster_id}' not found"
            
            logger.info(f"Found pattern: {cluster.cluster_name}")
            return f"""
# Pattern: {cluster.cluster_name}

**ID**: {cluster.cluster_id}
**Type**: {cluster.pattern_type or 'N/A'}
**Members**: {cluster.member_count or 0}
**Avg Score**: {cluster.avg_outlier_score or 'N/A'}

## Recurrence Info
- Ancestor: {cluster.ancestor_cluster_id or 'None (Original)'}
- Score: {cluster.recurrence_score or 0:.2f}
- Count: {cluster.recurrence_count or 0}
- Origin: {cluster.origin_cluster_id or cluster.cluster_id}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_pattern: {e}")
        return f"❌ Database error: Unable to fetch pattern. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error in get_pattern: {e}")
        return f"❌ Error fetching pattern: {str(e)[:100]}"


@mcp.resource("komission://recurrence/{cluster_id}")
async def get_recurrence(cluster_id: str) -> str:
    """
    재등장 lineage (배치 처리 결과)
    
    Returns pattern recurrence history and relationships.
    Note: This is pre-computed batch data, not real-time matching.
    """
    logger.info(f"Resource request: recurrence/{cluster_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            # Get cluster info
            cluster_result = await db.execute(
                select(PatternCluster).where(PatternCluster.cluster_id == cluster_id)
            )
            cluster = cluster_result.scalar_one_or_none()
            
            if not cluster:
                logger.warning(f"Cluster not found: {cluster_id}")
                return f"❌ Cluster '{cluster_id}' not found"
            
            # Get recurrence links (may be empty if not computed yet)
            try:
                links_result = await db.execute(
                    select(PatternRecurrenceLink)
                    .where(PatternRecurrenceLink.cluster_id_current == cluster_id)
                    .order_by(PatternRecurrenceLink.recurrence_score.desc())
                    .limit(10)
                )
                links = links_result.scalars().all()
            except Exception as link_err:
                logger.warning(f"Error fetching recurrence links: {link_err}")
                links = []
            
            links_text = ""
            if links:
                for link in links:
                    try:
                        links_text += (
                            f"- → {link.cluster_id_ancestor} "
                            f"(score: {link.recurrence_score:.2f}, status: {link.status})\n"
                        )
                    except Exception:
                        links_text += f"- → [Error parsing link]\n"
            else:
                links_text = "No recurrence links found"
            
            logger.info(f"Found {len(links)} recurrence links for {cluster_id}")
            return f"""
# Recurrence Lineage: {cluster_id}

## Current Cluster
- **Name**: {cluster.cluster_name}
- **Ancestor**: {cluster.ancestor_cluster_id or 'None (Original)'}
- **Origin**: {cluster.origin_cluster_id or cluster_id}
- **Recurrence Count**: {cluster.recurrence_count or 0}
- **Recurrence Score**: {cluster.recurrence_score or 0:.2f}
- **Last Recurrence**: {cluster.last_recurrence_at or 'Never'}

## Recurrence Links
{links_text}

> ⚠️ This data is from batch processing. Not real-time matching.
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_recurrence: {e}")
        return f"❌ Database error: Unable to fetch recurrence data."
    except Exception as e:
        logger.error(f"Unexpected error in get_recurrence: {e}")
        return f"❌ Error fetching recurrence: {str(e)[:100]}"
