"""Event tracking schemas"""

import html
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.models.event import EventType


class EventCreate(BaseModel):
    """Schema for creating a new event"""
    user_id: Optional[uuid.UUID] = Field(None, description="User ID (auto-filled from auth)")
    session_id: str = Field(..., min_length=1, max_length=255, description="Session ID")
    event_type: EventType = Field(..., description="Type of event")
    product_id: Optional[uuid.UUID] = Field(None, description="Product ID (optional)")
    search_query: Optional[str] = Field(None, max_length=200, description="Search query text")
    dwell_time: Optional[float] = Field(None, ge=0, description="Time spent in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    @field_validator("search_query")
    @classmethod
    def strip_html_tags(cls, v: Optional[str]) -> Optional[str]:
        """
        Sanitize search query for security.
        - Strips HTML tags
        - Escapes special characters
        - Max length enforced by Field(max_length=200)
        """
        if v is None:
            return v
        # Remove HTML tags using regex
        clean = re.sub(r'<[^>]+>', '', v)
        # Escape HTML special characters (&, <, >, ", ')
        clean = html.escape(clean)
        # Trim whitespace
        clean = clean.strip()
        return clean if clean else None
    
    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID is not empty"""
        if not v or not v.strip():
            raise ValueError("Session ID cannot be empty")
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "event_type": "view_product",
                    "product_id": "789e4567-e89b-12d3-a456-426614174999",
                    "timestamp": "2026-08-04T10:30:00"
                },
                {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "event_type": "search",
                    "search_query": "Python machine learning",
                    "timestamp": "2026-08-04T10:31:00"
                },
                {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "event_type": "time_on_page",
                    "dwell_time": 45.5,
                    "metadata": {"page_url": "/courses/123"},
                    "timestamp": "2026-08-04T10:32:00"
                }
            ]
        }
    }


class EventBatch(BaseModel):
    """Schema for batch event submission"""
    events: list[EventCreate] = Field(..., max_length=50, description="List of events (max 50)")
    
    @field_validator("events")
    @classmethod
    def validate_events_not_empty(cls, v: list[EventCreate]) -> list[EventCreate]:
        """Ensure events list is not empty"""
        if not v:
            raise ValueError("Events list cannot be empty")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "events": [
                        {
                            "user_id": "123e4567-e89b-12d3-a456-426614174000",
                            "session_id": "550e8400-e29b-41d4-a716-446655440000",
                            "event_type": "view_product",
                            "product_id": "789e4567-e89b-12d3-a456-426614174999"
                        },
                        {
                            "user_id": "123e4567-e89b-12d3-a456-426614174000",
                            "session_id": "550e8400-e29b-41d4-a716-446655440000",
                            "event_type": "scroll",
                            "metadata": {"depth_percent": 75}
                        }
                    ]
                }
            ]
        }
    }


class EventResponse(BaseModel):
    """Schema for event response"""
    id: str  # UUID as string
    user_id: str  # UUID as string
    session_id: str
    event_type: str
    product_id: Optional[str] = None  # UUID as string
    search_query: Optional[str] = None
    dwell_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str  # ISO format datetime string
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "456e4567-e89b-12d3-a456-426614174111",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "event_type": "view_product",
                    "product_id": "789e4567-e89b-12d3-a456-426614174999",
                    "timestamp": "2026-08-04T10:30:00"
                }
            ]
        }
    }


class BatchStatusResponse(BaseModel):
    """Response for batch event submission"""
    status: str = Field(..., description="Status of batch submission")
    queued_count: int = Field(..., description="Number of events queued")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "queued",
                    "queued_count": 15
                }
            ]
        }
    }


class EventHashResponse(BaseModel):
    """Response for event hash computation"""
    user_id: str
    event_hash: str
    event_count: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "event_hash": "5d41402abc4b2a76b9719d911017c592",
                    "event_count": 20
                }
            ]
        }
    }
