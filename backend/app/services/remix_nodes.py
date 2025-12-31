from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RemixNode
from app.utils.time import utcnow


async def generate_remix_node_id(db: AsyncSession, prefix: str = "remix") -> str:
    """Generate a date-scoped remix node ID (e.g., remix_20260107_001)."""
    date_str = utcnow().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(RemixNode.node_id.like(f"{prefix}_{date_str}%"))
    )
    count = count_result.scalar() or 0
    return f"{prefix}_{date_str}_{count + 1:03d}"
