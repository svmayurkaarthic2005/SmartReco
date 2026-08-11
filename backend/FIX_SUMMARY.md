# AI Recommendation Fix Summary

## Problem
User enrolled in **2 courses**:
- NFT Marketplace Development (Blockchain)
- Natural Language Processing with Transformers (AI/ML)

But recommendations show **ONLY AI/ML courses** (4 out of 8 top recommendations), with **ZERO Blockchain courses**, even though the user is actively enrolled in a Blockchain course.

## Root Causes

### 1. Category Filter Too Aggressive (FIXED ✅)
- Old logic: Applied filter when one category had >= 40% weight OR > 100 points
- User had: AI/ML (1013 points, 52%) vs Blockchain (943 points, 48%)
- Result: Only AI/ML courses retrieved
- **Fix**: Changed threshold to 70% to avoid filtering multi-interest users

### 2. Fallback Narrative Ignores Multi-Interest (FIXED ✅)
- Old logic: Always used the dominant category for learning goal
- Result: "Master AI/ML" even though user has both AI/ML and Blockchain interests
- **Fix**: Detect multi-category enrollments and create cross-domain narrative
- New narrative: "Advance your skills in AI/ML and Blockchain"

### 3. Semantic Query Not Balanced (FIXED ✅)
- Old logic: Listed enrolled courses but didn't emphasize category diversity
- Result: Vector search biased toward AI/ML
- **Fix**: Explicitly mention both enrolled categories in the query
- New query: "Advanced courses in AI/ML and Blockchain to complement current enrollments..."

### 4. Vector Search Still Not Finding Blockchain Courses (REMAINING ISSUE ❌)
- Even with "Blockchain" explicitly in the semantic query, vector search returns 20 candidates with ZERO Blockchain courses
- Possible causes:
  - Vector embeddings not properly matching Blockchain keywords
  - Chroma DB not properly configured
  - Enrolled Blockchain course being excluded before vector search

## Current Status

**Narrative**: ✅ Fixed - now says "Advance your skills in AI/ML and Blockchain"

**Recommendations**: ❌ Still broken - showing 4 AI/ML courses, 0 Blockchain courses

## Next Steps

Need to implement **category diversity enforcement** at the ranking stage:
1. After vector retrieval, check enrolled categories
2. If no courses from an enrolled category, fetch 1-2 courses from that category directly from DB
3. Inject them into the candidates before ranking
4. Ensure final recommendations have at least 1 course from each enrolled category

This ensures users with multi-category interests get balanced recommendations.
