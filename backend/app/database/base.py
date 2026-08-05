"""Database configuration and session management"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


from sqlalchemy.types import UUID
from sqlalchemy.ext.compiler import compiles

@compiles(UUID, 'sqlite')
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Create async engine
engine_kwargs = {
    "echo": settings.db_echo,
    "pool_pre_ping": True,
}
if "sqlite" not in settings.database_url:
    engine_kwargs["pool_size"] = settings.db_pool_size
    engine_kwargs["max_overflow"] = settings.db_max_overflow
    engine_kwargs["pool_timeout"] = settings.db_pool_timeout
    if settings.app_env == "test":
        engine_kwargs["poolclass"] = NullPool

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    **engine_kwargs
)


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
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


async def get_redis():
    """
    Dependency for getting Redis client with connection pooling.
    
    Usage in FastAPI:
        @app.get("/data")
        async def get_data(redis_client = Depends(get_redis)):
            value = await redis_client.get("key")
            return {"value": value}
    """
    import redis.asyncio as redis
    
    # Create connection pool with max_connections from settings
    client = await redis.from_url(
        settings.redis_url,
        password=settings.redis_password,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.redis_max_connections
    )
    try:
        yield client
    finally:
        await client.aclose()


async def init_db() -> None:
    """Initialize database tables (for development only)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables (for development only)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
