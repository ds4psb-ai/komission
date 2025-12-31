"""
MCP Tools - VDG 관련 도구
Elicitation 지원 (force=True 시 비용 확인 요청)
"""
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastmcp import Context
from fastmcp.dependencies import Progress
from fastmcp.server.context import AcceptedElicitation

from app.database import AsyncSessionLocal
from app.models import OutlierItem
from app.mcp.server import mcp, get_logger
from app.mcp.utils.validators import validate_uuid

logger = get_logger()


@mcp.tool(
    task=True,
    tags=["analysis", "write", "billable", "elicitation-required"],
)
async def reanalyze_vdg(
    outlier_id: str,
    force: bool = False,
    progress: Progress = Progress(),
    ctx: Context = None
) -> str:
    """
    VDG 재분석 요청 (명시적 동의 필요 - 비용 발생)
    
    Request a re-analysis of VDG (Video DNA Genome) for an outlier.
    This incurs API costs and requires explicit user consent.
    Runs as a background task with progress reporting (FastMCP 2.14+).
    
    When force=True is used to override existing analysis, user confirmation
    is requested via MCP Elicitation (FastMCP 2.14+).
    
    Args:
        outlier_id: UUID of the outlier to re-analyze
        force: Force re-analysis even if already completed (triggers elicitation)
        progress: Progress dependency for background task reporting
        ctx: MCP Context for elicitation (injected by FastMCP)
    """
    logger.info(f"Tool call: reanalyze_vdg(outlier_id='{outlier_id}', force={force})")
    
    # Set up progress tracking (5 steps total with elicitation)
    await progress.set_total(5)
    await progress.set_message("Validating outlier ID")
    
    # Validate UUID
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {outlier_id}")
        await progress.set_message("Invalid outlier ID")
        return f"❌ Error: Invalid outlier ID format. Expected UUID."
    
    await progress.increment()
    await progress.set_message("Fetching outlier from database")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            await progress.increment()
            
            if not outlier:
                logger.warning(f"Outlier not found: {outlier_id}")
                await progress.set_message("Outlier not found")
                return f"❌ Error: Outlier '{outlier_id}' not found."
            
            await progress.set_message("Checking analysis status")
            
            # Check current status
            if outlier.analysis_status == "completed":
                if not force:
                    logger.info(f"Outlier already analyzed, force={force}")
                    await progress.increment()
                    await progress.set_message("Already analyzed")
                    return f"""
# VDG Re-analysis Not Needed

The outlier "{outlier.title or 'Untitled'}" already has a completed VDG analysis.

**Current Status**: {outlier.analysis_status}
**Quality Score**: {outlier.vdg_quality_score or 'N/A'}
**Valid**: {outlier.vdg_quality_valid if outlier.vdg_quality_valid is not None else 'Unknown'}

To force re-analysis, set `force=True`. Note: This will incur additional API costs.
"""
                
                # Elicitation: force=True 시 비용 확인
                if ctx:
                    try:
                        await progress.set_message("Requesting user confirmation")
                        
                        response = await ctx.elicit(
                            message="⚠️ 이미 완료된 VDG 분석을 강제로 재분석하려고 합니다.\n"
                                    "Gemini API 비용이 발생합니다. 계속하시겠습니까?",
                            response_type=bool
                        )
                        
                        if not isinstance(response, AcceptedElicitation):
                            logger.info("Force re-analysis declined/cancelled")
                            await progress.set_message("Cancelled by user")
                            return "❌ 재분석이 취소되었습니다."
                        
                        if not response.data:
                            logger.info("User declined force re-analysis")
                            await progress.set_message("Declined by user")
                            return "❌ 사용자가 강제 재분석을 거부했습니다."
                        
                        logger.info("Force re-analysis confirmed by user")
                    except Exception as e:
                        # Elicitation not supported - proceed with warning logged
                        logger.warning(f"Elicitation failed (client may not support): {e}")
            
            await progress.increment()
            await progress.set_message("Queuing for re-analysis")
            
            # Queue for re-analysis
            outlier.analysis_status = "pending"
            await db.commit()
            
            logger.info(f"Queued {outlier_id} for VDG re-analysis")
            await progress.increment()
            await progress.set_message("Complete")
            return f"""
# VDG Re-analysis Queued

**Outlier**: {outlier.title or 'Untitled'}
**ID**: {outlier_id}
**Status**: Queued for re-analysis
{"**Note**: Force re-analysis requested (previous analysis will be replaced)" if force else ""}

The VDG pipeline will process this outlier in the next batch.
Estimated completion: 5-10 minutes.

> ⚠️ This action incurs API costs for Gemini video analysis.
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in reanalyze_vdg: {e}")
        await progress.set_message("Database error")
        return f"❌ Database error: Unable to queue re-analysis."
    except Exception as e:
        logger.error(f"Unexpected error in reanalyze_vdg: {e}")
        await progress.set_message("Error occurred")
        return f"❌ Error queuing re-analysis: {str(e)[:100]}"
