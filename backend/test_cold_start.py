"""
Test script to verify cold-start recommendation behavior.
Invalidates cache and regenerates recommendations for a user with no product interactions.
"""
import asyncio
import sys
from sqlalchemy import select
from app.database.base import AsyncSessionLocal
from app.models import User
from app.services.recommendation_service import RecommendationService
import redis.asyncio as redis
from app.config import settings

async def test_cold_start():
    # Target user: MAYUR (svmayurkaarthic1@gmail.com) - has only page navigation events
    target_email = "svmayurkaarthic1@gmail.com"
    
    async with AsyncSessionLocal() as session:
        # Find user
        stmt = select(User).where(User.email == target_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User not found: {target_email}")
            sys.exit(1)
        
        print(f"✅ Found user: {user.name} ({user.email})")
        print(f"   User ID: {user.id}")
        
        # Connect to Redis
        redis_client = await redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True
        )
        
        # Create recommendation service
        reco_service = RecommendationService(session, redis_client)
        
        # Invalidate cache to force fresh generation
        print("\n🔄 Invalidating cache...")
        await reco_service.invalidate_cache(user.id)
        
        # Generate fresh recommendations
        print("🎯 Generating fresh recommendations...")
        output = await reco_service.get_or_generate(user.id, user.name)
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Persona: {output.persona} ({output.confidence:.2%} confidence)")
        print(f"   Learning Goal: {output.narrative_result.learning_goal[:100]}...")
        print(f"\n📚 Recommended Courses ({len(output.ranked_products)}):")
        
        for idx, product in enumerate(output.ranked_products[:5], 1):
            print(f"   {idx}. [{product.category}] {product.title}")
            print(f"      Score: {product.final_score:.3f}")
        
        # Check category diversity
        categories = [p.category for p in output.ranked_products]
        unique_categories = set(categories)
        print(f"\n🌈 Category Diversity: {len(unique_categories)} unique categories in top {len(output.ranked_products)} recommendations")
        for cat in unique_categories:
            count = categories.count(cat)
            print(f"   - {cat}: {count} courses")
        
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_cold_start())
