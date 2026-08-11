"""
Deep test for unenrollment handling.
Tests how the system behaves when user unenrolls from courses.
"""
import asyncio
from sqlalchemy import select, delete
from app.database.base import AsyncSessionLocal
from app.models import User, Event, Product
from app.models.event import EventType
from app.services.recommendation_service import RecommendationService
from app.agents.behavior_agent import BehaviorAgent
import redis.asyncio as redis
from app.config import settings
from datetime import datetime
import uuid

async def test_unenroll_scenarios():
    """Test different unenrollment scenarios."""
    
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
        print("UNENROLLMENT HANDLING TEST")
        print("=" * 80)
        
        # Scenario 1: Check current state
        print(f"\n{'=' * 80}")
        print("CURRENT STATE: Active Enrollments")
        print(f"{'=' * 80}")
        
        behavior_agent = BehaviorAgent(session)
        summary = await behavior_agent.analyze(user.id, lookback_hours=72)
        
        print(f"\n📊 Current Behavior:")
        print(f"   Total Events: {summary.total_events}")
        print(f"   Enrolled Product IDs: {getattr(summary, 'enrolled_product_ids', [])}")
        print(f"   Enrolled Product Titles: {getattr(summary, 'enrolled_product_titles', [])}")
        print(f"   Enrolled Categories: {getattr(summary, 'enrolled_categories', [])}")
        print(f"   Unenrolled Product IDs: {getattr(summary, 'unenrolled_product_ids', [])}")
        print(f"   Unenrolled Product Titles: {getattr(summary, 'unenrolled_product_titles', [])}")
        print(f"   Unenrolled Categories: {getattr(summary, 'unenrolled_categories', [])}")
        
        # Get recommendations
        print(f"\n🎯 Current Recommendations:")
        reco_service = RecommendationService(session, redis_client)
        await reco_service.invalidate_cache(user.id)
        output = await reco_service.get_or_generate(user.id, "Test User")
        
        print(f"   Learning Goal: {output.narrative_result.learning_goal}")
        print(f"   Top 5 Courses:")
        from collections import Counter
        rec_categories = Counter(p.category for p in output.ranked_products)
        for idx, product in enumerate(output.ranked_products[:5], 1):
            print(f"      {idx}. [{product.category}] {product.title}")
        
        print(f"\n   Category Distribution:")
        for category, count in rec_categories.most_common():
            print(f"      - {category}: {count} courses")
        
        # Check if unenrolled categories are recommended
        unenrolled_categories = getattr(summary, 'unenrolled_categories', [])
        if unenrolled_categories:
            print(f"\n   ⚠️  Unenrolled Categories Check:")
            for uncat in unenrolled_categories:
                count = rec_categories.get(uncat, 0)
                if count > 0:
                    print(f"      ❌ {uncat}: {count} courses (SHOULD BE 0!)")
                else:
                    print(f"      ✅ {uncat}: 0 courses (correctly excluded)")
        
        # Scenario 2: Simulate unenrolling from another course
        print(f"\n{'=' * 80}")
        print("SCENARIO: Unenroll from Web Dev")
        print(f"{'=' * 80}")
        
        # Find Web Dev enrollment
        web_dev_course = None
        for enrolled_id in getattr(summary, 'enrolled_product_ids', []):
            try:
                product_uuid = uuid.UUID(enrolled_id)
                stmt = select(Product).where(Product.id == product_uuid)
                result = await session.execute(stmt)
                product = result.scalar_one_or_none()
                if product and product.category == 'Web Dev':
                    web_dev_course = product
                    break
            except:
                pass
        
        if web_dev_course:
            print(f"\n📝 Simulating unenrollment from: {web_dev_course.title}")
            
            # Create unenroll event
            unenroll_event = Event(
                id=uuid.uuid4(),
                user_id=user.id,
                session_id="test_unenroll",
                event_type=EventType.UNENROLL,
                product_id=web_dev_course.id,
                event_metadata={
                    'course_title': web_dev_course.title,
                    'category': web_dev_course.category
                },
                timestamp=datetime.utcnow()
            )
            session.add(unenroll_event)
            await session.commit()
            
            # Re-analyze behavior
            summary_after = await behavior_agent.analyze(user.id, lookback_hours=72)
            
            print(f"\n📊 Updated Behavior:")
            print(f"   Enrolled Categories: {getattr(summary_after, 'enrolled_categories', [])}")
            print(f"   Unenrolled Categories: {getattr(summary_after, 'unenrolled_categories', [])}")
            
            # Get new recommendations
            await reco_service.invalidate_cache(user.id)
            output_after = await reco_service.get_or_generate(user.id, "Test User")
            
            print(f"\n🎯 Updated Recommendations:")
            print(f"   Learning Goal: {output_after.narrative_result.learning_goal}")
            print(f"   Top 5 Courses:")
            rec_categories_after = Counter(p.category for p in output_after.ranked_products)
            for idx, product in enumerate(output_after.ranked_products[:5], 1):
                print(f"      {idx}. [{product.category}] {product.title}")
            
            print(f"\n   Category Distribution:")
            for category, count in rec_categories_after.most_common():
                print(f"      - {category}: {count} courses")
            
            # Verify Web Dev is excluded
            web_dev_count = rec_categories_after.get('Web Dev', 0)
            if web_dev_count == 0:
                print(f"\n   ✅ SUCCESS: Web Dev correctly excluded from recommendations")
            else:
                print(f"\n   ❌ FAIL: Web Dev still has {web_dev_count} courses (should be 0)")
            
            # Rollback the unenroll event
            await session.delete(unenroll_event)
            await session.commit()
            print(f"\n   ↩️  Rolled back unenroll event")
        
        # Scenario 3: What if user unenrolls from ALL courses?
        print(f"\n{'=' * 80}")
        print("SCENARIO: Unenroll from ALL courses")
        print(f"{'=' * 80}")
        
        # Create unenroll events for all enrolled courses
        all_enrolled_ids = getattr(summary, 'enrolled_product_ids', [])
        unenroll_events = []
        
        for enrolled_id in all_enrolled_ids:
            try:
                product_uuid = uuid.UUID(enrolled_id)
                stmt = select(Product).where(Product.id == product_uuid)
                result = await session.execute(stmt)
                product = result.scalar_one_or_none()
                if product:
                    unenroll_event = Event(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        session_id="test_unenroll_all",
                        event_type=EventType.UNENROLL,
                        product_id=product.id,
                        event_metadata={
                            'course_title': product.title,
                            'category': product.category
                        },
                        timestamp=datetime.utcnow()
                    )
                    session.add(unenroll_event)
                    unenroll_events.append(unenroll_event)
                    print(f"   Unenrolled: {product.title} ({product.category})")
            except:
                pass
        
        await session.commit()
        
        # Analyze behavior after unenrolling all
        summary_empty = await behavior_agent.analyze(user.id, lookback_hours=72)
        
        print(f"\n📊 Behavior After Unenrolling All:")
        print(f"   Enrolled Categories: {getattr(summary_empty, 'enrolled_categories', [])}")
        print(f"   Unenrolled Categories: {getattr(summary_empty, 'unenrolled_categories', [])}")
        
        # Get recommendations
        await reco_service.invalidate_cache(user.id)
        output_empty = await reco_service.get_or_generate(user.id, "Test User")
        
        print(f"\n🎯 Recommendations After Unenrolling All:")
        print(f"   Learning Goal: {output_empty.narrative_result.learning_goal}")
        print(f"   Top 5 Courses:")
        rec_categories_empty = Counter(p.category for p in output_empty.ranked_products)
        for idx, product in enumerate(output_empty.ranked_products[:5], 1):
            print(f"      {idx}. [{product.category}] {product.title}")
        
        print(f"\n   Category Distribution:")
        for category, count in rec_categories_empty.most_common():
            print(f"      - {category}: {count} courses")
        
        # Check if any unenrolled categories are recommended
        unenrolled_all = getattr(summary_empty, 'unenrolled_categories', [])
        has_unenrolled = False
        for uncat in unenrolled_all:
            count = rec_categories_empty.get(uncat, 0)
            if count > 0:
                print(f"\n   ❌ FAIL: Unenrolled category {uncat} has {count} courses")
                has_unenrolled = True
        
        if not has_unenrolled:
            print(f"\n   ✅ SUCCESS: All unenrolled categories correctly excluded")
        
        # Rollback all unenroll events
        for event in unenroll_events:
            await session.delete(event)
        await session.commit()
        print(f"\n   ↩️  Rolled back all unenroll events")
        
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_unenroll_scenarios())
