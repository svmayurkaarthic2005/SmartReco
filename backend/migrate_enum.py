import asyncio
from sqlalchemy import text
from app.database.base import AsyncSessionLocal

async def migrate_enum():
    """Add missing enum values to PostgreSQL event_type enum"""
    missing_values = ['unenroll', 'module_complete', 'lesson_complete', 're_enroll']
    
    async with AsyncSessionLocal() as db:
        # Check current enum values
        result = await db.execute(text("""
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'event_type'
            ORDER BY e.enumsortorder
        """))
        existing = set(r[0] for r in result.fetchall())
        print(f"Existing DB enum values: {existing}")

        for val in missing_values:
            if val not in existing:
                await db.execute(text(f"ALTER TYPE event_type ADD VALUE IF NOT EXISTS '{val}'"))
                print(f"Added: {val}")
            else:
                print(f"Already exists: {val}")

        await db.commit()
        
        # Verify
        result2 = await db.execute(text("""
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'event_type'
            ORDER BY e.enumsortorder
        """))
        final = [r[0] for r in result2.fetchall()]
        print(f"\nFinal DB enum values: {final}")
        print("Migration complete!")

asyncio.run(migrate_enum())
