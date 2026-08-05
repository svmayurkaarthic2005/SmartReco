import asyncio
from sqlalchemy import select, func
from app.database.base import get_async_session
from app.models.event import Event

async def check():
    session = get_async_session()
    async with session as db:
        # Get event types count
        result = await db.execute(
            select(Event.event_type, func.count(Event.id))
            .group_by(Event.event_type)
            .order_by(func.count(Event.id).desc())
        )
        print('Event types in database:')
        for row in result:
            print(f'  {row[0]}: {row[1]} events')
        
        # Get latest 5 events
        print('\nLatest 5 events:')
        result = await db.execute(
            select(Event)
            .order_by(Event.timestamp.desc())
            .limit(5)
        )
        events = result.scalars().all()
        for evt in events:
            print(f'  [{evt.timestamp}] {evt.event_type} - product_id={evt.product_id}')

asyncio.run(check())
