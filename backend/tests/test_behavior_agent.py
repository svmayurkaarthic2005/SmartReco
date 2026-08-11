"""Unit tests for BehaviorAgent unenroll and event ordering logic"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.agents.behavior_agent import BehaviorAgent
from app.models.event import Event, EventType


@pytest.mark.asyncio
async def test_unenroll_event_aggregation_order():
    """Verify that unenrollment correctly removes course from enrolled_product_ids when processed"""
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_res

    agent = BehaviorAgent(db=mock_db)
    
    user_id = uuid.uuid4()
    prod_id = uuid.uuid4()
    
    t0 = datetime.utcnow() - timedelta(minutes=10)
    t1 = datetime.utcnow()

    # Event 0 in DB (newest): UNENROLL at t1
    # Event 1 in DB (oldest): ENROLL at t0
    # get_user_events returns events in DESCENDING timestamp order (newest first)
    events_descending = [
        Event(
            id=uuid.uuid4(),
            user_id=user_id,
            session_id="sess-2",
            event_type=EventType.UNENROLL,
            product_id=prod_id,
            event_metadata={"course_title": "Python 101", "category": "Programming"},
            timestamp=t1
        ),
        Event(
            id=uuid.uuid4(),
            user_id=user_id,
            session_id="sess-1",
            event_type=EventType.ENROLL,
            product_id=prod_id,
            event_metadata={"course_title": "Python 101", "category": "Programming"},
            timestamp=t0
        )
    ]

    summary = await agent._aggregate_events(str(user_id), events_descending)

    # Since the latest event was UNENROLL, the course should NOT be in enrolled_product_ids
    assert str(prod_id) not in summary.enrolled_product_ids
    assert "Python 101" not in summary.enrolled_product_titles
    # The course SHOULD be in unenrolled_product_ids
    assert str(prod_id) in summary.unenrolled_product_ids
    assert "Python 101" in summary.unenrolled_product_titles
    assert summary.unenrollment_events == 1
