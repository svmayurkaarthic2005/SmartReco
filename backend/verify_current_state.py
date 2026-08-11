"""
Verify current live state of recommendations for user.
"""
import asyncio
from sqlalchemy import select
from app.database.base import AsyncSessionLocal
from app.models import User
from app.services.recommendation_service import RecommendationService
from app.agents.behavior_agent import BehaviorAgent
import redis.asyncio as redis
from app.config import settings
from collections import Counter

async def verify_state():
    """Verify current recommendation state."""
    
    target_email = "svmayurkaarthic1@gmail.com"
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == target_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User not found: {target_email}")
            return
        
        # Connect to Redis
        redis_client = await redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True
        )
        
        print("=" * 80)
        print("CURRENT LIVE STATE VERIFICATION")
        print("=" * 80)
        
        # Check current behavior
        behavior_agent = BehaviorAgent(session)
        summary = await behavior_agent.analyze(user.id, lookback_hours=72)
        
        print(f"\n📊 Your Current Enrollments:")
        for title in getattr(summary, 'enrolled_product_titles', []):
            print(f"   ✅ {title}")
        
        print(f"\n📊 Your Enrolled Categories:")
        for cat in getattr(summary, 'enrolled_categories', []):
            print(f"   ✅ {cat}")
        
        print(f"\n📊 Your Unenrolled Courses:")
        for title in getattr(summary, 'unenrolled_product_titles', []):
            print(f"   ❌ {title}")
        
        print(f"\n📊 Your Unenrolled Categories:")
        for cat in getattr(summary, 'unenrolled_categories', []):
            print(f"   ❌ {cat}")
        
        # Get fresh recommendations
        print(f"\n🔄 Generating FRESH recommendations (bypassing cache)...")
        reco_service = RecommendationService(session, redis_client)
        await reco_service.invalidate_cache(user.id)
        output = await reco_service.get_or_generate(user.id, "Test User")
        
        print(f"\n🎯 FRESH AI Recommendations:")
        print(f"   Learning Goal: {output.narrative_result.learning_goal}")
        
        print(f"\n   Top 8 Courses:")
        rec_categories = Counter(p.category for p in output.ranked_products)
        for idx, product in enumerate(output.ranked_products, 1):
            print(f"      {idx}. [{product.category}] {product.title}")
        
        print(f"\n   Category Distribution:")
        for category, count in rec_categories.most_common():
            print(f"      - {category}: {count} courses")
        
        # Verify no unenrolled categories
        print(f"\n✅ Verification:")
        unenrolled_categories = getattr(summary, 'unenrolled_categories', [])
        has_errors = False
        for uncat in unenrolled_categories:
            count = rec_categories.get(uncat, 0)
            if count > 0:
                print(f"   ❌ ERROR: {uncat} has {count} courses (should be 0)")
                has_errors = True
            else:
                print(f"   ✅ {uncat}: 0 courses (correctly excluded)")
        
        if not has_errors:
            print(f"\n🎉 SUCCESS: All unenrolled categories correctly excluded!")
            print(f"   System is working like YouTube/Udemy!")
        
        # Check minimum courses per enrolled category
        enrolled_categories = getattr(summary, 'enrolled_categories', [])
        print(f"\n✅ Enrolled Category Coverage:")
        for enrolled_cat in enrolled_categories:
            count = rec_categories.get(enrolled_cat, 0)
            if len(enrolled_categories) == 1:
                min_expected = 5
            elif len(enrolled_categories) == 2:
                min_expected = 3
            else:
                min_expected = 2
            
            if count >= min_expected:
                print(f"   ✅ {enrolled_cat}: {count} courses (minimum {min_expected})")
            else:
                print(f"   ⚠️  {enrolled_cat}: {count} courses (expected minimum {min_expected})")
        
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(verify_state())
