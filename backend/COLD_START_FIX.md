# Cold-Start Recommendation Fix

## Problem

Users with **no product interaction history** (only page navigation events) were being recommended **only AI/ML courses** with the narrative "Master AI/ML with structured learning", even though they had no AI/ML interest.

### Root Cause

1. **No product-specific events**: Users had only `VIEW_CATEGORY` and `TIME_ON_PAGE` events for page navigation, with no `product_id` or category data
2. **Empty behavioral data**: `BehaviorAgent` found no categories, product views, enrollments, or searches
3. **Generic semantic query fallback**: `RetrievalPlanner._build_semantic_query()` returned the generic query: `"General professional skill development and career growth"`
4. **Vector search bias**: This generic query semantically matched AI/ML courses in ChromaDB because they're highly relevant to "career growth" and "professional development"
5. **Misleading narrative**: The `NarrativeAgent` fallback used the first recommended product's category (AI/ML) for the learning goal

## Solution

### 1. Detect Cold-Start Scenario (retrieval_agent.py)

Modified `_build_semantic_query()` to return an **empty string** when no meaningful user behavior exists:

```python
def _build_semantic_query(self, summary: BehaviorSummary) -> str:
    parts = []
    
    # Try to build query from user data
    if last_viewed:
        parts.append(f"Next recommendations after viewing: {last_viewed}")
    if enrolled:
        parts.append(f"Advanced progression following enrolled course: ...")
    if summary.categories_explored:
        parts.append(f"Domain focus: {', '.join(top_cats)}")
    
    if parts:
        return ". ".join(parts) + "."
    
    # Cold-start: return empty string to signal diverse sampling
    return ""
```

### 2. Diverse Category Sampling (retrieval_agent.py)

Modified `retrieve()` and `_fallback_retrieve()` to handle empty semantic queries:

```python
async def retrieve(self, plan, db, parent_run_id):
    # Cold-start: no semantic query → skip vector search, use diverse sampling
    if not plan.semantic_query or plan.semantic_query.strip() == "":
        print("Cold-start detected: empty semantic query. Using diverse category sampling.")
        return await self._fallback_retrieve(plan, db)
    
    # Regular path: generate embedding and search vector store
    ...
```

**Diverse sampling strategy:**
- Get all unique categories from the product database
- Sample 2-3 random products from **each category**
- Return up to 15 diverse products across all categories
- Assign neutral similarity score (0.5) since there's no semantic relevance

### 3. Cold-Start Narrative (narrative_agent.py)

Modified `_create_fallback_narrative()` to detect cold-start and create appropriate narrative:

```python
def _create_fallback_narrative(self, summary, persona, ranked_products):
    has_category_history = bool(summary.categories_explored and sum(summary.categories_explored.values()) > 0)
    
    if not has_category_history and ranked_products:
        # Cold-start: diverse recommendations
        unique_categories = list(set(p.category for p in ranked_products[:5]))
        
        if len(unique_categories) >= 3:
            learning_goal = "Explore diverse professional development paths"
            story = (
                f"We've curated a diverse learning journey across {len(unique_categories)} domains including "
                f"{', '.join(unique_categories[:3])}. "
                f"Start with any course that sparks your interest to discover your path forward."
            )
    else:
        # User has history: focus on their dominant interest
        learning_goal = f"Master {top_category} with structured learning"
        story = f"Based on your exploration of {top_category}, ..."
```

## Results

### Before Fix
```
Learning Goal: Master AI/ML with structured learning
Recommended Courses:
  1. [AI/ML] Deep Learning with TensorFlow
  2. [AI/ML] Neural Networks Fundamentals
  3. [AI/ML] Computer Vision Basics
  ...

Category Diversity: 1 unique category (AI/ML only)
```

### After Fix
```
Learning Goal: Explore diverse professional development paths
Recommended Courses:
  1. [Cyber Security] Digital Forensics & Incident Response (DFIR)
  2. [Cyber Security] Cloud Security Architecture
  3. [Data Science] Time Series Analysis and Forecasting
  4. [AI/ML] Prompt Engineering & Fine-Tuning LLMs
  5. [Blockchain] DAO Governance & Tokenomics Design

Category Diversity: 6 unique categories
  - Cyber Security: 2 courses
  - Data Science: 1 course
  - AI/ML: 1 course
  - Blockchain: 1 course
  - Cloud: 1 course
  - Design: 2 courses
```

## Impact

- ✅ Cold-start users now see **diverse recommendations** across multiple domains
- ✅ Narrative accurately reflects the **exploration phase** of the learning journey
- ✅ No bias toward AI/ML or any single category
- ✅ Users can discover interests through browsing diverse options
- ✅ Maintains semantic relevance for users with behavioral history

## Testing

Run the test script to verify cold-start behavior:

```bash
cd backend
python test_cold_start.py
```

Expected output:
- "Cold-start detected: empty semantic query. Using diverse category sampling."
- 5-8 unique categories in recommendations
- Learning goal: "Explore diverse professional development paths"

## Files Modified

1. `app/agents/retrieval_agent.py`
   - `_build_semantic_query()`: Return empty string for cold-start
   - `retrieve()`: Detect and handle empty semantic query
   - `_fallback_retrieve()`: Implement diverse category sampling

2. `app/agents/narrative_agent.py`
   - `_create_fallback_narrative()`: Detect cold-start and create diverse exploration narrative

3. `test_cold_start.py` (new)
   - Test script to verify cold-start recommendation behavior
