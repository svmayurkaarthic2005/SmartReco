"""Persona Construction Agent - Classifies users into behavioral personas"""

import json
import enum
from dataclasses import dataclass, asdict
from typing import Optional
import redis.asyncio as redis

from app.agents.behavior_agent import BehaviorSummary
from app.config import settings
from app.observability.langsmith_client import trace_run


class Persona(str, enum.Enum):
    """User persona types based on behavioral patterns"""
    EXPLORER = "explorer"
    FOCUSED_BUILDER = "focused_builder"
    CAREER_SWITCHER = "career_switcher"
    PRICE_SENSITIVE = "price_sensitive"
    OVERWHELMED_LEARNER = "overwhelmed_learner"
    DROP_OFF_RISK = "drop_off_risk"


@dataclass
class PersonaResult:
    """Result of persona classification"""
    persona: Persona
    confidence: float  # 0.0 to 1.0
    reasoning: str
    recommended_strategy: str


class PersonaAgent:
    """
    Classifies users into personas using weighted scoring rules.
    
    Personas:
    - EXPLORER: Browses widely, low commitment
    - FOCUSED_BUILDER: Deep engagement in one area
    - CAREER_SWITCHER: Exploring new fields, beginner focus
    - PRICE_SENSITIVE: Evaluates options, doesn't purchase
    - OVERWHELMED_LEARNER: Views advanced content but doesn't engage
    - DROP_OFF_RISK: High exit rate, low engagement
    """
    
    def __init__(self):
        """Initialize PersonaAgent with Redis client"""
        self.redis_client: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5
            )
        return self.redis_client
    
    async def classify(
        self, 
        summary: BehaviorSummary,
        parent_run_id: Optional[str] = None
    ) -> PersonaResult:
        """
        Classify user into persona using weighted scoring.
        
        Args:
            summary: BehaviorSummary from BehaviorAgent
            parent_run_id: Optional parent trace ID for nesting
            
        Returns:
            PersonaResult with persona, confidence, reasoning, and strategy
            
        Scoring Rules (max score = 4 for each persona):
        - EXPLORER: Multiple categories (+2), low dwell (+1), category switches (+1)
        - FOCUSED_BUILDER: One dominant category (+2), high dwell (+2)
        - CAREER_SWITCHER: Multiple categories (+1), beginner queries (+2), search terms (+1)
        - PRICE_SENSITIVE: Cart activity but no purchase (+2), price keywords (+2)
        - OVERWHELMED_LEARNER: Advanced content viewed (+2), no enrollment (+1), low scroll (+1)
        - DROP_OFF_RISK: High exits (+2), low recent activity (+1), no enrollment (+1)
        """
        # Create behavior hash for tracing
        behavior_hash = f"{summary.total_events}_{len(summary.categories_explored)}_{summary.avg_dwell_time:.0f}"
        
        with trace_run(
            name="persona_classification",
            run_type="chain",
            inputs={
                "user_id": summary.user_id,
                "behavior_hash": behavior_hash,
                "total_events": summary.total_events,
                "categories_explored": len(summary.categories_explored),
                "avg_dwell_time": round(summary.avg_dwell_time, 2)
            },
            parent_run_id=parent_run_id,
            tags=["agent", "persona"]
        ) as run_id:
            # Check cache first
            cached = await self._get_cached_persona(summary.user_id)
            if cached:
                output = {
                    "persona": cached.persona.value,
                    "confidence": round(cached.confidence, 2),
                    "cached": True
                }
                return cached
            
            # Calculate scores for each persona
            scores = {
                Persona.EXPLORER: self._score_explorer(summary),
                Persona.FOCUSED_BUILDER: self._score_focused_builder(summary),
                Persona.CAREER_SWITCHER: self._score_career_switcher(summary),
                Persona.PRICE_SENSITIVE: self._score_price_sensitive(summary),
                Persona.OVERWHELMED_LEARNER: self._score_overwhelmed_learner(summary),
                Persona.DROP_OFF_RISK: self._score_drop_off_risk(summary),
            }
            
            # Select persona with highest score
            max_score = max(scores.values())
            
            # Default to EXPLORER if all scores are 0
            if max_score == 0:
                result = PersonaResult(
                    persona=Persona.EXPLORER,
                    confidence=0.4,
                    reasoning="New user with minimal behavioral data. Defaulting to explorer persona.",
                    recommended_strategy="Show diverse, popular content to help user discover interests."
                )
            else:
                # Find persona(s) with max score
                winning_personas = [p for p, s in scores.items() if s == max_score]
                persona = winning_personas[0]
                
                # Base confidence from persona criteria match
                base_confidence = max_score / 4.0
                
                # Engagement & interaction boost (up to +0.45)
                boost = 0.0
                if summary.total_events > 5 or summary.repeat_visits > 2 or summary.unique_products_viewed:
                    boost += 0.20
                if summary.enrollment_events > 0 or getattr(summary, 'enrolled_product_titles', []):
                    boost += 0.20
                if summary.categories_explored:
                    boost += 0.15
                
                confidence = min(0.95, max(0.60, base_confidence + boost))
                
                result = PersonaResult(
                    persona=persona,
                    confidence=confidence,
                    reasoning=self._generate_reasoning(persona, summary, scores[persona]),
                    recommended_strategy=self._get_strategy(persona)
                )
            
            # Cache result
            await self._cache_persona(summary.user_id, result)
            
            # Trace output
            return result
    
    def _score_explorer(self, summary: BehaviorSummary) -> int:
        """Score for EXPLORER persona (max: 4)"""
        score = 0
        
        # Multiple categories explored (+2)
        if len(summary.categories_explored) > 3:
            score += 2
        
        # Low average dwell time (+1)
        if summary.avg_dwell_time > 0 and summary.avg_dwell_time < 60:
            score += 1
        
        # Multiple category switches (+1)
        if summary.category_switches > 2:
            score += 1
        
        return score
    
    def _score_focused_builder(self, summary: BehaviorSummary) -> int:
        """Score for FOCUSED_BUILDER persona (max: 4)"""
        score = 0
        
        if not summary.categories_explored:
            return 0
        
        # One category dominates (>60% of events) (+2)
        max_category_count = max(summary.categories_explored.values())
        total_category_events = sum(summary.categories_explored.values())
        
        if total_category_events > 0:
            dominant_ratio = max_category_count / total_category_events
            if dominant_ratio > 0.6:
                score += 2
        
        # High average dwell time (+2)
        if summary.avg_dwell_time > 120:
            score += 2
        
        return score
    
    def _score_career_switcher(self, summary: BehaviorSummary) -> int:
        """Score for CAREER_SWITCHER persona (max: 4)"""
        score = 0

        # Multiple categories explored (+1) — signals exploring new fields
        if len(summary.categories_explored) > 1:
            score += 1

        # Beginner difficulty dominates their viewed content (+2)
        # Uses the real dominant_difficulty computed from product metadata
        dominant_diff = getattr(summary, 'dominant_difficulty', None)
        if dominant_diff and dominant_diff.lower() == 'beginner':
            score += 2
        elif len(summary.unique_products_viewed) > 5 and not dominant_diff:
            # Fallback: many views with no difficulty data (sparse catalog)
            score += 1

        # Search queries contain beginner keywords (+1)
        beginner_keywords = ['beginner', 'learn', 'start', 'intro', 'basics', 'fundamentals']
        for query in summary.search_queries:
            if any(keyword in query.lower() for keyword in beginner_keywords):
                score += 1
                break

        return score
    
    def _score_price_sensitive(self, summary: BehaviorSummary) -> int:
        """Score for PRICE_SENSITIVE persona (max: 4)"""
        score = 0
        
        # Cart events but no enrollment (+2)
        if summary.cart_events > 2 and summary.enrollment_events == 0:
            score += 2
        
        # Search queries contain price keywords (+2)
        price_keywords = ['free', 'discount', 'cheap', 'price', 'cost', 'affordable', 'sale']
        for query in summary.search_queries:
            if any(keyword in query.lower() for keyword in price_keywords):
                score += 2
                break
        
        return score
    
    def _score_overwhelmed_learner(self, summary: BehaviorSummary) -> int:
        """Score for OVERWHELMED_LEARNER persona (max: 4)"""
        score = 0

        # Advanced content dominates their viewed products (+2)
        # An overwhelmed learner is someone who views hard content but doesn't engage
        dominant_diff = getattr(summary, 'dominant_difficulty', None)
        if dominant_diff and dominant_diff.lower() == 'advanced':
            score += 2
        elif len(summary.unique_products_viewed) > 3 and summary.avg_dwell_time < 90 and not dominant_diff:
            # Fallback: many quick views with no difficulty data
            score += 2

        # No enrollment events (+1) — viewed content but didn't commit
        if summary.enrollment_events == 0:
            score += 1

        # Low scroll depth (+1) — not reading content deeply
        if summary.scroll_depth_avg > 0 and summary.scroll_depth_avg < 40:
            score += 1

        return score
    
    def _score_drop_off_risk(self, summary: BehaviorSummary) -> int:
        """Score for DROP_OFF_RISK persona (max: 4)"""
        # New users with zero events are NOT drop-off risks — they haven't started yet.
        # Without this guard, every new user scores 2 points (total_events<5 + no enrollment)
        # and gets mis-classified as drop_off_risk instead of explorer.
        if summary.total_events == 0:
            return 0

        score = 0

        # High exit events (+2)
        if summary.exit_events > 5:
            score += 2

        # Low total events in recent period (+1)
        # Assuming lookback is 72h by default, check if < 5 events
        if summary.total_events < 5:
            score += 1

        # No enrollment events (+1) — but skip if user has re-enrolled.
        # A re-enrolling user is actively engaged, not a drop-off risk.
        has_re_enrolled = getattr(summary, 're_enrollment_events', 0) > 0
        if summary.enrollment_events == 0 and not has_re_enrolled:
            score += 1

        return score
    
    def _generate_reasoning(self, persona: Persona, summary: BehaviorSummary, score: int) -> str:
        """Generate human-readable reasoning for persona classification"""
        reasons = {
            Persona.EXPLORER: f"User explores widely across {len(summary.categories_explored)} categories with {summary.category_switches} category switches, suggesting curiosity and broad interests.",
            Persona.FOCUSED_BUILDER: f"User shows deep focus with {summary.avg_dwell_time:.0f}s average dwell time in a dominant category, indicating commitment to mastering a specific domain.",
            Persona.CAREER_SWITCHER: f"User explores multiple fields ({len(summary.categories_explored)} categories) with beginner-focused searches, suggesting career transition or skill pivoting.",
            Persona.PRICE_SENSITIVE: f"User added {summary.cart_events} items to cart but hasn't enrolled, and searches include price-related terms, indicating cost consciousness.",
            Persona.OVERWHELMED_LEARNER: f"User views advanced content ({len(summary.unique_products_viewed)} products) but shows low engagement (scroll depth: {summary.scroll_depth_avg:.0f}%), suggesting content is too challenging.",
            Persona.DROP_OFF_RISK: f"User shows {summary.exit_events} exit events with low overall activity ({summary.total_events} events), indicating disengagement risk.",
        }
        
        return reasons.get(persona, "Persona classification based on behavioral patterns.")
    
    def _get_strategy(self, persona: Persona) -> str:
        """Get recommended strategy for persona"""
        strategies = {
            Persona.EXPLORER: "Recommend diverse, popular content across multiple categories. Show trending courses and new arrivals.",
            Persona.FOCUSED_BUILDER: "Recommend progressive content in their focused area. Suggest advanced courses and specializations in their dominant category.",
            Persona.CAREER_SWITCHER: "Recommend beginner-friendly learning paths and career transition guides. Highlight success stories and structured programs.",
            Persona.PRICE_SENSITIVE: "Highlight free content, discounts, and value propositions. Show ROI data and compare pricing options prominently.",
            Persona.OVERWHELMED_LEARNER: "Recommend foundational courses and prerequisites. Break content into smaller, more manageable chunks. Provide guided learning paths.",
            Persona.DROP_OFF_RISK: "Re-engage with personalized messages, incentives, and curated content matching past interests. Reduce friction in enrollment process.",
        }
        
        return strategies.get(persona, "Provide personalized recommendations based on behavioral patterns.")
    
    async def _get_cached_persona(self, user_id: str) -> Optional[PersonaResult]:
        """Get cached persona from Redis"""
        try:
            redis_client = await self._get_redis()
            cache_key = f"persona:{user_id}"
            cached_json = await redis_client.get(cache_key)
            
            if cached_json:
                data = json.loads(cached_json)
                return PersonaResult(
                    persona=Persona(data['persona']),
                    confidence=data['confidence'],
                    reasoning=data['reasoning'],
                    recommended_strategy=data['recommended_strategy']
                )
        except Exception as e:
            # Log error but don't fail - just skip cache
            print(f"Redis cache read error: {e}")
        
        return None
    
    async def _cache_persona(self, user_id: str, result: PersonaResult) -> None:
        """Cache persona result in Redis"""
        try:
            redis_client = await self._get_redis()
            cache_key = f"persona:{user_id}"
            
            data = {
                'persona': result.persona.value,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'recommended_strategy': result.recommended_strategy
            }
            
            # Cache with TTL from settings (default 3600s = 1 hour)
            await redis_client.set(
                cache_key,
                json.dumps(data),
                ex=settings.persona_cache_ttl
            )
        except Exception as e:
            # Log error but don't fail
            print(f"Redis cache write error: {e}")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.aclose()
