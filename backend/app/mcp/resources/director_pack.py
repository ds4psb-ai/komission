"""
MCP Resources - Director Pack 리소스
"""
import json

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import OutlierItem, RemixNode
from app.mcp.server import mcp, get_logger
from app.mcp.utils.validators import validate_uuid

logger = get_logger()


@mcp.resource("komission://director-pack/{outlier_id}")
async def get_director_pack(outlier_id: str) -> str:
    """
    Director Pack 조회 (VDG v4 기반, on-demand 생성)
    
    Returns DirectorPack JSON for a promoted outlier with VDG v4 analysis.
    """
    logger.info(f"Resource request: director-pack/{outlier_id}")
    
    uuid_val = validate_uuid(outlier_id)
    if not uuid_val:
        logger.warning(f"Invalid UUID format: {outlier_id}")
        return "❌ Invalid outlier ID format. Expected UUID."
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id == uuid_val)
            )
            outlier = result.scalar_one_or_none()
            
            if not outlier:
                logger.warning(f"Outlier not found: {outlier_id}")
                return f"❌ Outlier '{outlier_id}' not found"
            
            if not outlier.promoted_to_node_id:
                return "❌ Outlier is not promoted to RemixNode; no VDG analysis available."
            
            node_result = await db.execute(
                select(RemixNode).where(RemixNode.id == outlier.promoted_to_node_id)
            )
            node = node_result.scalar_one_or_none()
            
            if not node or not node.gemini_analysis:
                return "❌ VDG analysis not available for this outlier."
            
            analysis = node.gemini_analysis
            if "hook_genome" not in analysis or "scenes" not in analysis:
                return "❌ VDG v4 analysis required to compile DirectorPack."
            
            from app.services.vdg_2pass.director_compiler import compile_director_pack
            from app.schemas.vdg_v4 import VDGv4
            
            vdg_v4 = VDGv4(
                content_id=node.node_id,
                duration_sec=analysis.get("duration_sec", 0),
                **{k: v for k, v in analysis.items()
                   if k not in ["content_id", "duration_sec"]}
            )
            director_pack = compile_director_pack(vdg_v4)
            
            logger.info(f"DirectorPack compiled for outlier {outlier_id}")
            return json.dumps(director_pack.model_dump(), ensure_ascii=False, indent=2)
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_director_pack: {e}")
        return "❌ Database error: Unable to fetch DirectorPack."
    except Exception as e:
        logger.error(f"Unexpected error in get_director_pack: {e}")
        return f"❌ Error fetching DirectorPack: {str(e)[:100]}"
