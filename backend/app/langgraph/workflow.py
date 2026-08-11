"""LangGraph workflow for multi-agent recommendation system"""

from typing import TypedDict, Optional, List, Annotated, Any
from uuid import UUID
import uuid
from langgraph.graph import StateGraph, START, END
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents import (
    BehaviorAgent, BehaviorSummary,
    PersonaAgent, PersonaResult,
    RetrievalPlanner, RetrievalPlan,
    VectorRetrievalAgent, CandidateProduct,
    RankingAgent, RankedProduct,
    NarrativeAgent, NarrativeResult,
    RecoveryAgent, RecoveryResult
)
from app.vector import get_chroma_client, get_embedding_service
from app.models import Product


# Global references (injected by runner)
_db_session: Optional[AsyncSession] = None
_user_name: str = "there"


class AgentState(TypedDict):
    """State passed between workflow nodes"""
    user_id: str
    db: Optional[Any]               # Per-invocation DB session (thread-safe)
    behavior_summary: Optional[BehaviorSummary]
    persona_result: Optional[PersonaResult]
    retrieval_plan: Optional[RetrievalPlan]
    candidate_products: List[CandidateProduct]
    ranked_products: List[RankedProduct]
    narrative_result: Optional[NarrativeResult]
    recovery_result: Optional[RecoveryResult]
    is_recovery_mode: bool
    error: Optional[str]
    trace_id: str
    user_name: str                  # User display name, passed per-invocation
    parent_run_id: Optional[str]  # For LangSmith tracing


async def behavior_node(state: AgentState) -> dict:
    """
    Node 1: Analyze user behavior from events.
    
    Returns: {behavior_summary}
    """
    try:
        user_id = UUID(state["user_id"])
        parent_run_id = state.get("parent_run_id")
        db = state.get("db") or _db_session  # prefer per-invocation session

        # Instantiate agent
        behavior_agent = BehaviorAgent(db)

        # Analyze behavior (last 72 hours)
        summary = await behavior_agent.analyze(
            user_id,
            lookback_hours=72,
            parent_run_id=parent_run_id
        )
        
        print(f"[{state['trace_id']}] Behavior analyzed: {summary.total_events} events")
        
        return {"behavior_summary": summary}
    
    except Exception as e:
        print(f"[{state['trace_id']}] Behavior node error: {e}")
        return {"error": f"Behavior analysis failed: {str(e)}"}


async def persona_node(state: AgentState) -> dict:
    """
    Node 2: Classify user into persona.
    
    Returns: {persona_result}
    """
    try:
        if not state["behavior_summary"]:
            return {"error": "No behavior summary available"}
        
        parent_run_id = state.get("parent_run_id")
        
        # Instantiate agent
        persona_agent = PersonaAgent()
        
        # Classify persona
        persona = await persona_agent.classify(
            state["behavior_summary"],
            parent_run_id=parent_run_id
        )
        
        print(f"[{state['trace_id']}] Persona classified: {persona.persona.value} ({persona.confidence:.2f})")
        
        # Close Redis connection
        await persona_agent.close()
        
        return {"persona_result": persona}
    
    except Exception as e:
        print(f"[{state['trace_id']}] Persona node error: {e}")
        return {"error": f"Persona classification failed: {str(e)}"}


async def recovery_check_node(state: AgentState) -> dict:
    """
    Node 3: Check if user is at risk of dropping off.
    
    Returns: {is_recovery_mode}
    """
    try:
        if not state["behavior_summary"]:
            return {"is_recovery_mode": False}
        
        user_id = UUID(state["user_id"])
        parent_run_id = state.get("parent_run_id")
        db = state.get("db") or _db_session  # prefer per-invocation session

        # Instantiate agent
        recovery_agent = RecoveryAgent()

        # Detect risk
        is_at_risk = await recovery_agent.detect_risk(
            user_id,
            state["behavior_summary"],
            db,
            parent_run_id=parent_run_id
        )
        
        print(f"[{state['trace_id']}] Recovery check: at_risk={is_at_risk}")
        
        return {"is_recovery_mode": is_at_risk}
    
    except Exception as e:
        print(f"[{state['trace_id']}] Recovery check error: {e}")
        return {"is_recovery_mode": False}  # Default to normal mode on error


