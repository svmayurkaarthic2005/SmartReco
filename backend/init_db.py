"""
Initialize database tables
"""
import asyncio
from app.database.base import Base, engine
from app.models import User, Event, Product, Recommendation


async def init_tables():
    """Create all tables"""
    async with engine.begin() as conn:
        # Drop all tables (be careful in production!)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_tables())
