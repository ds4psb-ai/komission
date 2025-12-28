"""
Database configuration with async PostgreSQL (asyncpg)
"""
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Async Database URL
if settings.POSTGRES_HOST.startswith("/cloudsql/"):
    # Cloud Run + Cloud SQL Unix socket
    DATABASE_URL = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@/{settings.POSTGRES_DB}?host={settings.POSTGRES_HOST}"
    )
else:
    DATABASE_URL = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

# Connection pool defaults (Cloud SQL micro instances are very small)
if settings.POSTGRES_HOST.startswith("/cloudsql/"):
    default_pool_size = 5
    default_max_overflow = 0
else:
    default_pool_size = 20
    default_max_overflow = 10

pool_size = int(os.getenv("DB_POOL_SIZE", default_pool_size))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW", default_max_overflow))
pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Async Engine with connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=pool_timeout,
    pool_pre_ping=True,  # Check connection health
    echo=settings.ENVIRONMENT == "development",
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Backward-compatible alias (older modules expect async_session_maker)
async_session_maker = AsyncSessionLocal


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency for getting async database session.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