async def retrieval_plan_node(state: AgentState) -> dict:
    """
    Node 4: Plan retrieval strategy based on persona.
    
    Returns: {retrieval_plan}
    """
    try:
        if not state["behavior_summary"] or not state["persona_result"]:
            return {"error": "Missing behavior or persona data"}
        
        parent_run_id = state.get("parent_run_id")
        
        # Instantiate planner
        planner = RetrievalPlanner()
        
        # Create plan
        plan = planner.plan(
            state["behavior_summary"],
            state["persona_result"],
            parent_run_id=parent_run_id
        )
        
        print(f"[{state['trace_id']}] Retrieval planned: {plan.n_results} results, filter={plan.difficulty_filter}")
        
        return {"retrieval_plan": plan}
    
    except Exception as e:
        print(f"[{state['trace_id']}] Retrieval plan error: {e}")
        return {"error": f"Retrieval planning failed: {str(e)}"}


async def vector_retrieval_node(state: AgentState) -> dict:
    """
    Node 5: Retrieve candidate products from vector store.
    
    Returns: {candidate_products}
    """
    try:
        if not state["retrieval_plan"]:
            return {"error": "No retrieval plan available"}
        
        parent_run_id = state.get("parent_run_id")
        db = state.get("db") or _db_session  # prefer per-invocation session

        # Instantiate retrieval agent
        chroma = get_chroma_client()
        embeddings = get_embedding_service()
        retrieval_agent = VectorRetrievalAgent(chroma, embeddings)

        # Retrieve candidates
        candidates = await retrieval_agent.retrieve(
            state["retrieval_plan"],
            db,
            parent_run_id=parent_run_id
        )
        
        # DIVERSITY ENFORCEMENT: Ensure recommendations focus on ENROLLED categories only
        # YouTube/Udemy style: recommend next steps in domains you're ACTIVELY LEARNING
        # NOT random domains you just viewed/clicked
        if state["behavior_summary"]:
            enrolled_categories = getattr(state["behavior_summary"], 'enrolled_categories', [])
            enrolled_ids = getattr(state["behavior_summary"], 'enrolled_product_ids', [])
            
            if enrolled_categories:
                from collections import Counter
                candidate_categories = Counter(c.category for c in candidates)
                
                # Define minimum courses per enrolled category based on total enrolled domains
                if len(enrolled_categories) == 1:
                    min_per_category = 5  # Single focus: get plenty of options
                elif len(enrolled_categories) == 2:
                    min_per_category = 3  # Two domains: 3 each = 6 total
                elif len(enrolled_categories) == 3:
                    min_per_category = 2  # Three domains: 2 each = 6 total
                else:  # 4+ domains
                    min_per_category = 2  # Four+ domains: 2 each = 8+ total
                
                # Check ALL enrolled categories (not just missing ones)
                categories_needing_boost = []
                for enrolled_cat in enrolled_categories:
                    current_count = candidate_categories.get(enrolled_cat, 0)
                    if current_count < min_per_category:
                        categories_needing_boost.append((enrolled_cat, min_per_category - current_count))
                
                if categories_needing_boost:
                    print(f"[DIVERSITY-FIX] Enrolled categories need boosting: {[(cat, needed) for cat, needed in categories_needing_boost]}")
                    
                    # Fetch and inject additional courses FROM ENROLLED CATEGORIES ONLY
                    from uuid import UUID
                    for category, needed_count in categories_needing_boost:
                        stmt = select(Product).where(Product.category == category).limit(needed_count + 1)  # +1 for safety
                        # Exclude already-enrolled courses
                        if enrolled_ids:
                            try:
                                exclude_uuids = [UUID(pid) for pid in enrolled_ids]
                                stmt = stmt.where(Product.id.notin_(exclude_uuids))
                            except ValueError:
                                pass
                        
                        # Also exclude products already in candidates
                        existing_product_ids = {c.product_id for c in candidates}
                        
                        result = await db.execute(stmt)
                        products_to_inject = result.scalars().all()
                        
                        injected_count = 0
                        for product in products_to_inject:
                            if str(product.id) not in existing_product_ids and injected_count < needed_count:
                                from app.agents import CandidateProduct
                                candidate = CandidateProduct(
                                    product_id=str(product.id),
                                    title=product.title,
                                    description=product.description,
                                    category=product.category,
                                    difficulty=product.difficulty_level.value,
                                    price=product.price,
                                    tags=product.tags,
                                    similarity_score=0.85  # High score to ensure they rank well
                                )
                                candidates.append(candidate)
                                injected_count += 1
                                print(f"[DIVERSITY-FIX] Injected {product.category} course: {product.title}")
                    
                    print(f"[DIVERSITY-FIX] Focused on {len(enrolled_categories)} enrolled domains, Minimum per domain: {min_per_category}")
                
                # FILTER OUT non-enrolled categories for focused users (2+ enrollments)
                # This ensures recommendations stay focused on active learning domains
                if len(enrolled_categories) >= 2:
                    # Keep only courses from enrolled categories + high-ranking other courses
                    filtered_candidates = []
                    other_category_candidates = []
                    
                    for c in candidates:
                        if c.category in enrolled_categories:
                            filtered_candidates.append(c)
                        else:
                            # Keep non-enrolled courses only if they have very high similarity (>0.9)
                            if c.similarity_score >= 0.90:
                                other_category_candidates.append(c)
                    
                    # Add top 2 non-enrolled courses (for serendipity)
                    filtered_candidates.extend(sorted(other_category_candidates, key=lambda x: x.similarity_score, reverse=True)[:2])
                    
                    if len(filtered_candidates) < len(candidates):
                        print(f"[DIVERSITY-FIX] Filtered to enrolled categories: {len(candidates)} → {len(filtered_candidates)} candidates")
                        candidates = filtered_candidates
                
                # BALANCE CHECK: For multi-domain users (3+ enrolled categories), cap over-represented categories
                if len(enrolled_categories) >= 3:
                    # Recount after injections
                    candidate_categories = Counter(c.category for c in candidates)
                    
                    # Cap: no enrolled category should have more than 2x the minimum
                    max_per_enrolled_category = min_per_category * 2
                    
                    over_represented = [cat for cat in enrolled_categories 
                                      if candidate_categories.get(cat, 0) > max_per_enrolled_category]
                    
                    if over_represented:
                        print(f"[DIVERSITY-FIX] Capping over-represented categories to {max_per_enrolled_category} courses: {over_represented}")
                        balanced_candidates = []
                        
                        for c in candidates:
                            if c.category in over_represented:
                                current_count = sum(1 for bc in balanced_candidates if bc.category == c.category)
                                if current_count < max_per_enrolled_category:
                                    balanced_candidates.append(c)
                            else:
                                balanced_candidates.append(c)
                        
                        candidates = balanced_candidates
                        print(f"[DIVERSITY-FIX] Balanced to {len(candidates)} candidates")

        
        print(f"[{state['trace_id']}] Retrieved {len(candidates)} candidates")
        
        return {"candidate_products": candidates}
    
    except Exception as e:
        print(f"[{state['trace_id']}] Vector retrieval error: {e}")
        return {"error": f"Vector retrieval failed: {str(e)}"}


