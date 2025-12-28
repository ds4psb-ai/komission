
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.services.cache import cache


# pytest-asyncio event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session scope to avoid event loop cleanup issues."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

# Async Database URL
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# We do NOT create a global engine here to avoid event loop mismatch.

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Create engine per test to match the current event loop
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Start transaction
    connection = await engine.connect()
    transaction = await connection.begin()
    
    session_maker = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_maker()
    
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()
    await engine.dispose()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    # Disable Redis cache for tests
    cache._client = None
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()



