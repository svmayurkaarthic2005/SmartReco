"""
Debug script to check the current logged-in user's data and cache status.
"""
import asyncio
from sqlalchemy import select
from app.database.base import AsyncSessionLocal
from app.models import User, Event
from app.models.recommendation_cache import RecommendationCache
from app.services.event_service import compute_event_hash, get_user_events
from app.agents.behavior_agent import BehaviorAgent

async def debug_user():
    # Check the user that's currently logged in (MAYUR - svmayurkaarthic1@gmail.com)
    target_email = "svmayurkaarthic1@gmail.com"
    
    async with AsyncSessionLocal() as session:
        # Find user
        stmt = select(User).where(User.email == target_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User not found: {target_email}")
            return
        
        print(f"✅ User: {user.name} ({user.email})")
        print(f"   User ID: {user.id}")
        
        # Check events
        events = await get_user_events(user.id, limit=100, db=session)
        print(f"\n📊 Events: {len(events)} total")
        
        # Count by type
        from collections import Counter
        event_types = Counter([str(e.event_type) for e in events])
        for event_type, count in event_types.most_common():
            print(f"   - {event_type}: {count}")
        
        # Check for product interactions
        product_events = [e for e in events if e.product_id is not None]
        print(f"\n📦 Product Interactions: {len(product_events)}")
        for e in product_events[:5]:
            print(f"   - {e.event_type}: product_id={e.product_id}")
        
        # Check event hash
        event_hash = await compute_event_hash(user.id, session)
        print(f"\n🔑 Event Hash: {event_hash[:16]}...")
        
        # Check cache
        cache_stmt = select(RecommendationCache).where(RecommendationCache.user_id == user.id)
        cache_result = await session.execute(cache_stmt)
        cache_entry = cache_result.scalar_one_or_none()
        
        if cache_entry:
            print(f"\n💾 Cache Entry Found:")
            print(f"   Event Hash: {cache_entry.event_hash[:16]}...")
            print(f"   Expires At: {cache_entry.expires_at}")
            cached_data = cache_entry.cached_recommendation
            if cached_data:
                print(f"   Persona: {cached_data.get('persona')}")
                print(f"   Learning Goal: {cached_data.get('narrative_result', {}).get('learning_goal', 'N/A')[:80]}...")
                ranked = cached_data.get('ranked_products', [])
                if ranked:
                    print(f"   Top 3 Courses:")
                    for idx, p in enumerate(ranked[:3], 1):
                        print(f"      {idx}. [{p.get('category')}] {p.get('title')}")
        else:
            print(f"\n💾 No Cache Entry Found")
        
        # Analyze behavior
        print(f"\n🔍 Behavior Analysis:")
        behavior_agent = BehaviorAgent(session)
        summary = await behavior_agent.analyze(user.id, lookback_hours=72)
        
        print(f"   Total Events: {summary.total_events}")
        print(f"   Unique Products Viewed: {len(summary.unique_products_viewed)}")
        print(f"   Categories Explored: {dict(summary.categories_explored)}")
        print(f"   Search Queries: {summary.search_queries}")
        print(f"   Enrolled Products: {getattr(summary, 'enrolled_product_titles', [])}")
        print(f"   Recent Product Titles: {getattr(summary, 'recent_product_titles', [])}")

if __name__ == "__main__":
    asyncio.run(debug_user())
