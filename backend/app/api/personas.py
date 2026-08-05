"""Persona and behavior analysis API endpoints"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models import User
from app.agents import BehaviorAgent, PersonaAgent
from app.schemas.persona import (
    BehaviorSummaryResponse,
    PersonaResponse,
    UserAnalysisResponse
)


router = APIRouter(prefix="/personas", tags=["Personas"])


@router.get(
    "/behavior/me",
    response_model=BehaviorSummaryResponse,
    summary="Get my behavior analysis",
    description="Analyze authenticated user's behavioral patterns from event data"
)
async def get_my_behavior(
    lookback_hours: int = Query(
        default=72,
        ge=1,
        le=720,
        description="Hours of history to analyze (1-720, default: 72)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BehaviorSummaryResponse:
    """
    Analyze authenticated user's behavior.
    
    Args:
        lookback_hours: Hours of event history to analyze (default: 72 = 3 days)
        
    Returns:
        BehaviorSummaryResponse with aggregated behavioral metrics
    """
    # Create behavior agent
    behavior_agent = BehaviorAgent(db)
    
    # Analyze user behavior
    summary = await behavior_agent.analyze(current_user.id, lookback_hours)
    
    # Convert to response schema
    return BehaviorSummaryResponse(
        user_id=summary.user_id,
        total_events=summary.total_events,
        unique_products_viewed=summary.unique_products_viewed,
        categories_explored=summary.categories_explored,
        search_queries=summary.search_queries,
        avg_dwell_time=summary.avg_dwell_time,
        cart_events=summary.cart_events,
        wishlist_events=summary.wishlist_events,
        enrollment_events=summary.enrollment_events,
        repeat_visits=summary.repeat_visits,
        category_switches=summary.category_switches,
        session_durations=summary.session_durations,
        scroll_depth_avg=summary.scroll_depth_avg,
        exit_events=summary.exit_events,
        recent_event_types=summary.recent_event_types
    )


@router.get(
    "/behavior/user/{user_id}",
    response_model=BehaviorSummaryResponse,
    summary="Get user behavior (admin only)",
    description="Analyze any user's behavioral patterns. Requires admin role."
)
async def get_user_behavior(
    user_id: uuid.UUID,
    lookback_hours: int = Query(
        default=72,
        ge=1,
        le=720,
        description="Hours of history to analyze"
    ),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> BehaviorSummaryResponse:
    """
    Analyze any user's behavior (admin only).
    
    Security:
        Requires admin role
    """
    # Verify user exists
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Create behavior agent
    behavior_agent = BehaviorAgent(db)
    
    # Analyze user behavior
    summary = await behavior_agent.analyze(user_id, lookback_hours)
    
    # Convert to response schema
    return BehaviorSummaryResponse(
        user_id=summary.user_id,
        total_events=summary.total_events,
        unique_products_viewed=summary.unique_products_viewed,
        categories_explored=summary.categories_explored,
        search_queries=summary.search_queries,
        avg_dwell_time=summary.avg_dwell_time,
        cart_events=summary.cart_events,
        wishlist_events=summary.wishlist_events,
        enrollment_events=summary.enrollment_events,
        repeat_visits=summary.repeat_visits,
        category_switches=summary.category_switches,
        session_durations=summary.session_durations,
        scroll_depth_avg=summary.scroll_depth_avg,
        exit_events=summary.exit_events,
        recent_event_types=summary.recent_event_types
    )


@router.get(
    "/classify/me",
    response_model=PersonaResponse,
    summary="Get my persona classification",
    description="Classify authenticated user into behavioral persona"
)
async def get_my_persona(
    lookback_hours: int = Query(
        default=72,
        ge=1,
        le=720,
        description="Hours of history to analyze"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PersonaResponse:
    """
    Classify authenticated user into persona.
    
    Personas:
    - EXPLORER: Browses widely, low commitment
    - FOCUSED_BUILDER: Deep engagement in one area
    - CAREER_SWITCHER: Exploring new fields
    - PRICE_SENSITIVE: Evaluates options, doesn't purchase
    - OVERWHELMED_LEARNER: Views advanced content but doesn't engage
    - DROP_OFF_RISK: High exit rate, low engagement
    
    Returns:
        PersonaResponse with persona type, confidence, reasoning, and strategy
    """
    # Analyze behavior first
    behavior_agent = BehaviorAgent(db)
    summary = await behavior_agent.analyze(current_user.id, lookback_hours)
    
    # Classify into persona
    persona_agent = PersonaAgent()
    result = await persona_agent.classify(summary)
    
    # Close Redis connection
    await persona_agent.close()
    
    # Convert to response schema
    return PersonaResponse(
        persona=result.persona.value,
        confidence=result.confidence,
        reasoning=result.reasoning,
        recommended_strategy=result.recommended_strategy
    )


@router.get(
    "/classify/user/{user_id}",
    response_model=PersonaResponse,
    summary="Get user persona (admin only)",
    description="Classify any user into behavioral persona. Requires admin role."
)
async def get_user_persona(
    user_id: uuid.UUID,
    lookback_hours: int = Query(
        default=72,
        ge=1,
        le=720,
        description="Hours of history to analyze"
    ),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> PersonaResponse:
    """
    Classify any user into persona (admin only).
    
    Security:
        Requires admin role
    """
    # Verify user exists
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Analyze behavior first
    behavior_agent = BehaviorAgent(db)
    summary = await behavior_agent.analyze(user_id, lookback_hours)
    
    # Classify into persona
    persona_agent = PersonaAgent()
    result = await persona_agent.classify(summary)
    
    # Close Redis connection
    await persona_agent.close()
    
    # Convert to response schema
    return PersonaResponse(
        persona=result.persona.value,
        confidence=result.confidence,
        reasoning=result.reasoning,
        recommended_strategy=result.recommended_strategy
    )


@router.get(
    "/analyze/me",
    response_model=UserAnalysisResponse,
    summary="Get complete analysis (behavior + persona)",
    description="Get both behavioral analysis and persona classification in one call"
)
async def get_my_analysis(
    lookback_hours: int = Query(
        default=72,
        ge=1,
        le=720,
        description="Hours of history to analyze"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserAnalysisResponse:
    """
    Get complete user analysis (behavior + persona).
    
    More efficient than calling both endpoints separately.
    """
    # Analyze behavior
    behavior_agent = BehaviorAgent(db)
    summary = await behavior_agent.analyze(current_user.id, lookback_hours)
    
    # Classify persona
    persona_agent = PersonaAgent()
    persona_result = await persona_agent.classify(summary)
    
    # Close Redis connection
    await persona_agent.close()
    
    # Convert to response schemas
    behavior_response = BehaviorSummaryResponse(
        user_id=summary.user_id,
        total_events=summary.total_events,
        unique_products_viewed=summary.unique_products_viewed,
        categories_explored=summary.categories_explored,
        search_queries=summary.search_queries,
        avg_dwell_time=summary.avg_dwell_time,
        cart_events=summary.cart_events,
        wishlist_events=summary.wishlist_events,
        enrollment_events=summary.enrollment_events,
        repeat_visits=summary.repeat_visits,
        category_switches=summary.category_switches,
        session_durations=summary.session_durations,
        scroll_depth_avg=summary.scroll_depth_avg,
        exit_events=summary.exit_events,
        recent_event_types=summary.recent_event_types
    )
    
    persona_response = PersonaResponse(
        persona=persona_result.persona.value,
        confidence=persona_result.confidence,
        reasoning=persona_result.reasoning,
        recommended_strategy=persona_result.recommended_strategy
    )
    
    return UserAnalysisResponse(
        behavior=behavior_response,
        persona=persona_response
    )


@router.get(
    "/analyze/user/{user_id}",
    response_model=UserAnalysisResponse,
    summary="Get complete user analysis (admin only)",
    description="Get both behavioral analysis and persona classification for any user"
)
async def get_user_analysis(
    user_id: uuid.UUID,
    lookback_hours: int = Query(
        default=72,
        ge=1,
        le=720,
        description="Hours of history to analyze"
    ),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> UserAnalysisResponse:
    """
    Get complete user analysis (admin only).
    
    Security:
        Requires admin role
    """
    # Verify user exists
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Analyze behavior
    behavior_agent = BehaviorAgent(db)
    summary = await behavior_agent.analyze(user_id, lookback_hours)
    
    # Classify persona
    persona_agent = PersonaAgent()
    persona_result = await persona_agent.classify(summary)
    
    # Close Redis connection
    await persona_agent.close()
    
    # Convert to response schemas
    behavior_response = BehaviorSummaryResponse(
        user_id=summary.user_id,
        total_events=summary.total_events,
        unique_products_viewed=summary.unique_products_viewed,
        categories_explored=summary.categories_explored,
        search_queries=summary.search_queries,
        avg_dwell_time=summary.avg_dwell_time,
        cart_events=summary.cart_events,
        wishlist_events=summary.wishlist_events,
        enrollment_events=summary.enrollment_events,
        repeat_visits=summary.repeat_visits,
        category_switches=summary.category_switches,
        session_durations=summary.session_durations,
        scroll_depth_avg=summary.scroll_depth_avg,
        exit_events=summary.exit_events,
        recent_event_types=summary.recent_event_types
    )
    
    persona_response = PersonaResponse(
        persona=persona_result.persona.value,
        confidence=persona_result.confidence,
        reasoning=persona_result.reasoning,
        recommended_strategy=persona_result.recommended_strategy
    )
    
    return UserAnalysisResponse(
        behavior=behavior_response,
        persona=persona_response
    )
