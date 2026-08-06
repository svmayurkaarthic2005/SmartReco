"""Script to clear event logs, recommendation history, and recommendation cache"""

import asyncio
import redis.asyncio as redis_client
from sqlalchemy import text
from app.database.base import AsyncSessionLocal
from app.config import settings

async def clear_events_and_caches():
    print("[1/2] Clearing PostgreSQL events, recommendations, and recommendation_cache tables...")
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("DELETE FROM recommendation_cache;"))
            await session.execute(text("DELETE FROM recommendations;"))
            await session.execute(text("DELETE FROM events;"))
            await session.commit()
            print("  [SUCCESS] PostgreSQL tables cleared successfully!")
        except Exception as e:
            await session.rollback()
            print(f"  [ERROR] Error clearing PostgreSQL tables: {e}")

    print("[2/2] Clearing Redis caches and key-value entries...")
    try:
        r = await redis_client.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True
        )
        await r.flushdb()
        await r.close()
        print("  [SUCCESS] Redis database flushed successfully!")
    except Exception as e:
        print(f"  [WARNING] Could not flush Redis: {e}")

    print("\n[COMPLETE] ALL EVENT LOGS AND CACHES CLEARED CLEANLY!")

if __name__ == "__main__":
    asyncio.run(clear_events_and_caches())
