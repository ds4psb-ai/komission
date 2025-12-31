"""
MCP Resources - 아웃라이어 관련 리소스
"""
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import OutlierItem
from app.mcp.server import mcp, get_logger
from app.mcp.utils.validators import validate_uuid, safe_format_number
from app.mcp.utils.formatters import format_comments

logger = get_logger()


@mcp.resource("komission://comments/{outlier_id}")
async def get_comments(outlier_id: str) -> str:
    """
    베스트 댓글 5개 조회 (수집 시점 스냅샷)
    
    Returns top 5 comments from the outlier video,
    sorted by likes with language tags.
    """
    logger.info(f"Resource request: comments/{outlier_id}")
    
    # Validate UUID
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {outlier_id}")
        return f"❌ Invalid outlier ID format. Expected UUID, got: '{outlier_id[:50]}...'"
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Outlier not found: {outlier_id}")
                return f"❌ Outlier '{outlier_id}' not found"
            
            comments = outlier.best_comments or []
            
            logger.info(f"Found {len(comments)} comments for outlier")
            return f"""
# Best Comments for: {outlier.title or 'Untitled'}

**Platform**: {outlier.platform}
**Views**: {safe_format_number(outlier.view_count)}
**Tier**: {outlier.outlier_tier or 'N/A'}

## Top Comments
{format_comments(comments)}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_comments: {e}")
        return f"❌ Database error: Unable to fetch comments."
    except Exception as e:
        logger.error(f"Unexpected error in get_comments: {e}")
        return f"❌ Error fetching comments: {str(e)[:100]}"


@mcp.resource("komission://evidence/{pattern_id}")
async def get_evidence(pattern_id: str) -> str:
    """
    Evidence 요약 (댓글+신호+지표 종합)
    
    Returns comprehensive evidence summary including:
    - Engagement metrics
    - Best comments analysis
    - Growth signals
    """
    logger.info(f"Resource request: evidence/{pattern_id}")
    
    # Validate UUID
    uuid_val = validate_uuid(pattern_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {pattern_id}")
        return f"❌ Invalid pattern ID format. Expected UUID."
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Pattern not found: {pattern_id}")
                return f"❌ Pattern '{pattern_id}' not found"
            
            comments = outlier.best_comments or []
            
            # Analyze comment sentiment tags
            tag_counts = {}
            for c in comments:
                try:
                    tag = c.get("tag", "unknown")
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except Exception:
                    pass
            
            tag_summary = ", ".join([f"{k}: {v}" for k, v in tag_counts.items()]) or "No tags"
            
            logger.info(f"Evidence compiled for {pattern_id}")
            return f"""
# Evidence Summary

## Metrics
- **Views**: {safe_format_number(outlier.view_count)}
- **Likes**: {safe_format_number(outlier.like_count)}
- **Shares**: {safe_format_number(outlier.share_count)}
- **Growth Rate**: {outlier.growth_rate or 'N/A'}
- **Engagement Rate**: {outlier.engagement_rate or 'N/A'}

## Outlier Analysis
- **Tier**: {outlier.outlier_tier or 'N/A'}
- **Score**: {outlier.outlier_score or 'N/A'}
- **Creator Avg Views**: {safe_format_number(outlier.creator_avg_views)}

## Comment Signals
- **Total Comments**: {len(comments)}
- **Tag Distribution**: {tag_summary}

## Best Comments
{format_comments(comments)}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_evidence: {e}")
        return f"❌ Database error: Unable to fetch evidence."
    except Exception as e:
        logger.error(f"Unexpected error in get_evidence: {e}")
        return f"❌ Error fetching evidence: {str(e)[:100]}"


@mcp.resource("komission://vdg/{outlier_id}")
async def get_vdg(outlier_id: str) -> str:
    """
    VDG 분석 결과 조회
    
    Returns Video DNA Genome analysis results including
    quality scores and validation status.
    """
    logger.info(f"Resource request: vdg/{outlier_id}")
    
    # Validate UUID
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {outlier_id}")
        return f"❌ Invalid outlier ID format. Expected UUID."
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Outlier not found: {outlier_id}")
                return f"❌ Outlier '{outlier_id}' not found"
            
            logger.info(f"VDG data retrieved for {outlier_id}")
            return f"""
# VDG Analysis: {outlier.title or 'Untitled'}

## Basic Info
- **Platform**: {outlier.platform or 'N/A'}
- **Category**: {outlier.category or 'N/A'}
- **URL**: {outlier.video_url or 'N/A'}

## Analysis Status
- **Status**: {outlier.analysis_status or 'pending'}
- **Approved**: {outlier.approved_at or 'Not approved'}

## Quality Metrics
- **Quality Score**: {outlier.vdg_quality_score or 'Not analyzed'}
- **Valid**: {outlier.vdg_quality_valid if outlier.vdg_quality_valid is not None else 'Unknown'}
- **Issues**: {outlier.vdg_quality_issues or 'None'}

## Outlier Metrics
- **Tier**: {outlier.outlier_tier or 'N/A'}
- **Score**: {outlier.outlier_score or 'N/A'}
- **Views**: {safe_format_number(outlier.view_count)}
- **Growth**: {outlier.growth_rate or 'N/A'}
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_vdg: {e}")
        return f"❌ Database error: Unable to fetch VDG data."
    except Exception as e:
        logger.error(f"Unexpected error in get_vdg: {e}")
        return f"❌ Error fetching VDG: {str(e)[:100]}"
