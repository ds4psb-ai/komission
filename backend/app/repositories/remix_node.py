"""
RemixNode Repository - Data access layer for remix nodes
"""
from typing import Optional, List
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models import RemixNode, NodeLayer, NodePermission, NodeGovernance
from app.routers.remix import RemixNodeCreate
from app.services.graph_db import graph_db

class RemixNodeRepository(BaseRepository[RemixNode]):
    """
    Repository for RemixNode operations.
    Isolates all database queries for testability.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, id: str) -> Optional[RemixNode]:
        """Get a single remix node by UUID string (primary key)"""
        return await self.session.get(RemixNode, id)

    async def get_by_node_id(self, node_id: str) -> Optional[RemixNode]:
        """Get by business key (node_id)"""
        result = await self.session.execute(select(RemixNode).where(RemixNode.node_id == node_id))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[RemixNode]:
        """Get all remix nodes with pagination"""
        result = await self.session.execute(select(RemixNode).limit(limit).offset(offset))
        return result.scalars().all()

    async def create(self, node_in: RemixNodeCreate, owner_id: str) -> RemixNode:
        """Create a new remix node and sync to Neo4j"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        
        count_query = select(func.count()).where(RemixNode.node_id.like(f"remix_{date_str}%"))
        count_res = await self.session.execute(count_query)
        count = count_res.scalar() or 0
        node_id = f"remix_{date_str}_{count + 1:03d}"
        
        node = RemixNode(
            node_id=node_id,
            title=node_in.title,
            source_video_url=node_in.source_video_url,
            platform=node_in.platform,
            created_by=owner_id,
            layer=NodeLayer.MASTER,
            permission=NodePermission.READ_ONLY,
            governed_by=NodeGovernance.OPEN_COMMUNITY,
            owner_type="user" 
        )
        self.session.add(node)
        await self.session.commit()
        await self.session.refresh(node)
        
        # Async Graph Sync (Fire and Forget)
        # Note: In production, use BackgroundTasks or Celery
        try:
            await graph_db.create_remix_node(
                node_id=node.node_id,
                title=node.title,
                layer=node.layer.value,
                created_by=str(owner_id) 
            )
            # Create User node if not exists (Best effort)
            # Fetch user email/name if needed or just link by ID
            # await graph_db.create_user_node(str(owner_id), "Unknown", "Unknown") 
        except Exception as e:
            print(f"⚠️ Graph sync failed: {e}")

        return node

    async def update(self, node: RemixNode) -> RemixNode:
        """Update an existing remix node"""
        self.session.add(node)
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def delete(self, id: str) -> bool:
        """Delete a remix node by PK"""
        node = await self.get_by_id(id)
        if node:
            await self.session.delete(node)
            await self.session.commit()
            return True
        return False

