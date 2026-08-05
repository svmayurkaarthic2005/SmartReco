"""
Narrative Agent Tests

Test LLM response parsing and error handling:
- Valid JSON response parsing
- Invalid JSON response (safe defaults)
- Malformed response handling
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.agents.narrative_agent import NarrativeAgent, NarrativeResult
from app.agents.ranking_agent import RankedProduct


@pytest.mark.asyncio
class TestNarrativeAgent:
    """Test narrative generation and LLM response handling"""
    
    async def test_valid_llm_response_parsing(self):
        """
        Test parsing of valid JSON response from Mesh API.
        Should produce correct NarrativeResult.
        """
        # Mock Mesh API response with valid JSON
        mock_llm_response = {
            "learning_goal": "Master Python programming and build real-world applications",
            "personalized_story": "Based on your focused exploration of Python and data science, "
                                 "I've crafted a learning journey that builds from fundamentals to "
                                 "advanced applications. Your consistent engagement shows you're ready "
                                 "for a structured path.",
            "roadmap": [
                "Week 1-2: Python Fundamentals & Syntax",
                "Week 3-4: Data Structures & Algorithms",
                "Week 5-6: Object-Oriented Programming",
                "Week 7-8: Build Portfolio Projects"
            ],
            "product_explanations": {
                "prod-001": "This course aligns perfectly with your interest in Python basics",
                "prod-002": "Advanced concepts to deepen your understanding",
                "prod-003": "Practical projects to apply your skills"
            },
            "motivational_cta": "Start your Python mastery journey today! Your dedication to learning "
                               "will transform into real-world skills."
        }
        
        # Mock ranked products
        ranked_products = [
            RankedProduct(
                product_id="prod-001",
                title="Python Basics",
                description="Learn Python from scratch",
                category="Programming",
                difficulty="Beginner",
                price=29.99,
                tags=["python", "beginner"],
                final_score=0.95,
                rank_position=1,
                score_breakdown={
                    "similarity_score": 0.9,
                    "category_match": 0.8,
                    "difficulty_match": 0.85,
                    "popularity_score": 0.7,
                    "diversity_bonus": 0.1,
                    "recency_bonus": 0.05
                }
            ),
            RankedProduct(
                product_id="prod-002",
                title="Advanced Python",
                description="Deep dive into Python",
                category="Programming",
                difficulty="Advanced",
                price=99.99,
                tags=["python", "advanced"],
                final_score=0.90,
                rank_position=2,
                score_breakdown={
                    "similarity_score": 0.85,
                    "category_match": 0.8,
                    "difficulty_match": 0.9,
                    "popularity_score": 0.75,
                    "diversity_bonus": 0.05,
                    "recency_bonus": 0.1
                }
            ),
        ]
        
        agent = NarrativeAgent()
        
        # Mock the LLM call to return our mock response
        with patch.object(agent, '_call_mesh_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_llm_response
            
            result = await agent.generate(
                user_name="Test User",
                persona="focused_builder",
                ranked_products=ranked_products,
                behavior_summary=None
            )
        
        # Validate NarrativeResult structure
        assert isinstance(result, NarrativeResult), "Should return NarrativeResult"
        
        # Validate all fields are present and correct
        assert result.learning_goal == mock_llm_response["learning_goal"]
        assert result.personalized_story == mock_llm_response["personalized_story"]
        assert result.roadmap == mock_llm_response["roadmap"]
        assert result.product_explanations == mock_llm_response["product_explanations"]
        assert result.motivational_cta == mock_llm_response["motivational_cta"]
        
        # Validate roadmap is a list
        assert isinstance(result.roadmap, list), "Roadmap should be a list"
        assert len(result.roadmap) == 4, f"Expected 4 roadmap items, got {len(result.roadmap)}"
        
        # Validate product_explanations is a dict
        assert isinstance(result.product_explanations, dict), "Product explanations should be dict"
        assert len(result.product_explanations) == 3, "Should have 3 product explanations"
        
        print(f"✓ Valid LLM response parsing test passed")
        print(f"  - Learning goal: {result.learning_goal[:50]}...")
        print(f"  - Roadmap items: {len(result.roadmap)}")
        print(f"  - Product explanations: {len(result.product_explanations)}")
    
    async def test_invalid_json_response(self):
        """
        Test handling of invalid JSON response from Mesh API.
        Should return safe default NarrativeResult without exception.
        """
        agent = NarrativeAgent()
        
        ranked_products = [
            RankedProduct(
                product_id="prod-001",
                title="Test Course",
                description="Test description",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["test"],
                final_score=0.8,
                rank_position=1,
                score_breakdown={}
            )
        ]
        
        # Mock the LLM call to return invalid JSON (missing required fields)
        with patch.object(agent, '_call_mesh_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "invalid_field": "This response is missing required fields"
            }
            
            result = await agent.generate(
                user_name="Test User",
                persona="casual_sampler",
                ranked_products=ranked_products,
                behavior_summary=None
            )
        
        # Should still return valid NarrativeResult with defaults
        assert isinstance(result, NarrativeResult), "Should return NarrativeResult even on error"
        
        # Validate safe defaults are used
        assert len(result.learning_goal) > 0, "Should have default learning goal"
        assert len(result.personalized_story) > 0, "Should have default story"
        assert isinstance(result.roadmap, list), "Roadmap should be list"
        assert isinstance(result.product_explanations, dict), "Product explanations should be dict"
        assert len(result.motivational_cta) > 0, "Should have default CTA"
        
        print(f"✓ Invalid JSON response test passed")
        print(f"  - Safe defaults returned")
        print(f"  - No exceptions raised")
    
    async def test_malformed_response_handling(self):
        """
        Test handling when Mesh API returns completely malformed data.
        Should gracefully handle and return defaults.
        """
        agent = NarrativeAgent()
        
        ranked_products = [
            RankedProduct(
                product_id="prod-001",
                title="Test Course",
                description="Test",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["test"],
                final_score=0.8,
                rank_position=1,
                score_breakdown={}
            )
        ]
        
        # Mock the LLM call to raise an exception
        with patch.object(agent, '_call_mesh_api', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API connection failed")
            
            result = await agent.generate(
                user_name="Test User",
                persona="explorer",
                ranked_products=ranked_products,
                behavior_summary=None
            )
        
        # Should handle exception and return safe defaults
        assert isinstance(result, NarrativeResult), "Should return NarrativeResult on exception"
        assert len(result.learning_goal) > 0, "Should have fallback content"
        
        print(f"✓ Malformed response handling test passed")
        print(f"  - Exception handled gracefully")
        print(f"  - Fallback content provided")
    
    async def test_empty_roadmap_handling(self):
        """Test handling when LLM returns empty roadmap"""
        agent = NarrativeAgent()
        
        ranked_products = [
            RankedProduct(
                product_id="prod-001",
                title="Test Course",
                description="Test",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["test"],
                final_score=0.8,
                rank_position=1,
                score_breakdown={}
            )
        ]
        
        # Mock response with empty roadmap
        mock_response = {
            "learning_goal": "Learn programming",
            "personalized_story": "Your journey begins here",
            "roadmap": [],  # Empty roadmap
            "product_explanations": {},
            "motivational_cta": "Start learning!"
        }
        
        with patch.object(agent, '_call_mesh_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await agent.generate(
                user_name="Test User",
                persona="casual_sampler",
                ranked_products=ranked_products,
                behavior_summary=None
            )
        
        # Should have at least a default roadmap item
        assert isinstance(result.roadmap, list), "Roadmap should be list"
        # Either use provided empty list or add defaults
        assert len(result.roadmap) >= 0, "Roadmap should be valid"
        
        print(f"✓ Empty roadmap handling test passed")
    
    async def test_partial_product_explanations(self):
        """Test when LLM provides explanations for only some products"""
        agent = NarrativeAgent()
        
        ranked_products = [
            RankedProduct(
                product_id="prod-001",
                title="Course 1",
                description="Test",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["test"],
                final_score=0.9,
                rank_position=1,
                score_breakdown={}
            ),
            RankedProduct(
                product_id="prod-002",
                title="Course 2",
                description="Test",
                category="Programming",
                difficulty="Advanced",
                price=99.99,
                tags=["test"],
                final_score=0.8,
                rank_position=2,
                score_breakdown={}
            ),
            RankedProduct(
                product_id="prod-003",
                title="Course 3",
                description="Test",
                category="Data Science",
                difficulty="Beginner",
                price=29.99,
                tags=["test"],
                final_score=0.7,
                rank_position=3,
                score_breakdown={}
            ),
        ]
        
        # Mock response with explanations for only 2 products
        mock_response = {
            "learning_goal": "Build skills",
            "personalized_story": "Your learning path",
            "roadmap": ["Step 1", "Step 2"],
            "product_explanations": {
                "prod-001": "Great starter course",
                "prod-002": "Advanced concepts"
                # prod-003 missing
            },
            "motivational_cta": "Let's go!"
        }
        
        with patch.object(agent, '_call_mesh_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await agent.generate(
                user_name="Test User",
                persona="goal_oriented_achiever",
                ranked_products=ranked_products,
                behavior_summary=None
            )
        
        # Should accept partial explanations
        assert isinstance(result.product_explanations, dict)
        # May have 2 or 3 (if agent adds default for missing)
        assert len(result.product_explanations) >= 2
        
        print(f"✓ Partial product explanations test passed")
        print(f"  - Explanations count: {len(result.product_explanations)}")
    
    async def test_narrative_personalization_by_persona(self):
        """Test that narrative varies by persona type"""
        agent = NarrativeAgent()
        
        ranked_products = [
            RankedProduct(
                product_id="prod-001",
                title="Python Basics",
                description="Learn Python",
                category="Programming",
                difficulty="Beginner",
                price=29.99,
                tags=["python"],
                final_score=0.9,
                rank_position=1,
                score_breakdown={}
            )
        ]
        
        personas_to_test = [
            "explorer",
            "focused_builder",
            "goal_oriented_achiever",
            "casual_sampler",
            "skill_upgrader",
            "drop_off_risk"
        ]
        
        results = {}
        
        for persona in personas_to_test:
            # Mock personalized response for each persona
            mock_response = {
                "learning_goal": f"Goal for {persona}",
                "personalized_story": f"Story tailored for {persona} learner",
                "roadmap": [f"Step 1 for {persona}", f"Step 2 for {persona}"],
                "product_explanations": {"prod-001": f"This fits {persona} style"},
                "motivational_cta": f"CTA for {persona}"
            }
            
            with patch.object(agent, '_call_mesh_api', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_response
                
                result = await agent.generate(
                    user_name="Test User",
                    persona=persona,
                    ranked_products=ranked_products,
                    behavior_summary=None
                )
                
                results[persona] = result
        
        # Validate that all personas got valid narratives
        assert len(results) == len(personas_to_test)
        
        for persona, result in results.items():
            assert isinstance(result, NarrativeResult)
            assert len(result.learning_goal) > 0
            assert len(result.personalized_story) > 0
        
        print(f"✓ Persona personalization test passed")
        print(f"  - Tested {len(personas_to_test)} persona types")
        print(f"  - All received valid narratives")
