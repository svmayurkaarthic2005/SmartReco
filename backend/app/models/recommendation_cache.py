"""Recommendation cache model"""

import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import String, DateTime, ForeignKey, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.database.base import Base



class RecommendationCache(Base):
    """Cache model for storing recommendation results"""
    __tablename__ = "recommendation_cache"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    event_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    cached_recommendation: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, 'postgresql'),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<RecommendationCache(user_id={self.user_id}, expires_at={self.expires_at})>"
