"""Test database connection and query sample data"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import User, Product, Event, Recommendation, UserRole, DifficultyLevel


async def test_connection():
    """Test database connection and display sample data"""
    print("🔌 Testing database connection...\n")
    
    try:
        async with AsyncSessionLocal() as session:
            # Test 1: Count users
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar()
            print(f"✅ Connected to database successfully!")
            print(f"📊 Total users: {user_count}")
            
            # Test 2: Get admin user
            result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN).limit(1)
            )
            admin = result.scalar_one_or_none()
            if admin:
                print(f"👤 Admin user found: {admin.email}")
            else:
                print("⚠️  No admin user found. Run: python scripts/setup_db.py seed")
            
            # Test 3: Count products by category
            result = await session.execute(
                select(Product.category, func.count(Product.id))
                .group_by(Product.category)
                .order_by(Product.category)
            )
            categories = result.all()
            
            print(f"\n📚 Products by category:")
            total_products = 0
            for category, count in categories:
                print(f"   • {category}: {count} courses")
                total_products += count
            print(f"   Total: {total_products} courses")
            
            # Test 4: Sample products
            result = await session.execute(
                select(Product)
                .order_by(Product.created_at.desc())
                .limit(3)
            )
            products = result.scalars().all()
            
            if products:
                print(f"\n🎓 Sample courses:")
                for product in products:
                    print(f"   • {product.title}")
                    print(f"     Category: {product.category} | "
                          f"Level: {product.difficulty_level.value} | "
                          f"Price: ${product.price}")
            
            # Test 5: Event count
            result = await session.execute(select(func.count(Event.id)))
            event_count = result.scalar()
            print(f"\n📈 Total events: {event_count}")
            
            # Test 6: Recommendation count
            result = await session.execute(select(func.count(Recommendation.id)))
            rec_count = result.scalar()
            print(f"🎯 Total recommendations: {rec_count}")
            
            print("\n✅ Database is working correctly!\n")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}\n")
        print("Troubleshooting steps:")
        print("1. Ensure PostgreSQL is running: docker-compose ps postgres")
        print("2. Check DATABASE_URL in .env file")
        print("3. Run migrations: alembic upgrade head")
        print("4. Seed database: python scripts/setup_db.py seed")
        raise


if __name__ == "__main__":
    asyncio.run(test_connection())
