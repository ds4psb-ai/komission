import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.remix_node import RemixNodeRepository
from app.models import RemixNode, User
from app.routers.remix import RemixNodeCreate

@pytest.mark.asyncio
async def test_create_remix_node(db_session: AsyncSession):
    # Setup user
    user = User(email="repo_test@komission.com", firebase_uid="repo_uid", role="user")
    db_session.add(user)
    await db_session.flush()
    
    # Setup repository
    repo = RemixNodeRepository(db_session)
    
    # Test Create
    node_in = RemixNodeCreate(
        title="Repo Test Node",
        source_video_url="http://test.com/video.mp4",
        platform="youtube"
    )
    
    node = await repo.create(node_in, owner_id=user.id)
    
    assert node.id is not None
    assert node.title == "Repo Test Node"
    assert node.created_by == user.id
    assert node.layer == "master" # Default

@pytest.mark.asyncio
async def test_get_by_node_id(db_session: AsyncSession):
    # Setup user & node
    user = User(email="find@komission.com", firebase_uid="find_uid", role="user")
    db_session.add(user)
    await db_session.flush()
    
    node = RemixNode(
        title="Find Me",
        created_by=user.id,
        source_video_url="http://vid",
        node_id="unique-node-id"
    )
    db_session.add(node)
    await db_session.commit()
    
    # Test Get
    repo = RemixNodeRepository(db_session)
    found = await repo.get_by_node_id("unique-node-id")
    
    assert found is not None
    assert found.title == "Find Me"

@pytest.mark.asyncio
async def test_list_nodes(db_session: AsyncSession):
    repo = RemixNodeRepository(db_session)

    initial_nodes = await repo.get_all()
    initial_count = len(initial_nodes)
    
    # Create new
    user = User(email="list@komission.com", firebase_uid="list_uid", role="user")
    db_session.add(user)
    await db_session.flush()
    
    await repo.create(RemixNodeCreate(title="N1", source_video_url="v1"), user.id)
    await repo.create(RemixNodeCreate(title="N2", source_video_url="v2"), user.id)
    
    new_nodes = await repo.get_all()
    assert len(new_nodes) == initial_count + 2

