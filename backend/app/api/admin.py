"""
Admin API endpoints for dashboard, analytics, and system management
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.auth.dependencies import get_current_admin_user
from app.database import get_db
from app.models import User, Event, Recommendation, Product
from app.config import settings
from app.observability.langsmith_client import list_recent_runs
from pydantic import BaseModel


router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Response Models
# ============================================================================

class AdminStats(BaseModel):
    """Admin dashboard statistics"""
    total_users: int
    total_events_7d: int
    total_recommendations: int
    ai_calls: int
    drop_off_risk_count: int
    embedding_failures: int


class PersonaDistribution(BaseModel):
    """Persona distribution counts"""
    distribution: dict[str, int]


class EventVolumePoint(BaseModel):
    """Event volume data point"""
    hour: str
    count: int


class TraceRecord(BaseModel):
    """LangSmith trace record"""
    run_id: str
    name: str
    run_type: str
    status: str
    latency_ms: float
    timestamp: str
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None
    error: Optional[str] = None
    url: Optional[str] = None
    token_usage: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0


# ============================================================================
# Dashboard Stats
# ============================================================================

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user)
):
    """
    Get comprehensive admin dashboard statistics.
    
    Returns:
        AdminStats with 6 key metrics
    """
    ai_calls = 0
    try:
        redis_client = await redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True,
            socket_connect_timeout=1.0
        )
        ai_calls_str = await redis_client.get("ai_call_count")
        ai_calls = int(ai_calls_str) if ai_calls_str else 0
        await redis_client.aclose()
    except Exception as e:
        print(f"Redis unavailable for admin stats: {e}")

    
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    # Total events in last 7 days
    cutoff_7d = datetime.utcnow() - timedelta(days=7)
    events_7d_result = await db.execute(
        select(func.count(Event.id)).where(Event.timestamp >= cutoff_7d)
    )
    total_events_7d = events_7d_result.scalar() or 0

    # Total recommendations generated (all time)
    total_recs_result = await db.execute(select(func.count(Recommendation.id)))
    total_recommendations = total_recs_result.scalar() or 0

    # Drop-off risk count (personas marked as drop_off_risk)
    drop_off_result = await db.execute(
        select(func.count(Recommendation.id)).where(
            Recommendation.persona == "drop_off_risk"
        )
    )
    drop_off_risk_count = drop_off_result.scalar() or 0
    
    # Embedding failures (products with embedding_status = 'failed')
    embedding_failures_result = await db.execute(
        select(func.count(Product.id)).where(
            Product.embedding_status == "failed"
        )
    )
    embedding_failures = embedding_failures_result.scalar() or 0
    
    return AdminStats(
        total_users=total_users,
        total_events_7d=total_events_7d,
        total_recommendations=total_recommendations,
        ai_calls=ai_calls,
        drop_off_risk_count=drop_off_risk_count,
        embedding_failures=embedding_failures
    )


# ============================================================================
# Persona Distribution
# ============================================================================

@router.get("/persona-distribution", response_model=PersonaDistribution)
async def get_persona_distribution(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user)
):
    """
    Get persona distribution across all recommendations.
    
    Returns:
        PersonaDistribution with counts per persona type
    """
    # Query recommendations grouped by persona
    stmt = select(
        Recommendation.persona,
        func.count(Recommendation.id).label('count')
    ).group_by(Recommendation.persona)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Build distribution dict
    distribution = {row.persona: row.count for row in rows}
    
    return PersonaDistribution(distribution=distribution)


# ============================================================================
# Event Volume
# ============================================================================

@router.get("/event-volume", response_model=List[EventVolumePoint])
async def get_event_volume(
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user)
):
    """
    Get event volume over time (hourly aggregation).
    
    Args:
        hours: Number of hours to look back (default: 24, max: 168 = 1 week)
    
    Returns:
        List of EventVolumePoint with hourly event counts
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Query events grouped by hour
    # SQLite uses strftime, PostgreSQL uses date_trunc
    # Using func.date_trunc for PostgreSQL
    stmt = select(
        func.date_trunc('hour', Event.timestamp).label('hour'),
        func.count(Event.id).label('count')
    ).where(
        Event.timestamp >= cutoff
    ).group_by(
        func.date_trunc('hour', Event.timestamp)
    ).order_by(
        func.date_trunc('hour', Event.timestamp)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Format results
    volume_data = [
        EventVolumePoint(
            hour=row.hour.isoformat() if row.hour else "",
            count=row.count
        )
        for row in rows
    ]
    
    return volume_data


# ============================================================================
# LangSmith Traces
# ============================================================================

@router.get("/traces", response_model=List[TraceRecord])
async def get_langsmith_traces(
    limit: int = Query(default=50, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    _admin: User = Depends(get_current_admin_user)
):
    """
    Get recent LangSmith traces for AI workflow monitoring.
    
    Args:
        limit: Maximum number of traces to return (default: 50, max: 100)
        status: Optional filter by status ('success', 'error', 'pending')
    
    Returns:
        List of TraceRecord with run details
    """
    # Fetch traces from LangSmith
    traces = list_recent_runs(limit=limit, status=status)
    
    # Convert to response models
    trace_records = [
        TraceRecord(**trace) for trace in traces
    ]
    
    return trace_records


# ============================================================================
# Recent Recommendations
# ============================================================================

class RecentRecommendation(BaseModel):
    """Recent recommendation summary"""
    id: str
    user_id: str
    user_name: str
    persona: str
    confidence: float
    product_count: int
    generated_at: datetime


@router.get("/recent-recommendations", response_model=List[RecentRecommendation])
async def get_recent_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user)
):
    """
    Get recent recommendations with user info.
    
    Args:
        limit: Maximum recommendations to return (default: 10, max: 50)
    
    Returns:
        List of RecentRecommendation with user and persona data
    """
    # Query recommendations with user join
    stmt = (
        select(Recommendation, User.name)
        .join(User, Recommendation.user_id == User.id)
        .order_by(Recommendation.generated_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Format results
    recent_recs = [
        RecentRecommendation(
            id=str(rec.id),
            user_id=str(rec.user_id),
            user_name=user_name or "Unknown",
            persona=rec.persona,
            confidence=rec.confidence_score,
            product_count=len(rec.product_ids) if rec.product_ids else 0,
            generated_at=rec.generated_at
        )
        for rec, user_name in rows
    ]
    
    return recent_recs


# ============================================================================
# Product Management (Existing endpoints)
# ============================================================================
# Note: These endpoints should already exist in the codebase.
# If not, they need to be created separately.



# ============================================================================
# Product Management
# ============================================================================

class ProductResponse(BaseModel):
    """Product response model"""
    id: str
    title: str
    description: str
    category: str
    price: float
    difficulty_level: str
    duration_hours: float
    tags: List[str]
    embedding_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/products", response_model=List[ProductResponse])
async def get_admin_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get products list for admin dashboard.
    
    Args:
        skip: Number of products to skip
        limit: Maximum products to return
        category: Filter by category
        difficulty: Filter by difficulty level
        db: Database session
        admin: Current admin user
        
    Returns:
        List of products with metadata
    """
    stmt = select(Product)
    
    # Apply filters
    if category:
        stmt = stmt.where(Product.category == category)
    if difficulty:
        from app.models.product import DifficultyLevel
        try:
            difficulty_enum = DifficultyLevel(difficulty.lower())
            stmt = stmt.where(Product.difficulty_level == difficulty_enum)
        except ValueError:
            pass
    
    stmt = stmt.offset(skip).limit(limit).order_by(Product.created_at.desc())
    
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    return [
        ProductResponse(
            id=str(product.id),
            title=product.title,
            description=product.description,
            category=product.category,
            price=float(product.price),
            difficulty_level=product.difficulty_level.value,
            duration_hours=float(product.duration_hours),
            tags=product.tags or [],
            embedding_status=product.embedding_status.value,
            created_at=product.created_at
        )
        for product in products
    ]