async def ranking_node(state: AgentState) -> dict:
    """
    Node 6: Rank candidates using multi-factor scoring.
    
    Returns: {ranked_products}
    """
    try:
        candidates = state["candidate_products"]
        summary = state.get("behavior_summary")
        exclude_uuids = []
        if summary:
            for pid in getattr(summary, 'enrolled_product_ids', []) + getattr(summary, 'unenrolled_product_ids', []):
                try:
                    exclude_uuids.append(UUID(pid))
                except (ValueError, TypeError):
                    pass

        # Fallback 1: if no candidates were retrieved, fetch non-excluded products from DB
        db = state.get("db") or _db_session  # prefer per-invocation session
        if not candidates:
            stmt = select(Product).order_by(Product.created_at.desc()).limit(12)
            if exclude_uuids:
                stmt = stmt.where(Product.id.notin_(exclude_uuids))
            result = await db.execute(stmt)
            db_products = result.scalars().all()

            # If all DB products were excluded, fallback to all DB products
            if not db_products:
                stmt_all = select(Product).order_by(Product.created_at.desc()).limit(12)
                db_products = (await db.execute(stmt_all)).scalars().all()

            from app.agents import CandidateProduct
            candidates = [
                CandidateProduct(
                    product_id=str(p.id),
                    title=p.title,
                    description=p.description,
                    category=p.category,
                    difficulty=p.difficulty_level.value,
                    price=p.price,
                    tags=p.tags,
                    similarity_score=0.5
                )
                for p in db_products
            ]
            print(f"[{state['trace_id']}] Ranking fallback: using {len(candidates)} DB products")

        if not candidates:
            return {"error": "No candidates to rank (even DB fallback empty)"}
        
        if not state["behavior_summary"] or not state["persona_result"]:
            return {"error": "Missing behavior or persona data"}
        
        parent_run_id = state.get("parent_run_id")
        
        # Fetch full product metadata from database for candidates AND enrolled products
        product_ids = [UUID(c.product_id) for c in candidates]
        enrolled_ids = []
        if summary and hasattr(summary, 'enrolled_product_ids'):
            for pid in summary.enrolled_product_ids:
                try:
                    enrolled_ids.append(UUID(pid))
                except (ValueError, TypeError):
                    pass
        all_ids = list(set(product_ids + enrolled_ids))
        stmt = select(Product).where(Product.id.in_(all_ids))
        result = await db.execute(stmt)
        products_dict = {str(p.id): p for p in result.scalars().all()}
        
        # Instantiate ranking agent
        ranking_agent = RankingAgent()
        
        # Rank candidates
        ranked = ranking_agent.rank(
            candidates,
            state["behavior_summary"],
            state["persona_result"],
            products_dict,
            parent_run_id=parent_run_id
        )

        # Fallback 2: If ranking produced 0 valid products (e.g. all candidates were hard-clamped),
        # convert non-dropped, non-enrolled candidates to ranked products with baseline score 0.5
        if not ranked and candidates:
            from app.agents import RankedProduct
            unenrolled_ids_set = {str(pid).lower() for pid in getattr(summary, 'unenrolled_product_ids', [])}
            unenrolled_titles_set = {t.lower() for t in getattr(summary, 'unenrolled_product_titles', [])}
            enrolled_ids_set = {str(pid).lower() for pid in getattr(summary, 'enrolled_product_ids', [])}
            enrolled_titles_set = {t.lower() for t in getattr(summary, 'enrolled_product_titles', [])}
            
            non_dropped = [
                c for c in candidates
                if str(c.product_id).lower() not in unenrolled_ids_set
                and c.title.lower() not in unenrolled_titles_set
                and str(c.product_id).lower() not in enrolled_ids_set
                and c.title.lower() not in enrolled_titles_set
            ]
            fallback_source = non_dropped if non_dropped else candidates
            
            ranked = [
                RankedProduct(
                    product_id=c.product_id,
                    title=c.title,
                    description=c.description,
                    category=c.category,
                    difficulty=c.difficulty,
                    price=c.price,
                    tags=c.tags,
                    final_score=0.5,
                    rank_position=idx + 1,
                    score_breakdown={}
                )
                for idx, c in enumerate(fallback_source[:8])
            ]
        
        top_score = ranked[0].final_score if ranked else 0.0
        print(f"[{state['trace_id']}] Ranked {len(ranked)} products (top score: {top_score:.3f})")
        
        return {"ranked_products": ranked}
    
    except Exception as e:
        print(f"[{state['trace_id']}] Ranking error: {e}")
        return {"error": f"Ranking failed: {str(e)}"}


