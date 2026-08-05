"""Recommendation model"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base



class Recommendation(Base):
    """Recommendation model for storing generated recommendations"""
    __tablename__ = "recommendations"
    
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
    persona: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    product_ids: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )
    narrative_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="recommendations"
    )
    
    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, user_id={self.user_id}, confidence={self.confidence_score})>"
