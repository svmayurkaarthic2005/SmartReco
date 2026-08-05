"""
Recommendation service with smart caching and storage.

Implements intelligent cache invalidation based on:
- Event hash changes (new user behavior)
- Persona changes (behavioral shift)
- Time expiration (15 minutes)
"""

import json
import logging
import uuid
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.models.recommendation import Recommendation
from app.models.recommendation_cache import RecommendationCache

logger = logging.getLogger(__name__)
from app.services.event_service import compute_event_hash
from app.langgraph.runner import WorkflowRunner, RecommendationOutput

# Per-user generation locks to prevent duplicate concurrent workflow runs.
# When two requests arrive simultaneously (e.g. React StrictMode double-render),
# only the first acquires the lock and runs the workflow; the second waits, then
# reads the result from the cache the first one already stored.
_generation_locks: dict[str, asyncio.Lock] = {}
_generation_locks_meta_lock = asyncio.Lock()


async def _get_user_lock(user_id: str) -> asyncio.Lock:
    """Get or create a per-user asyncio lock (thread-safe)."""
    async with _generation_locks_meta_lock:
        if user_id not in _generation_locks:
            _generation_locks[user_id] = asyncio.Lock()
        return _generation_locks[user_id]



class RecommendationService:
    """
    Service for managing recommendation generation, storage, and caching.
    
    Smart regeneration logic:
    1. Check event hash (user behavior changed?)
    2. Check persona (classification changed?)
    3. Check timestamp (stale recommendation?)
    
    Storage layers:
    - Redis: Fast cache with 15min TTL
    - PostgreSQL recommendation_cache: Persistent cache with event_hash
    - PostgreSQL recommendations: Historical record
    """
    
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        """
        Initialize recommendation service.
        
        Args:
            db: Async SQLAlchemy session
            redis_client: Async Redis client
        """
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 900  # 15 minutes in seconds
    
    async def should_regenerate(self, user_id: uuid.UUID) -> bool:
        """
        Determine if recommendation should be regenerated.
        
        Returns True if ANY of these conditions are met:
        1. No cache exists (cache miss)
        2. Event hash differs (user behavior changed)
        3. Cached persona differs from current persona (persona changed)
        4. Cache older than 15 minutes (stale)
        
        Args:
            user_id: User UUID
            
        Returns:
            True if should regenerate, False if cache is valid
            
        Example:
            >>> service = RecommendationService(db, redis)
            >>> should_regen = await service.should_regenerate(user_id)
            >>> if should_regen:
            ...     output = await service.get_or_generate(user_id)
        """
        # 1. Compute current event hash
        current_event_hash = await compute_event_hash(user_id, self.db)
        
        # 2. Check Redis cache
        cache_key = f"reco_cache:{user_id}"
        try:
            cached_json = await self.redis.get(cache_key)
        except Exception:
            # Redis unavailable → regenerate
            return True
        
        # Cache miss → regenerate
        if not cached_json:
            return True
        
        # Parse cached data
        try:
            cached_data = json.loads(cached_json)
        except json.JSONDecodeError:
            # Corrupted cache → regenerate
            return True
        
        # 3. Check event hash match
        cached_event_hash = cached_data.get("event_hash", "")
        if cached_event_hash != current_event_hash:
            # User behavior changed → regenerate
            return True
        
        # 4. Check persona match
        persona_key = f"persona:{user_id}"
        try:
            current_persona_json = await self.redis.get(persona_key)
        except Exception:
            current_persona_json = None
        
        if current_persona_json:
            try:
                current_persona_data = json.loads(current_persona_json)
                current_persona = current_persona_data.get("persona")
                cached_persona = cached_data.get("persona")
                
                if current_persona and cached_persona and current_persona != cached_persona:
                    # Persona changed → regenerate
                    return True
            except json.JSONDecodeError:
                pass  # Can't compare, continue with time check
        
        # 5. Check timestamp (15 min expiration)
        generated_at_str = cached_data.get("generated_at")
        if generated_at_str:
            try:
                # Parse ISO format; strip timezone info for naive UTC comparison
                generated_at_raw = datetime.fromisoformat(generated_at_str.replace('Z', '+00:00'))
                # Normalize to naive UTC (remove tzinfo if present)
                if generated_at_raw.tzinfo is not None:
                    from datetime import timezone
                    generated_at = generated_at_raw.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    generated_at = generated_at_raw
                now = datetime.utcnow()
                age = (now - generated_at).total_seconds()
                
                if age > self.cache_ttl:
                    # Stale cache → regenerate
                    return True
            except (ValueError, TypeError):
                # Can't parse timestamp → regenerate to be safe
                return True
        
        # Cache is valid
        return False
    
    async def get_or_generate(
        self,
        user_id: uuid.UUID,
        user_name: Optional[str] = None
    ) -> RecommendationOutput:
        """
        Get cached recommendation or generate new one.
        
        Smart logic:
        - If cache is valid → deserialize and return
        - If should regenerate → run workflow, store, cache, return
        
        Args:
            user_id: User UUID
            user_name: User name for personalization (optional)
            
        Returns:
            RecommendationOutput with full recommendation data
            
        Raises:
            HTTPException: If workflow fails and no cache available
            
        Example:
            >>> service = RecommendationService(db, redis)
            >>> output = await service.get_or_generate(user_id, "John")
            >>> print(output.persona)
            focused_builder
        """
        # Check if regeneration is needed
        needs_regeneration = await self.should_regenerate(user_id)
        
        if not needs_regeneration:
            # Load from Redis cache
            try:
                cache_key = f"reco_cache:{user_id}"
                cached_json = await self.redis.get(cache_key)
                
                if cached_json:
                    try:
                        cached_data = json.loads(cached_json)
                        
                        # Deserialize to RecommendationOutput
                        output = self._deserialize_output(cached_data)
                        return output
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        # Cache corrupted, fall through to regeneration
                        logger.warning(f"Cache deserialization failed: {e}")
            except Exception as e:
                # Redis unavailable, fall through to regeneration
                logger.warning(f"Redis cache read failed: {e}")
        
        # Acquire per-user lock to prevent duplicate concurrent workflow runs.
        # If two requests arrive simultaneously, the second one waits here, then
        # re-checks the cache after the first finishes — avoiding a double LLM call.
        user_lock = await _get_user_lock(str(user_id))
        async with user_lock:
            # Re-check after acquiring lock (another coroutine may have just generated)
            needs_regeneration = await self.should_regenerate(user_id)
            if not needs_regeneration:
                try:
                    cache_key = f"reco_cache:{user_id}"
                    cached_json = await self.redis.get(cache_key)
                    if cached_json:
                        cached_data = json.loads(cached_json)
                        return self._deserialize_output(cached_data)
                except Exception:
                    pass  # Fall through to generate
            
            # Generate new recommendation
            runner = WorkflowRunner(db=self.db, redis_client=self.redis)
            output = await runner.run(user_id=user_id, user_name=user_name)
            
            # Store in all layers
            await self._store(user_id, output)
            
            return output
    
    async def _store(
        self,
        user_id: uuid.UUID,
        output: RecommendationOutput
    ) -> None:
        """
        Store recommendation in all storage layers.
        
        Storage layers:
        1. PostgreSQL recommendations table (historical record)
        2. PostgreSQL recommendation_cache table (persistent cache)
        3. Redis (fast cache with TTL)
        
        Args:
            user_id: User UUID
            output: RecommendationOutput to store
        """
        # Get current event hash
        event_hash = await compute_event_hash(user_id, self.db)
        
        # Serialize output to JSON
        output_dict = self._serialize_output(output, event_hash)
        output_json = json.dumps(output_dict)
        
        # 1. Insert into recommendations table (historical record)
        narrative_json = json.dumps({
            "learning_goal": output.narrative_result.learning_goal,
            "personalized_story": output.narrative_result.personalized_story,
            "roadmap": output.narrative_result.roadmap,
            "product_explanations": output.narrative_result.product_explanations,
            "motivational_cta": output.narrative_result.motivational_cta,
        })
        
        product_ids = [
            str(p.product_id) for p in output.ranked_products
        ]
        
        recommendation = Recommendation(
            user_id=user_id,
            persona=output.persona,
            narrative_data=narrative_json,
            product_ids=product_ids,
            confidence_score=output.confidence,
            generated_at=output.generated_at
        )
        self.db.add(recommendation)
        
        # 2. Upsert into recommendation_cache table
        expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl)
        
        stmt = pg_insert(RecommendationCache).values(
            user_id=user_id,
            event_hash=event_hash,
            cached_recommendation=output_dict,
            expires_at=expires_at
        )
        
        # On conflict (user_id), update all fields
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'event_hash': stmt.excluded.event_hash,
                'cached_recommendation': stmt.excluded.cached_recommendation,
                'expires_at': stmt.excluded.expires_at
            }
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        # 3. Set Redis cache with TTL (best effort, don't fail if Redis is unavailable)
        try:
            cache_key = f"reco_cache:{user_id}"
            await self.redis.set(
                cache_key,
                output_json,
                ex=self.cache_ttl
            )
        except Exception as e:
            logger.warning(f"Failed to set Redis cache for user {user_id}: {e}")
    
    async def get_history(
        self,
        user_id: uuid.UUID,
        limit: int = 5
    ) -> list[Recommendation]:
        """
        Get recommendation history for a user.
        
        Args:
            user_id: User UUID
            limit: Max recommendations to return (default 5)
            
        Returns:
            List of Recommendation ORM objects (most recent first)
            
        Example:
            >>> history = await service.get_history(user_id, limit=10)
            >>> for rec in history:
            ...     print(rec.persona, rec.generated_at)
        """
        stmt = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.generated_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        recommendations = result.scalars().all()
        
        return list(recommendations)
    
    async def invalidate_cache(self, user_id: uuid.UUID) -> None:
        """
        Invalidate all caches for a user.
        
        Forces fresh regeneration on next request.
        
        Args:
            user_id: User UUID
            
        Example:
            >>> await service.invalidate_cache(user_id)
            >>> output = await service.get_or_generate(user_id)  # Will regenerate
        """
        try:
            from sqlalchemy import delete
            stmt = delete(RecommendationCache).where(RecommendationCache.user_id == user_id)
            await self.db.execute(stmt)
            await self.db.commit()

            cache_key = f"reco_cache:{user_id}"
            persona_key = f"persona:{user_id}"
            await self.redis.delete(cache_key, persona_key)
        except Exception as e:
            logger.warning(f"Failed to delete cache for user {user_id}: {e}")
    
    def _serialize_output(
        self,
        output: RecommendationOutput,
        event_hash: str
    ) -> dict:
        """
        Serialize RecommendationOutput to dict for JSON storage.
        
        Args:
            output: RecommendationOutput to serialize
            event_hash: Current event hash for cache validation
            
        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "user_id": str(output.user_id),
            "persona": output.persona,
            "confidence": output.confidence,
            "event_hash": event_hash,
            "narrative_result": {
                "persona_display": output.narrative_result.persona_display,
                "learning_goal": output.narrative_result.learning_goal,
                "personalized_story": output.narrative_result.personalized_story,
                "roadmap": output.narrative_result.roadmap,
                "product_explanations": output.narrative_result.product_explanations,
                "motivational_cta": output.narrative_result.motivational_cta,
            },
            "ranked_products": [
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
            "recovery_result": (
                {
                    "is_at_risk": output.recovery_result.is_at_risk,
                    "recovery_narrative": output.recovery_result.recovery_narrative,
                    "email_subject": output.recovery_result.email_subject,
                    "email_body": output.recovery_result.email_body,
                }
                if output.recovery_result
                else None
            ),
            "is_recovery_mode": output.is_recovery_mode,
            "generated_at": output.generated_at.isoformat(),
            "trace_id": output.trace_id,
        }
    
    def _deserialize_output(self, data: dict) -> RecommendationOutput:
        """
        Deserialize dict to RecommendationOutput.
        
        Args:
            data: Dictionary from JSON
            
        Returns:
            RecommendationOutput instance
            
        Raises:
            KeyError: If required fields missing
            TypeError: If field types incorrect
        """
        from app.agents.ranking_agent import RankedProduct
        from app.agents.narrative_agent import NarrativeResult
        from app.agents.recovery_agent import RecoveryResult
        
        # Deserialize ranked products
        ranked_products = [
            RankedProduct(
                product_id=p["product_id"],
                title=p["title"],
                description=p["description"],
                category=p["category"],
                difficulty=p["difficulty"],
                price=p["price"],
                tags=p["tags"],
                final_score=p["final_score"],
                rank_position=p["rank_position"],
                score_breakdown=p["score_breakdown"],
            )
            for p in data["ranked_products"]
        ]
        
        # Deserialize narrative result
        narrative_data = data["narrative_result"]
        narrative_result = NarrativeResult(
            persona_display=narrative_data["persona_display"],
            learning_goal=narrative_data["learning_goal"],
            personalized_story=narrative_data["personalized_story"],
            roadmap=narrative_data["roadmap"],
            product_explanations=narrative_data["product_explanations"],
            motivational_cta=narrative_data["motivational_cta"],
        )
        
        # Deserialize recovery result (optional)
        recovery_result = None
        if data.get("recovery_result"):
            recovery_data = data["recovery_result"]
            # Import here to avoid circular dependency
            recovery_result = RecoveryResult(
                is_at_risk=recovery_data["is_at_risk"],
                recovery_narrative=recovery_data["recovery_narrative"],
                recovery_products=[],  # Not stored in cache
                email_subject=recovery_data["email_subject"],
                email_body=recovery_data["email_body"],
            )
        
        # Create output
        output = RecommendationOutput(
            user_id=uuid.UUID(data["user_id"]),
            persona=data["persona"],
            confidence=data["confidence"],
            narrative_result=narrative_result,
            ranked_products=ranked_products,
            recovery_result=recovery_result,
            is_recovery_mode=data["is_recovery_mode"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
            trace_id=data["trace_id"],
        )
        
        return output
