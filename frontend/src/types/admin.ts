/**
 * Admin TypeScript interfaces
 */

export interface AdminStats {
  total_users: number
  total_events_7d: number
  total_recommendations: number
  ai_calls: number
  drop_off_risk_count: number
  embedding_failures: number
}

export interface PersonaDistribution {
  [persona: string]: number
}

export interface EventVolumePoint {
  hour: string
  count: number
}

export interface Product {
  id: string
  title: string
  description: string
  category: string
  difficulty: string
  price: number
  duration_hours: number
  tags: string[]
  embedding_status: 'indexed' | 'pending' | 'failed'
  created_at: string
  updated_at: string
}

export interface ProductListResponse {
  products: Product[]
  total: number
  page: number
  page_size: number
}

export interface CreateProductPayload {
  title: string
  description: string
  category: string
  difficulty: string
  price: number
  duration_hours: number
  tags: string[]
}

export interface AdminUser {
  id: string
  name: string
  email: string
  role: string
  created_at: string
  total_events: number
  last_activity: string | null
}

export interface TraceRecord {
  run_id: string
  name: string
  status: 'success' | 'error' | 'pending'
  latency_ms: number
  token_usage: number
  timestamp: string
  inputs?: any
  outputs?: any
  error?: string
  run_type?: string
  total_cost?: number
  prompt_tokens?: number
  completion_tokens?: number
  url?: string
}

export interface RecentRecommendation {
  id: string
  user_id: string
  user_name: string
  persona: string
  confidence: number
  product_count: number
  generated_at: string
}
