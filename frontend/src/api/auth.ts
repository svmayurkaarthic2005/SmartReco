/**
 * Authentication API endpoints
 */

import { apiClient } from './client'
import { User } from '../store/authStore'

export interface RegisterPayload {
  name: string
  email: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  role: string
  name: string
}

export interface UserProfile {
  id: string
  name: string
  email: string
  role: string
  created_at: string
}

/**
 * Register a new user
 */
export const register = async (data: RegisterPayload): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/register', data)
  return response.data
}

/**
 * Login with email and password
 */
export const login = async (data: LoginPayload): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/login', data)
  return response.data
}

/**
 * Get current user profile
 */
export const getMe = async (token?: string): Promise<User> => {
  // When a fresh token is passed (right after login/register), set it explicitly.
  // Otherwise the request interceptor will use the stored token.
  const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {}
  const response = await apiClient.get<UserProfile>('/auth/me', config)
  
  return {
    id: response.data.id,
    name: response.data.name,
    email: response.data.email,
    role: response.data.role,
  }
}



/**
 * Refresh access token
 */
export const refreshToken = async (refreshToken: string): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  })
  return response.data
}
