"""Event model for user interaction tracking"""

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON, UUID
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database.base import Base



class EventType(str, enum.Enum):
    """User event type enumeration"""
    VIEW_PRODUCT = "view_product"
    VIEW_CATEGORY = "view_category"
    SEARCH = "search"
    ADD_TO_CART = "add_to_cart"
    WISHLIST = "wishlist"
    ENROLL = "enroll"
    SCROLL = "scroll"
    TIME_ON_PAGE = "time_on_page"
    REPEAT_VISIT = "repeat_visit"
    CATEGORY_SWITCH = "category_switch"
    SESSION_END = "session_end"
    EXIT = "exit"


class Event(Base):
    """Event model for tracking user interactions"""
    __tablename__ = "events"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType, name="event_type", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    search_query: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    dwell_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, 'postgresql'),
        nullable=True
    )


    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="events"
    )
    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        back_populates="events"
    )
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, user_id={self.user_id}, event_type={self.event_type})>"
