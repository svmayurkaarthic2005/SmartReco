/**
 * Recommendation TypeScript interfaces
 * Matching backend response schemas
 */

export interface RankedProduct {
  product_id: string
  title: string
  description: string
  category: string
  difficulty: string
  price: number
  tags: string[]
  final_score: number
  rank_position: number
  score_breakdown: {
    semantic: number
    difficulty_match: number
    learning_progression: number
    price_fit: number
    tag_overlap: number
    freshness: number
  }
}

export interface NarrativeResult {
  persona_display: string
  learning_goal: string
  personalized_story: string
  roadmap: string[]
  product_explanations: Record<string, string>
  motivational_cta: string
}

export interface RecoveryResult {
  is_at_risk: boolean
  recovery_narrative: string
  email_subject: string
  email_body: string
}

export interface RecommendationOutput {
  user_id: string
  persona: string
  confidence: number
  learning_goal: string
  personalized_story: string
  roadmap: string[]
  product_explanations: Record<string, string>
  motivational_cta: string
  ranked_products: RankedProduct[]
  recovery_result: RecoveryResult | null
  is_recovery_mode: boolean
  generated_at: string
  trace_id: string
}

export interface RecommendationHistoryItem {
  id: string
  persona: string
  confidence: number
  product_count: number
  generated_at: string
}
