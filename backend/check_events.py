import asyncio
from sqlalchemy import select, String
from app.database.base import AsyncSessionLocal
from app.models import Event, User, Product

async def check_db_events():
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
        print(f"Total Users in DB: {len(users)}")
        for u in users:
            print(f" - User: {u.name} ({u.email}) [ID: {u.id}]")

        products = (await session.execute(select(Product))).scalars().all()
        print(f"\nTotal Products in DB: {len(products)}")
        for p in products[:10]:
            print(f" - Product: id={p.id}, title='{p.title}'")

if __name__ == "__main__":
    asyncio.run(check_db_events())
