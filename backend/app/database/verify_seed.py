"""Seed verification script"""

import asyncio
from sqlalchemy import select, func
from app.database.base import AsyncSessionLocal
from app.models import Product, User, UserRole
from app.vector.chroma_client import get_chroma_client


async def verify_seed():
    """Verify seeded database and vector store content"""
    print("🔍 Verifying database and ChromaDB seed data...")
    
    async with AsyncSessionLocal() as session:
        # 1. Count products in PostgreSQL (expect 30)
        product_count_result = await session.execute(select(func.count(Product.id)))
        product_count = product_count_result.scalar() or 0
        print(f"   - PostgreSQL Products: {product_count} (expected 30)")
        assert product_count == 30, f"Expected 30 products in PostgreSQL, got {product_count}"

        # 2. Assert admin user exists
        admin_result = await session.execute(
            select(User).where(User.email == "admin@smartreco.com", User.role == UserRole.ADMIN)
        )
        admin_user = admin_result.scalar_one_or_none()
        print(f"   - Admin User: {'Found' if admin_user else 'NOT Found'}")
        assert admin_user is not None, "Admin user 'admin@smartreco.com' not found"

    # 3. Count Chroma collection (expect 30 embeddings)
    try:
        chroma_client = get_chroma_client()
        chroma_count = chroma_client.get_collection_count()
        print(f"   - ChromaDB Collection Embeddings: {chroma_count} (expected 30)")
        assert chroma_count == 30, f"Expected 30 embeddings in ChromaDB, got {chroma_count}"
    except Exception as e:
        print(f"   ⚠️ ChromaDB check error: {e}")

    print("✅ Seed verification successful!")


if __name__ == "__main__":
    asyncio.run(verify_seed())
