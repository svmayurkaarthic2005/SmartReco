"""Unit tests for PersonaAgent"""

import pytest
from app.agents.persona_agent import PersonaAgent, Persona
from app.agents.behavior_agent import BehaviorSummary


@pytest.mark.asyncio
async def test_persona_explorer():
    """Test EXPLORER persona classification"""
    agent = PersonaAgent()
    summary = BehaviorSummary(
        user_id="test_user_explorer",
        total_events=10,
        categories_explored={"AI/ML": 3, "Web Dev": 2, "Data Science": 3, "Cloud": 2},
        avg_dwell_time=30.0,
        category_switches=3
    )

    result = await agent.classify(summary)
    assert result.persona == Persona.EXPLORER
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_persona_focused_builder():
    """Test FOCUSED_BUILDER persona classification"""
    agent = PersonaAgent()
    summary = BehaviorSummary(
        user_id="test_user_focused",
        total_events=10,
        categories_explored={"AI/ML": 7, "Web Dev": 3},  # 70% in AI/ML
        avg_dwell_time=150.0,
        category_switches=1
    )

    result = await agent.classify(summary)
    assert result.persona == Persona.FOCUSED_BUILDER
    assert result.confidence >= 0.5


@pytest.mark.asyncio
async def test_persona_drop_off_risk():
    """Test DROP_OFF_RISK persona classification"""
    agent = PersonaAgent()
    summary = BehaviorSummary(
        user_id="test_user_drop_off",
        total_events=2,
        exit_events=6,
        enrollment_events=0
    )

    result = await agent.classify(summary)
    assert result.persona == Persona.DROP_OFF_RISK
