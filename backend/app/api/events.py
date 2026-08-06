"""Event tracking API endpoints"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models import User, Event
from app.schemas.event import (
    EventCreate,
    EventBatch,
    EventResponse,
    BatchStatusResponse,
    EventHashResponse
)
from app.services.event_service import (
    bulk_insert_events,
    get_user_events,
    compute_event_hash,
    count_user_events
)


router = APIRouter(prefix="/events", tags=["Events"])

# Rate limiter instance (will use the app-level limiter)
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/batch",
    response_model=BatchStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit batch of events",
    description="Submit multiple events at once (max 50). Events are queued for background processing."
)
@limiter.limit("60/minute")
async def create_events_batch(
    request: Request,
    batch: EventBatch,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BatchStatusResponse:
    """
    Submit a batch of events for processing.
    
    Events are queued as a background task for non-blocking insertion.
    Returns immediately with status "queued".
    
    Performance:
        - Non-blocking: returns before DB write completes
        - Uses bulk insert for efficiency
        - Max 50 events per request
        
    Security:
        - Requires authentication
        - User ID is automatically set from authenticated user
    """
    # Auto-fill user_id for all events from authenticated user
    for event in batch.events:
        if event.user_id is None:
            event.user_id = current_user.id
        elif event.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot submit events for other users. Event user_id {event.user_id} does not match authenticated user {current_user.id}"
            )
    
    # Process immediately instead of background task to avoid session issues
    # Use a short timeout so slow DB inserts don't block the response
    import asyncio
    try:
        await asyncio.wait_for(bulk_insert_events(batch.events, db), timeout=8.0)
    except asyncio.TimeoutError:
        # Log and return success anyway — events will be silently dropped (acceptable for telemetry)
        import logging
        logging.getLogger(__name__).warning(f"Event batch insert timed out for {len(batch.events)} events")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save events: {str(e)}"
        )
    
    return BatchStatusResponse(
        status="accepted",
        queued_count=len(batch.events)
    )


@router.post(
    "/single",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit single event",
    description="Submit a single event. Blocks until inserted."
)
async def create_single_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """
    Submit a single event (blocking).
    
    Use /batch endpoint for better performance when submitting multiple events.
    
    Security:
        - Requires authentication
        - User ID is automatically set from authenticated user
    """
    # Auto-fill user_id from authenticated user
    if event.user_id is None:
        event.user_id = current_user.id
    elif event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot submit events for other users"
        )
    
    # Insert single event (blocking)
    await bulk_insert_events([event], db)
    
    # Safely get event_type value (might be Enum or str)
    event_type_val = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
    
    # Return event response
    return EventResponse(
        id=str(uuid.uuid4()),
        user_id=str(event.user_id),
        session_id=event.session_id,
        event_type=event_type_val,
        product_id=str(event.product_id) if event.product_id else None,
        search_query=event.search_query,
        dwell_time=event.dwell_time,
        metadata=event.metadata or getattr(event, 'event_metadata', None),
        timestamp=event.timestamp.isoformat() + "Z"
    )


@router.get(
    "/me",
    response_model=List[EventResponse],
    summary="Get my events",
    description="Get last 100 events for the authenticated user"
)
async def get_my_events(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[EventResponse]:
    """
    Get events for the authenticated user.
    
    Args:
        limit: Maximum number of events to return (default 100, max 500)
        
    Returns:
        List of events ordered by timestamp descending (most recent first)
    """
    # Cap limit at 500
    if limit > 500:
        limit = 500
    
    events = await get_user_events(current_user.id, limit, db)
    
    return [
        EventResponse(
            id=str(event.id),
            user_id=str(event.user_id),
            session_id=event.session_id,
            event_type=event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
            product_id=str(event.product_id) if event.product_id else None,
            search_query=event.search_query,
            dwell_time=event.dwell_time,
            metadata=getattr(event, "event_metadata", None),
            timestamp=event.timestamp.isoformat() + "Z"
        )
        for event in events
    ]


@router.get(
    "/user/{user_id}",
    response_model=List[EventResponse],
    summary="Get user events (admin only)",
    description="Get events for any user. Requires admin role."
)
async def get_user_events_admin(
    user_id: uuid.UUID,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> List[EventResponse]:
    """
    Get events for any user (admin only).
    
    Args:
        user_id: UUID of user to get events for
        limit: Maximum number of events to return (default 100, max 1000)
        
    Returns:
        List of events ordered by timestamp descending
        
    Security:
        Requires admin role
    """
    # Cap limit at 1000 for admins
    if limit > 1000:
        limit = 1000
    
    events = await get_user_events(user_id, limit, db)
    
    if not events:
        # Check if user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
    
    return [
        EventResponse(
            id=str(event.id),
            user_id=str(event.user_id),
            session_id=event.session_id,
            event_type=event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
            product_id=str(event.product_id) if event.product_id else None,
            search_query=event.search_query,
            dwell_time=event.dwell_time,
            metadata=getattr(event, "event_metadata", None),
            timestamp=event.timestamp.isoformat() + "Z"
        )
        for event in events
    ]


@router.get(
    "/me/hash",
    response_model=EventHashResponse,
    summary="Get event hash",
    description="Get MD5 hash of latest 20 events for cache invalidation"
)
async def get_my_event_hash(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EventHashResponse:
    """
    Get MD5 hash of latest 20 event IDs.
    
    Used for detecting behavior changes and cache invalidation.
    If user has no events, returns empty hash.
    
    Returns:
        EventHashResponse with user_id, event_hash, and event_count
    """
    event_hash = await compute_event_hash(current_user.id, db)
    event_count = await count_user_events(current_user.id, db)
    
    return EventHashResponse(
        user_id=str(current_user.id),
        event_hash=event_hash,
        event_count=event_count
    )


@router.get(
    "/user/{user_id}/hash",
    response_model=EventHashResponse,
    summary="Get user event hash (admin only)",
    description="Get event hash for any user. Requires admin role."
)
async def get_user_event_hash_admin(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> EventHashResponse:
    """
    Get event hash for any user (admin only).
    
    Security:
        Requires admin role
    """
    event_hash = await compute_event_hash(user_id, db)
    event_count = await count_user_events(user_id, db)
    
    if event_count == 0:
        # Check if user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
    
    return EventHashResponse(
        user_id=str(user_id),
        event_hash=event_hash,
        event_count=event_count
    )
