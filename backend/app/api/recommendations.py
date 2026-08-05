"""
Recommendation API endpoints.
Integrates the full LangGraph workflow to deliver personalized recommendations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db, get_redis
from app.models import User
from app.schemas.recommendation import RecommendationResponse, RecommendationHistoryResponse
from app.services.recommendation_service import RecommendationService


router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Rate limiter instance (will use the app-level limiter)
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=RecommendationResponse)
@limiter.limit("10/minute")
async def get_my_recommendations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get personalized recommendations for the current user.
    
    **Smart Caching:**
    - Checks if regeneration needed based on:
      1. Event hash (behavior changed?)
      2. Persona (classification changed?)
      3. Timestamp (stale recommendation?)
    - Returns cached result if still valid (< 15 min, no behavior change)
    - Regenerates on cache miss or invalidation
    
    **Workflow Steps (on regeneration):**
    1. Analyze behavior (72h lookback)
    2. Classify persona (6 types)
    3. Check recovery risk
    4. Plan retrieval (semantic query)
    5. Retrieve candidates (ChromaDB + fallback)
    6. Rank products (6-factor scoring)
    7. Generate narrative (LLM)
    8. Store in database + cache
    
    **Response includes:**
    - Persona classification (confidence score)
    - Top 8 ranked products (with score breakdown)
    - Personalized learning journey narrative
    - Recovery recommendation (if at risk)
    - Trace ID for debugging
    
    **Performance:**
    - Cache hit: < 50ms
    - Cache miss: 1.5-3.5s (LLM-dominated)
    - Cache TTL: 15 minutes
    
    **Error Handling:**
    - Returns 503 if workflow fails AND no cached result
    - Trace ID included in error for support
    """
    
    # Initialize recommendation service with smart caching
    service = RecommendationService(db=db, redis_client=redis_client)
    
    try:
        # Get cached or generate new recommendation
        output = await service.get_or_generate(
            user_id=current_user.id,
            user_name=current_user.name or current_user.email.split("@")[0]
        )
        
        # Build response
        response = RecommendationResponse(
            user_id=str(output.user_id),
            persona=output.persona,
            confidence=output.confidence,
            learning_goal=output.narrative_result.learning_goal,
            personalized_story=output.narrative_result.personalized_story,
            roadmap=output.narrative_result.roadmap,
            product_explanations=output.narrative_result.product_explanations,
            motivational_cta=output.narrative_result.motivational_cta,
            ranked_products=[
                {
                    "product_id": p.product_id,
                    "title": p.title,
                    "description": p.description,
                    "category": p.category,
                    "difficulty": p.difficulty,
                    "price": p.price,
                    "tags": p.tags,
                    "final_score": p.final_score,
                    "rank_position": p.rank_position,
                    "score_breakdown": p.score_breakdown,
                }
                for p in output.ranked_products
            ],
            recovery_result=(
                {
                    "is_at_risk": output.recovery_result.is_at_risk,
                    "recovery_narrative": output.recovery_result.recovery_narrative,
                    "email_subject": output.recovery_result.email_subject,
                    "email_body": output.recovery_result.email_body,
                }
                if output.recovery_result
                else None
            ),
            is_recovery_mode=output.is_recovery_mode,
            generated_at=output.generated_at,
            trace_id=output.trace_id,
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 503 from runner)
        raise
    except Exception as e:
        # Unexpected error - log and return 500
        import traceback
        print(f"Unexpected error in recommendations endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating recommendations"
        )


