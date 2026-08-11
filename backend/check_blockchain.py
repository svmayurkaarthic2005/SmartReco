import asyncio
from sqlalchemy import select
from app.database.base import AsyncSessionLocal
from app.models import Product

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).where(Product.category == 'Blockchain'))
        blockchain_products = result.scalars().all()
        print(f'Blockchain courses: {len(blockchain_products)}')
        for p in blockchain_products[:10]:
            print(f'  - {p.title}')

asyncio.run(check())
