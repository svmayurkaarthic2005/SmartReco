"""Unit tests for RankingAgent"""

import pytest
import uuid
from app.agents.ranking_agent import RankingAgent
from app.agents.retrieval_agent import CandidateProduct
from app.agents.behavior_agent import BehaviorSummary
from app.agents.persona_agent import PersonaResult, Persona
from app.models.product import Product, DifficultyLevel


def test_ranking_agent_rank():
    """Test ranking 10 candidate products with multi-factor scoring"""
    agent = RankingAgent()

    # Mock 10 candidate products
    candidates = []
    db_products = {}
    for i in range(10):
        pid = str(uuid.uuid4())
        candidate = CandidateProduct(
            product_id=pid,
            title=f"Course {i+1}",
            description=f"Description for course {i+1}",
            category="AI/ML" if i % 2 == 0 else "Web Dev",
            difficulty="beginner" if i < 4 else "intermediate",
            price=29.99 + (i * 10),
            tags=["python", "ai"],
            similarity_score=0.95 - (i * 0.05)
        )
        candidates.append(candidate)

        db_product = Product(
            id=uuid.UUID(pid),
            title=candidate.title,
            description=candidate.description,
            category=candidate.category,
            price=candidate.price,
            difficulty_level=DifficultyLevel.BEGINNER if candidate.difficulty == "beginner" else DifficultyLevel.INTERMEDIATE,
            duration_hours=10.0,
            tags=candidate.tags
        )
        db_products[pid] = db_product

    summary = BehaviorSummary(
        user_id="test_user_ranking",
        total_events=15,
        categories_explored={"AI/ML": 10, "Web Dev": 5},
        search_queries=["python", "ai"],
        avg_dwell_time=90.0
    )

    persona = PersonaResult(
        persona=Persona.FOCUSED_BUILDER,
        confidence=0.85,
        reasoning="Focused on AI/ML",
        recommended_strategy="Provide advanced courses"
    )

    result = agent.rank(candidates, summary, persona, db_products)

    # 1. Assert len(result) == 8
    assert len(result) == 8

    # 2. Assert all score_breakdown dicts have 6 keys
    expected_factors = {
        'semantic',
        'difficulty_match',
        'learning_progression',
        'price_fit',
        'tag_overlap',
        'freshness'
    }
    for item in result:
        assert isinstance(item.score_breakdown, dict)
        assert len(item.score_breakdown) == 6
        assert set(item.score_breakdown.keys()) == expected_factors

    # 3. Assert rank_positions are 1..8 sequential
    rank_positions = [item.rank_position for item in result]
    assert rank_positions == [1, 2, 3, 4, 5, 6, 7, 8]