@router.get("/history", response_model=List[RecommendationHistoryResponse])
async def get_my_recommendation_history(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get recommendation history for the current user.
    
    Returns the last N generated recommendations with:
    - Persona classification
    - Confidence score
    - Product IDs
    - Generation timestamp
    
    Args:
        limit: Max recommendations to return (default 5, max 20)
        
    Returns:
        List of historical recommendations (most recent first)
        
    Example response:
        [
            {
                "id": "uuid",
                "persona": "focused_builder",
                "confidence": 0.85,
                "product_count": 8,
                "generated_at": "2026-08-04T10:30:00Z"
            }
        ]
    """
    # Cap limit at 20
    if limit > 20:
        limit = 20
    
    service = RecommendationService(db=db, redis_client=redis_client)
    history = await service.get_history(current_user.id, limit=limit)
    
    return [
        RecommendationHistoryResponse(
            id=str(rec.id),
            persona=rec.persona,
            confidence=rec.confidence_score,
            product_count=len(rec.product_ids),
            generated_at=rec.generated_at
        )
        for rec in history
    ]


@router.post("/refresh", response_model=RecommendationResponse)
@limiter.limit("5/minute")
async def refresh_my_recommendations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Force refresh recommendations for the current user.
    
    **Behavior:**
    - Invalidates all caches (Redis + PostgreSQL)
    - Generates fresh recommendation (always runs workflow)
    - Stores new result in all caches
    
    **Use cases:**
    - User manually requests refresh
    - User wants to see updated recommendations immediately
    - Testing/debugging
    
    **Performance:**
    - Always runs full workflow: 1.5-3.5s
    - No cache shortcuts
    
    **Rate limiting:**
    - Recommended: 5 requests/minute per user
    - High LLM cost for frequent refreshes
    """
    service = RecommendationService(db=db, redis_client=redis_client)
    
    # Invalidate cache to force regeneration
    await service.invalidate_cache(current_user.id)
    
    try:
        # Generate fresh recommendation
        output = await service.get_or_generate(
            user_id=current_user.id,
            user_name=current_user.name or current_user.email.split("@")[0]
        )
        
        # Build response (same as /me endpoint)
        response = RecommendationResponse(
            user_id=str(output.user_id),
            persona=output.persona,
            confidence=output.confidence,
            learning_goal=output.narrative_result.learning_goal,
            personalized_story=output.narrative_result.personalized_story,
            roadmap=output.narrative_result.roadmap,
            product_explanations=output.narrative_result.product_explanations,
            motivational_cta=output.narrative_result.motivational_cta,
            ranked_products=[
                {
                    "product_id": p.product_id,
                    "title": p.title,
                    "description": p.description,
                    "category": p.category,
                    "difficulty": p.difficulty,
                    "price": p.price,
                    "tags": p.tags,
                    "final_score": p.final_score,
                    "rank_position": p.rank_position,
                    "score_breakdown": p.score_breakdown,
                }
                for p in output.ranked_products
            ],
            recovery_result=(
                {
                    "is_at_risk": output.recovery_result.is_at_risk,
                    "recovery_narrative": output.recovery_result.recovery_narrative,
                    "email_subject": output.recovery_result.email_subject,
                    "email_body": output.recovery_result.email_body,
                }
                if output.recovery_result
                else None
            ),
            is_recovery_mode=output.is_recovery_mode,
            generated_at=output.generated_at,
            trace_id=output.trace_id,
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Unexpected error in refresh endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while refreshing recommendations"
        )


@router.get("/user/{user_id}", response_model=RecommendationResponse)
async def get_user_recommendations(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get recommendations for a specific user (admin only).
    
    **Requires:** Admin role
    **Behavior:** Same smart caching as /me endpoint
    """
    # Validate and fetch target user
    from sqlalchemy import select
    from uuid import UUID
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Use recommendation service with smart caching
    service = RecommendationService(db=db, redis_client=redis_client)
    
    try:
        # Get cached or generate new recommendation
        output = await service.get_or_generate(
            user_id=target_user.id,
            user_name=target_user.name or target_user.email.split("@")[0]
        )
        
        # Build response (same as /me)
        response = RecommendationResponse(
            user_id=str(output.user_id),
            persona=output.persona,
            confidence=output.confidence,
            learning_goal=output.narrative_result.learning_goal,
            personalized_story=output.narrative_result.personalized_story,
            roadmap=output.narrative_result.roadmap,
            product_explanations=output.narrative_result.product_explanations,
            motivational_cta=output.narrative_result.motivational_cta,
            ranked_products=[
                {
                    "product_id": p.product_id,
                    "title": p.title,
                    "description": p.description,
                    "category": p.category,
                    "difficulty": p.difficulty,
                    "price": p.price,
                    "tags": p.tags,
                    "final_score": p.final_score,
                    "rank_position": p.rank_position,
                    "score_breakdown": p.score_breakdown,
                }
                for p in output.ranked_products
            ],
            recovery_result=(
                {
                    "is_at_risk": output.recovery_result.is_at_risk,
                    "recovery_narrative": output.recovery_result.recovery_narrative,
                    "email_subject": output.recovery_result.email_subject,
                    "email_body": output.recovery_result.email_body,
                }
                if output.recovery_result
                else None
            ),
            is_recovery_mode=output.is_recovery_mode,
            generated_at=output.generated_at,
            trace_id=output.trace_id,
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Unexpected error in recommendations endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating recommendations"
        )
