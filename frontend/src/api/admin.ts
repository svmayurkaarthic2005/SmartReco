/**
 * Admin API endpoints
 */

import { apiClient } from './client'
import {
  AdminStats,
  PersonaDistribution,
  EventVolumePoint,
  Product,
  ProductListResponse,
  CreateProductPayload,
  AdminUser,
  TraceRecord,
  RecentRecommendation,
} from '../types/admin'

// ============================================================================
// Dashboard Stats
// ============================================================================

export const getStats = async (): Promise<AdminStats> => {
  const response = await apiClient.get<AdminStats>('/admin/stats')
  return response.data
}

export const getPersonaDistribution = async (): Promise<PersonaDistribution> => {
  const response = await apiClient.get<PersonaDistribution>('/admin/persona-distribution')
  return response.data
}

export const getEventVolume = async (hours: number = 24): Promise<EventVolumePoint[]> => {
  const response = await apiClient.get<EventVolumePoint[]>('/admin/event-volume', {
    params: { hours }
  })
  return response.data
}

export const getRecentRecommendations = async (limit: number = 10): Promise<RecentRecommendation[]> => {
  const response = await apiClient.get<RecentRecommendation[]>('/admin/recent-recommendations', {
    params: { limit }
  })
  return response.data
}

// ============================================================================
// Products
// ============================================================================

export const getProducts = async (params: {
  page?: number
  page_size?: number
  search?: string
  category?: string
  difficulty?: string
  embedding_status?: string
}): Promise<ProductListResponse> => {
  const response = await apiClient.get<ProductListResponse>('/admin/products', { params })
  return response.data
}

export const createProduct = async (data: CreateProductPayload): Promise<Product> => {
  const response = await apiClient.post<Product>('/admin/products', data)
  return response.data
}

export const updateProduct = async (id: string, data: Partial<CreateProductPayload>): Promise<Product> => {
  const response = await apiClient.put<Product>(`/admin/products/${id}`, data)
  return response.data
}

export const deleteProduct = async (id: string): Promise<void> => {
  await apiClient.delete(`/admin/products/${id}`)
}

export const reembedProduct = async (id: string): Promise<void> => {
  await apiClient.post(`/admin/products/${id}/re-embed`)
}

export const retryFailedEmbeddings = async (): Promise<{ count: number }> => {
  const response = await apiClient.post<{ count: number }>('/admin/embeddings/retry-failed')
  return response.data
}

// ============================================================================
// Users
// ============================================================================

export const getUsers = async (params: {
  page?: number
  page_size?: number
  search?: string
  role?: string
}): Promise<{ users: AdminUser[]; total: number }> => {
  const response = await apiClient.get('/admin/users', { params })
  return response.data
}

export const updateUserRole = async (userId: string, role: string): Promise<AdminUser> => {
  const response = await apiClient.patch<AdminUser>(`/admin/users/${userId}/role`, { role })
  return response.data
}

// ============================================================================
// Traces
// ============================================================================

export const getLangSmithTraces = async (params: {
  limit?: number
  status?: string
}): Promise<TraceRecord[]> => {
  const response = await apiClient.get<TraceRecord[]>('/admin/traces', { params })
  return response.data
}
