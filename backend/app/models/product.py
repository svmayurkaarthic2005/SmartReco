"""Product model"""

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, Float, DateTime, ARRAY, JSON, UUID
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base




class DifficultyLevel(str, enum.Enum):
    """Product difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EmbeddingStatus(str, enum.Enum):
    """Embedding indexing status"""
    INDEXED = "indexed"
    PENDING = "pending"
    FAILED = "failed"


class Product(Base):
    """Product (course/content) model"""
    __tablename__ = "products"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SQLEnum(DifficultyLevel, name="difficulty_level", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    tags: Mapped[List[str]] = mapped_column(
        JSON().with_variant(ARRAY(String), 'postgresql'),
        nullable=False,
        default=list
    )
    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        SQLEnum(EmbeddingStatus, name="embedding_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        default=EmbeddingStatus.PENDING,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="product",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title={self.title}, category={self.category})>"
