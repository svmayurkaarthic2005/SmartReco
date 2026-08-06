import asyncio
from sqlalchemy import text
from app.database.base import AsyncSessionLocal

async def check_pg_enum():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT unnest(enum_range(NULL::eventtype))"))
        vals = [r[0] for r in result.fetchall()]
        print('DB EventType enum values:', vals)

asyncio.run(check_pg_enum())
