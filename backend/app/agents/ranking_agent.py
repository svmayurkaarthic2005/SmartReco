"""Ranking Agent - Re-ranks candidate products using multi-factor scoring"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter

from app.agents.behavior_agent import BehaviorSummary
from app.agents.persona_agent import PersonaResult, Persona
from app.agents.retrieval_agent import CandidateProduct
from app.models.product import Product, DifficultyLevel
from app.observability.langsmith_client import trace_run


@dataclass
class RankedProduct:
    """Product with ranking score and breakdown"""
    product_id: str
    title: str
    description: str
    category: str
    difficulty: str
    price: float
    tags: List[str]
    final_score: float
    rank_position: int
    score_breakdown: Dict[str, float]  # Explainability: shows each scoring factor


class RankingAgent:
    """
    Re-ranks candidate products using weighted multi-factor scoring.
    
    Scoring Factors (6):
    1. Semantic Similarity (35%) - Vector similarity from retrieval
    2. Difficulty Match (20%) - Matches persona's expected difficulty
    3. Learning Progression (15%) - One level above current skill
    4. Price Fit (10%) - Price sensitivity for PRICE_SENSITIVE persona
    5. Tag Overlap (10%) - Tags match search queries/categories
    6. Freshness (10%) - Recent content prioritized
    
    All signals normalized 0-1, weighted sum produces final score.
    """
    
    # Scoring weights (must sum to 1.0)
    WEIGHT_SEMANTIC = 0.30
    WEIGHT_DIFFICULTY_MATCH = 0.15
    WEIGHT_LEARNING_PROGRESSION = 0.15
    WEIGHT_PRICE_FIT = 0.10
    WEIGHT_TAG_OVERLAP = 0.10
    WEIGHT_FRESHNESS = 0.10
    WEIGHT_DURATION_FIT = 0.10  # Was previously unlabelled — now declared (total = 1.0)
    
    def rank(
        self,
        candidates: List[CandidateProduct],
        summary: BehaviorSummary,
        persona: PersonaResult,
        db_products: Dict[str, Product],
        parent_run_id: Optional[str] = None
    ) -> List[RankedProduct]:
        """
        Rank candidates using multi-factor scoring.
        
        Args:
            candidates: Retrieved candidate products
            summary: User behavioral summary
            persona: Persona classification result
            db_products: Dict mapping product_id to Product model (for metadata)
            parent_run_id: Optional parent trace ID for nesting
            
        Returns:
            List of RankedProduct sorted by final_score (top 8)
            
        Example:
            >>> agent = RankingAgent()
            >>> ranked = agent.rank(candidates, summary, persona, products_dict)
            >>> for product in ranked[:3]:
            ...     print(f"{product.rank_position}. {product.title} - {product.final_score:.3f}")
            1. Advanced Python - 0.892
            2. Machine Learning Basics - 0.845
            3. Data Science Fundamentals - 0.812
        """
        with trace_run(
            name="re_ranking",
            run_type="chain",
            inputs={
                "input_count": len(candidates),
                "persona": persona.persona.value,
                "user_id": summary.user_id
            },
            parent_run_id=parent_run_id,
            tags=["agent", "ranking"]
        ) as run_id:
            if not candidates:
                return []
            
            print(f"[RANK-DEBUG] Ranking {len(candidates)} candidates")
            print(f"[RANK-DEBUG] enrolled_ids: {summary.enrolled_product_ids}")
            print(f"[RANK-DEBUG] enrolled_titles: {summary.enrolled_product_titles}")
            print(f"[RANK-DEBUG] unenrolled_ids: {summary.unenrolled_product_ids}")
            print(f"[RANK-DEBUG] unenrolled_titles: {summary.unenrolled_product_titles}")
            
            # Compute all scores for each candidate
            ranked_products = []
            
            for candidate in candidates:
                # Get full product metadata from database
                product = db_products.get(candidate.product_id)
                
                # Compute individual scoring factors
                scores = self._compute_scores(
                    candidate,
                    product,
                    summary,
                    persona,
                    candidates  # Pass all candidates for normalization
                )
                
                # 1. Enrolled Track Boost: Boost courses in user's ACTIVE enrolled categories
                enrollment_boost = 0.0
                enrolled_titles = [t.lower() for t in getattr(summary, 'enrolled_product_titles', [])]
                enrolled_ids = getattr(summary, 'enrolled_product_ids', [])

                # Use the explicitly-tracked enrolled_categories field (accurate after ENROLL/UNENROLL events)
                enrolled_cats = set(c.lower() for c in getattr(summary, 'enrolled_categories', []))

                # Also add top explored categories from summary (weight > 50) as secondary signal
                if summary and summary.categories_explored:
                    top_cats = [c.lower() for c, w in summary.categories_explored.items() if w > 50]
                    enrolled_cats.update(top_cats)

                if candidate.category and candidate.category.lower() in enrolled_cats:
                    enrollment_boost = 0.40

                # Check if user is currently enrolled in this exact course
                is_already_enrolled = (
                    candidate.product_id in enrolled_ids
                    or str(candidate.product_id).lower() in [str(e).lower() for e in enrolled_ids]
                    or candidate.title.lower() in enrolled_titles
                )

                # 2. Unenrollment Penalty: if user explicitly dropped this course, hard-clamp
                unenrolled_ids_lower = [str(pid).lower() for pid in getattr(summary, 'unenrolled_product_ids', [])]
                unenrolled_titles_lower = [t.lower() for t in getattr(summary, 'unenrolled_product_titles', [])]
                unenrolled_cats = [c.lower() for c in getattr(summary, 'unenrolled_categories', [])]

                is_unenrolled_course = (
                    str(candidate.product_id).lower() in unenrolled_ids_lower
                    or candidate.title.lower() in unenrolled_titles_lower
                )

                unenrolled_course_penalty = -1.0 if is_unenrolled_course else 0.0
                unenrolled_cat_penalty = -0.35 if (candidate.category and candidate.category.lower() in unenrolled_cats and candidate.category.lower() not in enrolled_cats) else 0.0

                # No penalty needed — already_enrolled courses will be hard-clamped below
                already_enrolled_penalty = 0.0

                # 3. Completion Boost: if user completed lessons/modules in this category
                completion_boost = 0.0
                completion_counts = getattr(summary, 'completion_counts', {})
                if candidate.category and completion_counts:
                    comp_key = next((k for k in completion_counts if k.lower() == candidate.category.lower()), None)
                    if comp_key:
                        completions = completion_counts[comp_key]
                        total_completions = max(1, sum(completion_counts.values()))
                        completion_boost = min(0.30, 0.15 + (completions / total_completions) * 0.15)

                # 4. Category & Recency Boost
                cat_boost = 0.0
                last_viewed_cat = getattr(summary, 'last_viewed_category', None)
                
                if candidate.category:
                    if last_viewed_cat and candidate.category.lower() == last_viewed_cat.lower():
                        cat_boost = 0.25
                    elif summary.categories_explored:
                        matching_key = next((k for k in summary.categories_explored if k.lower() == candidate.category.lower()), None)
                        if matching_key:
                            total_w = max(1, sum(summary.categories_explored.values()))
                            cat_w = summary.categories_explored[matching_key]
                            cat_boost = 0.10 + (cat_w / total_w) * 0.15

                # 5. Re-enrollment commitment boost
                re_enroll_boost = 0.0
                re_enrolled_cats = getattr(summary, 're_enrolled_categories', [])
                if candidate.category and any(c.lower() == candidate.category.lower() for c in re_enrolled_cats):
                    re_enroll_boost = 0.25

                # Weighted sum + boosts + penalties
                raw_score = (
                    scores['semantic'] * self.WEIGHT_SEMANTIC +
                    scores['difficulty_match'] * self.WEIGHT_DIFFICULTY_MATCH +
                    scores['learning_progression'] * self.WEIGHT_LEARNING_PROGRESSION +
                    scores['price_fit'] * self.WEIGHT_PRICE_FIT +
                    scores['tag_overlap'] * self.WEIGHT_TAG_OVERLAP +
                    scores['freshness'] * self.WEIGHT_FRESHNESS +
                    scores['duration_fit'] * self.WEIGHT_DURATION_FIT +
                    enrollment_boost +
                    completion_boost +
                    cat_boost +
                    re_enroll_boost +
                    already_enrolled_penalty +
                    unenrolled_course_penalty +
                    unenrolled_cat_penalty
                )

                # Hard clamp final_score = 0.0 for dropped OR already-enrolled courses
                # Already enrolled courses should not appear in recommendations (next steps only)
                if is_unenrolled_course or is_already_enrolled:
                    final_score = 0.0
                else:
                    final_score = min(1.0, max(0.05, raw_score))
                
                ranked_product = RankedProduct(
                    product_id=candidate.product_id,
                    title=candidate.title,
                    description=candidate.description,
                    category=candidate.category,
                    difficulty=candidate.difficulty,
                    price=candidate.price,
                    tags=candidate.tags,
                    final_score=final_score,
                    rank_position=0,  # Will be assigned after sorting
                    score_breakdown=scores
                )
                
                ranked_products.append(ranked_product)
            
            # Exclude zero-score (dropped) courses if non-zero candidates exist
            zero_scored = [p for p in ranked_products if p.final_score == 0.0]
            valid_ranked = [p for p in ranked_products if p.final_score > 0.0]
            if zero_scored:
                print(f"[RANK-DEBUG] EXCLUDED {len(zero_scored)} courses (score=0): {[p.title for p in zero_scored]}")
            if valid_ranked:
                ranked_products = valid_ranked

            # Sort by final_score descending
            ranked_products.sort(key=lambda x: x.final_score, reverse=True)
            
            # Assign rank positions (1-indexed)
            for i, product in enumerate(ranked_products, start=1):
                product.rank_position = i
            
            # Get top 8
            top_8 = ranked_products[:8]
            print(f"[RANK-DEBUG] Final top {len(top_8)}: {[(p.title, f'{p.final_score:.2f}') for p in top_8]}")
            
            return top_8
    
    def _compute_scores(
        self,
        candidate: CandidateProduct,
        product: Product,
        summary: BehaviorSummary,
        persona: PersonaResult,
        all_candidates: List[CandidateProduct]
    ) -> Dict[str, float]:
        """
        Compute all 6 scoring factors for a candidate.
        
        Returns:
            Dict with keys: semantic, difficulty_match, learning_progression,
                           price_fit, tag_overlap, freshness
        """
        return {
            'semantic': self._score_semantic_similarity(candidate, all_candidates),
            'difficulty_match': self._score_difficulty_match(candidate, persona, summary),
            'learning_progression': self._score_learning_progression(candidate, summary),
            'price_fit': self._score_price_fit(candidate, persona, summary, all_candidates),
            'tag_overlap': self._score_tag_overlap(candidate, summary),
            'freshness': self._score_freshness(product) if product else 0.5,
            'duration_fit': self._score_duration_fit(candidate, summary)
        }
    
    def _score_semantic_similarity(
        self,
        candidate: CandidateProduct,
        all_candidates: List[CandidateProduct]
    ) -> float:
        """
        Score based on vector similarity (normalized 0-1).
        
        Weight: 35%
        
        Normalize by dividing by max similarity in batch to ensure
        relative ranking even if absolute scores are low.
        """
        if not all_candidates:
            return 0.5
        
        # Get max similarity score in batch
        max_similarity = max(c.similarity_score for c in all_candidates)
        
        if max_similarity == 0:
            return 0.5
        
        # Normalize to 0-1
        normalized = candidate.similarity_score / max_similarity
        
        return max(0.0, min(1.0, normalized))
    
    def _score_difficulty_match(
        self,
        candidate: CandidateProduct,
        persona: PersonaResult,
        summary: BehaviorSummary
    ) -> float:
        """
        Score based on difficulty match with persona expectations.
        
        Weight: 20%
        
        Rules:
        - CAREER_SWITCHER → beginner (1.0 if beginner, 0.5 if intermediate, 0.0 if advanced)
        - OVERWHELMED_LEARNER → intermediate (1.0 if intermediate, 0.5 if beginner/advanced)
        - FOCUSED_BUILDER → dominant_level from behavior
        - Others → any (0.5 flat)
        """
        candidate_difficulty = candidate.difficulty.lower()
        
        # Determine expected difficulty based on persona
        if persona.persona == Persona.CAREER_SWITCHER:
            expected = DifficultyLevel.BEGINNER.value
        
        elif persona.persona == Persona.OVERWHELMED_LEARNER:
            expected = DifficultyLevel.INTERMEDIATE.value
        
        elif persona.persona == Persona.FOCUSED_BUILDER:
            # Use dominant difficulty from behavior
            expected = self._get_dominant_difficulty(summary)
        
        else:
            # EXPLORER, PRICE_SENSITIVE, DROP_OFF_RISK → any difficulty
            return 0.5
        
        # Score based on match
        if candidate_difficulty == expected:
            return 1.0
        elif self._is_adjacent_difficulty(candidate_difficulty, expected):
            return 0.5
        else:
            return 0.0
    
    def _score_learning_progression(
        self,
        candidate: CandidateProduct,
        summary: BehaviorSummary
    ) -> float:
        """
        Score based on learning progression (one level above current).
        
        Weight: 15%
        
        Rules:
        - Product is one level above current: 1.0
        - Product is same level: 0.5
        - Product is below current: 0.2
        """
        # Determine user's current dominant difficulty
        current_difficulty = self._get_dominant_difficulty(summary)
        
        if not current_difficulty:
            return 0.5  # No data, neutral score
        
        candidate_difficulty = candidate.difficulty.lower()
        
        # Define progression
        difficulty_order = [
            DifficultyLevel.BEGINNER.value,
            DifficultyLevel.INTERMEDIATE.value,
            DifficultyLevel.ADVANCED.value
        ]
        
        try:
            current_idx = difficulty_order.index(current_difficulty)
            candidate_idx = difficulty_order.index(candidate_difficulty)
            
            diff = candidate_idx - current_idx
            
            if diff == 1:  # One level above
                return 1.0
            elif diff == 0:  # Same level
                return 0.5
            else:  # Below or far above
                return 0.2
        
        except ValueError:
            return 0.5  # Invalid difficulty, neutral score
    
    def _score_price_fit(
        self,
        candidate: CandidateProduct,
        persona: PersonaResult,
        summary: BehaviorSummary,
        all_candidates: List[CandidateProduct]
    ) -> float:
        """
        Score based on price fit and user's observed budget range.
        
        Weight: 10%
        """
        avg_budget = getattr(summary, 'avg_budget', 0.0)
        min_budget = getattr(summary, 'min_budget', 0.0)
        max_budget = getattr(summary, 'max_budget', 0.0)

        if avg_budget > 0:
            # Check if candidate falls within user's observed budget range (+/- $15 tolerance)
            if (min_budget - 15.0) <= candidate.price <= (max_budget + 15.0):
                base_score = 1.0
            else:
                # Calculate penalty based on price distance from user's average budget
                price_diff = abs(candidate.price - avg_budget)
                base_score = max(0.1, 1.0 - (price_diff / avg_budget))

            if persona.persona == Persona.PRICE_SENSITIVE:
                max_price = max(c.price for c in all_candidates) if all_candidates else 1.0
                if max_price > 0:
                    base_score = base_score * 0.5 + (1.0 - (candidate.price / max_price)) * 0.5

            return max(0.0, min(1.0, base_score))

        # Default fallback if no prices observed
        if persona.persona == Persona.PRICE_SENSITIVE:
            max_price = max(c.price for c in all_candidates) if all_candidates else 1.0
            if max_price == 0:
                return 0.5
            return max(0.0, min(1.0, 1.0 - (candidate.price / max_price)))
        
        return 0.5
    
    def _score_tag_overlap(
        self,
        candidate: CandidateProduct,
        summary: BehaviorSummary
    ) -> float:
        """
        Score based on tag overlap with user interests.
        
        Weight: 10%
        
        Count how many product tags appear in:
        - Search query words
        - Category names
        
        Normalize by number of tags: overlap_count / len(tags)
        """
        if not candidate.tags:
            return 0.0
        
        # Build user interest keywords from search queries and categories
        user_keywords = set()
        
        # Add words from search queries
        for query in summary.search_queries:
            words = query.lower().replace(',', ' ').replace('.', ' ').split()
            user_keywords.update(words)
        
        # Add category names
        for category in summary.categories_explored.keys():
            category_words = category.lower().replace('-', ' ').replace('_', ' ').split()
            user_keywords.update(category_words)
        
        # Count overlapping tags
        overlap_count = 0
        for tag in candidate.tags:
            tag_lower = tag.lower()
            if tag_lower in user_keywords:
                overlap_count += 1
        
        # Normalize by number of tags
        score = overlap_count / len(candidate.tags)
        
        return max(0.0, min(1.0, score))
    
    def _score_freshness(self, product: Product) -> float:
        """
        Score based on product freshness (recent content prioritized).
        
        Weight: 10%
        
        Formula: score = 1 / (1 + 0.01 * days_old)
        - Products < 30 days old: score near 1.0
        - Products > 100 days old: score near 0.5
        - Products > 200 days old: score near 0.33
        """
        if not product or not product.created_at:
            return 0.5  # No data, neutral score
        
        # Calculate days old
        days_old = (datetime.utcnow() - product.created_at).days
        
        # Apply decay formula
        score = 1.0 / (1.0 + 0.01 * days_old)
        
        return max(0.0, min(1.0, score))
    
    def _get_dominant_difficulty(self, summary: BehaviorSummary) -> str:
        """
        Determine user's dominant difficulty level from behavioral summary.
        """
        dom = getattr(summary, 'dominant_difficulty', None)
        if dom:
            return dom.lower()
        return DifficultyLevel.INTERMEDIATE.value

    def _score_duration_fit(self, candidate: CandidateProduct, summary: BehaviorSummary) -> float:
        """
        Score candidate based on user's preferred course duration depth.

        Uses avg_duration_preference from BehaviorSummary (hours the user
        typically spends on courses they engage with deeply).
        If no preference data, returns neutral 0.5.
        """
        pref_duration = getattr(summary, 'avg_duration_preference', 0.0)
        if pref_duration <= 0:
            return 0.5  # No preference data — neutral score

        # CandidateProduct doesn't carry duration_hours in its schema.
        # Proxy: price is loosely correlated with course length (longer courses cost more).
        # Use price as a rough proxy: $0-30 → short, $30-80 → medium, $80+ → long
        price = candidate.price or 0.0
        estimated_hours = 5.0 + (price / 10.0)  # e.g. $50 course ≈ 10h

        if estimated_hours <= 0:
            return 0.5

        ratio = pref_duration / estimated_hours
        # Ideal ratio ≈ 1.0 (preference matches course length)
        # Penalise proportionally for deviation
        score = max(0.0, 1.0 - abs(1.0 - ratio) * 0.5)
        return max(0.0, min(1.0, score))
    
    def _is_adjacent_difficulty(self, difficulty1: str, difficulty2: str) -> bool:
        """Check if two difficulty levels are adjacent (one step apart)"""
        difficulty_order = [
            DifficultyLevel.BEGINNER.value,
            DifficultyLevel.INTERMEDIATE.value,
            DifficultyLevel.ADVANCED.value
        ]
        
        try:
            idx1 = difficulty_order.index(difficulty1)
            idx2 = difficulty_order.index(difficulty2)
            return abs(idx1 - idx2) == 1
        except ValueError:
            return False
