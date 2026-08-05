"""Unit tests for NarrativeAgent"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.narrative_agent import NarrativeAgent, NarrativeResult, mesh_client
from app.agents.behavior_agent import BehaviorSummary
from app.agents.persona_agent import PersonaResult, Persona
from app.agents.ranking_agent import RankedProduct


@pytest.mark.asyncio
async def test_narrative_agent_valid_json():
    """Test NarrativeAgent with valid LLM JSON response"""
    agent = NarrativeAgent()

    summary = BehaviorSummary(
        user_id="user_narrative_test",
        total_events=10,
        categories_explored={"AI/ML": 5},
        search_queries=["machine learning"]
    )
    persona = PersonaResult(
        persona=Persona.EXPLORER,
        confidence=0.8,
        reasoning="Explores AI/ML",
        recommended_strategy="Show AI courses"
    )
    ranked_products = [
        RankedProduct(
            product_id="prod_1",
            title="Python ML Basics",
            description="Intro to ML",
            category="AI/ML",
            difficulty="beginner",
            price=49.99,
            tags=["python"],
            final_score=0.9,
            rank_position=1,
            score_breakdown={}
        )
    ]

    valid_json_payload = json.dumps({
        "learning_goal": "Master Python for AI",
        "personalized_story": "You are beginning your voyage into Artificial Intelligence.",
        "roadmap": ["Python ML Basics"],
        "product_explanations": {"prod_1": "Great starting point for beginners."},
        "motivational_cta": "Keep learning!"
    })

    mock_choice = MagicMock()
    mock_choice.message.content = valid_json_payload
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    with patch.object(mesh_client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        result = await agent.generate(summary, persona, ranked_products)

        assert isinstance(result, NarrativeResult)
        assert result.learning_goal == "Master Python for AI"
        assert result.personalized_story == "You are beginning your voyage into Artificial Intelligence."
        assert result.roadmap == ["Python ML Basics"]
        assert result.product_explanations == {"prod_1": "Great starting point for beginners."}
        assert result.motivational_cta == "Keep learning!"


@pytest.mark.asyncio
async def test_narrative_agent_invalid_json():
    """Test NarrativeAgent with invalid LLM response returns safe default without exception"""
    agent = NarrativeAgent()

    summary = BehaviorSummary(
        user_id="user_narrative_test",
        total_events=5,
        categories_explored={"Web Dev": 3}
    )
    persona = PersonaResult(
        persona=Persona.FOCUSED_BUILDER,
        confidence=0.7,
        reasoning="Web focus",
        recommended_strategy="Build apps"
    )
    ranked_products = [
        RankedProduct(
            product_id="prod_2",
            title="React Bootcamp",
            description="Full React guide",
            category="Web Dev",
            difficulty="intermediate",
            price=59.99,
            tags=["react"],
            final_score=0.85,
            rank_position=1,
            score_breakdown={}
        )
    ]

    invalid_content = "NOT_VALID_JSON {{{ this is broken response"
    mock_choice = MagicMock()
    mock_choice.message.content = invalid_content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = None

    with patch.object(mesh_client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        # Should not raise exception
        result = await agent.generate(summary, persona, ranked_products)

        assert isinstance(result, NarrativeResult)
        assert result.personalized_story is not None
        assert len(result.personalized_story) > 0
