"""Pytest fixtures for SmartReco tests"""

import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator

# Set required environment variables for Settings initialization in tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("MESH_API_KEY", "test_mesh_key_1234567890")
os.environ.setdefault("SECRET_KEY", "test_secret_key_12345678901234567890")

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app

from app.database import get_db, get_redis
from app.database.base import Base
from app.models import User, UserRole
from app.auth.password import hash_password

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class MockRedis:
    """Mock Redis client for testing"""
    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        self.store[key] = value

    async def setex(self, key: str, seconds: int, value: str):
        self.store[key] = value

    async def delete(self, key: str):
        self.store.pop(key, None)

    async def incr(self, key: str):
        val = int(self.store.get(key, 0)) + 1
        self.store[key] = str(val)
        return val

    async def close(self):
        pass

    async def aclose(self):
        pass


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """Create all tables before testing and drop after"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for a test"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient wired to the FastAPI app with test DB dependency overrides"""
    mock_redis = MockRedis()

    async def _get_test_db():
        yield db_session

    async def _get_test_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_redis] = _get_test_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
