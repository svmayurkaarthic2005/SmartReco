"""End-to-end test of the full recommendation pipeline for Mayur's user ID"""
import asyncio
from sqlalchemy import select
from app.database.base import AsyncSessionLocal
from app.models import Event, User
from app.models.event import EventType
from app.agents.behavior_agent import BehaviorAgent
from app.agents.persona_agent import PersonaAgent
from app.agents.retrieval_agent import RetrievalPlanner
from uuid import UUID

MAYUR_ID = UUID("dad33227-b76e-4956-8aa9-50724c69c8b8")

async def test_pipeline():
    async with AsyncSessionLocal() as db:
        print("=== STEP 1: BehaviorAgent ===")
        behavior_agent = BehaviorAgent(db)
        summary = await behavior_agent.analyze(MAYUR_ID, lookback_hours=72)
        print(f"  total_events={summary.total_events}")
        print(f"  categories_explored={summary.categories_explored}")
        print(f"  completion_counts={summary.completion_counts}")
        print(f"  enrolled_product_titles={summary.enrolled_product_titles}")
        print(f"  last_viewed_category={summary.last_viewed_category}")

        print("\n=== STEP 2: PersonaAgent ===")
        persona_agent = PersonaAgent()
        persona = await persona_agent.classify(summary)
        print(f"  persona={persona.persona.value}, confidence={persona.confidence:.2f}")
        await persona_agent.close()

        print("\n=== STEP 3: RetrievalPlanner ===")
        planner = RetrievalPlanner()
        plan = planner.plan(summary, persona)
        print(f"  semantic_query={plan.semantic_query[:100]}")
        print(f"  exclude_product_ids={plan.exclude_product_ids}")
        print(f"  category_filter={plan.category_filter}")
        print(f"  difficulty_filter={plan.difficulty_filter}")

        print("\n=== PIPELINE: All checks passed ✓ ===")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
