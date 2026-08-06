"""Narrative Agent - Generates personalized learning journey narratives using Mesh API"""

import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import openai
import redis.asyncio as redis

from app.config import settings
from app.agents.behavior_agent import BehaviorSummary
from app.agents.persona_agent import PersonaResult
from app.agents.ranking_agent import RankedProduct
from app.observability.langsmith_client import trace_run


# Initialize Mesh API client at module level (max_retries=0 so slow gateway calls fail fast to fallback)
mesh_client = openai.AsyncOpenAI(
    api_key=settings.mesh_api_key,
    base_url=settings.mesh_api_base_url,
    max_retries=0
)


@dataclass
class NarrativeResult:
    """Result of narrative generation"""
    persona_display: str
    learning_goal: str
    personalized_story: str  # 2-3 sentence journey description
    roadmap: List[str]  # Ordered course titles = learning path
    product_explanations: Dict[str, str]  # product_id → one-sentence reason
    motivational_cta: str


class NarrativeAgent:
    """
    Generates personalized learning journey narratives using LLM.
    
    Uses Mesh API (OpenAI-compatible) to create:
    - Learning goals and personalized stories
    - Course roadmaps (learning paths)
    - Product-specific explanations
    - Motivational CTAs
    """
    
    SYSTEM_PROMPT = """You are SmartReco, an AI Learning Journey Coach. Generate personalized, motivating recommendations.

Be empathetic, specific, and action-oriented.

CRITICAL RULES:
1. NEVER invent course names — use ONLY courses from the provided list
2. Respond ONLY with valid JSON (no markdown, no explanations)
3. All course titles in 'roadmap' must exactly match titles from the provided list
4. All product_ids in 'product_explanations' must exactly match IDs from the provided list
5. Keep 'personalized_story' to 2-3 sentences
6. Make 'product_explanations' concise (one sentence each)

Output Format:
{
  "learning_goal": "Clear, specific learning objective",
  "personalized_story": "2-3 sentence journey description",
  "roadmap": ["Course Title 1", "Course Title 2", "Course Title 3"],
  "product_explanations": {
    "product-id-1": "One sentence explaining why this course fits",
    "product-id-2": "One sentence explaining why this course fits"
  },
  "motivational_cta": "Encouraging call-to-action"
}"""
    
    def __init__(self):
        """Initialize NarrativeAgent"""
        self.redis_client = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True
            )
        return self.redis_client
    
    async def generate(
        self,
        summary: BehaviorSummary,
        persona: PersonaResult,
        ranked_products: List[RankedProduct],
        parent_run_id: Optional[str] = None
    ) -> NarrativeResult:
        """
        Generate personalized narrative for recommendations.
        
        Args:
            summary: User behavioral summary
            persona: Persona classification result
            ranked_products: Top-ranked products (usually 8)
            parent_run_id: Optional parent trace ID for nesting
            
        Returns:
            NarrativeResult with personalized content
            
        Example:
            >>> agent = NarrativeAgent()
            >>> narrative = await agent.generate(summary, persona, ranked_products)
            >>> print(narrative.personalized_story)
            "You're on a focused journey in Python development..."
        """
        start_time = datetime.utcnow()
        
        with trace_run(
            name="narrative_generation",
            run_type="llm",
            inputs={
                "persona": persona.persona.value,
                "product_count": len(ranked_products),
                "user_id": summary.user_id
            },
            parent_run_id=parent_run_id,
            tags=["agent", "narrative", "llm"]
        ) as run_id:
            try:
                # Build user prompt
                user_prompt = self._build_user_prompt(summary, persona, ranked_products)
                
                # Call Mesh API with 8-second timeout fallback
                import asyncio
                response = await asyncio.wait_for(
                    mesh_client.chat.completions.create(
                        model=settings.mesh_model,
                        messages=[
                            {"role": "system", "content": self.SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=settings.mesh_temperature,
                        max_tokens=settings.mesh_max_tokens
                    ),
                    timeout=4.0
                )
                
                # Calculate latency
                end_time = datetime.utcnow()
                latency_ms = (end_time - start_time).total_seconds() * 1000
                
                # Extract content
                content = response.choices[0].message.content
                
                # Extract token usage
                usage = response.usage
                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0
                total_tokens = usage.total_tokens if usage else 0
                
                # Increment AI call counter
                await self._increment_ai_call_counter()
                
                # Parse JSON response
                parsed = self._parse_response(content)
                
                # Build result
                result = NarrativeResult(
                    persona_display=self._format_persona_display(persona),
                    learning_goal=parsed.get('learning_goal', 'Expand your professional skills'),
                    personalized_story=parsed.get('personalized_story', 'Your learning journey continues.'),
                    roadmap=parsed.get('roadmap', [p.title for p in ranked_products[:3]]),
                    product_explanations=parsed.get('product_explanations', {}),
                    motivational_cta=parsed.get('motivational_cta', 'Start learning today!')
                )
                
                return result
                
            except Exception as e:
                # Log error and return fallback
                print(f"Narrative generation failed: {e}")
                fallback_result = self._create_fallback_narrative(summary, persona, ranked_products)
                return fallback_result

    
    def _build_user_prompt(
        self,
        summary: BehaviorSummary,
        persona: PersonaResult,
        ranked_products: List[RankedProduct]
    ) -> str:
        """
        Build user prompt with context and constraints.
        """
        # Get top categories, prioritizing the top-ranked recommendation category
        primary_category = ranked_products[0].category if ranked_products else "various topics"
        if summary.categories_explored:
            sorted_cats = [cat for cat, _ in sorted(summary.categories_explored.items(), key=lambda x: x[1], reverse=True)]
            if primary_category in sorted_cats:
                sorted_cats.remove(primary_category)
            sorted_cats.insert(0, primary_category)
            categories_str = ", ".join(sorted_cats[:3])
        else:
            categories_str = primary_category
        
        # Get recent search queries
        recent_queries = ", ".join(summary.search_queries[-3:]) if summary.search_queries else "general learning"
        
        # Format product list (only essential fields)
        products_json = json.dumps([
            {
                "id": p.product_id,
                "title": p.title,
                "description": p.description[:150] + "...",  # Truncate
                "category": p.category,
                "difficulty": p.difficulty
            }
            for p in ranked_products
        ], indent=2)

        # Build enrollment context to inform the LLM about unenroll/re-enroll/completion signals
        enrollment_ctx_parts = []
        if summary.enrolled_product_titles:
            enrollment_ctx_parts.append(f"Currently enrolled in: {', '.join(summary.enrolled_product_titles[:3])}")
        if getattr(summary, 're_enrollment_events', 0) > 0:
            re_cats = getattr(summary, 're_enrolled_categories', [])
            re_cats_str = (', '.join(re_cats[:3])) if re_cats else 'unknown'
            enrollment_ctx_parts.append(
                f"Re-enrolled {summary.re_enrollment_events} time(s) in: {re_cats_str} — strong commitment signal"
            )
        completion_counts = getattr(summary, 'completion_counts', {})
        if completion_counts:
            comp_str = ", ".join(
                f"{cat}: {count} lesson(s) completed"
                for cat, count in sorted(completion_counts.items(), key=lambda x: -x[1])[:3]
            )
            enrollment_ctx_parts.append(f"Lesson completions: {comp_str}")
        # Check if last meaningful event was an unenroll (user dropped a course)
        if summary.enrollment_events == 0 and getattr(summary, 're_enrollment_events', 0) == 0 and summary.total_events > 3:
            enrollment_ctx_parts.append("Note: user has unenrolled from courses recently — suggest a fresh start or alternative tracks")
        enrollment_context = "\n".join(f"- {p}" for p in enrollment_ctx_parts) if enrollment_ctx_parts else "- No enrollment activity yet"
        
        prompt = f"""Learner Persona: {persona.persona.value} (confidence: {persona.confidence:.0%})

Behavior Summary:
- Primary Category: {primary_category}
- All Explored categories: {categories_str}
- Searched for: {recent_queries}
- Average dwell time: {summary.avg_dwell_time:.0f}s
- Total events: {summary.total_events}

Enrollment & Progress Context:
{enrollment_context}

Available courses (use ONLY these):
{products_json}

Generate a personalized learning recommendation in JSON format:
{{
  "learning_goal": "Specific learning objective focused on {primary_category}",
  "personalized_story": "2-3 sentences describing their learning journey in {primary_category} and next steps",
  "roadmap": ["Course Title 1", "Course Title 2", "Course Title 3"],
  "product_explanations": {{
    "product-id": "One sentence why this course fits their journey"
  }},
  "motivational_cta": "Encouraging call-to-action to start learning"
}}

Remember: Use ONLY course titles and IDs from the list above."""
        
        return prompt
    
    def _parse_response(self, content: str) -> Dict:
        """
        Parse LLM response, handling markdown code fences.
        """
        # Strip markdown code fences if present
        content = content.strip()
        
        # Remove ```json ... ``` if present
        if content.startswith('```'):
            # Find first { and last }
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end+1]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Content: {content[:200]}")
            return {}
    
    def _format_persona_display(self, persona: PersonaResult) -> str:
        """Format persona for display"""
        persona_names = {
            'explorer': 'Explorer',
            'focused_builder': 'Focused Builder',
            'career_switcher': 'Career Switcher',
            'price_sensitive': 'Budget-Conscious Learner',
            'overwhelmed_learner': 'Thoughtful Learner',
            'drop_off_risk': 'Returning Learner'
        }
        return persona_names.get(persona.persona.value, persona.persona.value.title())
    
    def _create_fallback_narrative(
        self,
        summary: BehaviorSummary,
        persona: PersonaResult,
        ranked_products: List[RankedProduct]
    ) -> NarrativeResult:
        """
        Create safe fallback narrative if AI generation fails.
        """
        # Top category matches the #1 ranked recommendation product category
        top_category = ranked_products[0].category if ranked_products else "your interests"
        if not top_category or top_category.lower() == 'general':
            if summary.last_viewed_category:
                top_category = summary.last_viewed_category
            elif summary.categories_explored:
                top_category = max(summary.categories_explored.items(), key=lambda x: x[1])[0]
        
        return NarrativeResult(
            persona_display=self._format_persona_display(persona),
            learning_goal=f"Master {top_category} with structured learning",
            personalized_story=f"Based on your exploration of {top_category}, we've curated courses that match your learning style and pace. Continue building your expertise with these carefully selected recommendations.",
            roadmap=[p.title for p in ranked_products[:3]],
            product_explanations={
                p.product_id: f"Recommended next step for your enrolled & completed track in {p.category}"
                for p in ranked_products[:5]
            },
            motivational_cta="Start your learning journey today!"
        )
    
    async def _increment_ai_call_counter(self):
        """Increment Redis counter for AI API calls"""
        try:
            redis_client = await self._get_redis()
            await redis_client.incr("ai_call_count")
        except Exception as e:
            print(f"Redis counter error: {e}")
            # Don't fail on counter error
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
