/**
 * Zustand authentication store
 * 
 * Manages user authentication state with localStorage persistence
 */

import { create } from 'zustand'
import { getMe } from '../api/auth'

export interface User {
  id: string
  name: string
  email: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (token: string, user: User) => void
  logout: () => void
  initFromStorage: () => Promise<void>
  setError: (error: string | null) => void
}

const AUTH_TOKEN_KEY = 'sr_token'

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: (token: string, user: User) => {
    // Persist token to localStorage
    localStorage.setItem(AUTH_TOKEN_KEY, token)
    
    set({
      user,
      token,
      isAuthenticated: true,
      error: null,
    })
  },

  logout: () => {
    // Remove token from localStorage
    localStorage.removeItem(AUTH_TOKEN_KEY)
    
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    })
  },

  initFromStorage: async () => {
    try {
      // Read token from localStorage
      const token = localStorage.getItem(AUTH_TOKEN_KEY)
      
      if (!token) {
        set({ isLoading: false })
        return
      }
      
      // Fetch user profile with token
      const user = await getMe()
      
      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })
    } catch (error) {
      // Token invalid or expired
      localStorage.removeItem(AUTH_TOKEN_KEY)
      
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      })
    }
  },

  setError: (error: string | null) => {
    set({ error })
  },
}))

// Initialize auth state on app load
useAuthStore.getState().initFromStorage()
