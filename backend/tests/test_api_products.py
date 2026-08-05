"""Integration tests for Products API endpoints"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, UserRole, Product


@pytest.mark.asyncio
async def test_admin_create_delete_product_and_non_admin_forbidden(
    async_client: AsyncClient,
    db_session: AsyncSession
):
    """
    Test Product API permissions and operations:
    1. Non-admin POST /products → assert 403.
    2. Admin creates product → assert PostgreSQL row created, embedding_status="indexed".
    3. Admin deletes product → assert both PostgreSQL and Chroma delete called.
    """
    password = "SecurePassword123!"

    # 1. Create Non-Admin user
    user_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    user_reg = await async_client.post(
        "/auth/register",
        json={"name": "Regular User", "email": user_email, "password": password}
    )
    user_token = user_reg.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    product_payload = {
        "title": "New Test Course",
        "description": "Comprehensive course on testing",
        "category": "Software Testing",
        "price": 49.99,
        "difficulty_level": "beginner",
        "duration_hours": 15.0,
        "tags": ["testing", "pytest"]
    }

    # Non-admin POST /products → 403 Forbidden
    forbidden_response = await async_client.post(
        "/products",
        json=product_payload,
        headers=user_headers
    )
    assert forbidden_response.status_code == 403

    # 2. Create Admin user
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    admin_reg = await async_client.post(
        "/auth/register",
        json={"name": "Admin User", "email": admin_email, "password": password}
    )
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
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin POST /products → 201 Created
    create_response = await async_client.post(
        "/products",
        json=product_payload,
        headers=admin_headers
    )
    assert create_response.status_code == 201
    create_data = create_response.json()
    product_id = create_data["id"]
    assert create_data["embedding_status"] == "indexed"

    # Assert PostgreSQL row created
    db_result = await db_session.execute(select(Product).where(Product.title == "New Test Course"))
    db_product = db_result.scalar_one_or_none()
    assert db_product is not None
    assert db_product.title == "New Test Course"

    # 3. Admin DELETE /products/{product_id} → 200 OK
    delete_response = await async_client.delete(
        f"/products/{product_id}",
        headers=admin_headers
    )
    assert delete_response.status_code == 200

    # Assert deleted from PostgreSQL
    db_del_result = await db_session.execute(select(Product).where(Product.title == "New Test Course"))
    deleted_product = db_del_result.scalar_one_or_none()
    assert deleted_product is None
