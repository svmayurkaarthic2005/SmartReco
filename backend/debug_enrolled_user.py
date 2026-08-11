"""
Debug script to check enrolled user's behavior and recommendations.
"""
import asyncio
from sqlalchemy import select
from app.database.base import AsyncSessionLocal
from app.models import User, Event
from app.models.recommendation_cache import RecommendationCache
from app.services.event_service import compute_event_hash, get_user_events
from app.agents.behavior_agent import BehaviorAgent

async def debug_enrolled():
    target_email = "svmayurkaarthic1@gmail.com"
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == target_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User not found: {target_email}")
            return
        
        print(f"✅ User: {user.name} ({user.email})")
        print(f"   User ID: {user.id}")
        
        # Get all events
        events = await get_user_events(user.id, limit=100, db=session)
        print(f"\n📊 Total Events: {len(events)}")
        
        # Check enrollment events
        enrollment_events = [e for e in events if 'enroll' in str(e.event_type).lower()]
        print(f"\n📚 Enrollment Events: {len(enrollment_events)}")
        for e in enrollment_events:
            meta = e.event_metadata or {}
            course_title = meta.get('course_title', 'Unknown')
            category = meta.get('category', 'Unknown')
            print(f"   - {e.event_type}: {course_title} [{category}]")
            print(f"     Product ID: {e.product_id}")
            print(f"     Timestamp: {e.timestamp}")
        
        # Analyze behavior
        print(f"\n🔍 Behavior Summary:")
        behavior_agent = BehaviorAgent(session)
        summary = await behavior_agent.analyze(user.id, lookback_hours=72)
        
        print(f"   Total Events: {summary.total_events}")
        print(f"   Unique Products Viewed: {len(summary.unique_products_viewed)}")
        print(f"   Enrolled Product IDs: {getattr(summary, 'enrolled_product_ids', [])}")
        print(f"   Enrolled Product Titles: {getattr(summary, 'enrolled_product_titles', [])}")
        print(f"   Enrolled Categories: {getattr(summary, 'enrolled_categories', [])}")
        print(f"   Categories Explored (weighted): {dict(summary.categories_explored)}")
        print(f"   Recent Product Titles: {getattr(summary, 'recent_product_titles', [])}")
        
        # Check cache
        cache_stmt = select(RecommendationCache).where(RecommendationCache.user_id == user.id)
        cache_result = await session.execute(cache_stmt)
        cache_entry = cache_result.scalar_one_or_none()
        
        if cache_entry:
            print(f"\n💾 Cache Entry:")
            cached_data = cache_entry.cached_recommendation
            print(f"   Persona: {cached_data.get('persona')}")
            print(f"   Learning Goal: {cached_data.get('narrative_result', {}).get('learning_goal')}")
            ranked = cached_data.get('ranked_products', [])
            if ranked:
                print(f"   Top 5 Recommended Courses:")
                for idx, p in enumerate(ranked[:5], 1):
                    print(f"      {idx}. [{p.get('category')}] {p.get('title')}")

if __name__ == "__main__":
    asyncio.run(debug_enrolled())
