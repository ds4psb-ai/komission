"""
MCP Tools - 소스팩 생성 도구
Elicitation 지원 (대량 생성 시 사용자 확인 요청)
"""
import json
from typing import Union, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastmcp import Context
from fastmcp.server.context import AcceptedElicitation

from app.database import AsyncSessionLocal
from app.models import OutlierItem
from app.mcp.server import mcp, get_logger
from app.mcp.utils.validators import validate_uuid, safe_format_number
from app.mcp.schemas.packs import VDGInfo, PackSource, SourcePackResponse
from app.utils.time import iso_now

logger = get_logger()

# Elicitation 임계값
ELICITATION_THRESHOLD = 20


@mcp.tool(
    tags=["generation", "write", "elicitation-required"],
)
async def generate_source_pack(
    outlier_ids: list[str],
    pack_name: str,
    include_comments: bool = True,
    include_vdg: bool = True,
    output_format: str = "markdown",
    ctx: Context = None
) -> Union[str, SourcePackResponse]:
    """
    NotebookLM 소스팩 생성 (명시적 동의 필요 - 데이터 생성)
    
    Generate a NotebookLM-compatible source pack from selected outliers.
    This creates new data and requires explicit user consent.
    
    When more than 20 outliers are selected, user confirmation is requested
    via MCP Elicitation (FastMCP 2.14+).
    
    Args:
        outlier_ids: List of outlier UUIDs to include
        pack_name: Name for the source pack
        include_comments: Include best comments in pack
        include_vdg: Include VDG analysis data
        output_format: markdown | json (structured Pydantic output)
        ctx: MCP Context for elicitation (injected by FastMCP)
    
    Returns:
        str (markdown) or SourcePackResponse (Pydantic model when json format)
    """
    logger.info(
        f"Tool call: generate_source_pack(count={len(outlier_ids)}, name='{pack_name}', format={output_format})"
    )
    
    # Input validation
    if not outlier_ids or len(outlier_ids) == 0:
        return "❌ Error: No outlier IDs provided."
    
    if len(outlier_ids) > 100:
        return "❌ Error: Maximum 100 outliers per source pack."
    
    if not pack_name or len(pack_name.strip()) == 0:
        return "❌ Error: Pack name is required."
    
    pack_name = pack_name[:100]  # Limit name length
    output_format = (output_format or "markdown").lower()
    
    # Elicitation: 대량 생성 시 사용자 확인 요청
    if len(outlier_ids) > ELICITATION_THRESHOLD and ctx:
        try:
            response = await ctx.elicit(
                message=f"⚠️ {len(outlier_ids)}개의 아웃라이어가 선택되었습니다.\n"
                        f"많은 양의 데이터를 처리합니다. 계속하시겠습니까?",
                response_type=bool
            )
            
            if not isinstance(response, AcceptedElicitation):
                logger.info(f"Elicitation declined/cancelled for {len(outlier_ids)} outliers")
                return "❌ 작업이 취소되었습니다. 더 적은 수의 아웃라이어로 다시 시도해주세요."
            
            if not response.data:
                logger.info(f"User declined source pack generation for {len(outlier_ids)} outliers")
                return "❌ 사용자가 소스팩 생성을 거부했습니다."
            
            logger.info(f"Elicitation accepted for {len(outlier_ids)} outliers")
        except Exception as e:
            # Elicitation not supported by client - proceed anyway
            logger.warning(f"Elicitation failed (client may not support): {e}")
    
    # Validate UUIDs
    valid_uuids = []
    for oid in outlier_ids:
        uuid_val = validate_uuid(oid)
        if uuid_val:
            valid_uuids.append(uuid_val)
    
    if not valid_uuids:
        return "❌ Error: No valid UUIDs provided."
    
    try:
        async with AsyncSessionLocal() as db:
            # Fetch outliers
            result = await db.execute(
                select(OutlierItem).where(OutlierItem.id.in_(valid_uuids))
            )
            outliers = result.scalars().all()
            
            if not outliers:
                logger.warning("No outliers found for source pack")
                return "❌ Error: No valid outliers found for the provided IDs."
            
            created_at = iso_now()
            
            # Build PackSource list using Pydantic models
            sources: list[PackSource] = []
            for outlier in outliers:
                try:
                    vdg_info = None
                    if include_vdg:
                        vdg_info = VDGInfo(
                            quality_score=outlier.vdg_quality_score,
                            quality_valid=outlier.vdg_quality_valid,
                            analysis_status=outlier.analysis_status,
                        )
                    
                    source = PackSource(
                        id=str(outlier.id),
                        title=outlier.title or "Untitled",
                        platform=outlier.platform or "unknown",
                        category=outlier.category or "unknown",
                        tier=outlier.outlier_tier,
                        score=float(outlier.outlier_score) if outlier.outlier_score else 0,
                        views=outlier.view_count or 0,
                        growth_rate=outlier.growth_rate,
                        video_url=outlier.video_url or "",
                        comments=outlier.best_comments[:5] if include_comments and outlier.best_comments else None,
                        vdg=vdg_info,
                    )
                    sources.append(source)
                except Exception as src_err:
                    logger.warning(f"Error processing outlier for pack: {src_err}")
            
            logger.info(f"Generated source pack with {len(sources)} sources")
            
            # Build SourcePackResponse
            pack_response = SourcePackResponse(
                name=pack_name,
                created_at=created_at,
                outlier_count=len(sources),
                sources=sources
            )
            
            if output_format in {"json", "structured"}:
                return pack_response
            
            # Format output (markdown)
            source_list = []
            for i, s in enumerate(sources):
                try:
                    source_list.append(
                        f"### {i+1}. {s.title}\n"
                        f"- **Tier**: {s.tier or 'N/A'} | **Score**: {s.score:.0f}\n"
                        f"- **Platform**: {s.platform} | **Category**: {s.category}\n"
                        f"- **Views**: {safe_format_number(s.views)} | **Growth**: {s.growth_rate or 'N/A'}\n"
                        f"- **URL**: {s.video_url}\n"
                    )
                except Exception:
                    source_list.append(f"### {i+1}. [Error formatting source]\n")
            
            # Serialize for markdown JSON block
            pack_dict = pack_response.model_dump()
            
            return f"""
# Source Pack Generated: {pack_name}

**Created**: {created_at}
**Sources**: {len(sources)} outliers

## Included Sources

""" + "\n".join(source_list) + f"""

## Pack Data (JSON)

```json
{json.dumps(pack_dict, indent=2, default=str)}
```

> ⚠️ This source pack is ready for NotebookLM import.
"""
    except SQLAlchemyError as e:
        logger.error(f"Database error in generate_source_pack: {e}")
        return f"❌ Database error: Unable to generate source pack."
    except Exception as e:
        logger.error(f"Unexpected error in generate_source_pack: {e}")
        return f"❌ Error generating source pack: {str(e)[:100]}"
