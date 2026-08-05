"""
Persona Agent Tests

Test persona classification logic with various behavior patterns:
- EXPLORER: Multiple categories, moderate dwell time
- FOCUSED_BUILDER: Single category dominance, high dwell time
- DROP_OFF_RISK: High exit rate, low engagement
"""

import pytest
from app.agents.persona_agent import PersonaAgent, Persona
from app.agents.behavior_agent import BehaviorSummary


@pytest.mark.asyncio
class TestPersonaAgent:
    """Test persona classification logic"""
    
    async def test_explorer_persona(self):
        """
        Test EXPLORER classification:
        - 4 categories explored
        - Moderate dwell time (30s)
        - Frequent category switches (3)
        """
        behavior = BehaviorSummary(
            total_events=50,
            view_count=30,
            search_count=15,
            enrollment_count=1,
            exit_count=5,
            avg_dwell_time=30.0,
            top_categories=["Programming", "Data Science", "Design", "Business"],
            category_distribution={
                "Programming": 25,
                "Data Science": 25,
                "Design": 25,
                "Business": 25
            },
            search_keywords=["python", "data science", "design", "business"],
            has_purchases=False,
            recency_days=1,
            engagement_score=0.6
        )
        
        agent = PersonaAgent()
        result = await agent.classify(behavior)
        
        # Validate persona is EXPLORER
        assert result.persona == Persona.EXPLORER, \
            f"Expected EXPLORER, got {result.persona.value}"
        
        # Validate confidence is reasonable
        assert result.confidence > 0.5, \
            f"Confidence too low: {result.confidence}"
        assert result.confidence <= 1.0, \
            f"Confidence out of range: {result.confidence}"
        
        # Validate reasoning exists
        assert len(result.reasoning) > 0, "Reasoning should not be empty"
        assert "explore" in result.reasoning.lower() or "categor" in result.reasoning.lower(), \
            "Reasoning should mention exploration or categories"
        
        print(f"✓ EXPLORER persona test passed")
        print(f"  - Persona: {result.persona.value}")
        print(f"  - Confidence: {result.confidence:.2f}")
        print(f"  - Reasoning: {result.reasoning}")
    
    async def test_focused_builder_persona(self):
        """
        Test FOCUSED_BUILDER classification:
        - One category dominates (70%)
        - High dwell time (150s)
        - Enrollments present
        """
        behavior = BehaviorSummary(
            total_events=60,
            view_count=45,
            search_count=10,
            enrollment_count=3,
            exit_count=2,
            avg_dwell_time=150.0,
            top_categories=["Programming", "Computer Science", "Algorithms"],
            category_distribution={
                "Programming": 70,
                "Computer Science": 20,
                "Algorithms": 10
            },
            search_keywords=["python advanced", "algorithms", "design patterns"],
            has_purchases=True,
            recency_days=1,
            engagement_score=0.9
        )
        
        agent = PersonaAgent()
        result = await agent.classify(behavior)
        
        # Validate persona is FOCUSED_BUILDER
        assert result.persona == Persona.FOCUSED_BUILDER, \
            f"Expected FOCUSED_BUILDER, got {result.persona.value}"
        
        # Validate high confidence due to strong signals
        assert result.confidence > 0.7, \
            f"Confidence should be high for strong signals: {result.confidence}"
        
        # Validate reasoning mentions focus or commitment
        reasoning_lower = result.reasoning.lower()
        assert any(keyword in reasoning_lower for keyword in ["focus", "commit", "deep", "consistent"]), \
            "Reasoning should mention focus or commitment"
        
        print(f"✓ FOCUSED_BUILDER persona test passed")
        print(f"  - Persona: {result.persona.value}")
        print(f"  - Confidence: {result.confidence:.2f}")
        print(f"  - Reasoning: {result.reasoning}")
    
    async def test_drop_off_risk_persona(self):
        """
        Test DROP_OFF_RISK classification:
        - High exit events (6 exits, 2 views)
        - No enrollments
        - Very low engagement
        """
        behavior = BehaviorSummary(
            total_events=8,
            view_count=2,
            search_count=0,
            enrollment_count=0,
            exit_count=6,
            avg_dwell_time=5.0,
            top_categories=["Programming"],
            category_distribution={"Programming": 100},
            search_keywords=[],
            has_purchases=False,
            recency_days=30,
            engagement_score=0.1
        )
        
        agent = PersonaAgent()
        result = await agent.classify(behavior)
        
        # Validate persona is DROP_OFF_RISK
        assert result.persona == Persona.DROP_OFF_RISK, \
            f"Expected DROP_OFF_RISK, got {result.persona.value}"
        
        # Validate confidence
        assert result.confidence > 0.5, \
            f"Confidence should be reasonable: {result.confidence}"
        
        # Validate reasoning mentions risk or disengagement
        reasoning_lower = result.reasoning.lower()
        assert any(keyword in reasoning_lower for keyword in ["risk", "disengage", "exit", "concern"]), \
            "Reasoning should mention risk or disengagement"
        
        print(f"✓ DROP_OFF_RISK persona test passed")
        print(f"  - Persona: {result.persona.value}")
        print(f"  - Confidence: {result.confidence:.2f}")
        print(f"  - Reasoning: {result.reasoning}")
    
    async def test_goal_oriented_achiever_persona(self):
        """
        Test GOAL_ORIENTED_ACHIEVER classification:
        - High enrollment count
        - Consistent engagement
        - Clear learning path
        """
        behavior = BehaviorSummary(
            total_events=80,
            view_count=40,
            search_count=20,
            enrollment_count=8,
            exit_count=12,
            avg_dwell_time=120.0,
            top_categories=["Programming", "Data Science", "Cloud Computing"],
            category_distribution={
                "Programming": 40,
                "Data Science": 35,
                "Cloud Computing": 25
            },
            search_keywords=["certification", "career", "job ready", "complete course"],
            has_purchases=True,
            recency_days=1,
            engagement_score=0.85
        )
        
        agent = PersonaAgent()
        result = await agent.classify(behavior)
        
        # Validate persona is GOAL_ORIENTED_ACHIEVER
        assert result.persona == Persona.GOAL_ORIENTED_ACHIEVER, \
            f"Expected GOAL_ORIENTED_ACHIEVER, got {result.persona.value}"
        
        # High confidence expected
        assert result.confidence > 0.7, \
            f"Confidence should be high: {result.confidence}"
        
        print(f"✓ GOAL_ORIENTED_ACHIEVER persona test passed")
        print(f"  - Persona: {result.persona.value}")
        print(f"  - Confidence: {result.confidence:.2f}")
    
    async def test_casual_sampler_persona(self):
        """
        Test CASUAL_SAMPLER classification:
        - Low event count
        - Short dwell times
        - No enrollments
        - Browsing behavior
        """
        behavior = BehaviorSummary(
            total_events=15,
            view_count=12,
            search_count=3,
            enrollment_count=0,
            exit_count=0,
            avg_dwell_time=20.0,
            top_categories=["Hobbies", "Lifestyle", "Art"],
            category_distribution={
                "Hobbies": 50,
                "Lifestyle": 30,
                "Art": 20
            },
            search_keywords=["fun", "hobby", "beginner"],
            has_purchases=False,
            recency_days=5,
            engagement_score=0.4
        )
        
        agent = PersonaAgent()
        result = await agent.classify(behavior)
        
        # Validate persona is CASUAL_SAMPLER
        assert result.persona == Persona.CASUAL_SAMPLER, \
            f"Expected CASUAL_SAMPLER, got {result.persona.value}"
        
        assert result.confidence > 0.5
        
        print(f"✓ CASUAL_SAMPLER persona test passed")
        print(f"  - Persona: {result.persona.value}")
        print(f"  - Confidence: {result.confidence:.2f}")
    
    async def test_skill_upgrader_persona(self):
        """
        Test SKILL_UPGRADER classification:
        - Professional/career keywords
        - Advanced content preference
        - Specific skill searches
        """
        behavior = BehaviorSummary(
            total_events=45,
            view_count=30,
            search_count=15,
            enrollment_count=2,
            exit_count=0,
            avg_dwell_time=90.0,
            top_categories=["Professional Development", "Technology", "Business"],
            category_distribution={
                "Professional Development": 50,
                "Technology": 30,
                "Business": 20
            },
            search_keywords=["advanced", "professional", "certification", "career advancement"],
            has_purchases=True,
            recency_days=2,
            engagement_score=0.75
        )
        
        agent = PersonaAgent()
        result = await agent.classify(behavior)
        
        # Validate persona is SKILL_UPGRADER
        assert result.persona == Persona.SKILL_UPGRADER, \
            f"Expected SKILL_UPGRADER, got {result.persona.value}"
        
        assert result.confidence > 0.6
        
        print(f"✓ SKILL_UPGRADER persona test passed")
        print(f"  - Persona: {result.persona.value}")
        print(f"  - Confidence: {result.confidence:.2f}")
    
    async def test_edge_case_minimal_data(self):
        """Test persona classification with minimal data"""
        behavior = BehaviorSummary(
            total_events=1,
            view_count=1,
            search_count=0,
            enrollment_count=0,
            exit_count=0,
            avg_dwell_time=10.0,
            top_categories=["General"],
            category_distribution={"General": 100},
            search_keywords=[],
            has_purchases=False,
            recency_days=0,
            engagement_score=0.1
        )
        
        agent = PersonaAgent()
        result = await agent.classify(behavior)
        
        # Should still return a valid persona (likely CASUAL_SAMPLER or EXPLORER)
        assert result.persona in list(Persona), "Should return valid persona"
        
        # Confidence should be lower due to minimal data
        assert result.confidence < 0.7, \
            f"Confidence should be lower for minimal data: {result.confidence}"
        
        print(f"✓ Minimal data test passed")
        print(f"  - Persona: {result.persona.value}")
        print(f"  - Confidence: {result.confidence:.2f}")
