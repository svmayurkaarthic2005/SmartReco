/**
 * React Query hook for recommendations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMyRecommendations, refreshRecommendations, getHistory } from '../api/recommendations'

export const useRecommendations = () => {
  const queryClient = useQueryClient()

  // Fetch recommendations with 5-minute stale time
  const recommendationsQuery = useQuery({
    queryKey: ['recommendations'],
    queryFn: getMyRecommendations,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })

  // Refresh mutation
  const refreshMutation = useMutation({
    mutationFn: refreshRecommendations,
    onSuccess: (data) => {
      // Update cache with new data
      queryClient.setQueryData(['recommendations'], data)
      // Invalidate to refetch
      queryClient.invalidateQueries({ queryKey: ['recommendations'] })
    },
  })

  // History query
  const historyQuery = useQuery({
    queryKey: ['recommendations', 'history'],
    queryFn: () => getHistory(5),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })

  return {
    // Recommendations
    recommendations: recommendationsQuery.data,
    isLoading: recommendationsQuery.isLoading,
    isError: recommendationsQuery.isError,
    error: recommendationsQuery.error,
    
    // Refresh
    refresh: refreshMutation.mutate,
    isRefreshing: refreshMutation.isPending,
    
    // History
    history: historyQuery.data,
    isLoadingHistory: historyQuery.isLoading,
  }
}
