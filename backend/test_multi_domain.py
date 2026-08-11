"""
Deep test for multi-domain enrollment handling.
Tests scenarios with 1, 2, 3, and 4 domain enrollments.
"""
import asyncio
from sqlalchemy import select
from app.database.base import AsyncSessionLocal
from app.models import User, Event, Product
from app.models.event import EventType
from app.services.recommendation_service import RecommendationService
from app.agents.behavior_agent import BehaviorAgent
import redis.asyncio as redis
from app.config import settings
from datetime import datetime
import uuid

async def simulate_enrollments(user_id, num_domains: int, session):
    """
    Simulate enrollments in N different domains.
    num_domains: 1, 2, 3, or 4
    """
    # Get products from different categories
    categories_to_enroll = []
    if num_domains >= 1:
        categories_to_enroll.append('AI/ML')
    if num_domains >= 2:
        categories_to_enroll.append('Blockchain')
    if num_domains >= 3:
        categories_to_enroll.append('Cloud')
    if num_domains >= 4:
        categories_to_enroll.append('Web Dev')
    
    enrolled_products = []
    for category in categories_to_enroll:
        # Find a product in this category
        stmt = select(Product).where(Product.category == category).limit(1)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()
        
        if product:
            # Create enrollment event
            event = Event(
                id=uuid.uuid4(),
                user_id=user_id,
                session_id=f"test_session_{num_domains}",
                event_type=EventType.ENROLL,
                product_id=product.id,
                event_metadata={
                    'course_title': product.title,
                    'category': product.category
                },
                timestamp=datetime.utcnow()
            )
            session.add(event)
            enrolled_products.append(product)
            print(f"  ✓ Enrolled: [{product.category}] {product.title}")
    
    await session.commit()
    return enrolled_products

async def analyze_recommendations(user_id, enrolled_categories, session, redis_client):
    """Analyze the recommendation quality for multi-domain users."""
    
    # Get behavior summary
    behavior_agent = BehaviorAgent(session)
    summary = await behavior_agent.analyze(user_id, lookback_hours=72)
    
    print(f"\n  📊 Behavior Analysis:")
    print(f"     Total Events: {summary.total_events}")
    print(f"     Enrolled Categories: {getattr(summary, 'enrolled_categories', [])}")
    print(f"     Categories Explored: {dict(summary.categories_explored)}")
    
    # Generate recommendations
    reco_service = RecommendationService(session, redis_client)
    await reco_service.invalidate_cache(user_id)
    
    print(f"\n  🎯 Generating Recommendations...")
    output = await reco_service.get_or_generate(user_id, "Test User")
    
    # Analyze results
    print(f"\n  ✅ Results:")
    print(f"     Persona: {output.persona} ({output.confidence:.1%} confidence)")
    print(f"     Learning Goal: {output.narrative_result.learning_goal}")
    
    # Category breakdown
    from collections import Counter
    recommended_categories = Counter(p.category for p in output.ranked_products)
    
    print(f"\n  📚 Recommended Courses ({len(output.ranked_products)} total):")
    for idx, product in enumerate(output.ranked_products, 1):
        print(f"     {idx}. [{product.category}] {product.title}")
        print(f"        Score: {product.final_score:.3f}")
    
    print(f"\n  🌈 Category Distribution:")
    for category in enrolled_categories:
        count = recommended_categories.get(category, 0)
        percentage = (count / len(output.ranked_products)) * 100 if output.ranked_products else 0
        status = "✅" if count > 0 else "❌"
        print(f"     {status} {category}: {count} courses ({percentage:.0f}%)")
    
    # Check for missing enrolled categories
    missing = [cat for cat in enrolled_categories if recommended_categories.get(cat, 0) == 0]
    if missing:
        print(f"\n  ⚠️  WARNING: Missing enrolled categories: {missing}")
        return False
    
    # Check for over-representation (>50% for multi-domain users)
    if len(enrolled_categories) >= 3:
        for category, count in recommended_categories.items():
            if category in enrolled_categories:
                percentage = (count / len(output.ranked_products)) * 100
                if percentage > 50:
                    print(f"\n  ⚠️  WARNING: {category} is over-represented ({percentage:.0f}%)")
                    return False
    
    print(f"\n  ✅ All enrolled categories represented appropriately!")
    return True

async def test_multi_domain():
    """Test recommendation quality with different numbers of domain enrollments."""
    
    # Create test user
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
        
        # Clear existing events for clean test
        from sqlalchemy import delete
        await session.execute(delete(Event).where(Event.user_id == user.id))
        await session.commit()
        
        print("=" * 80)
        print("MULTI-DOMAIN ENROLLMENT TEST")
        print("=" * 80)
        
        # Test scenarios
        test_scenarios = [
            # (num_domains, description)
            (1, "Single Domain (AI/ML only)"),
            (2, "Two Domains (AI/ML + Blockchain)"),
            (3, "Three Domains (AI/ML + Blockchain + Cloud)"),
            (4, "Four Domains (AI/ML + Blockchain + Cloud + Web Dev)"),
        ]
        
        results = {}
        
        for num_domains, description in test_scenarios:
            print(f"\n{'=' * 80}")
            print(f"TEST SCENARIO: {description}")
            print(f"{'=' * 80}")
            
            # Clear events and enrollments from previous test
            await session.execute(delete(Event).where(Event.user_id == user.id))
            await session.commit()
            
            # Simulate enrollments
            print(f"\n🎓 Enrolling in {num_domains} domain(s):")
            enrolled_products = await simulate_enrollments(user.id, num_domains, session)
            enrolled_categories = [p.category for p in enrolled_products]
            
            # Analyze recommendations
            success = await analyze_recommendations(
                user.id,
                enrolled_categories,
                session,
                redis_client
            )
            
            results[description] = success
        
        # Summary
        print(f"\n{'=' * 80}")
        print("TEST SUMMARY")
        print(f"{'=' * 80}")
        for scenario, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {scenario}")
        
        all_passed = all(results.values())
        if all_passed:
            print(f"\n🎉 All tests passed! Multi-domain handling is working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Review the output above for details.")
        
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_multi_domain())
