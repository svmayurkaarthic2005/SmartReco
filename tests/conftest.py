"""
Pytest configuration and fixtures for SmartReco tests
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database.base import Base, get_db
from app.models import User, Product
from app.auth.password import get_password_hash
from app.config import settings


# Test database URL (use SQLite for tests or separate PostgreSQL database)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test_smartreco.db"
)


# Override settings for testing
settings.database_url = TEST_DATABASE_URL
settings.rate_limit_enabled = False  # Disable rate limiting in tests
settings.langsmith_tracing_enabled = False  # Disable tracing in tests


# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Don't pool connections in tests
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Rolls back all changes after the test completes.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with database override.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    from app.models.user import UserRole
    
    user = User(
        email="testuser@example.com",
        name="Test User",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user"""
    from app.models.user import UserRole
    
    admin = User(
        email="admin@example.com",
        name="Admin User",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def user_token(client: AsyncClient) -> str:
    """Get JWT token for test user"""
    # Register user
    register_data = {
        "email": "tokenuser@example.com",
        "password": "TestPass123!",
        "name": "Token User"
    }
    response = await client.post("/auth/register", json=register_data)
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Get JWT token for admin user"""
    from app.models.user import UserRole
    
    # Create admin user directly in database
    admin = User(
        email="tokenadmin@example.com",
        name="Token Admin",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()

    
    # Login to get token
    login_data = {
        "email": "tokenadmin@example.com",
        "password": "AdminPass123!"
    }
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def sample_products(db_session: AsyncSession) -> list[Product]:
    """Create sample products for testing"""
    products = [
        Product(
            title="Python Basics",
            description="Learn Python programming from scratch",
            category="Programming",
            difficulty="Beginner",
            price=29.99,
            tags=["python", "programming", "beginner"],
            embedding_status="indexed",
            embedding_vector=[0.1] * 384  # Mock embedding
        ),
        Product(
            title="Advanced Machine Learning",
            description="Deep dive into ML algorithms and techniques",
            category="Data Science",
            difficulty="Advanced",
            price=99.99,
            tags=["machine-learning", "ai", "advanced"],
            embedding_status="indexed",
            embedding_vector=[0.2] * 384
        ),
        Product(
            title="Web Development with React",
            description="Build modern web applications with React",
            category="Web Development",
            difficulty="Intermediate",
            price=49.99,
            tags=["react", "javascript", "frontend"],
            embedding_status="indexed",
            embedding_vector=[0.3] * 384
        ),
        Product(
            title="Data Structures & Algorithms",
            description="Master DSA for coding interviews",
            category="Computer Science",
            difficulty="Intermediate",
            price=59.99,
            tags=["algorithms", "data-structures", "interview-prep"],
            embedding_status="indexed",
            embedding_vector=[0.4] * 384
        ),
        Product(
            title="Introduction to SQL",
            description="Learn database queries and design",
            category="Database",
            difficulty="Beginner",
            price=39.99,
            tags=["sql", "database", "beginner"],
            embedding_status="indexed",
            embedding_vector=[0.5] * 384
        ),
    ]
    
    for product in products:
        db_session.add(product)
    
    await db_session.commit()
    
    # Refresh to get IDs
    for product in products:
        await db_session.refresh(product)
    
    return products


@pytest.fixture
def mock_behavior_summary():
    """Mock BehaviorSummary for agent tests"""
    from app.agents.behavior_agent import BehaviorSummary
    
    return BehaviorSummary(
        total_events=50,
        view_count=30,
        search_count=15,
        enrollment_count=2,
        exit_count=3,
        avg_dwell_time=90.5,
        top_categories=["Programming", "Data Science", "Web Development"],
        category_distribution={"Programming": 60, "Data Science": 25, "Web Development": 15},
        search_keywords=["python", "machine learning", "react"],
        has_purchases=True,
        recency_days=2,
        engagement_score=0.75
    )


@pytest.fixture
def mock_persona_result():
    """Mock PersonaResult for tests"""
    from app.agents.persona_agent import PersonaResult, Persona
    
    return PersonaResult(
        persona=Persona.FOCUSED_BUILDER,
        confidence=0.85,
        reasoning="User shows consistent focus on programming category with high dwell time"
    )


@pytest.fixture
def mock_candidate_products():
    """Mock CandidateProduct list for ranking tests"""
    from app.agents.retrieval_agent import CandidateProduct
    
    products = []
    categories = ["Programming", "Data Science", "Web Development"]
    difficulties = ["Beginner", "Intermediate", "Advanced"]
    
    for i in range(10):
        products.append(
            CandidateProduct(
                product_id=f"prod-{i:03d}",
                title=f"Course {i}: {categories[i % 3]}",
                description=f"Learn {categories[i % 3]} skills",
                category=categories[i % 3],
                difficulty=difficulties[i % 3],
                price=29.99 + (i * 10),
                tags=[categories[i % 3].lower(), "popular", "trending"],
                similarity_score=0.9 - (i * 0.05)
            )
        )
    
    return products


# Cleanup after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Clean up test database after all tests"""
    yield
    # Remove test database file if using SQLite
    if "sqlite" in TEST_DATABASE_URL:
        import os
        db_file = "./test_smartreco.db"
        if os.path.exists(db_file):
            os.remove(db_file)
