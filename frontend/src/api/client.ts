/**
 * Axios HTTP client with authentication interceptors
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../store/authStore'

// In development, use an empty baseURL so requests go through Vite's proxy (avoids CORS).
// In production, VITE_API_BASE_URL should be set to the deployed backend URL.
const API_BASE_URL = import.meta.env.PROD
  ? (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')
  : ''

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

// Request interceptor - attach auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // If Authorization header is already set, don't overwrite it
    if (!config.headers.Authorization) {
      const token = useAuthStore.getState().token || localStorage.getItem('sr_token')
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Only auto-logout on 401s from protected endpoints.
    // Auth endpoints (/auth/login, /auth/register) return 401 for invalid
    // credentials — those should be handled by the calling code, not redirected.
    const isAuthEndpoint = error.config?.url?.startsWith('/auth/login') ||
                           error.config?.url?.startsWith('/auth/register')

    if (error.response?.status === 401 && !isAuthEndpoint) {
      // Token expired or invalid - logout and redirect
      const authStore = useAuthStore.getState()
      authStore.logout()
      
      // Redirect to login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?expired=true'
      }
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
