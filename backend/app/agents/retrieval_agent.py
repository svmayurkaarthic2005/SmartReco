"""Retrieval Agent - Fetches relevant content from vector store"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from collections import Counter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.behavior_agent import BehaviorSummary
from app.agents.persona_agent import PersonaResult, Persona
from app.models.product import Product, DifficultyLevel
from app.observability.langsmith_client import trace_run


@dataclass
class RetrievalPlan:
    """Plan for retrieving candidate products"""
    semantic_query: str
    difficulty_filter: Optional[str] = None
    category_filter: Optional[str] = None
    exclude_product_ids: List[str] = field(default_factory=list)
    n_results: int = 15
    boost_keywords: List[str] = field(default_factory=list)


@dataclass
class CandidateProduct:
    """Candidate product from retrieval"""
    product_id: str
    title: str
    description: str
    category: str
    difficulty: str
    price: float
    tags: List[str]
    similarity_score: float


class RetrievalPlanner:
    """
    Plans retrieval strategy based on user behavior and persona.
    
    Generates semantic queries, applies filters, and configures
    retrieval parameters optimized for each persona type.
    """
    
    def plan(
        self,
        summary: BehaviorSummary,
        persona: PersonaResult,
        parent_run_id: Optional[str] = None
    ) -> RetrievalPlan:
        """
        Create retrieval plan based on behavioral summary and persona.
        
        Args:
            summary: User behavioral summary
            persona: Persona classification result
            parent_run_id: Optional parent trace ID for nesting
            
        Returns:
            RetrievalPlan with query, filters, and parameters
            
        Example:
            >>> planner = RetrievalPlanner()
            >>> plan = planner.plan(summary, persona)
            >>> print(plan.semantic_query)
            "Learning path for Python, Machine Learning. Topics: neural networks, tensorflow"
        """
        with trace_run(
            name="retrieval_planning",
            run_type="chain",
            inputs={
                "user_id": summary.user_id,
                "persona": persona.persona.value,
                "categories_explored": len(summary.categories_explored),
                "search_queries": len(summary.search_queries)
            },
            parent_run_id=parent_run_id,
            tags=["agent", "retrieval", "planning"]
        ) as run_id:
            # Build semantic query
            semantic_query = self._build_semantic_query(summary)
            print(f"[RETRIEVAL-DEBUG] Semantic Query: {semantic_query[:200]}...")
            
            # Determine difficulty filter based on persona
            difficulty_filter = self._get_difficulty_filter(persona, summary)
            
            # Determine n_results based on persona
            n_results = self._get_n_results(persona)
            
            # Exclude already-enrolled products & explicitly dropped products to recommend fresh next steps
            enrolled_ids = list(getattr(summary, 'enrolled_product_ids', []))
            unenrolled_ids = list(getattr(summary, 'unenrolled_product_ids', []))
            exclude_product_ids = list(set(enrolled_ids + unenrolled_ids))
            
            # Extract boost keywords from search queries
            boost_keywords = self._extract_boost_keywords(summary.search_queries)
            
            # Get category filter (if applicable)
            category_filter = self._get_category_filter(persona, summary)
            print(f"[RETRIEVAL-DEBUG] Category Filter: {category_filter}")
            
            plan = RetrievalPlan(
                semantic_query=semantic_query,
                difficulty_filter=difficulty_filter,
                category_filter=category_filter,
                exclude_product_ids=exclude_product_ids,
                n_results=n_results,
                boost_keywords=boost_keywords
            )
            
            return plan
    
    def _build_semantic_query(self, summary: BehaviorSummary) -> str:
        """
        Build semantic query from user behavior.
        
        YouTube/Udemy-style recommendations:
        1. Prioritize ENROLLED courses (active learning) - recommend next steps in same domain
        2. Include completed courses (progression signal)
        3. Only explore new domains if user has < 2 enrollments (early exploration phase)
        
        For cold-start users (no meaningful interactions), returns empty string to trigger diverse sampling.
        """
        parts = []
        
        # Get enrolled courses and categories (highest priority - ACTIVE learning)
        enrolled = getattr(summary, 'enrolled_product_titles', [])
        enrolled_categories = getattr(summary, 'enrolled_categories', [])
        
        if enrolled:
            # For users with enrollments, FOCUS recommendations on enrolled domains
            # This mimics YouTube: "Continue watching" + "Because you watched X"
            if enrolled_categories and len(enrolled_categories) >= 2:
                parts.append(f"Next courses to advance skills in {' and '.join(enrolled_categories)} following current enrollments: {', '.join(enrolled[:2])}")
            elif enrolled_categories:
                parts.append(f"Advanced progression in {enrolled_categories[0]} following enrolled course: {', '.join(enrolled[:2])}")
            else:
                # enrolled_categories may be empty if products had no category set
                parts.append(f"Next steps following enrolled courses: {', '.join(enrolled[:2])}")
        
        # Completion signal (courses where user completed modules/lessons)
        completion_counts = getattr(summary, 'completion_counts', {})
        if completion_counts:
            completed_categories = list(completion_counts.keys())[:2]
            if completed_categories:
                parts.append(f"Advanced courses in actively progressing domains: {', '.join(completed_categories)}")
        
        # ONLY explore new domains if user has < 2 enrollments (exploration phase)
        # This prevents random category suggestions when user is focused on their enrolled courses
        if len(enrolled) < 2:
            # Recent viewed titles (exploration pattern - only for new users)
            recent_titles = getattr(summary, 'recent_product_titles', [])
            if recent_titles:
                filtered_recent = [t for t in recent_titles if t not in enrolled][:2]
                if filtered_recent:
                    parts.append(f"Also exploring: {', '.join(filtered_recent)}")
        
        # Budget tier preference (always include if available)
        avg_b = getattr(summary, 'avg_budget', 0.0)
        if avg_b > 0:
            parts.append(f"Target price range around ${int(avg_b)}")

        # Search queries (explicit interest signal)
        recent_queries = summary.search_queries[-2:] if summary.search_queries else []
        if recent_queries:
            parts.append(f"Search interest: {', '.join(recent_queries)}")
            
        if parts:
            return ". ".join(parts) + "."
        
        # Cold-start: no product views, no enrollments, no categories, no searches
        # Return empty string to signal that we should use diverse category sampling instead
        return ""
    
    def _get_difficulty_filter(
        self,
        persona: PersonaResult,
        summary: BehaviorSummary
    ) -> Optional[str]:
        """
        Determine difficulty filter based on persona.

        Rules:
        - CAREER_SWITCHER → "beginner" (new to field, needs foundation)
        - FOCUSED_BUILDER → dominant difficulty from user's behavior
        - OVERWHELMED_LEARNER → None (allow any; let ranking demote hard content)
        - EXPLORER, PRICE_SENSITIVE, DROP_OFF_RISK → None (no filter)
        """
        persona_type = persona.persona

        if persona_type == Persona.CAREER_SWITCHER:
            return DifficultyLevel.BEGINNER.value

        elif persona_type == Persona.FOCUSED_BUILDER:
            # Use dominant difficulty level from user behavior if available
            dom = getattr(summary, 'dominant_difficulty', None)
            return dom if dom else None

        # All other personas (EXPLORER, PRICE_SENSITIVE, DROP_OFF_RISK,
        # OVERWHELMED_LEARNER) — no hard difficulty filter; let ranking handle it
        return None
    
    def _get_n_results(self, persona: PersonaResult) -> int:
        """
        Determine number of results based on persona.
        """
        if persona.persona == Persona.EXPLORER:
            return 20
        else:
            return 15
    
    def _extract_boost_keywords(self, search_queries: List[str]) -> List[str]:
        """
        Extract boost keywords from search queries.
        """
        if not search_queries:
            return []
        
        keywords = []
        for query in search_queries:
            words = query.lower().replace(',', ' ').replace('.', ' ').split()
            keywords.extend(words)
        
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen and len(keyword) > 2:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    def _get_category_filter(
        self,
        persona: PersonaResult,
        summary: BehaviorSummary
    ) -> Optional[str]:
        """
        Get category filter if applicable.
        
        Only apply hard category filter if user has a DOMINANT single-category focus (>= 70% weight).
        For multi-interest users (e.g. 50/50 AI/ML & Blockchain), return None to allow diverse retrieval.
        """
        if summary.categories_explored:
            total_weight = sum(summary.categories_explored.values())
            if total_weight > 0:
                dominant_category, weight = max(
                    summary.categories_explored.items(),
                    key=lambda x: x[1]
                )
                # Only filter if one category is TRULY dominant (70%+ of activity)
                # This ensures multi-interest users get diverse recommendations
                if (weight / total_weight) >= 0.70:
                    return dominant_category
        
        return None


class VectorRetrievalAgent:
    """
    Retrieves candidate products using vector similarity search.
    
    Uses ChromaDB for semantic search with fallback to PostgreSQL
    for cold-start scenarios.
    """
    
    def __init__(self, chroma_client, embedding_service):
        """
        Initialize VectorRetrievalAgent.
        
        Args:
            chroma_client: ChromaDB client wrapper
            embedding_service: Service for generating embeddings
        """
        self.chroma_client = chroma_client
        self.embedding_service = embedding_service
    
    async def retrieve(
        self,
        plan: RetrievalPlan,
        db: AsyncSession,
        parent_run_id: Optional[str] = None
    ) -> List[CandidateProduct]:
        """
        Retrieve candidate products based on retrieval plan.
        
        Steps:
        1. If semantic query is empty (cold-start), skip vector search and use diverse DB sampling
        2. Otherwise, generate query embedding
        3. Search ChromaDB with filters
        4. Filter out already-viewed products
        5. If < 5 results, fallback to PostgreSQL
        6. Merge and deduplicate results
        
        Args:
            plan: RetrievalPlan with query and filters
            db: Database session for fallback queries
            parent_run_id: Optional parent trace ID for nesting
            
        Returns:
            List of CandidateProduct objects
        """
        with trace_run(
            name="vector_retrieval",
            run_type="retriever",
            inputs={
                "query_preview": plan.semantic_query[:100] if plan.semantic_query else "[cold-start: empty query]",
                "n_results": plan.n_results,
                "difficulty_filter": plan.difficulty_filter,
                "category_filter": plan.category_filter
            },
            parent_run_id=parent_run_id,
            tags=["agent", "retrieval", "vector"]
        ) as run_id:
            # Cold-start: no semantic query → skip vector search, use diverse sampling
            if not plan.semantic_query or plan.semantic_query.strip() == "":
                print("Cold-start detected: empty semantic query. Using diverse category sampling.")
                return await self._fallback_retrieve(plan, db)
            
            candidates = []
            
            # Step 1: Generate query embedding
            try:
                query_embedding = await self.embedding_service.generate_embedding(
                    plan.semantic_query
                )
            except Exception as e:
                print(f"Embedding generation failed: {e}")
                # Fallback to PostgreSQL only
                fallback_results = await self._fallback_retrieve(plan, db)
                return fallback_results
            
            # Step 2: Build ChromaDB filter
            chroma_filter = self._build_chroma_filter(plan)
            
            # Step 3: Search ChromaDB
            try:
                chroma_results = await self.chroma_client.search_products(
                    query_embedding=query_embedding,
                    n_results=plan.n_results,
                    where=chroma_filter
                )
                
                # Step 4: Convert to CandidateProduct and filter exclusions (case-insensitive ID & title check)
                exclude_ids_lower = {str(pid).lower() for pid in plan.exclude_product_ids}
                for result in chroma_results:
                    product_id = result.get('id') or result.get('product_id')
                    title = result.get('title', '')
                    
                    if str(product_id).lower() not in exclude_ids_lower:
                        raw_dist = float(result.get('distance', 0.5))
                        # Convert ChromaDB cosine distance (0.0 to 2.0) to similarity score (0.0 to 1.0)
                        similarity_score = max(0.0, min(1.0, 1.0 - (raw_dist / 2.0)))
                        
                        candidate = CandidateProduct(
                            product_id=product_id,
                            title=result.get('title', ''),
                            description=result.get('description', ''),
                            category=result.get('category', ''),
                            difficulty=result.get('difficulty', ''),
                            price=result.get('price', 0.0),
                            tags=result.get('tags', []),
                            similarity_score=similarity_score
                        )
                        candidates.append(candidate)
            
            except Exception as e:
                print(f"ChromaDB search failed: {e}")
                # Continue to fallback
            
            # Step 5: If < 5 results, fallback to PostgreSQL
            if len(candidates) < 5:
                fallback_products = await self._fallback_retrieve(plan, db)
                
                # Merge results (dedupe by product_id)
                existing_ids = {c.product_id for c in candidates}
                for product in fallback_products:
                    if product.product_id not in existing_ids:
                        candidates.append(product)
                        existing_ids.add(product.product_id)
            
            return candidates
    
    def _build_chroma_filter(self, plan: RetrievalPlan) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB where filter from plan.
        
        Example: {"difficulty": "beginner", "category": "python"}
        """
        filter_dict = {}
        
        if plan.difficulty_filter:
            filter_dict['difficulty'] = plan.difficulty_filter
        
        if plan.category_filter:
            filter_dict['category'] = plan.category_filter
        
        return filter_dict if filter_dict else None
    
    async def _fallback_retrieve(
        self,
        plan: RetrievalPlan,
        db: AsyncSession
    ) -> List[CandidateProduct]:
        """
        Fallback retrieval using PostgreSQL.
        
        For cold-start (empty semantic query), retrieves a diverse sample across all categories.
        Otherwise queries products table ordered by created_at desc, limit 20 (then cap to 15).
        Apply category_filter if set to return domain-relevant courses.
        """
        from uuid import UUID
        from sqlalchemy import func
        from collections import defaultdict

        # Cold-start: no semantic query → diverse category sampling
        if not plan.semantic_query or plan.semantic_query.strip() == "":
            # Get all unique categories
            cat_stmt = select(Product.category).distinct()
            cat_result = await db.execute(cat_stmt)
            categories = [c for c in cat_result.scalars().all() if c]
            
            # Sample 2-3 products from each category (up to 15 total)
            candidates = []
            per_category = max(2, 15 // len(categories)) if categories else 3
            
            for category in categories:
                stmt = (
                    select(Product)
                    .where(Product.category == category)
                    .order_by(func.random())  # Random sampling for diversity
                    .limit(per_category)
                )
                if plan.exclude_product_ids:
                    try:
                        exclude_uuids = [UUID(pid) for pid in plan.exclude_product_ids]
                        stmt = stmt.where(Product.id.notin_(exclude_uuids))
                    except ValueError:
                        pass
                
                result = await db.execute(stmt)
                products = list(result.scalars().all())
                
                for product in products:
                    candidate = CandidateProduct(
                        product_id=str(product.id),
                        title=product.title,
                        description=product.description,
                        category=product.category,
                        difficulty=product.difficulty_level.value,
                        price=product.price,
                        tags=product.tags,
                        similarity_score=0.5  # Neutral score for cold-start
                    )
                    candidates.append(candidate)
                
                if len(candidates) >= 15:
                    break
            
            return candidates[:15]

        # Regular fallback: semantic query exists
        def build_stmt(with_category: bool):
            stmt = select(Product).order_by(Product.created_at.desc()).limit(20)
            if plan.difficulty_filter:
                stmt = stmt.where(Product.difficulty_level == plan.difficulty_filter)
            if with_category and plan.category_filter:
                stmt = stmt.where(Product.category == plan.category_filter)
            if plan.exclude_product_ids:
                try:
                    exclude_uuids = [UUID(pid) for pid in plan.exclude_product_ids]
                    stmt = stmt.where(Product.id.notin_(exclude_uuids))
                except ValueError:
                    pass
            return stmt

        # First try with category filter applied
        result = await db.execute(build_stmt(with_category=True))
        products = list(result.scalars().all())

        # If not enough, fall back to no category filter
        if len(products) < 5:
            result = await db.execute(build_stmt(with_category=False))
            all_fallback = list(result.scalars().all())
            
            # Sort all_fallback products so those matching keywords in semantic_query rank higher
            query_lower = (plan.semantic_query or "").lower()
            def match_score(p: Product):
                score = 0
                p_cat = (p.category or "").lower()
                p_title = (p.title or "").lower()
                if p_cat and p_cat in query_lower:
                    score += 5
                if p_title and p_title in query_lower:
                    score += 3
                return score

            all_fallback.sort(key=match_score, reverse=True)
            products = all_fallback

        # Convert to CandidateProduct
        candidates = []
        for product in products[:15]:
            candidate = CandidateProduct(
                product_id=str(product.id),
                title=product.title,
                description=product.description,
                category=product.category,
                difficulty=product.difficulty_level.value,
                price=product.price,
                tags=product.tags,
                similarity_score=0.0
            )
            candidates.append(candidate)
        
        return candidates