async def narrative_node(state: AgentState) -> dict:
    """
    Node 7: Generate personalized narrative.
    
    Returns: {narrative_result}
    """
    try:
        if not state["ranked_products"]:
            return {"error": "No ranked products for narrative"}
        
        if not state["behavior_summary"] or not state["persona_result"]:
            return {"error": "Missing behavior or persona data"}
        
        parent_run_id = state.get("parent_run_id")
        
        # Instantiate narrative agent
        narrative_agent = NarrativeAgent()
        
        # Generate narrative
        narrative = await narrative_agent.generate(
            state["behavior_summary"],
            state["persona_result"],
            state["ranked_products"],
            parent_run_id=parent_run_id
        )
        
        print(f"[{state['trace_id']}] Narrative generated: {narrative.learning_goal[:50]}...")
        
        # Close Redis connection
        await narrative_agent.close()
        
        return {"narrative_result": narrative}
    
    except Exception as e:
        print(f"[{state['trace_id']}] Narrative error: {e}")
        return {"error": f"Narrative generation failed: {str(e)}"}


async def recovery_node(state: AgentState) -> dict:
    """
    Node 8: Generate recovery recommendation for at-risk users.
    
    Returns: {recovery_result, ranked_products}
    """
    try:
        if not state["behavior_summary"] or not state["persona_result"]:
            return {"error": "Missing behavior or persona data"}
        
        user_id = UUID(state["user_id"])
        db = state.get("db") or _db_session  # prefer per-invocation session
        
        # For recovery mode, we still need some products to recommend
        # Use retrieval to get candidates
        planner = RetrievalPlanner()
        plan = planner.plan(state["behavior_summary"], state["persona_result"])
        
        chroma = get_chroma_client()
        embeddings = get_embedding_service()
        retrieval_agent = VectorRetrievalAgent(chroma, embeddings)
        candidates = await retrieval_agent.retrieve(plan, db)
        
        # Rank them
        product_ids = [UUID(c.product_id) for c in candidates]
        stmt = select(Product).where(Product.id.in_(product_ids))
        result = await db.execute(stmt)
        products_dict = {str(p.id): p for p in result.scalars().all()}
        
        ranking_agent = RankingAgent()
        ranked = ranking_agent.rank(
            candidates,
            state["behavior_summary"],
            state["persona_result"],
            products_dict
        )
        
        # Generate recovery recommendation
        recovery_agent = RecoveryAgent()
        recovery = await recovery_agent.generate_recovery_recommendation(
            user_id,
            state["behavior_summary"],
            ranked,
            user_name=state.get("user_name") or _user_name  # prefer per-invocation name
        )
        
        print(f"[{state['trace_id']}] Recovery generated: {len(recovery.recovery_products)} products")
        
        return {
            "recovery_result": recovery,
            "ranked_products": ranked  # Include for narrative node
        }
    
    except Exception as e:
        print(f"[{state['trace_id']}] Recovery error: {e}")
        return {"error": f"Recovery generation failed: {str(e)}"}


