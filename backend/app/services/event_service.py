"""Event tracking service layer"""

import hashlib
import uuid
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event, EventType
from app.schemas.event import EventCreate


logger = logging.getLogger(__name__)


async def bulk_insert_events(
    events: List[EventCreate],
    db: AsyncSession
) -> None:
    """
    Bulk insert events using SQLAlchemy core insert() for performance.
    
    Args:
        events: List of EventCreate schemas
        db: Database session
        
    Performance:
        Uses single INSERT with multiple VALUES for efficiency.
        Significantly faster than ORM add() for bulk operations.
        
    Example:
        >>> events = [EventCreate(user_id=uuid4(), session_id="abc", event_type="view_product")]
        >>> await bulk_insert_events(events, db)
    """
    if not events:
        return
    
    try:
        # Convert Pydantic models to dict for bulk insert (ignoring scroll events)
        event_dicts = []
        for event in events:
            if event.event_type in (EventType.SCROLL, 'scroll'):
                continue
            
            # Handle timestamp - convert to naive UTC if timezone-aware
            timestamp = event.timestamp if event.timestamp else datetime.utcnow()
            if timestamp.tzinfo is not None:
                # Convert timezone-aware to naive UTC
                timestamp = timestamp.replace(tzinfo=None)
            
            event_dict = {
                "id": uuid.uuid4(),
                "user_id": event.user_id,
                "session_id": event.session_id,
                "event_type": event.event_type,
                "product_id": event.product_id,
                "search_query": event.search_query,
                "dwell_time": event.dwell_time,
                "event_metadata": event.metadata or getattr(event, 'event_metadata', None),
                "timestamp": timestamp
            }
            event_dicts.append(event_dict)
        
        if not event_dicts:
            return

        # Bulk insert using SQLAlchemy core
        stmt = insert(Event).values(event_dicts)
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Successfully inserted {len(event_dicts)} events")
        
    except Exception as e:
        logger.error(f"Failed to insert events: {e}", exc_info=True)
        await db.rollback()
        raise


async def get_user_events(
    user_id: uuid.UUID,
    limit: int = 100,
    db: AsyncSession = None
) -> List[Event]:
    """
    Get events for a specific user, ordered by timestamp descending (excluding scroll events).
    """
    stmt = (
        select(Event)
        .where(Event.user_id == user_id)
        .where(Event.event_type != EventType.SCROLL)
        .order_by(Event.timestamp.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    return list(events)


async def get_user_events_by_type(
    user_id: uuid.UUID,
    event_type: EventType,
    limit: int = 100,
    db: AsyncSession = None
) -> List[Event]:
    """
    Get events for a specific user filtered by event type.
    
    Args:
        user_id: User UUID
        event_type: EventType to filter by
        limit: Maximum number of events to return
        db: Database session
        
    Returns:
        List of Event ORM objects
    """
    stmt = (
        select(Event)
        .where(Event.user_id == user_id)
        .where(Event.event_type == event_type)
        .order_by(Event.timestamp.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    return list(events)


async def compute_event_hash(
    user_id: uuid.UUID,
    db: AsyncSession
) -> str:
    """
    Compute MD5 hash of latest 20 event IDs concatenated.
    
    This hash can be used to detect changes in user behavior for cache invalidation.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        MD5 hash string (32 characters hex)
        Empty string if user has no events
        
    Example:
        >>> hash_val = await compute_event_hash(user_id, db)
        >>> len(hash_val) == 32 or len(hash_val) == 0
        True
    """
    # Get latest 20 event IDs
    stmt = (
        select(Event.id)
        .where(Event.user_id == user_id)
        .order_by(Event.timestamp.desc())
        .limit(20)
    )
    
    result = await db.execute(stmt)
    event_ids = result.scalars().all()
    
    if not event_ids:
        return ""
    
    # Concatenate event IDs and compute MD5
    concatenated = "".join(str(event_id) for event_id in event_ids)
    hash_object = hashlib.md5(concatenated.encode())
    
    return hash_object.hexdigest()


async def get_session_events(
    session_id: str,
    db: AsyncSession
) -> List[Event]:
    """
    Get all events for a specific session.
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        List of Event ORM objects ordered by timestamp
    """
    stmt = (
        select(Event)
        .where(Event.session_id == session_id)
        .order_by(Event.timestamp.asc())
    )
    
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    return list(events)


async def count_user_events(
    user_id: uuid.UUID,
    db: AsyncSession
) -> int:
    """
    Count total events for a user.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        Total event count
    """
    from sqlalchemy import func
    
    stmt = select(func.count(Event.id)).where(Event.user_id == user_id)
    result = await db.execute(stmt)
    count = result.scalar_one()
    
    return count


async def delete_old_events(
    days_to_keep: int,
    db: AsyncSession
) -> int:
    """
    Delete events older than specified days (for data retention).
    
    Args:
        days_to_keep: Number of days to retain
        db: Database session
        
    Returns:
        Number of deleted events
    """
    from datetime import timedelta
    from sqlalchemy import delete
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    stmt = delete(Event).where(Event.timestamp < cutoff_date)
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount
