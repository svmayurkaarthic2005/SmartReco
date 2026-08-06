import asyncio
from sqlalchemy import text, insert
from app.database.base import AsyncSessionLocal
from app.models.event import Event, EventType
import uuid
from datetime import datetime

MAYUR_ID = uuid.UUID("dad33227-b76e-4956-8aa9-50724c69c8b8")
PROD_ID = uuid.UUID("bd4e24e4-7eea-41d2-a038-d7044befa545")

async def test_unenroll():
    async with AsyncSessionLocal() as db:
        # Verify enum values in DB
        result = await db.execute(text("""
            SELECT e.enumlabel FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'event_type'
            ORDER BY e.enumsortorder
        """))
        vals = [r[0] for r in result.fetchall()]
        print(f"DB enum values: {vals}")
        print(f"unenroll in DB: {'unenroll' in vals}")
        print(f"lesson_complete in DB: {'lesson_complete' in vals}")

        # Test inserting unenroll via ORM insert
        try:
            stmt = insert(Event).values([{
                "id": uuid.uuid4(),
                "user_id": MAYUR_ID,
                "session_id": "test-sess-" + str(uuid.uuid4()),
                "event_type": EventType.UNENROLL,
                "product_id": PROD_ID,
                "search_query": None,
                "dwell_time": None,
                "event_metadata": {"course_title": "Test", "category": "Cyber Security"},
                "timestamp": datetime.utcnow()
            }])
            await db.execute(stmt)
            await db.commit()
            print("ORM unenroll insert: SUCCESS")
        except Exception as e:
            await db.rollback()
            print(f"ORM unenroll insert FAILED: {e}")

asyncio.run(test_unenroll())