def route_after_recovery_check(state: AgentState) -> str:
    """
    Conditional routing: recovery mode or normal mode?
    
    Returns:
        "recovery_node" if at risk
        "retrieval_plan_node" if normal
    """
    if state.get("is_recovery_mode", False):
        return "recovery_node"
    else:
        return "retrieval_plan_node"


def build_workflow() -> StateGraph:
    """
    Build the complete LangGraph workflow.
    
    Flow:
        START → behavior → persona → recovery_check
                                         ├→ [at risk] → recovery → narrative → END
                                         └→ [normal] → retrieval → vector → ranking → narrative → END
    
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("behavior_node", behavior_node)
    workflow.add_node("persona_node", persona_node)
    workflow.add_node("recovery_check_node", recovery_check_node)
    workflow.add_node("retrieval_plan_node", retrieval_plan_node)
    workflow.add_node("vector_retrieval_node", vector_retrieval_node)
    workflow.add_node("ranking_node", ranking_node)
    workflow.add_node("narrative_node", narrative_node)
    workflow.add_node("recovery_node", recovery_node)
    
    # Add edges
    workflow.add_edge(START, "behavior_node")
    workflow.add_edge("behavior_node", "persona_node")
    workflow.add_edge("persona_node", "recovery_check_node")
    
    # Conditional routing from recovery_check
    workflow.add_conditional_edges(
        "recovery_check_node",
        route_after_recovery_check,
        {
            "recovery_node": "recovery_node",
            "retrieval_plan_node": "retrieval_plan_node"
        }
    )
    
    # Recovery path
    workflow.add_edge("recovery_node", "narrative_node")
    
    # Normal path
    workflow.add_edge("retrieval_plan_node", "vector_retrieval_node")
    workflow.add_edge("vector_retrieval_node", "ranking_node")
    workflow.add_edge("ranking_node", "narrative_node")
    
    # Both paths converge at narrative, then end
    workflow.add_edge("narrative_node", END)
    
    # Compile
    return workflow.compile()


# Module-level compiled graph (singleton)
_compiled_graph = None


def get_workflow() -> StateGraph:
    """
    Get compiled workflow (singleton pattern).
    
    Returns:
        Compiled StateGraph
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_workflow()
    return _compiled_graph
