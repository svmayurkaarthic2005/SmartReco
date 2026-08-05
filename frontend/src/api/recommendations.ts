/**
 * Recommendations API endpoints
 */

import { apiClient } from './client'
import { RecommendationOutput, RecommendationHistoryItem } from '../types/recommendation'

/**
 * Get personalized recommendations for current user
 */
export const getMyRecommendations = async (): Promise<RecommendationOutput> => {
  const response = await apiClient.get<RecommendationOutput>('/recommendations/me')
  return response.data
}

/**
 * Force refresh recommendations (ignore cache)
 */
export const refreshRecommendations = async (): Promise<RecommendationOutput> => {
  const response = await apiClient.post<RecommendationOutput>('/recommendations/refresh')
  return response.data
}

/**
 * Get recommendation history
 */
export const getHistory = async (limit: number = 5): Promise<RecommendationHistoryItem[]> => {
  const response = await apiClient.get<RecommendationHistoryItem[]>('/recommendations/history', {
    params: { limit }
  })
  return response.data
}
