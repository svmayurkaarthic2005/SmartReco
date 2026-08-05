"""
Ranking Agent Tests

Test ranking logic with various candidate products and behavior patterns:
- Validate score breakdown (6 factors)
- Validate rank positions are sequential 1..8
- Validate top products have highest scores
"""

import pytest
from app.agents.ranking_agent import RankingAgent
from app.agents.retrieval_agent import CandidateProduct
from app.agents.behavior_agent import BehaviorSummary


@pytest.mark.asyncio
class TestRankingAgent:
    """Test product ranking logic"""
    
    async def test_rank_products_basic(self, mock_candidate_products, mock_behavior_summary):
        """
        Test basic ranking with 10 candidate products.
        Validate:
        - Returns top 8 products
        - All have score_breakdown with 6 keys
        - Rank positions are sequential 1..8
        """
        agent = RankingAgent()
        
        result = await agent.rank(
            candidates=mock_candidate_products,
            behavior_summary=mock_behavior_summary,
            persona="focused_builder",
            top_k=8
        )
        
        # Validate result length
        assert len(result) == 8, f"Expected 8 products, got {len(result)}"
        
        # Validate all have score_breakdown with 6 keys
        expected_score_keys = [
            "similarity_score",
            "category_match",
            "difficulty_match",
            "popularity_score",
            "diversity_bonus",
            "recency_bonus"
        ]
        
        for product in result:
            assert product.score_breakdown is not None, \
                f"Product {product.product_id} missing score_breakdown"
            
            assert len(product.score_breakdown) == 6, \
                f"Expected 6 score factors, got {len(product.score_breakdown)}"
            
            for key in expected_score_keys:
                assert key in product.score_breakdown, \
                    f"Missing score factor: {key}"
                
                # Validate score values are numeric and in valid range
                score_value = product.score_breakdown[key]
                assert isinstance(score_value, (int, float)), \
                    f"{key} should be numeric, got {type(score_value)}"
                assert 0 <= score_value <= 1, \
                    f"{key} out of range [0,1]: {score_value}"
        
        # Validate rank positions are sequential 1..8
        rank_positions = [p.rank_position for p in result]
        expected_positions = list(range(1, 9))
        
        assert rank_positions == expected_positions, \
            f"Rank positions should be 1..8, got {rank_positions}"
        
        # Validate products are sorted by final_score (descending)
        final_scores = [p.final_score for p in result]
        sorted_scores = sorted(final_scores, reverse=True)
        
        assert final_scores == sorted_scores, \
            "Products should be sorted by final_score descending"
        
        print(f"✓ Basic ranking test passed")
        print(f"  - Products ranked: {len(result)}")
        print(f"  - Top product score: {result[0].final_score:.3f}")
        print(f"  - Bottom product score: {result[-1].final_score:.3f}")
        print(f"  - Score breakdown keys: {list(result[0].score_breakdown.keys())}")
    
    async def test_rank_products_similarity_weight(self):
        """
        Test that similarity scores are properly weighted.
        Products with higher similarity should rank higher.
        """
        # Create products with varying similarity scores
        candidates = [
            CandidateProduct(
                product_id=f"prod-{i:03d}",
                title=f"Course {i}",
                description="Test course",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["python", "programming"],
                similarity_score=0.95 - (i * 0.1)  # Decreasing similarity
            )
            for i in range(10)
        ]
        
        behavior = BehaviorSummary(
            total_events=50,
            view_count=30,
            search_count=15,
            enrollment_count=2,
            exit_count=3,
            avg_dwell_time=90.0,
            top_categories=["Programming"],
            category_distribution={"Programming": 100},
            search_keywords=["python"],
            has_purchases=True,
            recency_days=1,
            engagement_score=0.8
        )
        
        agent = RankingAgent()
        result = await agent.rank(
            candidates=candidates,
            behavior_summary=behavior,
            persona="focused_builder",
            top_k=8
        )
        
        # The first candidate (highest similarity) should be in top positions
        top_product_ids = [p.product_id for p in result[:3]]
        assert "prod-000" in top_product_ids or "prod-001" in top_product_ids, \
            "Highest similarity products should rank in top 3"
        
        print(f"✓ Similarity weight test passed")
        print(f"  - Top 3 products: {top_product_ids}")
    
    async def test_rank_products_category_match(self):
        """
        Test category matching bonus.
        Products matching user's top categories should rank higher.
        """
        # Create products with different categories
        candidates = [
            CandidateProduct(
                product_id="matching-1",
                title="Python Course",
                description="Learn Python",
                category="Programming",  # Matches top category
                difficulty="Intermediate",
                price=49.99,
                tags=["python"],
                similarity_score=0.7
            ),
            CandidateProduct(
                product_id="matching-2",
                title="Data Science Course",
                description="Learn Data Science",
                category="Data Science",  # Matches second category
                difficulty="Intermediate",
                price=49.99,
                tags=["data-science"],
                similarity_score=0.7
            ),
            CandidateProduct(
                product_id="non-matching",
                title="Cooking Course",
                description="Learn Cooking",
                category="Cooking",  # Does NOT match
                difficulty="Intermediate",
                price=49.99,
                tags=["cooking"],
                similarity_score=0.7
            ),
        ] * 3  # Repeat to get enough candidates
        
        behavior = BehaviorSummary(
            total_events=50,
            view_count=30,
            search_count=15,
            enrollment_count=2,
            exit_count=3,
            avg_dwell_time=90.0,
            top_categories=["Programming", "Data Science"],
            category_distribution={"Programming": 60, "Data Science": 40},
            search_keywords=["python", "data"],
            has_purchases=True,
            recency_days=1,
            engagement_score=0.8
        )
        
        agent = RankingAgent()
        result = await agent.rank(
            candidates=candidates[:10],  # Use first 10
            behavior_summary=behavior,
            persona="focused_builder",
            top_k=8
        )
        
        # Check that matching products have category_match bonus
        for product in result:
            if product.category in ["Programming", "Data Science"]:
                assert product.score_breakdown["category_match"] > 0, \
                    f"Product {product.product_id} should have category match bonus"
        
        print(f"✓ Category match test passed")
    
    async def test_rank_products_difficulty_alignment(self):
        """
        Test difficulty matching for different personas.
        - EXPLORER: Should prefer Beginner/Intermediate
        - FOCUSED_BUILDER: Should prefer Intermediate/Advanced
        """
        candidates = [
            CandidateProduct(
                product_id="beginner-1",
                title="Beginner Course",
                description="For beginners",
                category="Programming",
                difficulty="Beginner",
                price=29.99,
                tags=["beginner"],
                similarity_score=0.8
            ),
            CandidateProduct(
                product_id="intermediate-1",
                title="Intermediate Course",
                description="For intermediate learners",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["intermediate"],
                similarity_score=0.8
            ),
            CandidateProduct(
                product_id="advanced-1",
                title="Advanced Course",
                description="For advanced learners",
                category="Programming",
                difficulty="Advanced",
                price=99.99,
                tags=["advanced"],
                similarity_score=0.8
            ),
        ] * 4  # Repeat to get enough candidates
        
        behavior = BehaviorSummary(
            total_events=100,
            view_count=60,
            search_count=30,
            enrollment_count=5,
            exit_count=5,
            avg_dwell_time=150.0,
            top_categories=["Programming"],
            category_distribution={"Programming": 100},
            search_keywords=["advanced", "expert"],
            has_purchases=True,
            recency_days=1,
            engagement_score=0.9
        )
        
        agent = RankingAgent()
        
        # Test for FOCUSED_BUILDER (should prefer Advanced)
        result_focused = await agent.rank(
            candidates=candidates[:10],
            behavior_summary=behavior,
            persona="focused_builder",
            top_k=8
        )
        
        # Count difficulty levels in top 5
        top_5_difficulties = [p.difficulty for p in result_focused[:5]]
        advanced_count = top_5_difficulties.count("Advanced")
        
        # FOCUSED_BUILDER should have some advanced courses in top 5
        assert advanced_count >= 1, \
            f"FOCUSED_BUILDER should prefer advanced courses, got {top_5_difficulties}"
        
        print(f"✓ Difficulty alignment test passed")
        print(f"  - Top 5 difficulties: {top_5_difficulties}")
    
    async def test_rank_products_diversity(self):
        """
        Test diversity bonus to avoid all products from same subcategory.
        """
        # Create products with same category but different subcategories
        candidates = [
            CandidateProduct(
                product_id=f"python-{i}",
                title=f"Python Course {i}",
                description="Learn Python",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["python", "programming"],
                similarity_score=0.85
            )
            for i in range(5)
        ] + [
            CandidateProduct(
                product_id=f"javascript-{i}",
                title=f"JavaScript Course {i}",
                description="Learn JavaScript",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["javascript", "programming"],
                similarity_score=0.80
            )
            for i in range(5)
        ]
        
        behavior = BehaviorSummary(
            total_events=50,
            view_count=30,
            search_count=15,
            enrollment_count=2,
            exit_count=3,
            avg_dwell_time=90.0,
            top_categories=["Programming"],
            category_distribution={"Programming": 100},
            search_keywords=["programming"],
            has_purchases=True,
            recency_days=1,
            engagement_score=0.8
        )
        
        agent = RankingAgent()
        result = await agent.rank(
            candidates=candidates,
            behavior_summary=behavior,
            persona="explorer",
            top_k=8
        )
        
        # Check that we have some diversity (not all Python or all JavaScript)
        python_count = sum(1 for p in result if "python" in p.product_id)
        javascript_count = sum(1 for p in result if "javascript" in p.product_id)
        
        # Should have mix of both (not 0 or 8 of either)
        assert 0 < python_count < 8, \
            f"Should have diversity, got {python_count} Python courses"
        assert 0 < javascript_count < 8, \
            f"Should have diversity, got {javascript_count} JavaScript courses"
        
        print(f"✓ Diversity test passed")
        print(f"  - Python courses: {python_count}")
        print(f"  - JavaScript courses: {javascript_count}")
    
    async def test_rank_products_edge_cases(self):
        """Test edge cases in ranking"""
        
        # Edge case 1: Empty candidates
        agent = RankingAgent()
        behavior = BehaviorSummary(
            total_events=10,
            view_count=5,
            search_count=3,
            enrollment_count=0,
            exit_count=2,
            avg_dwell_time=30.0,
            top_categories=["Programming"],
            category_distribution={"Programming": 100},
            search_keywords=["python"],
            has_purchases=False,
            recency_days=1,
            engagement_score=0.5
        )
        
        result = await agent.rank(
            candidates=[],
            behavior_summary=behavior,
            persona="casual_sampler",
            top_k=8
        )
        
        assert len(result) == 0, "Empty candidates should return empty result"
        
        # Edge case 2: Fewer candidates than top_k
        few_candidates = [
            CandidateProduct(
                product_id=f"prod-{i}",
                title=f"Course {i}",
                description="Test",
                category="Programming",
                difficulty="Intermediate",
                price=49.99,
                tags=["test"],
                similarity_score=0.8
            )
            for i in range(3)
        ]
        
        result = await agent.rank(
            candidates=few_candidates,
            behavior_summary=behavior,
            persona="casual_sampler",
            top_k=8
        )
        
        # Should return all 3 products
        assert len(result) == 3, f"Should return all available products, got {len(result)}"
        
        # Rank positions should still be sequential
        assert [p.rank_position for p in result] == [1, 2, 3], \
            "Rank positions should be sequential even with fewer products"
        
        print(f"✓ Edge cases test passed")
        print(f"  - Empty candidates: handled")
        print(f"  - Fewer candidates: handled")
