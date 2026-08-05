"""
Initialize database tables - Direct connection without config cache
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import models
from app.database.base import Base
from app.models import User, Event, Product, Recommendation


async def init_tables():
    """Create all tables"""
    # Create engine directly with the new password
    DATABASE_URL = "postgresql+asyncpg://smartreco:smartreco123@localhost:5432/smartreco_db"
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
    )
    
    print(f"Connecting to database: {DATABASE_URL.replace('smartreco123', '***')}")
    
    try:
        async with engine.begin() as conn:
            print("Dropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            
            print("Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
        
        print("\n✅ Database tables created successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - events")
        print("  - products")
        print("  - recommendations")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("SmartReco Database Initialization")
    print("=" * 60)
    asyncio.run(init_tables())
