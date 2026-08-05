/**
 * Events API endpoints
 */

import { apiClient } from './client'

export interface EventCreatePayload {
  user_id: string
  session_id: string
  event_type: 'view_product' | 'view_category' | 'click' | 'search' | 'dwell_time' | 'enroll' | 'scroll' | 'time_on_page'
  product_id?: string
  search_query?: string
  dwell_time?: number
  event_metadata?: Record<string, any>
  timestamp?: string
}

export interface UserEvent {
  id: string
  user_id: string
  session_id: string
  event_type: string
  product_id?: string
  search_query?: string
  dwell_time?: number
  metadata?: Record<string, any>
  timestamp: string
}

export interface EventHashResponse {
  user_id: string
  event_hash: string
  event_count: number
}

/**
 * Submit a single event
 */
export const trackEvent = async (event: EventCreatePayload): Promise<any> => {
  try {
    const payload = {
      ...event,
      timestamp: event.timestamp || new Date().toISOString()
    }
    const response = await apiClient.post('/events/single', payload)
    return response.data
  } catch (error) {
    console.warn('Failed to send event:', error)
    return null
  }
}

/**
 * Get user events
 */
export const getMyEvents = async (limit: number = 50): Promise<UserEvent[]> => {
  try {
    const response = await apiClient.get<UserEvent[]>('/events/me', { params: { limit } })
    return response.data
  } catch (error) {
    return []
  }
}

/**
 * Get event hash and metrics
 */
export const getMyEventHash = async (): Promise<EventHashResponse | null> => {
  try {
    const response = await apiClient.get<EventHashResponse>('/events/me/hash')
    return response.data
  } catch (error) {
    return null
  }
}
