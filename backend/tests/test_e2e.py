"""End-to-End full integration test flow"""

import pytest
import uuid
from httpx import AsyncClient
from app.agents.persona_agent import Persona
from app.models import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@pytest.mark.asyncio
async def test_full_e2e_flow(async_client: AsyncClient, db_session: AsyncSession):
    """
    Full flow integration test:
    1. POST /auth/register → assert 201/200, token received.
    2. POST /auth/login → assert 200, token received.
    3. POST /events/batch (20 view_product + search events) with Authorization header → assert 200/202.
    4. GET /recommendations/me → assert: persona present, ranked_products list length > 0, personalized_story not empty.
    5. POST /recommendations/refresh → assert new generated_at >= previous.
    6. Admin login → GET /admin/stats → assert all 6 stat fields present and numeric.
    7. Admin GET /admin/persona-distribution → assert keys match Persona enum values.
    """
    user_email = f"e2e_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"

    # Seed test products for recommendation retrieval
    from app.models.product import Product, DifficultyLevel, EmbeddingStatus
    for i in range(10):
        prod = Product(
            id=uuid.uuid4(),
            title=f"E2E Course {i}",
            description=f"Course description for E2E course {i}",
            category="Python" if i % 2 == 0 else "Data Science",
            price=49.99 + i,
            difficulty_level=DifficultyLevel.BEGINNER,
            duration_hours=10.0,
            tags=["python", "ml"],
            embedding_status=EmbeddingStatus.INDEXED
        )
        db_session.add(prod)
    await db_session.commit()

    # 1. Register User
    reg_response = await async_client.post(
        "/auth/register",
        json={"name": "E2E Tester", "email": user_email, "password": password}
    )
    assert reg_response.status_code in (200, 201)
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    user_id = reg_data["user_id"]
    user_token = reg_data["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 2. Login User
    login_response = await async_client.post(
        "/auth/login",
        json={"email": user_email, "password": password}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    user_token = login_data["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. POST /events/batch (20 events)
    session_id = str(uuid.uuid4())
    events = []
    for i in range(15):
        events.append({
            "user_id": user_id,
            "session_id": session_id,
            "event_type": "view_product",
            "product_id": str(uuid.uuid4()),
            "dwell_time": 25.0
        })
    for i in range(5):
        events.append({
            "user_id": user_id,
            "session_id": session_id,
            "event_type": "search",
            "search_query": "Python machine learning"
        })

    batch_response = await async_client.post(
        "/events/batch",
        json={"events": events},
        headers=user_headers
    )
    assert batch_response.status_code in (200, 202)

    # 4. GET /recommendations/me
    rec_response = await async_client.get(
        "/recommendations/me",
        headers=user_headers
    )
    assert rec_response.status_code == 200
    rec_data = rec_response.json()
    assert "persona" in rec_data
    assert isinstance(rec_data["ranked_products"], list)
    assert len(rec_data["ranked_products"]) > 0
    assert rec_data.get("personalized_story") is not None
    assert len(rec_data["personalized_story"]) > 0
    prev_generated_at = rec_data.get("generated_at")

    # 5. POST /recommendations/refresh
    ref_response = await async_client.post(
        "/recommendations/refresh",
        headers=user_headers
    )
    assert ref_response.status_code == 200
    ref_data = ref_response.json()
    new_generated_at = ref_data.get("generated_at")
    assert new_generated_at >= prev_generated_at

    # 6. Admin Login & GET /admin/stats
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    admin_reg = await async_client.post(
        "/auth/register",
        json={"name": "Admin Tester", "email": admin_email, "password": password}
    )
    assert admin_reg.status_code in (200, 201)
    admin_id = admin_reg.json()["user_id"]

    # Promote to Admin in DB
    result = await db_session.execute(select(User).where(User.email == admin_email))
    admin_user = result.scalar_one()
    admin_user.role = UserRole.ADMIN
    await db_session.commit()

    admin_login = await async_client.post(
        "/auth/login",
        json={"email": admin_email, "password": password}
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    stats_response = await async_client.get("/admin/stats", headers=admin_headers)
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    required_stat_fields = [
        "total_users",
        "total_events_7d",
        "total_recommendations",
        "ai_calls",
        "drop_off_risk_count",
        "embedding_failures"
    ]
    for field in required_stat_fields:
        assert field in stats_data
        assert isinstance(stats_data[field], (int, float))

    # 7. Admin GET /admin/persona-distribution
    dist_response = await async_client.get("/admin/persona-distribution", headers=admin_headers)
    assert dist_response.status_code == 200
    dist_data = dist_response.json()
    assert "distribution" in dist_data
    valid_personas = {p.value for p in Persona}
    for key in dist_data["distribution"].keys():
        assert key in valid_personas
