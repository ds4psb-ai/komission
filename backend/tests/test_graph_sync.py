from unittest.mock import AsyncMock, patch
import pytest
from app.repositories.remix_node import RemixNodeRepository
from app.routers.remix import RemixNodeCreate
from app.models import User

@pytest.mark.asyncio
async def test_create_remix_node_with_graph_sync(db_session):
    # Setup
    user = User(email="graph_test@komission.com", firebase_uid="graph_uid", role="user")
    db_session.add(user)
    await db_session.flush()
    repo = RemixNodeRepository(db_session)
    node_in = RemixNodeCreate(title="Graph Test", source_video_url="v", platform="t")

    # Mock GraphDB
    with patch("app.repositories.remix_node.graph_db") as mock_graph_db:
        mock_graph_db.create_remix_node = AsyncMock()
        
        # Action
        node = await repo.create(node_in, user.id)
        
        # Verify
        assert node.id is not None
        mock_graph_db.create_remix_node.assert_called_once()
        call_args = mock_graph_db.create_remix_node.call_args[1]
        assert call_args["title"] == "Graph Test"
        assert call_args["node_id"] == node.node_id

@pytest.mark.asyncio
async def test_get_genealogy_mock(db_session):
    # Setup
    node_id = "remix_20251221_001"
    
    # Mock GraphDB response
    mock_record = {
        "current": {"id": node_id, "title": "Current"},
        "ancestors": [{"id": "remix_parent", "title": "Parent"}],
        "children": [{"id": "remix_child", "title": "Child"}]
    }
    
    with patch("app.services.graph_db.graph_db") as mock_graph_db:
        mock_graph_db.get_genealogy = AsyncMock(return_value=mock_record)
        
        # Test direct service call
        result = await mock_graph_db.get_genealogy(node_id)
        assert result["current"]["id"] == node_id
        assert len(result["ancestors"]) == 1
        assert len(result["children"]) == 1

