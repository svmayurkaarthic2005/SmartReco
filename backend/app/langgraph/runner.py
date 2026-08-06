"""Workflow runner for executing recommendation pipeline"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.langgraph.workflow import get_workflow, AgentState, _db_session, _user_name
from app.agents import (
    NarrativeResult,
    RankedProduct,
    RecoveryResult
)
from app.config import settings
from app.observability.langsmith_client import trace_run
import app.langgraph.workflow as workflow_module


@dataclass
class RecommendationOutput:
    """Final recommendation output"""
    user_id: str
    persona: str
    confidence: float
    narrative_result: NarrativeResult
    ranked_products: List[RankedProduct]
    recovery_result: Optional[RecoveryResult]
    is_recovery_mode: bool
    generated_at: datetime
    trace_id: str


class WorkflowRunner:
    """
    Executes the LangGraph recommendation workflow.
    
    Orchestrates all 7 agents through a state machine graph.
    Includes error handling and caching fallback.
    """
    
    def __init__(self, db: AsyncSession, redis_client: Optional[redis.Redis] = None):
        """
        Initialize workflow runner.
        
        Args:
            db: Database session
            redis_client: Redis client for caching (optional)
        """
        self.db = db
        self.redis_client = redis_client
        self.workflow = get_workflow()
    
    async def run(
        self,
        user_id: UUID,
        user_name: str = "there"
    ) -> RecommendationOutput:
        """
        Run the complete recommendation workflow.
        
        Args:
            user_id: User UUID
            user_name: User's name for personalization
            
        Returns:
            RecommendationOutput with all results
            
        Raises:
            HTTPException 503 if workflow fails and no cache available
            
        Example:
            >>> runner = WorkflowRunner(db, redis_client)
            >>> output = await runner.run(user_id)
            >>> print(output.narrative_result.learning_goal)
        """
        # Generate trace ID for debugging
        trace_id = str(uuid.uuid4())
        
        # Wrap entire workflow in parent trace
        with trace_run(
            name="smartreco_workflow",
            run_type="chain",
            inputs={
                "user_id": str(user_id),
                "user_name": user_name
            },
            tags=["workflow", "parent"]
        ) as parent_run_id:
            # Inject dependencies into workflow module (global context)
            workflow_module._db_session = self.db
            workflow_module._user_name = user_name
            
            # Initialize state with parent_run_id
            initial_state: AgentState = {
                "user_id": str(user_id),
                "behavior_summary": None,
                "persona_result": None,
                "retrieval_plan": None,
                "candidate_products": [],
                "ranked_products": [],
                "narrative_result": None,
                "recovery_result": None,
                "is_recovery_mode": False,
                "error": None,
                "trace_id": trace_id,
                "parent_run_id": parent_run_id  # Add for child traces
            }
            
            try:
                print(f"[{trace_id}] Starting workflow for user {user_id}")
                
                # Execute workflow
                final_state = await self.workflow.ainvoke(initial_state)
                
                # Check for errors
                if final_state.get("error"):
                    raise Exception(f"Workflow error: {final_state['error']}")
                
                # Validate required outputs
                if not final_state.get("persona_result"):
                    raise Exception("Persona classification failed")
                
                if not final_state.get("narrative_result"):
                    raise Exception("Narrative generation failed")
                
                if not final_state.get("ranked_products"):
                    # In recovery mode, ranked_products might come from recovery_node
                    if not final_state.get("is_recovery_mode"):
                        raise Exception("No ranked products generated")
                
                # Compute real-time AI Match Confidence (70% top recommendation match score + 30% persona fit)
                top_ranked_score = final_state["ranked_products"][0].final_score if final_state.get("ranked_products") else 0.85
                persona_conf = final_state["persona_result"].confidence
                realtime_confidence = min(0.98, max(0.65, top_ranked_score * 0.70 + persona_conf * 0.30))

                # Build output
                output = RecommendationOutput(
                    user_id=str(user_id),
                    persona=final_state["persona_result"].persona.value,
                    confidence=realtime_confidence,
                    narrative_result=final_state["narrative_result"],
                    ranked_products=final_state["ranked_products"],
                    recovery_result=final_state.get("recovery_result"),
                    is_recovery_mode=final_state.get("is_recovery_mode", False),
                    generated_at=datetime.utcnow(),
                    trace_id=trace_id
                )
                
                # Cache successful result
                await self._cache_recommendation(user_id, output)
                
                print(f"[{trace_id}] Workflow completed successfully")
                return output
            
            except Exception as e:
                print(f"[{trace_id}] Workflow failed: {e}")
                
                # Try loading from cache
                cached = await self._load_cached_recommendation(user_id)
                
                if cached:
                    print(f"[{trace_id}] Returning cached recommendation")
                    return cached
                
                # No cache available, raise error
                raise HTTPException(
                    status_code=503,
                    detail=f"Recommendation system temporarily unavailable. Trace ID: {trace_id}"
                )
    
    async def _cache_recommendation(
        self,
        user_id: UUID,
        output: RecommendationOutput
    ) -> None:
        """
        Cache recommendation result in Redis.
        
        Args:
            user_id: User UUID
            output: Recommendation output to cache
        """
        if not self.redis_client:
            return
        
        try:
            cache_key = f"reco_cache:{user_id}"
            
            # Serialize output (convert dataclasses to dict)
            cache_data = {
                "user_id": output.user_id,
                "persona": output.persona,
                "confidence": output.confidence,
                "narrative_result": asdict(output.narrative_result),
                "ranked_products": [asdict(p) for p in output.ranked_products],
                "recovery_result": asdict(output.recovery_result) if output.recovery_result else None,
                "is_recovery_mode": output.is_recovery_mode,
                "generated_at": output.generated_at.isoformat(),
                "trace_id": output.trace_id
            }
            
            # Store with TTL (1 hour)
            await self.redis_client.set(
                cache_key,
                json.dumps(cache_data),
                ex=3600
            )
            
            print(f"Cached recommendation for user {user_id}")
        
        except Exception as e:
            print(f"Cache write error: {e}")
            # Don't fail on cache errors
    
    async def _load_cached_recommendation(
        self,
        user_id: UUID
    ) -> Optional[RecommendationOutput]:
        """
        Load cached recommendation from Redis.
        
        Args:
            user_id: User UUID
            
        Returns:
            Cached RecommendationOutput or None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"reco_cache:{user_id}"
            cached_json = await self.redis_client.get(cache_key)
            
            if not cached_json:
                return None
            
            # Deserialize
            cache_data = json.loads(cached_json)
            
            # Reconstruct objects
            from app.agents import NarrativeResult, RankedProduct, RecoveryResult
            
            narrative_result = NarrativeResult(**cache_data["narrative_result"])
            
            ranked_products = [
                RankedProduct(**p) for p in cache_data["ranked_products"]
            ]
            
            recovery_result = None
            if cache_data.get("recovery_result"):
                recovery_result = RecoveryResult(**cache_data["recovery_result"])
            
            output = RecommendationOutput(
                user_id=cache_data["user_id"],
                persona=cache_data["persona"],
                confidence=cache_data["confidence"],
                narrative_result=narrative_result,
                ranked_products=ranked_products,
                recovery_result=recovery_result,
                is_recovery_mode=cache_data["is_recovery_mode"],
                generated_at=datetime.fromisoformat(cache_data["generated_at"]),
                trace_id=cache_data["trace_id"]
            )
            
            return output
        
        except Exception as e:
            print(f"Cache read error: {e}")
            return None


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client for caching.
    
    Returns:
        Redis client
    """
    return await redis.from_url(
        settings.redis_url,
        password=settings.redis_password,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=0.5
    )
